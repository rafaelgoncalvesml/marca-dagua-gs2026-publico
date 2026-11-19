"""Lambda de ingestão do Marca d'Água (API Gateway HTTP API -> Lambda -> DynamoDB).

Recebe POST /leituras com o mesmo JSON da API FastAPI, valida, classifica,
grava no DynamoDB e publica métricas no CloudWatch (formato EMF, via log).
Um alarme do CloudWatch sobre a métrica "Alertas" aciona o SNS.

Segurança por padrão:
- chave por dispositivo no cabeçalho x-api-key (lida do ambiente, nunca do código);
- comparação em tempo constante e resposta 401 igual para chave ausente, errada
  ou dispositivo desconhecido;
- limite de tamanho do corpo e validação de todos os campos antes de gravar;
- a classificação de risco é sempre refeita aqui (o que o nó mandar é ignorado);
- nenhuma chave nem corpo completo vai para o log.

Variáveis de ambiente:
  TABELA       nome da tabela do DynamoDB (padrão marca_dagua_leituras)
  DEVICE_KEYS  JSON com {"device_id": "chave"}
"""
import base64
import hmac
import json
import math
import os
import re
import time
from datetime import datetime
from decimal import Decimal

LIMITE_CORPO_BYTES = 2048
DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

# campo -> (mínimo, máximo), mesmos limites da API FastAPI
FAIXAS = {
    "nivel_cm": (0, 1000),
    "chuva_mm_h": (0, 500),
    "temperatura_c": (-20, 60),
    "umidade_pct": (0, 100),
}

# campo -> (limiar de ATENCAO, limiar de ALERTA); valor >= limiar entra na faixa.
# Manter igual a python-api/classificacao.py (limiares ainda provisórios).
LIMIARES = {"nivel_cm": (120, 180), "chuva_mm_h": (15, 30), "umidade_pct": (90, 95)}
SENSORES = {"nivel": "nivel_cm", "chuva": "chuva_mm_h", "umidade": "umidade_pct"}
ORDEM = ("OK", "ATENCAO", "ALERTA")


# ---------------------------------------------------------------- validação
def _numero(valor) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)


def validar(dados: dict) -> list[str]:
    """Devolve a lista de erros; vazia quando a leitura é válida."""
    erros = []
    if not (isinstance(dados.get("device_id"), str) and DEVICE_ID_RE.match(dados["device_id"])):
        erros.append("device_id: 1 a 40 caracteres entre letras, números, '-' e '_'")

    seq = dados.get("seq")
    if not (isinstance(seq, int) and not isinstance(seq, bool) and seq >= 0):
        erros.append("seq: inteiro maior ou igual a 0")

    ts = dados.get("ts")
    try:
        if not isinstance(ts, str) or datetime.fromisoformat(ts).tzinfo is None:
            raise ValueError
    except ValueError:
        erros.append("ts: data e hora ISO 8601 com fuso, como 2026-11-10T14:32:05-03:00")

    for campo, (minimo, maximo) in FAIXAS.items():
        valor = dados.get(campo)
        if not (_numero(valor) and minimo <= valor <= maximo):
            erros.append(f"{campo}: número de {minimo} a {maximo}")

    if "reenviado" in dados and not isinstance(dados["reenviado"], bool):
        erros.append("reenviado: verdadeiro ou falso")
    return erros


def classificar(dados: dict) -> dict:
    """Cada sensor vira OK, ATENCAO ou ALERTA e o risco é o pior deles."""
    status = {}
    for nome, campo in SENSORES.items():
        atencao, alerta = LIMIARES[campo]
        valor = dados[campo]
        status[nome] = "ALERTA" if valor >= alerta else "ATENCAO" if valor >= atencao else "OK"
    return {"status": status, "risco": max(status.values(), key=ORDEM.index)}


# ----------------------------------------------------------------- métricas
def emitir_metricas(registro: dict) -> None:
    """Escreve métricas no formato EMF; o CloudWatch as lê dos logs da função."""
    alerta = registro["risco"] == "ALERTA"
    print(json.dumps({
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [{
                "Namespace": "MarcaDagua",
                "Dimensions": [["DeviceId"]],
                "Metrics": [
                    {"Name": "Leituras", "Unit": "Count"},
                    {"Name": "Alertas", "Unit": "Count"},
                    {"Name": "NivelCm", "Unit": "None"},
                ],
            }],
        },
        "DeviceId": registro["device_id"],
        "Leituras": 1,
        "Alertas": 1 if alerta else 0,
        "NivelCm": registro["nivel_cm"],
    }))


# ------------------------------------------------------------------ gravação
def gravar_dynamodb(tabela, item: dict) -> bool:
    """Grava a leitura; devolve False se (device_id, seq) já existir."""
    from botocore.exceptions import ClientError  # já vem no runtime da Lambda

    paraDecimal = lambda v: Decimal(str(v)) if isinstance(v, float) else v  # DynamoDB não aceita float
    try:
        tabela.put_item(
            Item={k: paraDecimal(v) for k, v in item.items()},
            ConditionExpression="attribute_not_exists(device_id)",
        )
        return True
    except ClientError as erro:
        if erro.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


# ----------------------------------------------------------------- principal
def _resposta(codigo: int, corpo: dict) -> dict:
    return {
        "statusCode": codigo,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(corpo, ensure_ascii=False),
    }


def processar(evento: dict, chaves: dict, gravar) -> dict:
    """Lógica da ingestão, separada do handler para testar sem AWS."""
    http = evento.get("requestContext", {}).get("http", {})
    if http.get("method") != "POST":
        return _resposta(405, {"erro": "use POST /leituras"})

    corpo = evento.get("body") or ""
    if evento.get("isBase64Encoded"):
        corpo = base64.b64decode(corpo).decode("utf-8", errors="replace")
    if len(corpo.encode("utf-8")) > LIMITE_CORPO_BYTES:
        return _resposta(413, {"erro": "corpo maior que o limite"})
    try:
        dados = json.loads(corpo)
        if not isinstance(dados, dict):
            raise ValueError
    except ValueError:
        return _resposta(400, {"erro": "corpo precisa ser um JSON de objeto"})

    # autenticação antes da validação: quem não tem chave não sonda as regras
    cabecalhos = {k.lower(): v for k, v in (evento.get("headers") or {}).items()}
    enviada = cabecalhos.get("x-api-key", "")
    esperada = chaves.get(dados.get("device_id") if isinstance(dados.get("device_id"), str) else "", "")
    if not esperada or not hmac.compare_digest(enviada.encode(), esperada.encode()):
        return _resposta(401, {"erro": "não autorizado"})

    erros = validar(dados)
    if erros:
        return _resposta(422, {"erros": erros})

    registro = {
        "device_id": dados["device_id"],
        "seq": dados["seq"],
        "ts": dados["ts"],
        "nivel_cm": dados["nivel_cm"],
        "chuva_mm_h": dados["chuva_mm_h"],
        "temperatura_c": dados["temperatura_c"],
        "umidade_pct": dados["umidade_pct"],
        "reenviado": dados.get("reenviado", False),
        **classificar(dados),
    }
    if not gravar(registro):
        return _resposta(409, {"erro": f"leitura {registro['device_id']}/{registro['seq']} já recebida"})

    emitir_metricas(registro)
    print(f"leitura {registro['device_id']}/{registro['seq']} risco={registro['risco']}")
    return _resposta(201, registro)


def lambda_handler(evento, contexto):
    import boto3  # já vem no runtime da Lambda

    tabela = boto3.resource("dynamodb").Table(os.environ.get("TABELA", "marca_dagua_leituras"))
    chaves = json.loads(os.environ.get("DEVICE_KEYS", "{}"))
    return processar(evento, chaves, lambda item: gravar_dynamodb(tabela, item))

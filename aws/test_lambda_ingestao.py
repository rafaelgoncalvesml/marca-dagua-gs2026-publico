"""Testes locais da Lambda de ingestão (sem AWS). Rode com: pytest"""
import base64
import json

import pytest

import lambda_ingestao as li

CHAVES = {"MD-POA-001": "chave-de-teste"}
BASE = {
    "device_id": "MD-POA-001", "seq": 1, "ts": "2026-11-10T14:32:05-03:00",
    "nivel_cm": 45.0, "chuva_mm_h": 0.4, "temperatura_c": 24.1, "umidade_pct": 62.0,
}


class Banco:
    """Gravador falso: imita a regra de (device_id, seq) único."""
    def __init__(self):
        self.itens = {}

    def __call__(self, item):
        chave = (item["device_id"], item["seq"])
        if chave in self.itens:
            return False
        self.itens[chave] = item
        return True


def evento(corpo, chave="chave-de-teste", metodo="POST", base64_=False):
    texto = corpo if isinstance(corpo, str) else json.dumps(corpo)
    if base64_:
        texto = base64.b64encode(texto.encode()).decode()
    cab = {"Content-Type": "application/json"}
    if chave is not None:
        cab["X-Api-Key"] = chave
    return {"requestContext": {"http": {"method": metodo}}, "headers": cab,
            "body": texto, "isBase64Encoded": base64_}


def chamar(corpo, banco=None, **kw):
    banco = banco if banco is not None else Banco()
    resp = li.processar(evento(corpo, **kw), CHAVES, banco)
    return resp["statusCode"], json.loads(resp["body"]), banco


@pytest.mark.parametrize("campos, risco", [
    ({}, "OK"),
    ({"nivel_cm": 135.0, "chuva_mm_h": 18.0, "umidade_pct": 91.0}, "ATENCAO"),
    ({"nivel_cm": 195.5, "chuva_mm_h": 42.0, "umidade_pct": 97.0}, "ALERTA"),
])
def test_cenarios_gravam_e_classificam(campos, risco):
    codigo, corpo, banco = chamar({**BASE, **campos})
    assert codigo == 201 and corpo["risco"] == risco
    assert len(banco.itens) == 1


def test_pior_sensor_define_o_risco():
    _, corpo, _ = chamar({**BASE, "nivel_cm": 200.0})
    assert corpo["status"] == {"nivel": "ALERTA", "chuva": "OK", "umidade": "OK"}
    assert corpo["risco"] == "ALERTA"


def test_risco_enviado_pelo_no_e_ignorado():
    _, corpo, _ = chamar({**BASE, "nivel_cm": 200.0, "risco": "OK", "status": {"nivel": "OK"}})
    assert corpo["risco"] == "ALERTA"


@pytest.mark.parametrize("chave", [None, "", "errada"])
def test_chave_ausente_ou_errada_da_401(chave):
    codigo, _, banco = chamar(BASE, chave=chave)
    assert codigo == 401 and not banco.itens


def test_dispositivo_desconhecido_da_401_igual():
    codigo, corpo, _ = chamar({**BASE, "device_id": "MD-XXX-999"})
    assert codigo == 401 and corpo == {"erro": "não autorizado"}


def test_cabecalho_sem_diferenca_de_maiusculas():
    ev = evento(BASE)
    ev["headers"] = {"x-api-key": "chave-de-teste"}
    assert li.processar(ev, CHAVES, Banco())["statusCode"] == 201


@pytest.mark.parametrize("campo, valor", [
    ("nivel_cm", 1001), ("nivel_cm", -1), ("chuva_mm_h", 501), ("temperatura_c", 61),
    ("umidade_pct", 101), ("seq", -1), ("seq", "1"), ("seq", True),
    ("ts", "2026-11-10T14:32:05"), ("ts", "ontem"), ("nivel_cm", "45"), ("nivel_cm", float("nan")),
    ("reenviado", "sim"),
])
def test_valores_invalidos_dao_422_e_nao_gravam(campo, valor):
    codigo, corpo, banco = chamar({**BASE, campo: valor})
    assert codigo == 422 and campo in " ".join(corpo["erros"]) and not banco.itens


def test_campo_obrigatorio_ausente_da_422():
    dados = {k: v for k, v in BASE.items() if k != "umidade_pct"}
    codigo, _, _ = chamar(dados)
    assert codigo == 422


def test_leitura_repetida_da_409_e_nao_duplica():
    banco = Banco()
    assert chamar(BASE, banco=banco)[0] == 201
    assert chamar(BASE, banco=banco)[0] == 409
    assert len(banco.itens) == 1


def test_corpo_grande_da_413():
    assert chamar({**BASE, "lixo": "x" * 3000})[0] == 413


@pytest.mark.parametrize("corpo", ["não é json", "[1, 2]", "", "null"])
def test_corpo_que_nao_e_objeto_da_400(corpo):
    assert chamar(corpo)[0] == 400


def test_so_aceita_post():
    resp = li.processar(evento(BASE, metodo="GET"), CHAVES, Banco())
    assert resp["statusCode"] == 405


def test_corpo_em_base64():
    assert chamar(BASE, base64_=True)[0] == 201


def test_metrica_emf_so_conta_alerta_quando_ha_alerta(capsys):
    chamar({**BASE, "seq": 1})
    chamar({**BASE, "seq": 2, "nivel_cm": 195.5})
    linhas = [json.loads(l) for l in capsys.readouterr().out.splitlines() if l.startswith("{")]
    assert [l["Alertas"] for l in linhas] == [0, 1]
    assert linhas[0]["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "MarcaDagua"
    assert linhas[1]["DeviceId"] == "MD-POA-001" and linhas[1]["NivelCm"] == 195.5


def test_log_nao_vaza_a_chave(capsys):
    chamar(BASE)
    assert "chave-de-teste" not in capsys.readouterr().out

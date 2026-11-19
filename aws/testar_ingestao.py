"""Envia os 3 cenários (normal, atenção, alerta) à API publicada na AWS.

Uso:
  export API_URL="https://<id>.execute-api.sa-east-1.amazonaws.com/leituras"
  export DEVICE_ID="MD-POA-001"
  export DEVICE_KEY="<chave do dispositivo>"
  python testar_ingestao.py

A chave vem do ambiente para não ficar no código nem no histórico do Git.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

CENARIOS = {
    "normal":  dict(nivel_cm=45.0,  chuva_mm_h=0.4,  temperatura_c=24.1, umidade_pct=62.0),
    "atencao": dict(nivel_cm=135.0, chuva_mm_h=18.0, temperatura_c=22.0, umidade_pct=91.0),
    "alerta":  dict(nivel_cm=195.5, chuva_mm_h=42.0, temperatura_c=20.3, umidade_pct=97.0),
}


def enviar(url: str, chave: str, corpo: dict) -> tuple[int, str]:
    req = urllib.request.Request(
        url, data=json.dumps(corpo).encode(), method="POST",
        headers={"Content-Type": "application/json", "x-api-key": chave},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as erro:  # 4xx/5xx também interessam ao teste
        return erro.code, erro.read().decode()


def main() -> int:
    try:
        url, device, chave = (os.environ[k] for k in ("API_URL", "DEVICE_ID", "DEVICE_KEY"))
    except KeyError as faltando:
        print(f"defina a variável de ambiente {faltando}")
        return 2

    fuso = timezone(timedelta(hours=-3))
    seq = int(time.time())  # seq crescente evita 409 em execuções repetidas
    falhas = 0
    for i, (nome, medidas) in enumerate(CENARIOS.items()):
        corpo = {"device_id": device, "seq": seq + i,
                 "ts": datetime.now(fuso).isoformat(timespec="seconds"), **medidas}
        codigo, texto = enviar(url, chave, corpo)
        risco = json.loads(texto).get("risco", "-") if codigo == 201 else "-"
        print(f"{nome:8} -> HTTP {codigo} risco={risco}")
        falhas += codigo != 201

    # deve ser rejeitada: reenvio da mesma leitura
    codigo, _ = enviar(url, chave, corpo)
    print(f"repetida -> HTTP {codigo} (esperado 409)")
    falhas += codigo != 409

    # deve ser rejeitada: chave errada
    codigo, _ = enviar(url, "chave-errada", {**corpo, "seq": seq + 99})
    print(f"sem auth -> HTTP {codigo} (esperado 401)")
    falhas += codigo != 401
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())

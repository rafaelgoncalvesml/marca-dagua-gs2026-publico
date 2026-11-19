"""Roda os 3 cenários (normal, atenção e alerta) contra a API no ar e mostra o resultado.

Uso: python cenarios.py [URL_DA_API]   (padrão http://127.0.0.1:8000)

A API pede chave. Defina MD_API_KEY (a chave do dispositivo MD-POA-001) e MD_READ_KEY (a de leitura)
no terminal antes de rodar.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# nome -> (corpo do POST sem seq e ts, risco esperado)
CENARIOS = {
    "normal": (
        {"device_id": "MD-POA-001", "nivel_cm": 45.0, "chuva_mm_h": 0.4, "temperatura_c": 24.1, "umidade_pct": 62.0},
        "OK",
    ),
    "atencao": (
        {"device_id": "MD-POA-001", "nivel_cm": 135.0, "chuva_mm_h": 24.0, "temperatura_c": 22.5, "umidade_pct": 91.0},
        "ATENCAO",
    ),
    "alerta": (
        {"device_id": "MD-POA-001", "nivel_cm": 195.5, "chuva_mm_h": 60.0, "temperatura_c": 21.0, "umidade_pct": 97.0},
        "ALERTA",
    ),
}


def chamar(metodo: str, url: str, corpo: dict | None = None, cabecalhos: dict | None = None) -> tuple[int, dict]:
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={"Content-Type": "application/json", **(cabecalhos or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main(base: str) -> int:
    chave, leitura = os.environ.get("MD_API_KEY"), os.environ.get("MD_READ_KEY")
    if not chave or not leitura:
        print("Defina MD_API_KEY e MD_READ_KEY no terminal antes de rodar (veja o README).")
        return 2
    seq = int(time.time())  # seq novo a cada execução, para o reenvio não cair no 409
    falhas = 0
    for nome, (corpo, esperado) in CENARIOS.items():
        seq += 1
        ts = datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="seconds")
        codigo, resp = chamar("POST", f"{base}/leituras", {**corpo, "seq": seq, "ts": ts},
                               {"X-API-Key": chave})
        ok = codigo == 201 and resp.get("risco") == esperado
        falhas += not ok
        print(f"[{'OK' if ok else 'FALHOU'}] {nome}: HTTP {codigo}, esperado {esperado}")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    print("\nIndicadores:")
    print(json.dumps(chamar("GET", f"{base}/indicadores", cabecalhos={"X-Read-Key": leitura})[1], ensure_ascii=False, indent=2))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"))

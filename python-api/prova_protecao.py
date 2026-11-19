"""Prova a proteção da API com a API no ar e mostra um quadro para o print.

Uso: python prova_protecao.py [URL_DA_API]   (padrão http://127.0.0.1:8000)

Variáveis: MD_API_KEY (chave do MD-POA-001), MD_READ_KEY (chave de leitura) e, se mudou o limite
da API, MD_LIMITE_POR_MINUTO. Rode logo depois de subir a API: o limite vale por minuto.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


def chamar(metodo, url, corpo=None, cabecalhos=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    cab = {"Content-Type": "application/json", **(cabecalhos or {})}
    req = urllib.request.Request(url, data=dados, method=metodo, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)


def leitura(seq, device_id="MD-POA-001"):
    ts = datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="seconds")
    return {"device_id": device_id, "seq": seq, "ts": ts, "nivel_cm": 45.0, "chuva_mm_h": 0.4,
            "temperatura_c": 24.0, "umidade_pct": 62.0}


def main(base):
    chave, leitura_key = os.environ.get("MD_API_KEY"), os.environ.get("MD_READ_KEY")
    if not chave or not leitura_key:
        print("Defina MD_API_KEY e MD_READ_KEY no terminal antes de rodar.")
        return 2
    limite = int(os.environ.get("MD_LIMITE_POR_MINUTO") or 60)
    seq = int(time.time())
    falhas = 0

    def passo(descricao, esperado, resultado):
        nonlocal falhas
        codigo = resultado[0]
        ok = codigo == esperado
        falhas += not ok
        print(f"[{'OK' if ok else 'FALHOU'}] {descricao:<58} HTTP {codigo} (esperado {esperado})")

    print(f"API em {base}, limite de {limite} requisições por minuto\n")
    passo("GET /health, aberto, sem chave", 200, chamar("GET", f"{base}/health"))
    passo("POST sem chave", 401, chamar("POST", f"{base}/leituras", leitura(seq)))
    passo("POST com chave errada", 401, chamar("POST", f"{base}/leituras", leitura(seq), {"X-API-Key": "chave-errada"}))
    passo("POST com a chave do dispositivo", 201, chamar("POST", f"{base}/leituras", leitura(seq + 1), {"X-API-Key": chave}))
    passo("POST com a chave, mas em nome de outro dispositivo", 403,
          chamar("POST", f"{base}/leituras", leitura(seq + 2, "MD-POA-099"), {"X-API-Key": chave}))
    grande = {**leitura(seq + 3), "status": {"x": "a" * 9000}}
    passo("POST com corpo acima de 8 KB", 413, chamar("POST", f"{base}/leituras", grande, {"X-API-Key": chave}))
    passo("GET /leituras sem chave de leitura", 401, chamar("GET", f"{base}/leituras"))
    passo("GET /leituras com a chave de leitura", 200, chamar("GET", f"{base}/leituras", cabecalhos={"X-Read-Key": leitura_key}))

    print(f"\nRajada: {limite + 5} POSTs seguidos com a chave certa")
    codigos, primeiro_429, espera = [], None, None
    for i in range(limite + 5):
        codigo, cab = chamar("POST", f"{base}/leituras", leitura(seq + 100 + i), {"X-API-Key": chave})
        codigos.append(codigo)
        if codigo == 429 and primeiro_429 is None:
            primeiro_429, espera = i + 1, cab.get("Retry-After") or cab.get("retry-after")
    mostrar = {1, 2, 3, len(codigos)}
    if primeiro_429:
        mostrar |= {primeiro_429 - 1, primeiro_429, primeiro_429 + 1}
    for n in sorted(m for m in mostrar if 1 <= m <= len(codigos)):
        print(f"  chamada {n:>3}: HTTP {codigos[n - 1]}")
    ok = primeiro_429 is not None
    falhas += not ok
    print(f"[{'OK' if ok else 'FALHOU'}] primeiro 429 na chamada {primeiro_429} desta rajada, Retry-After de {espera} s")
    print("\n" + ("Tudo como esperado." if not falhas else f"{falhas} verificação(ões) fora do esperado."))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"))

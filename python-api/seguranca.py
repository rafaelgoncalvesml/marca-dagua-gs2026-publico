"""Proteção da API: chave por dispositivo, chave de leitura, limite de requisições e de tamanho.

Variáveis de ambiente (nunca no código):
  MD_API_KEYS          pares dispositivo:chave separados por vírgula (MD-POA-001:abc,MD-POA-002:def)
  MD_READ_KEY          chave de quem consulta o histórico
  MD_LIMITE_POR_MINUTO requisições por minuto de cada chave (padrão 60)
"""
import hmac
import math
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse

LIMITE_PADRAO = 60
JANELA_S = 60
TAMANHO_MAX = 8192  # bytes; a Lambda aceita 8000 caracteres

agora = time.monotonic  # os testes trocam o relógio


def chaves_dos_dispositivos() -> dict[str, str]:
    pares = {}
    for item in os.environ.get("MD_API_KEYS", "").split(","):
        dispositivo, sep, chave = item.strip().partition(":")
        if sep and dispositivo and chave:
            pares[dispositivo] = chave
    return pares


def exige_configuracao():
    if not chaves_dos_dispositivos():
        raise RuntimeError("defina MD_API_KEYS (dispositivo:chave, separados por vírgula) antes de subir a API")
    if not os.environ.get("MD_READ_KEY"):
        raise RuntimeError("defina MD_READ_KEY antes de subir a API")


def _igual(a: str, b: str) -> bool:
    # tempo constante, e em bytes porque compare_digest recusa texto fora do ASCII
    return hmac.compare_digest(a.encode(), b.encode())


def dono_da_chave(chave: str | None) -> str | None:
    if not chave:
        return None
    achado = None
    for dispositivo, esperada in chaves_dos_dispositivos().items():
        if _igual(chave, esperada):
            achado = dispositivo
    return achado


class LimiteJanela:
    def __init__(self):
        self._eventos = defaultdict(deque)
        self._trava = threading.Lock()

    @staticmethod
    def limite() -> int:
        return int(os.environ.get("MD_LIMITE_POR_MINUTO") or LIMITE_PADRAO)

    def tentar(self, quem: str) -> int:
        """Devolve 0 se a requisição passa, ou quantos segundos faltam para liberar."""
        t = agora()
        with self._trava:
            fila = self._eventos[quem]
            while fila and t - fila[0] >= JANELA_S:
                fila.popleft()
            if len(fila) >= self.limite():
                return max(1, math.ceil(JANELA_S - (t - fila[0])))
            fila.append(t)
            return 0

    def reiniciar(self):
        with self._trava:
            self._eventos.clear()


limitador = LimiteJanela()


def _limitar(request: Request, quem: str | None):
    # quem não provou quem é conta por endereço, o que também freia o chute de chaves
    identidade = quem or f"ip:{request.client.host if request.client else 'desconhecido'}"
    espera = limitador.tentar(identidade)
    if espera:
        raise HTTPException(429, "limite de requisições excedido", headers={"Retry-After": str(espera)})


def exige_chave_de_dispositivo(request: Request, x_api_key: str | None = Header(default=None)) -> str:
    dono = dono_da_chave(x_api_key)
    _limitar(request, f"dispositivo:{dono}" if dono else None)
    if dono is None:
        raise HTTPException(401, "chave ausente ou inválida", headers={"WWW-Authenticate": "ApiKey"})
    return dono


def exige_chave_de_leitura(request: Request, x_read_key: str | None = Header(default=None)):
    esperada = os.environ.get("MD_READ_KEY", "")
    valida = bool(esperada) and bool(x_read_key) and _igual(x_read_key, esperada)
    _limitar(request, "leitura" if valida else None)
    if not valida:
        raise HTTPException(401, "chave de leitura ausente ou inválida", headers={"WWW-Authenticate": "ApiKey"})


async def limita_tamanho(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        tamanho = request.headers.get("content-length")
        if tamanho is None:
            return JSONResponse({"detail": "Content-Length obrigatório"}, status_code=411)
        if not tamanho.isdigit() or int(tamanho) > TAMANHO_MAX:
            return JSONResponse({"detail": f"corpo acima de {TAMANHO_MAX} bytes"}, status_code=413)
    return await call_next(request)

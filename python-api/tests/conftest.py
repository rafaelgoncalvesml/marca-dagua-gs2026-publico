import pytest

import seguranca

CHAVE = "chave-teste-001"
CHAVE_OUTRO = "chave-teste-002"
LEITURA = "chave-de-leitura-teste"


@pytest.fixture(autouse=True)
def ambiente_com_chaves(monkeypatch):
    monkeypatch.setenv("MD_API_KEYS", f"MD-POA-001:{CHAVE},MD-POA-002:{CHAVE_OUTRO}")
    monkeypatch.setenv("MD_READ_KEY", LEITURA)
    monkeypatch.delenv("MD_LIMITE_POR_MINUTO", raising=False)
    seguranca.limitador.reiniciar()

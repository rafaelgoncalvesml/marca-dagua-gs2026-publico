import pytest
from fastapi.testclient import TestClient

import seguranca
from conftest import CHAVE, CHAVE_OUTRO, LEITURA
from main import app


@pytest.fixture
def anonimo(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_CSV_PATH", str(tmp_path / "leituras.csv"))
    return TestClient(app)


def leitura(seq=1, device_id="MD-POA-001"):
    return {"device_id": device_id, "seq": seq, "ts": "2026-11-10T14:32:05-03:00",
            "nivel_cm": 45.0, "chuva_mm_h": 0.4, "temperatura_c": 24.0, "umidade_pct": 62.0}


def envia(c, seq=1, chave=CHAVE, device_id="MD-POA-001", **extra):
    cab = {"X-API-Key": chave} if chave is not None else {}
    return c.post("/leituras", json=leitura(seq, device_id), headers=cab, **extra)


# ---- chave por dispositivo

def test_post_sem_chave_devolve_401(anonimo):
    r = envia(anonimo, chave=None)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "ApiKey"


def test_post_com_chave_errada_devolve_401(anonimo):
    assert envia(anonimo, chave="chave-errada").status_code == 401


def test_post_com_a_chave_certa_devolve_201(anonimo):
    assert envia(anonimo).status_code == 201


def test_chave_de_um_dispositivo_nao_assina_por_outro(anonimo):
    r = envia(anonimo, chave=CHAVE, device_id="MD-POA-002")
    assert r.status_code == 403


def test_cada_dispositivo_usa_a_propria_chave(anonimo):
    assert envia(anonimo, chave=CHAVE_OUTRO, device_id="MD-POA-002").status_code == 201


def test_chave_com_caractere_fora_do_ascii_nao_derruba_a_api(anonimo):
    r = anonimo.post("/leituras", json=leitura(), headers={"X-API-Key": "chavé".encode("latin-1")})
    assert r.status_code == 401


def test_sem_chaves_configuradas_nega_tudo(anonimo, monkeypatch):
    monkeypatch.delenv("MD_API_KEYS")
    assert envia(anonimo).status_code == 401


# ---- chave de leitura

@pytest.mark.parametrize("rota", ["/leituras", "/indicadores"])
def test_consulta_sem_chave_de_leitura_devolve_401(anonimo, rota):
    assert anonimo.get(rota).status_code == 401


@pytest.mark.parametrize("rota", ["/leituras", "/indicadores"])
def test_consulta_com_chave_de_leitura_devolve_200(anonimo, rota):
    assert anonimo.get(rota, headers={"X-Read-Key": LEITURA}).status_code == 200


def test_chave_de_dispositivo_nao_serve_para_consultar(anonimo):
    assert anonimo.get("/leituras", headers={"X-Read-Key": CHAVE}).status_code == 401


def test_sem_chave_de_leitura_configurada_nega_a_consulta(anonimo, monkeypatch):
    monkeypatch.delenv("MD_READ_KEY")
    assert anonimo.get("/leituras", headers={"X-Read-Key": LEITURA}).status_code == 401


def test_health_continua_aberto(anonimo):
    assert anonimo.get("/health").status_code == 200


# ---- limite de requisições

def test_acima_do_limite_por_minuto_devolve_429_com_retry_after(anonimo, monkeypatch):
    monkeypatch.setenv("MD_LIMITE_POR_MINUTO", "3")
    codigos = [envia(anonimo, seq=i).status_code for i in range(1, 5)]
    assert codigos == [201, 201, 201, 429]
    r = envia(anonimo, seq=5)
    assert r.status_code == 429
    assert 1 <= int(r.headers["retry-after"]) <= 60


def test_o_limite_padrao_deixa_passar_o_ritmo_normal_do_no_com_folga(anonimo):
    # o nó envia a cada 2 s, 30 por minuto; o padrão é o dobro disso
    codigos = [envia(anonimo, seq=i).status_code for i in range(1, 62)]
    assert codigos[:60] == [201] * 60
    assert codigos[60] == 429


def test_o_limite_vale_por_dispositivo(anonimo, monkeypatch):
    monkeypatch.setenv("MD_LIMITE_POR_MINUTO", "2")
    for i in range(1, 4):
        envia(anonimo, seq=i)
    assert envia(anonimo, seq=1, chave=CHAVE_OUTRO, device_id="MD-POA-002").status_code == 201


def test_tentativas_sem_chave_tambem_esbarram_no_limite(anonimo, monkeypatch):
    monkeypatch.setenv("MD_LIMITE_POR_MINUTO", "3")
    codigos = [envia(anonimo, seq=i, chave="chute").status_code for i in range(1, 6)]
    assert codigos == [401, 401, 401, 429, 429]


def test_a_janela_reabre_depois_de_um_minuto(anonimo, monkeypatch):
    monkeypatch.setenv("MD_LIMITE_POR_MINUTO", "1")
    relogio = [1000.0]
    monkeypatch.setattr(seguranca, "agora", lambda: relogio[0])
    assert envia(anonimo, seq=1).status_code == 201
    assert envia(anonimo, seq=2).status_code == 429
    relogio[0] += 61
    assert envia(anonimo, seq=3).status_code == 201


def test_a_consulta_tambem_tem_limite(anonimo, monkeypatch):
    monkeypatch.setenv("MD_LIMITE_POR_MINUTO", "2")
    codigos = [anonimo.get("/leituras", headers={"X-Read-Key": LEITURA}).status_code for _ in range(3)]
    assert codigos == [200, 200, 429]


# ---- limite de tamanho

def test_corpo_acima_de_8_kb_devolve_413(anonimo):
    grande = {**leitura(), "status": {"x": "a" * 9000}}
    r = anonimo.post("/leituras", json=grande, headers={"X-API-Key": CHAVE})
    assert r.status_code == 413


def test_corpo_sem_content_length_devolve_411(anonimo):
    r = anonimo.post("/leituras", content=iter([b'{"device_id": "MD-POA-001"}']),
                     headers={"X-API-Key": CHAVE, "Content-Type": "application/json"})
    assert r.status_code == 411


# ---- configuração na subida

def test_a_api_nao_sobe_sem_as_chaves(monkeypatch):
    monkeypatch.delenv("MD_API_KEYS")
    with pytest.raises(RuntimeError, match="MD_API_KEYS"):
        with TestClient(app):
            pass


def test_a_api_sobe_com_as_chaves_configuradas():
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200

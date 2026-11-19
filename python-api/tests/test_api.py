import pytest
from fastapi.testclient import TestClient

import cenarios
from conftest import CHAVE, LEITURA
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_CSV_PATH", str(tmp_path / "leituras.csv"))
    return TestClient(app, headers={"X-API-Key": CHAVE, "X-Read-Key": LEITURA})


def leitura(seq=1, **campos):
    base = {
        "device_id": "MD-POA-001", "seq": seq, "ts": "2026-11-10T14:32:05-03:00",
        "nivel_cm": 45.0, "chuva_mm_h": 0.4, "temperatura_c": 24.0, "umidade_pct": 62.0,
    }
    return {**base, **campos}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("nome", ["normal", "atencao", "alerta"])
def test_tres_cenarios(client, nome):
    payload, esperado = cenarios.CENARIOS[nome]
    r = client.post("/leituras", json={**payload, "seq": 1, "ts": "2026-11-10T14:32:05-03:00"})
    assert r.status_code == 201
    assert r.json()["risco"] == esperado


def test_api_reclassifica_e_ignora_status_do_dispositivo(client):
    r = client.post("/leituras", json=leitura(nivel_cm=195.5, risco="OK", status={"nivel": "OK"}))
    assert r.json()["risco"] == "ALERTA"
    assert r.json()["status"]["nivel"] == "ALERTA"


@pytest.mark.parametrize("campo,valor", [
    ("nivel_cm", -1), ("nivel_cm", "alto"), ("umidade_pct", 120),
    ("device_id", ""), ("ts", "2026-11-10T14:32:05"),  # sem fuso
])
def test_entrada_invalida_devolve_422(client, campo, valor):
    assert client.post("/leituras", json=leitura(**{campo: valor})).status_code == 422


def test_campo_obrigatorio_ausente(client):
    corpo = leitura()
    del corpo["nivel_cm"]
    assert client.post("/leituras", json=corpo).status_code == 422


def test_reenvio_duplicado_devolve_409_e_nao_grava_duas_vezes(client):
    assert client.post("/leituras", json=leitura(seq=7)).status_code == 201
    assert client.post("/leituras", json=leitura(seq=7, reenviado=True)).status_code == 409
    assert len(client.get("/leituras").json()) == 1


def test_get_filtra_por_risco_e_limita(client):
    for seq, nivel in [(1, 40.0), (2, 190.0), (3, 195.0)]:
        client.post("/leituras", json=leitura(seq=seq, nivel_cm=nivel))
    assert len(client.get("/leituras").json()) == 3
    assert [x["seq"] for x in client.get("/leituras?risco=ALERTA").json()] == [2, 3]
    assert len(client.get("/leituras?limite=1").json()) == 1
    assert client.get("/leituras?risco=XYZ").status_code == 422


def test_indicadores_via_api(client):
    for seq, nivel in [(1, 40.0), (2, 190.0), (4, 130.0)]:
        client.post("/leituras", json=leitura(seq=seq, nivel_cm=nivel))
    ind = client.get("/indicadores").json()
    assert ind["total_alertas"] == 1
    assert ind["nivel_maximo_cm"] == 190.0
    assert ind["lacunas_seq"] == {"MD-POA-001": 1}

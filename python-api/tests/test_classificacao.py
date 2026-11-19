from classificacao import classificar, classificar_valor
from indicadores import calcular_indicadores


def leitura(nivel=45.0, chuva=0.4, umidade=62.0):
    return {"nivel_cm": nivel, "chuva_mm_h": chuva, "umidade_pct": umidade}


def test_limites_de_cada_faixa():
    # abaixo do 1o limiar, no 1o, abaixo do 2o, no 2o
    assert classificar_valor("nivel_cm", 99.9) == "OK"
    assert classificar_valor("nivel_cm", 100) == "ATENCAO"
    assert classificar_valor("nivel_cm", 179.9) == "ATENCAO"
    assert classificar_valor("nivel_cm", 180) == "ALERTA"


def test_umidade_so_informa():
    r = classificar(leitura(umidade=97.0))
    assert r["status"]["umidade"] == "ATENCAO"
    assert r["risco"] == "OK"


def test_chuva_nos_limiares_do_sketch():
    assert classificar_valor("chuva_mm_h", 12.0) == "OK"
    assert classificar_valor("chuva_mm_h", 24.0) == "ATENCAO"
    assert classificar_valor("chuva_mm_h", 48.0) == "ATENCAO"
    assert classificar_valor("chuva_mm_h", 60.0) == "ALERTA"


def test_risco_e_o_pior_status():
    r = classificar(leitura(nivel=195.5, chuva=0.4, umidade=62.0))
    assert r["status"] == {"nivel": "ALERTA", "chuva": "OK", "umidade": "OK"}
    assert r["risco"] == "ALERTA"


def test_tudo_normal():
    assert classificar(leitura())["risco"] == "OK"


def test_indicadores():
    regs = [
        {"device_id": "A", "seq": 1, "nivel_cm": 40.0, "risco": "OK"},
        {"device_id": "A", "seq": 2, "nivel_cm": 190.0, "risco": "ALERTA"},
        {"device_id": "A", "seq": 5, "nivel_cm": 130.0, "risco": "ATENCAO"},  # faltam 3 e 4
    ]
    ind = calcular_indicadores(regs)
    assert ind["total_leituras"] == 3
    assert ind["total_alertas"] == 1
    assert ind["nivel_maximo_cm"] == 190.0
    assert ind["lacunas_seq"] == {"A": 2}


def test_indicadores_sem_leituras():
    ind = calcular_indicadores([])
    assert ind["total_leituras"] == 0 and ind["nivel_maximo_cm"] is None

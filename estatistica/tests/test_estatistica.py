import numpy as np
import pandas as pd

import analise
from preparar_base import agregar_diario, ler_horario

CABECALHO = "REGIAO:;S\nUF:;RS\nESTACAO:;PORTO ALEGRE\nCODIGO (WMO):;A801\nLATITUDE:;-30,05\nLONGITUDE:;-51,17\nALTITUDE:;46,97\nDATA DE FUNDACAO:;22/09/00\n"


def csv_inmet(linha_data, linha_hora, horas=24, chuva="1,5", falha_em=None):
    """CSV horário no formato do INMET para um dia UTC (o layout de 2019+ usa '/' e '0000 UTC')."""
    colunas = "Data;Hora UTC;PRECIPITAÇÃO TOTAL, HORÁRIO (mm);PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB);TEMPERATURA DO AR - BULBO SECO, HORARIA (°C);UMIDADE RELATIVA DO AR, HORARIA (%);\n"
    linhas = []
    for h in range(horas):
        p = "-9999" if h == falha_em else chuva
        linhas.append(f"{linha_data};{linha_hora(h)};{p};1010,2;20,0;80;")
    return (CABECALHO + colunas + "\n".join(linhas) + "\n").encode("latin-1")


def test_le_os_dois_layouts_e_trata_falha():
    novo = ler_horario(csv_inmet("2019/01/02", lambda h: f"{h:02d}00 UTC", falha_em=5))
    antigo = ler_horario(csv_inmet("2014-01-02", lambda h: f"{h:02d}:00"))
    assert novo["chuva"].isna().sum() == 1 and novo["pressao"].iloc[0] == 1010.2
    assert antigo["chuva"].notna().all()
    # 00 UTC do dia 2 = 21h do dia 1 em Brasília
    assert novo["momento"].iloc[0] == pd.Timestamp("2019-01-01 21:00")


def test_dia_incompleto_fica_vazio():
    h = ler_horario(csv_inmet("2019/01/02", lambda h: f"{h:02d}00 UTC"))
    d = agregar_diario(h)
    # dia 1: só 3 horas (21h a 23h) -> vazio; dia 2: 21 horas -> chuva somada
    assert np.isnan(d.loc["2019-01-01", "chuva_mm"])
    assert d.loc["2019-01-02", "chuva_mm"] == 21 * 1.5


def test_analise_roda_de_ponta_a_ponta(tmp_path, monkeypatch):
    # dados sintéticos só para conferir que o código roda; os resultados reais vêm da base do INMET
    rng = np.random.default_rng(0)
    dias = pd.date_range("2014-01-01", "2025-12-31", freq="D")
    umid = rng.normal(78, 9, len(dias)).clip(30, 100)
    pressao = rng.normal(1010, 6, len(dias))
    chuva = np.where(rng.random(len(dias)) < 0.3, rng.gamma(1.2, 8, len(dias)) * (umid / 78) ** 3, 0)
    base = pd.DataFrame({
        "data": dias, "chuva_mm": chuva.round(1), "temp_media_c": rng.normal(20, 5, len(dias)),
        "umidade_media_pct": umid, "pressao_media_hpa": pressao, "vento_medio_ms": rng.gamma(2, 1, len(dias)),
    })
    caminho = tmp_path / "base.csv"
    base.to_csv(caminho, index=False)
    monkeypatch.setattr(analise, "BASE", caminho)
    monkeypatch.setattr(analise, "SAIDAS", tmp_path / "saidas")
    assert analise.main() == 0
    assert (tmp_path / "saidas" / "resultados.md").exists()
    assert len(list((tmp_path / "saidas").glob("*.png"))) == 4

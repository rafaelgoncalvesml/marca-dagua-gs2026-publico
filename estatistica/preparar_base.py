"""Monta a base diária do INMET de Porto Alegre (estação A801) a partir dos arquivos anuais.

Coloque em dados/brutos/ os ZIPs anuais baixados de https://portal.inmet.gov.br/dadoshistoricos
(ou só os CSVs da A801 já extraídos) e rode:  python preparar_base.py
Saída: dados/inmet_poa_diario.csv, uma linha por dia (horário de Brasília).
"""
import io
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).parent / "dados"
ESTACAO = "A801"

# início do nome da coluna no INMET (sem acento, maiúsculo) -> nome na base
COLUNAS = {
    "PRECIPITACAO TOTAL": "chuva",
    "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO": "pressao",
    "TEMPERATURA DO AR - BULBO SECO": "temp",
    "TEMPERATURA MAXIMA NA HORA ANT": "temp_max",
    "TEMPERATURA MINIMA NA HORA ANT": "temp_min",
    "UMIDADE RELATIVA DO AR, HORARIA": "umidade",
    "VENTO, RAJADA MAXIMA": "rajada",
    "VENTO, VELOCIDADE HORARIA": "vento",
}
MIN_HORAS = 18  # dia sem pelo menos 18 das 24 horas válidas numa variável fica vazio nela


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper().strip()


def ler_horario(conteudo: bytes) -> pd.DataFrame:
    """Lê um CSV horário do INMET (8 linhas de cabeçalho, ';', vírgula decimal, -9999 = falha)."""
    df = pd.read_csv(io.BytesIO(conteudo), sep=";", decimal=",", encoding="latin-1", skiprows=8, dtype=str)
    nomes = {}
    for col in df.columns[2:]:
        for prefixo, nome in COLUNAS.items():
            if _sem_acento(col).startswith(prefixo):
                nomes[col] = nome
    dados = df[list(nomes)].rename(columns=nomes).reindex(columns=list(COLUNAS.values()))
    dados = dados.apply(lambda s: pd.to_numeric(s.astype("string").str.replace(",", "."), errors="coerce").astype(float))
    dados = dados.mask(dados <= -9999)

    data = df.iloc[:, 0].str.replace("/", "-")
    hora = df.iloc[:, 1].str.extract(r"(\d{2})")[0]
    utc = pd.to_datetime(data + " " + hora, format="%Y-%m-%d %H")
    dados.insert(0, "momento", utc - pd.Timedelta(hours=3))  # UTC -> horário de Brasília
    return dados


# coluna diária -> (coluna horária, agregação)
DIARIO = {
    "chuva_mm": ("chuva", "sum"),
    "temp_media_c": ("temp", "mean"),
    "temp_max_c": ("temp_max", "max"),
    "temp_min_c": ("temp_min", "min"),
    "umidade_media_pct": ("umidade", "mean"),
    "pressao_media_hpa": ("pressao", "mean"),
    "vento_medio_ms": ("vento", "mean"),
    "rajada_max_ms": ("rajada", "max"),
}


def agregar_diario(horario: pd.DataFrame) -> pd.DataFrame:
    g = horario.groupby(horario["momento"].dt.date)
    diario = pd.DataFrame({
        nome: g[col].agg(func).where(g[col].count() >= MIN_HORAS) for nome, (col, func) in DIARIO.items()
    }).round(2)
    diario.index = pd.to_datetime(diario.index)
    diario.index.name = "data"
    return diario


def arquivos_da_estacao(pasta: Path):
    """Devolve (nome, bytes) de cada CSV da estação, dentro de ZIPs ou solto na pasta."""
    for caminho in sorted(pasta.iterdir()):
        if caminho.suffix.lower() == ".zip":
            with zipfile.ZipFile(caminho) as z:
                for nome in z.namelist():
                    if ESTACAO in nome.upper() and nome.upper().endswith(".CSV"):
                        yield nome, z.read(nome)
        elif caminho.suffix.lower() == ".csv" and ESTACAO in caminho.name.upper():
            yield caminho.name, caminho.read_bytes()


def main() -> int:
    partes = []
    for nome, conteudo in arquivos_da_estacao(PASTA / "brutos"):
        print("lendo", nome)
        partes.append(ler_horario(conteudo))
    if not partes:
        print(f"Nenhum arquivo da estação {ESTACAO} em {PASTA / 'brutos'}. Veja o README.")
        return 1
    horario = pd.concat(partes).drop_duplicates("momento").sort_values("momento")
    diario = agregar_diario(horario)
    diario = diario.loc["2014-01-01":"2025-12-31"]
    saida = PASTA / "inmet_poa_diario.csv"
    diario.to_csv(saida)

    print(f"\n{len(diario)} dias, de {diario.index.min():%d/%m/%Y} a {diario.index.max():%d/%m/%Y}")
    print("Dias sem dado (falha de medição) por coluna:")
    print((diario.isna().mean() * 100).round(1).astype(str).add(" %").to_string())
    print("\nGravado em", saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())

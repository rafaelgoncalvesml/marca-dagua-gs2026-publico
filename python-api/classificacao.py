"""Regras de classificação: cada sensor vira OK, ATENCAO ou ALERTA e o risco é o pior deles."""

ORDEM = ("OK", "ATENCAO", "ALERTA")

# campo da leitura -> (limiar de ATENCAO, limiar de ALERTA), valor >= limiar entra na faixa.
# Mesmos valores do sketch do Wokwi e do aws/lambda_ingestao.py; seguem provisórios até conferir a cota oficial do Gasômetro.
# A umidade só informa: não tem faixa de ALERTA e não entra no risco, como no sketch.
LIMIARES = {
    "nivel_cm": (100, 180),
    "chuva_mm_h": (20, 50),
    "umidade_pct": (90, None),
}

# nome do status no JSON -> campo medido
SENSORES = {"nivel": "nivel_cm", "chuva": "chuva_mm_h", "umidade": "umidade_pct"}
SENSORES_DE_RISCO = ("nivel", "chuva")


def classificar_valor(campo: str, valor: float) -> str:
    atencao, alerta = LIMIARES[campo]
    if alerta is not None and valor >= alerta:
        return "ALERTA"
    if valor >= atencao:
        return "ATENCAO"
    return "OK"


def classificar(leitura: dict) -> dict:
    status = {nome: classificar_valor(campo, leitura[campo]) for nome, campo in SENSORES.items()}
    risco = max((status[s] for s in SENSORES_DE_RISCO), key=ORDEM.index)
    return {"status": status, "risco": risco}

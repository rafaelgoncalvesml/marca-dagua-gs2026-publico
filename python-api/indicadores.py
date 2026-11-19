"""Indicadores calculados sobre as leituras gravadas."""
from collections import Counter, defaultdict


def calcular_indicadores(registros: list[dict]) -> dict:
    por_risco = Counter(r["risco"] for r in registros)

    seqs = defaultdict(set)
    for r in registros:
        seqs[r["device_id"]].add(r["seq"])
    # lacuna = números de sequência que não chegaram entre o menor e o maior já vistos
    lacunas = {d: max(s) - min(s) + 1 - len(s) for d, s in seqs.items()}

    return {
        "total_leituras": len(registros),
        "total_alertas": por_risco["ALERTA"],
        "nivel_maximo_cm": max((r["nivel_cm"] for r in registros), default=None),
        "por_risco": dict(por_risco),
        "lacunas_seq": {d: n for d, n in lacunas.items() if n},
    }

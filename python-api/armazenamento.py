"""Persistência em CSV. O caminho vem de MD_CSV_PATH (padrão: data/leituras.csv)."""
import csv
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

CAMPOS = [
    "device_id", "seq", "ts", "nivel_cm", "chuva_mm_h", "temperatura_c", "umidade_pct",
    "status_nivel", "status_chuva", "status_umidade", "risco", "reenviado", "recebido_em",
]
_FLOATS = ("nivel_cm", "chuva_mm_h", "temperatura_c", "umidade_pct")
_trava = threading.Lock()


def caminho() -> Path:
    return Path(os.environ.get("MD_CSV_PATH") or Path(__file__).parent / "data" / "leituras.csv")


def ler() -> list[dict]:
    arquivo = caminho()
    if not arquivo.exists():
        return []
    with arquivo.open(newline="", encoding="utf-8") as f:
        registros = list(csv.DictReader(f))
    for r in registros:
        r["seq"] = int(r["seq"])
        r["reenviado"] = r["reenviado"] == "true"
        for campo in _FLOATS:
            r[campo] = float(r[campo])
    return registros


def gravar(leitura: dict) -> bool:
    """Acrescenta a leitura ao CSV. Devolve False, sem gravar, se (device_id, seq) já existe."""
    linha = {
        **leitura,
        "status_nivel": leitura["status"]["nivel"],
        "status_chuva": leitura["status"]["chuva"],
        "status_umidade": leitura["status"]["umidade"],
        "reenviado": str(leitura["reenviado"]).lower(),
        "recebido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    arquivo = caminho()
    with _trava:
        # ponytail: relê o arquivo inteiro a cada POST; trocar por índice em memória se passar de milhares de leituras
        if any(r["device_id"] == leitura["device_id"] and r["seq"] == leitura["seq"] for r in ler()):
            return False
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        novo = not arquivo.exists()
        with arquivo.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
            if novo:
                w.writeheader()
            w.writerow(linha)
    return True

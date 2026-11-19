"""API do nó Marca d'Água: recebe leituras em JSON, classifica, grava em CSV e consulta."""
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import AwareDatetime, BaseModel, Field

import armazenamento
import seguranca
from classificacao import classificar
from indicadores import calcular_indicadores



@asynccontextmanager
async def ciclo_de_vida(_):
    seguranca.exige_configuracao()  # sem chave configurada a API nem sobe
    yield


app = FastAPI(title="Marca d'Água API", version="1.1", lifespan=ciclo_de_vida)
app.middleware("http")(seguranca.limita_tamanho)


class Leitura(BaseModel):
    device_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    seq: int = Field(ge=0)
    ts: AwareDatetime  # exige fuso, como no contrato (ex.: 2026-11-10T14:32:05-03:00)
    nivel_cm: float = Field(ge=0, le=1000)
    chuva_mm_h: float = Field(ge=0, le=500)
    temperatura_c: float = Field(ge=-20, le=60)
    umidade_pct: float = Field(ge=0, le=100)
    reenviado: bool = False
    # o dispositivo pode mandar status e risco, mas a API sempre reclassifica e ignora o que veio
    status: dict | None = None
    risco: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/leituras", status_code=201)
def receber_leitura(leitura: Leitura, dispositivo: str = Depends(seguranca.exige_chave_de_dispositivo)):
    if leitura.device_id != dispositivo:
        raise HTTPException(403, "a chave não pertence a este dispositivo")
    registro = leitura.model_dump(mode="json", exclude={"status", "risco"})
    registro.update(classificar(registro))
    if not armazenamento.gravar(registro):
        raise HTTPException(409, f"leitura {registro['device_id']}/{registro['seq']} já recebida")
    return registro


@app.get("/leituras", dependencies=[Depends(seguranca.exige_chave_de_leitura)])
def listar_leituras(
    device_id: str | None = None,
    risco: Literal["OK", "ATENCAO", "ALERTA"] | None = None,
    limite: int = Query(100, ge=1, le=1000),
):
    registros = [
        r for r in armazenamento.ler()
        if (device_id is None or r["device_id"] == device_id) and (risco is None or r["risco"] == risco)
    ]
    return registros[-limite:]


@app.get("/indicadores", dependencies=[Depends(seguranca.exige_chave_de_leitura)])
def indicadores():
    return calcular_indicadores(armazenamento.ler())

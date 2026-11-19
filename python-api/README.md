# API Marca d'Água (Computational Thinking with Python)

API FastAPI que recebe as leituras do nó comunitário em JSON, valida, classifica cada sensor, grava o histórico em CSV e devolve consultas e um indicador calculado.

## Como rodar

Requer Python 3.12 ou mais novo. Na pasta `python-api`, no PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

A API pede chave e não sobe sem elas. Gere duas chaves, uma para o nó e outra para quem consulta, e defina as variáveis no terminal (os nomes estão em [.env.example](.env.example); não grave as chaves em arquivo versionado):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(24))"
$env:MD_API_KEYS = "MD-POA-001:COLE_A_CHAVE_DO_NO"
$env:MD_READ_KEY = "COLE_A_CHAVE_DE_LEITURA"
uvicorn main:app
```

Abra http://127.0.0.1:8000/health (deve mostrar `{"status":"ok"}`, é a única rota aberta) e http://127.0.0.1:8000/docs para ver os endpoints.

Com a API no ar, em outro terminal (com o ambiente ativado e `MD_API_KEY` com a chave do nó), rode os 3 cenários, a prova da proteção e os testes:

```powershell
$env:MD_API_KEY = "COLE_A_CHAVE_DO_NO"
$env:MD_READ_KEY = "COLE_A_CHAVE_DE_LEITURA"
python cenarios.py
python prova_protecao.py
pytest
```

O CSV é gravado em `data/leituras.csv` (ignorado pelo Git). Para mudar o caminho, defina `MD_CSV_PATH`. Um exemplo do resultado dos cenários está em [exemplos/leituras_exemplo.csv](exemplos/leituras_exemplo.csv).

## Endpoints

| Método e rota | O que faz |
|---|---|
| `GET /health` | Confere se a API está no ar. Aberta, sem chave. |
| `POST /leituras` | Exige `X-API-Key`. Valida o JSON, classifica, grava no CSV e devolve a leitura classificada (201). Leitura repetida (mesmo `device_id` e `seq`) devolve 409 e não grava. JSON inválido devolve 422. |
| `GET /leituras` | Exige `X-Read-Key`. Lista as leituras gravadas. Filtros opcionais: `device_id`, `risco` (`OK`, `ATENCAO` ou `ALERTA`) e `limite` (padrão 100, devolve as mais recentes). |
| `GET /indicadores` | Exige `X-Read-Key`. Total de leituras, total de alertas, nível máximo, contagem por risco e lacunas na sequência por dispositivo. |

## Contrato JSON

Igual ao do restante do projeto (ver [o desenho](../docs/superpowers/specs/2026-11-05-marca-dagua-design.md#3-contrato-de-dados)).

```json
{
  "device_id": "MD-POA-001",
  "seq": 1234,
  "ts": "2026-11-10T14:32:05-03:00",
  "nivel_cm": 182.4,
  "chuva_mm_h": 12.5,
  "temperatura_c": 24.1,
  "umidade_pct": 88.0,
  "reenviado": false
}
```

| Campo | Regra de validação |
|---|---|
| `device_id` | Texto com 1 a 40 caracteres entre letras, números, `-` e `_`. |
| `seq` | Inteiro maior ou igual a 0. Cresce a cada leitura do dispositivo. |
| `ts` | Data e hora ISO 8601 com fuso. Sem fuso é recusado. |
| `nivel_cm` | Número de 0 a 1000. |
| `chuva_mm_h` | Número de 0 a 500. |
| `temperatura_c` | Número de -20 a 60. |
| `umidade_pct` | Número de 0 a 100. |
| `reenviado` | Booleano, `false` por padrão. `true` quando a leitura saiu da fila offline. |

O dispositivo pode mandar também `status` e `risco`, mas a API ignora os dois e reclassifica pelos valores medidos. A resposta traz `status` (por sensor) e `risco` calculados pela API.

## Regras de classificação

Cada sensor vira `OK`, `ATENCAO` ou `ALERTA` por limiar (valor maior ou igual ao limiar entra na faixa). O `risco` da leitura é o pior status entre nível e chuva. A umidade só informa: aparece no `status`, mas não eleva o risco.

| Sensor | ATENCAO a partir de | ALERTA a partir de |
|---|---|---|
| `nivel_cm` | 100 | 180 |
| `chuva_mm_h` | 20 | 50 |
| `umidade_pct` | 90 | não tem |

Os limiares são provisórios, ficam em `classificacao.py` e devem ser alinhados com os do sketch do Wokwi e com a cota de inundação oficial do Gasômetro.

## Indicador calculado

`GET /indicadores` calcula, sobre o CSV: `total_alertas` (leituras com risco `ALERTA`), `nivel_maximo_cm` e `lacunas_seq`, que conta os números de sequência que faltam entre o menor e o maior já recebidos de cada dispositivo. É assim que a API percebe leituras perdidas quando a fila offline do nó não alcançou a rede.

## Proteção da API

Resposta de cada situação, em ordem de checagem:

| Situação | Resposta |
|---|---|
| POST sem `Content-Length` | 411 |
| Corpo com mais de 8 KB | 413 |
| Mais de 60 requisições por minuto da mesma chave (ou do mesmo endereço, quando não há chave válida) | 429, com `Retry-After` em segundos |
| Chave ausente, errada ou não configurada | 401, com `WWW-Authenticate: ApiKey` |
| Chave válida, mas de outro dispositivo que o do corpo (`device_id`) | 403 |

Como funciona. Cada dispositivo tem a própria chave em `MD_API_KEYS` (pares `dispositivo:chave`) e ela só vale para o seu `device_id`. A consulta usa outra chave, `MD_READ_KEY`, que não assina leituras. As chaves vêm do ambiente, são comparadas em tempo constante e nunca vão para o log. O limite padrão (60 por minuto, ajustável em `MD_LIMITE_POR_MINUTO`) é o dobro do ritmo normal do nó, que envia uma leitura a cada 2 s. Tentativas sem chave válida também contam, por endereço, o que freia quem tenta adivinhar uma chave. Sem `MD_API_KEYS` e `MD_READ_KEY` a API recusa subir.

`python prova_protecao.py` roda a sequência completa contra a API no ar (401, 403, 413, uma rajada até o 429) e imprime um quadro para o print. A análise de ameaças que levou a essas escolhas está em [../ciberseguranca/inventario-ameacas.md](../ciberseguranca/inventario-ameacas.md).

## Estrutura

| Arquivo | Papel |
|---|---|
| `main.py` | Endpoints e validação do JSON (FastAPI e pydantic). |
| `seguranca.py` | Chaves, limite de requisições e limite de tamanho. |
| `classificacao.py` | Limiares e funções de classificação. |
| `armazenamento.py` | Leitura e gravação do CSV. |
| `indicadores.py` | Cálculo dos indicadores. |
| `cenarios.py` | Script dos 3 cenários (normal, atenção e alerta) contra a API no ar. |
| `prova_protecao.py` | Prova da proteção: 401, 403, 413 e 429 contra a API no ar. |
| `.env.example` | Nomes das variáveis de ambiente, sem valores. |
| `tests/` | Testes do `pytest` para as regras, os indicadores e os endpoints. |

## Limites conhecidos

- O CSV é relido a cada `POST` para detectar leitura repetida. Para milhares de leituras seria melhor um índice em memória ou um banco.
- O limite de requisições fica na memória de um processo: não vale com várias instâncias, e o controle guarda uma entrada por endereço novo, sem limpeza.
- Atrás de um túnel ou proxy, todas as requisições sem chave chegam do mesmo endereço e dividem um único limite de tentativas. O cabeçalho `X-Forwarded-For` não é usado.
- A chave do nó fica no firmware. Quem tiver o aparelho e souber extrair a memória a obtém. Em produção, o caminho é chave por aparelho com rotação e proteção da memória flash.
- A API não faz TLS. O HTTPS vem do túnel ou de um proxy na frente dela.

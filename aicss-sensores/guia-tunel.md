# Wokwi falando com a API (dia 10/11)

O Wokwi só enxerga a internet pública, não o `localhost` do seu computador. Para o nó alcançar a API, abrimos um túnel do `cloudflared` que dá um endereço `https://...trycloudflare.com` apontando para a API local.

Este guia cobre três coisas: subir tudo, rodar o Wokwi e provar a fila offline com prints. Tempo previsto: 60 min.

## O que você vai guardar

Salve cada print em `aicss-sensores/evidencias/` com o nome da lista (PNG ou JPG). O PDF do AICSS puxa esses arquivos pelo nome.

| Arquivo | O que mostrar |
|---|---|
| `10-01-api-e-tunel.png` | Os dois terminais lado a lado: uvicorn no ar e cloudflared com o endereço público |
| `10-02-post-ok-serial.png` | Serial do Wokwi com `enviada: HTTP 201` |
| `10-03-leituras-na-api.png` | `GET /leituras` no navegador (ou o CSV aberto) com as leituras recebidas |
| `10-04-api-parada-fila.png` | Serial com `envio falhou` e a fila crescendo |
| `10-05-reenvio-em-ordem.png` | Serial com `reenviada da fila` e o `seq` subindo sem pular |
| `10-06-indicadores.png` | `GET /indicadores` com `lacunas_seq` vazio e `GET /leituras` mostrando `reenviado: true` |

## 1. Instalar o cloudflared (uma vez)

No PowerShell:

```powershell
winget install --id Cloudflare.cloudflared
```

Feche e abra o terminal e confira com `cloudflared --version`.

## 2. Preparar a API

Na pasta `python-api`, com o ambiente ativado (veja o README da pasta):

A API agora exige chave e não sobe sem elas. Gere uma chave para o nó e outra para quem consulta (guarde só na sua máquina, fora do Git):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

```powershell
$env:MD_API_KEYS = "MD-POA-001:COLE_A_CHAVE_DO_NO"
$env:MD_READ_KEY = "COLE_A_CHAVE_DE_LEITURA"
Remove-Item data\leituras.csv -ErrorAction SilentlyContinue
uvicorn main:app
```

Apagar o CSV antes de cada rodada é necessário. O nó recomeça o `seq` em 1 cada vez que você reinicia o Wokwi, e a API recusa (409) um `seq` que já gravou.

Confira em http://127.0.0.1:8000/health.

## 3. Abrir o túnel

Em outro terminal:

```powershell
cloudflared tunnel --url http://localhost:8000
```

Ele imprime uma linha como `https://nome-aleatorio.trycloudflare.com`. Copie esse endereço. Teste antes de ir ao Wokwi:

```powershell
curl.exe https://nome-aleatorio.trycloudflare.com/health
```

Deve voltar `{"status":"ok"}`. Tire o print `10-01`.

O endereço muda toda vez que o cloudflared reinicia. Por isso, durante o teste offline, **pare só a API, nunca o túnel**.

## 4. Colocar o endereço no sketch

No `sketch.ino`, troque a constante:

```cpp
const char* API_URL = "https://nome-aleatorio.trycloudflare.com/leituras";
const char* API_KEY = "COLE_A_CHAVE_DO_NO";
```

O final `/leituras` fica. A chave é a mesma que você pôs em `MD_API_KEYS` para `MD-POA-001`. Cole só no Wokwi e nunca faça commit com a chave real. Copie o sketch inteiro para o projeto do Wokwi (junto do `diagram.json` e da lista de bibliotecas: DHT sensor library e ArduinoJson) e rode.

Na serial devem aparecer, a cada 2 s, a linha `[OK] nivel=...`, o JSON e `enviada: HTTP 201`. O primeiro envio pode demorar uns segundos pelo HTTPS. Print `10-02`, e depois `10-03` com http://127.0.0.1:8000/leituras aberto no navegador.

## 5. Testar a fila offline

1. Com o Wokwi rodando e enviando, vá ao terminal do uvicorn e pare a API (Ctrl+C). O túnel continua aberto e passa a responder 502.
2. Deixe uns 30 s. A serial mostra `envio falhou (502), leitura na fila (1)` e depois `API fora, leitura na fila (N)`, com N subindo de 1 a cada 2 s. Print `10-04`.
3. Suba a API de novo (`uvicorn main:app`, sem apagar o CSV).
4. Em até 10 s o nó tenta de novo e a serial mostra `reenviada da fila: HTTP 201, restam N`, 5 leituras por ciclo, com o `seq` na ordem e `"reenviado":true` no JSON. Print `10-05`.
5. Abra http://127.0.0.1:8000/indicadores. `lacunas_seq` deve vir `{}`, o que prova que nenhuma leitura se perdeu. Abra também `/leituras` e mostre as leituras com `reenviado: true`. Print `10-06`.

Fique abaixo de uns 100 s offline. A fila guarda 60 leituras; passando disso o nó descarta as mais antigas e `lacunas_seq` mostra o buraco. Se quiser, faça isso de propósito numa segunda rodada e guarde o print como bônus (`10-07-fila-cheia-lacuna.png`).

## Se algo der errado

| Sintoma | Causa provável |
|---|---|
| `envio falhou (-1)` desde o começo | Endereço do túnel errado no sketch, ou o Wokwi ainda sem Wi-Fi |
| `enviada: HTTP 401` | A chave do sketch não é a de `MD_API_KEYS` para `MD-POA-001`, ou a API subiu sem a variável no mesmo terminal |
| `enviada: HTTP 429` | Passou de 60 envios por minuto (o nó normal manda 30). O reenvio da fila offline pode estourar o limite por alguns segundos. A leitura continua na fila e o nó tenta de novo |
| `enviada: HTTP 409` | O CSV ficou da rodada anterior. Pare a API, apague `data\leituras.csv` e reinicie o Wokwi |
| `enviada: HTTP 422` | A leitura saiu com `ts` ou algum campo nulo (sem Wi-Fi na partida, DHT sem resposta). Reinicie o Wokwi |
| `envio falhou (502)` com a API no ar | O túnel aponta para outra porta. Reabra com `--url http://localhost:8000` |
| Nada aparece no `/leituras` | Confira se a API que você abriu é a da pasta `python-api` e se o CSV está em `python-api/data/` |

## Plano de reserva

Se o túnel ou o Wokwi não colaborarem, o enunciado de Python aceita requisições HTTP simuladas com o mesmo JSON. Defina `MD_API_KEY` (a chave do nó) e `MD_READ_KEY` no terminal, rode `python cenarios.py` na pasta `python-api` com a API no ar e guarde a saída, mais o print da serial do Wokwi mostrando o JSON impresso. Registre no relatório que o envio foi simulado.

## Cuidados

- Enquanto o túnel estiver aberto, a API fica acessível a qualquer pessoa com o endereço. Agora ela pede chave e limita requisições, mas feche o cloudflared quando terminar.
- O sketch usa HTTPS sem validar o certificado. Para a demo basta. Entra como limitação no relatório.
- A fila fica na RAM. Se o nó reiniciar com leituras na fila, elas se perdem. Memória não volátil seria a evolução.

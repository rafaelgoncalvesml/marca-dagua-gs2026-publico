# Roteiro da prova de proteção da API

Tarefa do dia 14 (Cybersecurity): mostrar uma chamada sem chave devolvendo 401 e várias chamadas seguidas devolvendo 429, com prints. Tempo previsto: 30 minutos.

Antes de começar, uma regra para todos os prints: a tela não pode mostrar o valor de nenhuma chave. Os comandos abaixo usam `$env:MD_API_KEY`, que aparece como o nome da variável, não como o valor. Confira o print antes de salvar.

## 1. Subir a API com as chaves (terminal 1)

Na pasta `python-api`, com o ambiente ativado:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

Rode duas vezes e guarde as duas chaves num lugar fora do Git (um gerenciador de senhas serve). Depois:

```powershell
$env:MD_API_KEYS = "MD-POA-001:COLE_A_PRIMEIRA_CHAVE"
$env:MD_READ_KEY = "COLE_A_SEGUNDA_CHAVE"
Remove-Item data\leituras.csv -ErrorAction SilentlyContinue
uvicorn main:app
```

Se esquecer uma variável, a API recusa subir e diz qual faltou. Isso também é parte da proteção.

## 2. Prova em um comando (terminal 2)

Na mesma pasta, com o ambiente ativado e logo depois de subir a API (o limite vale por minuto):

```powershell
$env:MD_API_KEY = "COLE_A_PRIMEIRA_CHAVE"
$env:MD_READ_KEY = "COLE_A_SEGUNDA_CHAVE"
python prova_protecao.py
```

O quadro mostra, uma linha por verificação: rota aberta (200), sem chave (401), chave errada (401), chave certa (201), chave em nome de outro dispositivo (403), corpo grande (413), consulta sem chave de leitura (401), consulta com ela (200) e uma rajada com o primeiro 429. Todas as linhas devem sair `[OK]`.

Prints, salvos na pasta `ciberseguranca/evidencias/`:

| Arquivo | O que mostrar |
|---|---|
| `14-01-prova-protecao.png` | O quadro inteiro, com o comando visível e a linha final "Tudo como esperado." |
| `14-02-api-subiu-com-chaves.png` | O terminal 1 com a API no ar e as linhas das chamadas (401, 201, 403, 413, 429) |
| `14-03-testes.png` | `pytest` terminando com 45 testes passando |

## 3. As duas chamadas pedidas, à mão (opcional)

Se o professor ou o relatório pedir as chamadas separadas, use o `curl.exe` com o arquivo `exemplos\leitura_exemplo.json`.

Sem chave, resposta 401:

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/leituras -H "Content-Type: application/json" --data "@exemplos/leitura_exemplo.json"
```

Com a chave, resposta 201 (troque o `seq` no arquivo a cada tentativa, ou a segunda dá 409):

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/leituras -H "Content-Type: application/json" -H "X-API-Key: $env:MD_API_KEY" --data "@exemplos/leitura_exemplo.json"
```

Várias seguidas, com 429 no fim:

```powershell
1..70 | ForEach-Object { curl.exe -s -o NUL -w "%{http_code}`n" -X POST http://127.0.0.1:8000/leituras -H "Content-Type: application/json" -H "X-API-Key: $env:MD_API_KEY" --data "@exemplos/leitura_exemplo.json" }
```

Com o mesmo `seq`, a primeira dá 201 e as seguintes dão 409, porque a leitura repetida é recusada depois de passar pelo limite. A partir da sexagésima primeira, o que aparece é 429. Para uma sequência limpa de 201 até o 429, prefira o `prova_protecao.py`, que troca o `seq` a cada chamada.

## 4. Gerar o PDF do relatório

Com os três prints salvos em `ciberseguranca/evidencias/`, na raiz do repositório:

```powershell
python ciberseguranca/relatorio/gerar_pdf.py
```

O script embute os prints pelo nome e gera `ciberseguranca/relatorio/Cyber-Marca-dAgua.pdf`. Print que falta vira uma caixa amarela com o nome esperado. As caixas amarelas de "Decidir antes de enviar" saem quando você apagar a linha `<!--DECIDIR ...-->` correspondente em `ciberseguranca/relatorio/relatorio.html`, depois de escrever a decisão no texto.

## 5. O que vai para o relatório

- O quadro do passo 2 e a explicação de cada código (401 e 403 para autenticação, 413 e 411 para tamanho, 429 para frequência).
- A nuvem na AWS já exige chave por dispositivo no API Gateway e na Lambda (401 sem chave válida, na captura `aws/evidencias/06-teste-ponta-a-ponta.png`). Esta prova cobre a API local; a da nuvem está na seção 5.1 do inventário de ameaças.
- O risco que sobra: a chave fica no firmware do nó, o limite é em memória de um processo e a função da nuvem usa a LabRole, que é ampla (seção 5.3 do inventário).

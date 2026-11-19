# Inventário de ameaças do Marca d'Água

Global Solution 2026.2, Cybersecurity. Rafael Gonçalves (RM 569461) e Charles Augusto (RM 571908).

Rascunho de 12/11/2026, atualizado em 16/11/2026 para a nuvem que foi de fato implantada. A primeira versão descrevia uma Lambda com Function URL, banco RDS PostgreSQL e Hugging Face. Essa versão nunca foi publicada e foi substituída por API Gateway, Lambda, DynamoDB, CloudWatch e SNS (relatório de AWS do Charles, 15/11). Por isso as ameaças do RDS e da Hugging Face saíram, e entraram as da arquitetura nova. Onde o texto diz "feito", o controle foi conferido no repositório ou aparece nas capturas de `aws/evidencias/`. O que está como "planejado" ainda não foi feito.

A pontuação desta atualização é uma reavaliação de 16/11 que a dupla ainda precisa confirmar. A prioridade 3, que era o banco aberto à internet, foi trocada (seção 5.3), porque o risco deixou de existir.

## 1. Escopo e método

O inventário cobre o que o projeto tem hoje ou terá na entrega: o nó ESP32 (no Wokwi), a API em FastAPI, a nuvem na AWS (API Gateway, Lambda, DynamoDB, CloudWatch e SNS), o túnel usado na demonstração e o repositório. O modelo de dados em Oracle e MongoDB entra como ativo de demonstração, com dados fictícios e sem ligação com a nuvem. O cadastro de moradores existe só nesse modelo, não em código que o alerta use.

Para cada ameaça:

1. Probabilidade (P) e impacto (I) de 1 a 3.
2. Risco = P × I. De 1 a 2 é baixo, de 3 a 4 é médio, 6 ou mais é alto.
3. "Risco atual" considera só os controles que já estão feitos. "Risco previsto" considera também os planejados.

A pontuação é um julgamento para ordenar o trabalho. Não é medida.

## 2. O sistema e as fronteiras de confiança

```
Nó ESP32 (nível, chuva, temperatura, umidade; LED e buzzer)
   | (1) internet, HTTPS
   +--> API FastAPI (local, via túnel na demonstração) -> CSV
   |
   +--> API Gateway (POST /leituras, 5 req/s)
            | (2) só o API Gateway pode invocar a função
            v
        Lambda marca-dagua-ingestao (perfil LabRole)
            | (3) PutItem                  | métrica Alertas
            v                              v
        DynamoDB                      CloudWatch -> alarme -> SNS -> e-mail

Modelo de dados (Oracle e MongoDB): dados fictícios, sem ligação com a nuvem
```

Quatro fronteiras concentram o risco. A primeira é entre o nó e a internet. A segunda é a entrada pública, o endereço do API Gateway e a API local. A terceira é a permissão da função sobre a conta, que no Learner Lab é a LabRole, ampla. A quarta é a saída do alerta, o e-mail do SNS, que chega só a quem assinou o tópico.

## 3. Ativos

| ID | Ativo | O que mais importa proteger |
|---|---|---|
| A1 | Leituras do nó (nível, chuva, temperatura, umidade) | Integridade: uma leitura falsa gera alerta falso ou esconde um alerta real |
| A2 | Relatos de moradores (hoje só no MongoDB de demonstração, fictícios) | Confidencialidade: texto livre pode trazer nome, endereço, situação de saúde |
| A3 | Tabela `marca_dagua_leituras` no DynamoDB | Integridade e disponibilidade do histórico |
| A4 | Perfil de execução da função (LabRole) | Quanto dano uma função comprometida consegue fazer na conta |
| A5 | Disponibilidade do aviso | Disponibilidade: o sistema vale mais justamente quando a rede está ruim |
| A6 | Função Lambda, API Gateway e API local | Integridade do código e controle de quem chama |
| A7 | Chave de cada dispositivo (`DEVICE_KEYS`) e chave de leitura da API local | Confidencialidade: quem tem a chave fala em nome do nó |
| A8 | Repositório Git | Ausência de segredos no código e no histórico |
| A9 | Cadastro de moradores (hoje só modelo, com dados fictícios) | Confidencialidade: nome, telefone e e-mail são dado pessoal |
| A10 | Endereço de e-mail do assinante do tópico SNS | Confidencialidade: é dado pessoal tratado pela AWS |

## 4. Matriz de risco

| ID | Ameaça | Onde | P | I | Risco atual | Risco previsto |
|---|---|---|---|---|---|---|
| T01 | Leitura falsa enviada com chave roubada ou extraída do firmware | API, Lambda | 1 | 3 | 3 médio | 3 médio |
| T02 | Leitura pública dos dados | API local | 1 | 2 | 2 baixo | 2 baixo |
| T03 | Permissão ampla da função (LabRole) | Lambda, conta AWS | 2 | 2 | 4 médio | 2 baixo |
| T04 | Excesso de chamadas, custo e esgotamento de cota | API Gateway, Lambda, DynamoDB | 2 | 2 | 4 médio | 2 baixo |
| T05 | Dado pessoal em relato livre ou em log | Lambda, CloudWatch | 1 | 2 | 2 baixo | 2 baixo |
| T06 | Túnel da demonstração expõe a API local | Túnel, sketch | 2 | 2 | 4 médio | 2 baixo |
| T07 | Falso senso de segurança causado pelo modelo de ML | ML, aviso ao morador | 2 | 2 | 4 médio | 2 baixo |
| T08 | Segredo exposto (chave do dispositivo, chaves da API) | Repositório, Lambda, terminal | 1 | 3 | 3 médio | 2 baixo |
| T09 | Interceptação entre o nó e a API local | Nó | 1 | 3 | 3 médio | 3 médio |
| T10 | Nó ou rede fora do ar durante a enchente | Nó, rede | 3 | 1 | 3 médio | 3 médio |
| T11 | Cadastro de moradores sem proteção (quando for ligado ao alerta) | Cadastro | 1 | 3 | 3 médio | 3 médio |
| T12 | Entrada maliciosa ou fora do formato | API, Lambda | 1 | 1 | 1 baixo | 1 baixo |
| T13 | Reenvio de leitura antiga | API, Lambda | 1 | 1 | 1 baixo | 1 baixo |
| T14 | O aviso não chega ao morador (e-mail só para assinantes, sem reenvio) | SNS, alarme | 2 | 3 | 6 alto | 4 médio |
| T15 | Dependências vulneráveis ou sem versão fixa | API local | 1 | 2 | 2 baixo | 1 baixo |

Mudanças em relação ao rascunho de 12/11. T01 e T02 caíram porque a Lambda passou a exigir chave por dispositivo e não tem rota de leitura. O banco aberto (antiga T03) e o token da IA saíram junto com o RDS e a Hugging Face. T13 caiu porque a Lambda agora também rejeita `device_id` e `seq` repetidos. T14 era o TLS sem verificação entre Lambda e RDS e passou a ser o risco de o aviso não chegar. Esse é o único risco alto que sobrou, porque o alerta aos moradores hoje é um e-mail para quem assinou o tópico.

## 5. As três prioridades

A ordem segue duas perguntas: o que atrapalha a função principal do sistema (avisar a tempo) e o que cabe nos dias que restam.

### 5.1 Acesso sem autenticação (T01 e T02)

O que acontece. Quem souber a URL grava leituras em nome de qualquer nó. Um POST com `nivel_cm: 0` durante uma enchente apaga o aviso na nuvem. Um POST com `nivel_cm: 900` dispara um alerta falso, e alertas falsos repetidos ensinam o morador a ignorar o aviso. O endereço vai aparecer no relatório e no vídeo, então não dá para contar com sigilo.

Evidência de antes do controle. Em 12/11, na API local, um POST com leitura forjada sem nenhuma chave devolveu 201, e o GET de `/leituras` e de `/indicadores` devolveu 200 para qualquer um.

Controles feitos na API Python em 12/11:
- Uma chave por dispositivo no cabeçalho `X-API-Key`, lida da variável de ambiente `MD_API_KEYS`, comparada com `hmac.compare_digest`. A chave só vale para o `device_id` a que pertence (403 para outro).
- Sem chave ou com chave errada, 401. A consulta pede uma chave de leitura separada (`X-Read-Key`). A API não sobe sem as duas variáveis.

Controles feitos na Lambda, conferidos no relatório de AWS de 15/11:
- Cabeçalho `x-api-key` por dispositivo, validado contra `DEVICE_KEYS`. Chave errada e dispositivo desconhecido recebem o mesmo 401, sem revelar qual falhou. A autenticação vem antes da validação dos campos, então quem não tem chave não testa as regras.
- A política da função só aceita invocação do API Gateway, pela rota `/leituras` desta API.
- Não existe rota de leitura na Lambda. Ela só recebe POST, e o resultado vai para o DynamoDB.
- O risco é sempre recalculado no servidor, e `status` e `risco` enviados pelo dispositivo são ignorados.

Como provar. API local: `python prova_protecao.py` contra a API no ar, com o roteiro em [roteiro-prova-protecao.md](roteiro-prova-protecao.md). Nuvem: o `testar_ingestao.py` devolveu 201 nos três cenários e 401 com chave inválida (captura `aws/evidencias/06-teste-ponta-a-ponta.png`).

O que sobra. A chave fica gravada no firmware, e quem tiver o aparelho e souber extrair a memória a obtém. A chave do dispositivo na nuvem foi rotacionada depois de aparecer em testes, segundo o relatório. Em produção, a saída é chave por aparelho com rotação, proteção da memória flash do ESP32 e as chaves no Secrets Manager.

### 5.2 Excesso de chamadas, custo e cota (T04)

O que acontece. Um laço de POST gera uma invocação da Lambda e uma gravação no DynamoDB por chamada. O resultado possível é custo inesperado na conta e o aviso indisponível justamente na enchente.

Evidência de antes do controle. Na API local, 60 POSTs seguidos foram todos aceitos, e um corpo de 2 MB também.

Controles feitos:
- API Gateway com limite de 5 requisições por segundo e rajada de 10 na rota. O corpo é limitado a 2 KB na Lambda (413), e o DynamoDB está em modo sob demanda.
- API Python: 60 requisições por minuto por chave, com 429 e cabeçalho `Retry-After`. Tentativas sem chave válida contam por endereço. Corpo limitado a 8 KB (413), com `Content-Length` obrigatório (411).

O que falta. Concorrência reservada na função e um alerta de orçamento na conta. Nenhum dos dois aparece no relatório de AWS, então devem ser tratados como não feitos até alguém confirmar no console.

O que sobra. O limite da API Python fica na memória de um processo, então não vale com várias instâncias. O limite do API Gateway é por rota, não por dispositivo.

### 5.3 Permissão ampla da função (T03)

Substitui a prioridade confirmada em 12/11 (banco RDS aberto à internet), que deixou de existir com a troca de arquitetura.

O que acontece. No Learner Lab não dá para criar perfis de acesso, então a função usa a LabRole, que tem permissões muito maiores que as necessárias. Se alguém conseguir executar código na função, ele age na conta com essa permissão.

Por que pesa. A função só precisa gravar uma linha no DynamoDB e escrever log. A LabRole não reflete esse privilégio mínimo.

Controles que existem. A política da função só deixa o API Gateway invocá-la. A Lambda não tem dependências externas além do que vem no ambiente (`boto3`), não executa o que recebe e só faz `PutItem`.

Controle a aplicar em produção. Um perfil próprio com `AWSLambdaBasicExecutionRole` e uma política embutida só com `dynamodb:PutItem` no ARN da tabela. O roteiro de AWS já descreve isso e o relatório declara a LabRole como limitação.

Como provar. Captura da política da função (`aws/evidencias/04-lambda-politica-recursos.png`) e a captura do perfil (`03-lambda-perfil-labrole.png`).

## 6. Demais ameaças

| ID | Cenário | O que já existe | O que fazer |
|---|---|---|---|
| T05 | Um relato em texto livre pode trazer nome, endereço ou saúde. Na versão atual a Lambda não recebe relato e não grava texto livre. Os relatos existem só como dados fictícios no MongoDB de demonstração. | A Lambda guarda só `device_id`, `seq`, `ts`, medições, risco e `reenviado`. Os logs mostram `device_id`, `seq` e risco, sem o corpo e sem a chave. | Se um relato real for ligado à nuvem, validar de novo: tamanho, retenção do log e aviso ao morador. Ver o [rascunho de LGPD](lgpd-rascunho.md). |
| T06 | O túnel da demonstração liga a API local à internet. | Túnel encerrado depois do teste. A API pede chave. A URL do sketch é um texto de exemplo. | Só abrir um túnel de novo com as chaves configuradas, e fechar ao terminar. |
| T07 | O modelo de ML tem ganho modesto (PR-AUC de teste 0,20 contra 0,083 do acaso) e a faixa "baixo" ainda contém 24% das linhas com evento. Um morador pode ler "baixo" como "seguro". | A decisão imediata vem do nível medido pelo nó, que não usa o modelo. O modelo não está ligado à API nem à nuvem. | Nunca mostrar "sem risco". Mostrar "sem aviso do modelo" junto de uma frase sobre o limite. Detalhes na seção 17 do notebook de ML. |
| T08 | Segredo no código ou no histórico. O relatório de AWS conta que a chave do dispositivo apareceu em testes e foi rotacionada. | Chaves só em variável de ambiente da Lambda (cifradas em repouso) e no terminal de teste. `.env` ignorado. Busca por padrões de chave no repositório não achou nada em 12/11 (seção 9). | Rodar a busca de novo antes de entregar. Em produção, Secrets Manager. Nunca imprimir chave em log. |
| T09 | O sketch usa `setInsecure()`, ou seja, não valida o certificado do servidor. Alguém no meio do caminho poderia alterar a leitura. | O endpoint do API Gateway usa HTTPS. A falha é do firmware, aceita na demonstração (Wokwi). | Em produção, fixar o certificado da CA no firmware. Registrar como limitação. |
| T10 | A internet cai durante a enchente. | O alerta local não depende de rede. A fila em memória guarda as leituras e reenvia com backoff. A API e a Lambda detectam repetição pelo `seq`. | Documentar. A fila é de RAM e some se o nó reiniciar. |
| T11 | O cadastro tem nome, telefone, e-mail e a data do consentimento. É o dado mais sensível do sistema quando existir de verdade. | Existe só no modelo Oracle com dados fictícios, sem ligação com a AWS. A telemetria não leva dado pessoal. | Só ligar ao alerta com consentimento, finalidade escrita e acesso restrito. Ver o rascunho de LGPD. |
| T12 | Entrada fora do formato ou hostil. | A Lambda valida tipo e faixa de todos os campos (422) e não usa SQL: só faz `PutItem` parametrizado pela biblioteca. Mensagens de erro genéricas. | Se um painel exibir dados do banco, escapar o texto na saída. |
| T13 | Um POST válido repetido cria duplicata. | A API Python e a Lambda recusam o mesmo `device_id` e `seq` (409). O relatório mostra o 409 na repetida. | Nada além de manter o teste. |
| T14 | O alerta aos moradores é um e-mail para quem assinou o tópico do SNS. Não há reenvio, nem aviso de "resolvido", e o alarme é por dispositivo e por minuto. O cadastro do Oracle não está ligado. | O alarme `Alertas >= 1` passou a "Em alarme" e o e-mail chegou no teste (capturas 07 e 10). | SMS e ligação com o cadastro, como evolução futura declarada. Para a entrega, dizer com clareza que o aviso é por e-mail a assinantes. |
| T15 | `requirements.txt` da API usa `>=` sem versão fixa. A Lambda não usa pacote externo. | `pip-audit` não achou vulnerabilidade conhecida em 12/11. | Fixar as versões depois da última instalação e repetir a auditoria antes da entrega. |

## 7. As ameaças da nuvem que o roteiro mandou conferir

| Item do roteiro | Onde está neste inventário | Situação |
|---|---|---|
| Banco RDS aberto à internet | Antiga T03 | Não se aplica mais. O projeto usa DynamoDB, sem porta de banco aberta. O risco virou a permissão ampla da LabRole (T03) |
| Function URL sem autenticação | T01 e T02, prioridade 5.1 | Substituída por API Gateway com chave por dispositivo. Feito e testado (401 sem chave válida) |
| Token da IA | Antiga T08 | Não se aplica mais. A Hugging Face saiu do projeto e não há token de IA |
| Custo por excesso de chamadas | T04, prioridade 5.2 | Limite de taxa feito no API Gateway. Orçamento e concorrência reservada ainda não constam |

## 8. Privacidade e LGPD

O tratamento de dados pessoais e as propostas de base legal, consentimento e retenção ficam no [rascunho de LGPD](lgpd-rascunho.md), que foi atualizado junto com este inventário. Resumo do que mudou: a telemetria que vai à nuvem não tem dado pessoal, a nuvem não recebe relato nem coordenada, e o único dado pessoal tratado pela AWS é o e-mail do assinante do SNS.

## 9. O que foi verificado e o que só foi lido

Executado em 12/11, antes e depois dos controles da API Python:
- API local com `TestClient`: antes do controle, POST com leitura forjada sem chave deu 201, o mesmo `seq` de novo deu 409, corpo de 2 MB deu 201 e sessenta POSTs seguidos deram 201.
- `pytest` na `python-api`: 45 testes passaram (21 anteriores e 24 novos de segurança), com dois comportamentos conferidos por mutação.
- `prova_protecao.py` contra a API no ar: rota aberta 200, sem chave 401, chave errada 401, chave certa 201, chave de outro dispositivo 403, corpo de 9 KB 413, consulta sem chave de leitura 401, com ela 200, e uma rajada de 65 POSTs com o primeiro 429 na chamada 59.
- `pip-audit` sobre `python-api/requirements.txt`: sem vulnerabilidade conhecida.
- Busca por padrões de segredo (`git grep`) e por arquivos `.env`, `.pem` e `.key` rastreados: nada encontrado. Não rodei o `gitleaks`.

Conferido pelo relatório de AWS do Charles (15/11), com as capturas em `aws/evidencias/`:
- Teste ponta a ponta na conta real: 201 nos três cenários (OK, ATENCAO, ALERTA), 409 na repetida, 401 sem chave válida.
- Itens gravados no DynamoDB, alarme em estado "Em alarme" e e-mail recebido do SNS.
- Política da função que só aceita o API Gateway.
- 34 testes automatizados da Lambda, citados no relatório. Não os reexecutei nesta atualização.

Apenas lido, sem teste real:
- Que o orçamento e a concorrência reservada não foram configurados (não aparecem no relatório).
- `setInsecure()` no sketch.
- O cabeçalho `X-API-Key` que o sketch envia não foi compilado nem rodado no Wokwi. É uma linha, mas precisa de um teste na próxima rodada de demonstração.

## 10. Pendências

| Quem | O que |
|---|---|
| Rafael | Rodar o roteiro de [roteiro-prova-protecao.md](roteiro-prova-protecao.md) e salvar os prints, se ainda não foi feito. |
| Rafael | Testar o sketch com a chave no Wokwi, colando a chave só lá. |
| Charles | Conferir no console da AWS se há alerta de orçamento e concorrência reservada na função. Se não houver, configurar ou declarar como limitação. |
| Rafael e Charles | Confirmar a pontuação da matriz da seção 4 e a troca da prioridade 3. |
| Dupla | Definir o canal do titular e os prazos de retenção do [rascunho de LGPD](lgpd-rascunho.md) e fazer a revisão jurídica. |

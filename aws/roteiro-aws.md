# Marca d'Água: roteiro AWS (ingestão e alerta)

> **Executado no AWS Academy (Learner Lab), região us-east-1, em 15/11/2026.** O enunciado da entrega de AWS não foi confirmado; o desenho cobre ingestão serverless, alarme e notificação. Se o enunciado pedir outra coisa, ajuste.

## Arquitetura

```
ESP32 --HTTPS/TLS--> API Gateway (HTTP API, throttling)
                          |
                       Lambda (lambda_ingestao.py)
                        |            \
                  DynamoDB          CloudWatch (métrica "Alertas", via EMF)
              (criptografado)            |
                                  Alarme (Alertas >= 1)
                                         |
                                    SNS (e-mail)
```

A Lambda repete a validação e a classificação da API FastAPI, com os mesmos limites e limiares (`nivel_cm` 120/180, `chuva_mm_h` 15/30, `umidade_pct` 90/95). Esses limiares ainda são provisórios; se mudarem, altere nos dois lugares.

## Segurança por padrão

| Camada | Medida |
|---|---|
| Em trânsito | HTTPS do API Gateway (TLS) |
| Autenticação | `x-api-key` por dispositivo, lida da variável `DEVICE_KEYS`; 401 igual para chave errada ou dispositivo desconhecido |
| Autorização | Role da Lambda com apenas `dynamodb:PutItem` na tabela e escrita de logs |
| Entrada | Limite de 2 KB, validação de todos os campos, risco sempre recalculado no servidor |
| Em repouso | DynamoDB com criptografia (padrão da AWS; opcionalmente chave KMS própria) |
| Abuso | Throttling na rota (ex.: 5 req/s, burst 10) |
| Logs | Sem chave e sem corpo completo |

Observação: guardar chaves em variável de ambiente serve para a entrega. Em produção o caminho seria o Secrets Manager.

## Passo a passo no console

1. **DynamoDB**: criar a tabela `marca_dagua_leituras`, chave de partição `device_id` (String, com sublinhado, sem espaço), chave de classificação `seq` (Number), modo sob demanda. Criptografia em repouso com chave de propriedade da AWS. Atenção: um nome de chave errado gera `ValidationException` e HTTP 500 na API.
2. **IAM**: no Learner Lab não é possível criar roles; a Lambda usa a role pronta **LabRole**. Em produção, o desenho correto é uma role própria com `AWSLambdaBasicExecutionRole` mais uma política embutida só com `dynamodb:PutItem` no ARN da tabela.
3. **Lambda**: criar a função `marca-dagua-ingestao` (Python 3.12, role LabRole, timeout 10 s), subir `lambda_ingestao.py` renomeado para `lambda_function.py` (foi assim no deploy; ou ajustar o handler para `lambda_ingestao.lambda_handler`). Variáveis de ambiente:
   - `TABELA` = `marca_dagua_leituras`
   - `DEVICE_KEYS` = `{"MD-POA-001": "<chave longa e aleatória>"}`

   Gerar a chave com `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
4. **API Gateway**: criar uma HTTP API `marca-dagua-api`, rota `POST /leituras` integrada à Lambda (payload 2.0), estágio `$default` com implantação automática. Throttling em *Proteger > Controle de utilização*: taxa 5 e burst 10 (no console aparecem como "limite de taxa" e "limite de intermitência").
5. **SNS**: criar o tópico `marca-dagua-alertas` e assinar um e-mail; confirmar a assinatura pelo link recebido. SMS exige configuração extra de conta, então use e-mail na demonstração.
6. **CloudWatch**: criar o alarme sobre a métrica `Alertas` (namespace `MarcaDagua`, dimensão `DeviceId`), estatística Soma, período de 1 minuto, limite `>= 1`, ação de notificar o tópico SNS. Em "dados ausentes", escolher "tratar como não violando".
7. **Teste**: `python testar_ingestao.py` com `API_URL`, `DEVICE_ID` e `DEVICE_KEY` definidos. Esperado: 201 para os três cenários, 409 na repetida, 401 sem chave válida. O cenário `alerta` deve disparar o e-mail em poucos minutos.

## Para a evidência (print/vídeo)

- Tabela do DynamoDB com os 3 itens (risco OK, ATENCAO, ALERTA).
- Gráfico da métrica `Alertas` e o alarme em estado "Em alarme".
- E-mail recebido do SNS.
- Saída do `testar_ingestao.py`.
- Política da role mostrando o privilégio mínimo.

## Testes locais

```
pip install pytest
pytest          # 34 testes, sem precisar de conta AWS
```

## Limitações assumidas

- O alerta aos moradores é um e-mail para quem assinou o tópico; o cadastro real de moradores (tabela `morador` do Oracle) não está integrado à AWS nesta entrega.
- O alarme é por dispositivo e por minuto; não há regra de reenvio ou de "alerta resolvido".
- Testado em conta AWS real (Learner Lab): 201 nos três cenários, 409 na repetida, 401 na chave errada, alarme em estado "Em alarme" e e-mail do SNS recebido.
- A chave do dispositivo fica em variável de ambiente da Lambda (serve para a entrega; em produção, Secrets Manager) e nunca vai para o repositório.

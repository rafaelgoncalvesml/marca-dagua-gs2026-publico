# Marca d'Água: desenho do projeto

Global Solution 2026.2, FIAP, 1TIA. Dupla: Rafael Gonçalves (RM 569461) e Charles Augusto (RM 571908). Entrega no Portal até 19/11/2026, 23h55.

## 1. Problema e público

Em Porto Alegre, o alerta de alagamento costuma chegar tarde ou por um canal que quem mora na área de risco não usa. Em 2024 a cidade viu isso de perto, e parte das estações de chuva do estado que deveriam transmitir em tempo real estavam fora do ar ([IHU](https://www.ihu.unisinos.br/639820-maioria-das-estacoes-do-governo-do-rs-que-enviam-dados-de-chuva-em-tempo-real-nao-funciona)).

Público: moradores de áreas de risco (ilhas, Sarandi, Humaitá e vizinhas) e a Defesa Civil municipal, que atende pelo 199.

Condições de acesso que o desenho considera: internet instável durante a enchente, parte dos moradores sem smartphone, pessoas com deficiência auditiva ou visual, e sensores comunitários de baixo custo no lugar de estações caras.

ODS relacionados: 11 (cidades e comunidades sustentáveis), 13 (ação contra a mudança do clima), 3 (saúde e bem-estar, pelo risco de vida e de doenças pós-enchente) e 10 (redução das desigualdades, porque levar monitoramento e alerta a bairros com pouca infraestrutura é o que o enunciado de Cloud destaca). O ODS 10 entrou depois do enunciado de Cloud e vale para o projeto todo.

## 2. Solução

Um nó comunitário com ESP32 mede o nível da água e a chuva, avisa no próprio local e envia as leituras a uma API. A API grava o histórico. Modelos de ML e de rede neural estimam o risco para as próximas horas. Na nuvem, uma função Lambda recebe a leitura do nó (ou de um simulador) e o relato do morador, classifica o risco por limiar, lê o relato com um modelo de IA da Hugging Face e grava tudo no RDS PostgreSQL. Quando a leitura passa do limite crítico, a resposta marca o alerta ao morador.

```
ESP32 (nível, chuva, temp/umid + LED e buzzer)
   -> alerta local (funciona sem internet)
   -> JSON
   -> API FastAPI -> CSV
   -> Oracle e MongoDB
   -> ML e rede neural (risco nas próximas horas)
   -> AWS: Lambda (POST /ocorrencias) -> Hugging Face (relato) -> RDS PostgreSQL
   -> resposta com risco e alerta; GET /ocorrencias para painel ou Defesa Civil
```

O envio de SMS ou e-mail ao morador (SNS) não faz parte do enunciado de Cloud e fica como evolução futura. A Lambda só marca `alerta: true` na resposta, no log como WARNING e no banco.

Inovação (AICSS): o nó guarda as leituras em memória quando a rede cai e reenvia quando volta, com número de sequência para a API detectar lacunas. O alerta local não depende de rede. Acessibilidade: LED para quem não ouve e padrões de buzzer distintos por nível para quem não enxerga.

## 3. Contrato de dados

Um JSON único, igual em AICSS, Python, Oracle, Mongo e AWS. Este é o rascunho; a versão final fica em `docs/contrato-json.md` quando o AICSS fechar os campos.

```json
{
  "device_id": "MD-POA-001",
  "seq": 1234,
  "ts": "2026-11-10T14:32:05-03:00",
  "nivel_cm": 182.4,
  "chuva_mm_h": 12.5,
  "temperatura_c": 24.1,
  "umidade_pct": 88.0,
  "status": { "nivel": "ALERTA", "chuva": "OK", "umidade": "OK" },
  "risco": "ATENCAO",
  "reenviado": false
}
```

Sem dado pessoal na telemetria. Morador e telefone existem só no cadastro, com consentimento.

### Formato da nuvem

O enunciado de Cloud define um corpo próprio para a Lambda, com uma métrica por envio:

```json
{
  "dispositivo_id": "MD-POA-001",
  "tipo": "esp32",
  "latitude": -30.0153,
  "longitude": -51.2395,
  "metrica": "nivel_agua_cm",
  "valor": 182.4,
  "relato": "A água já entrou no pátio"
}
```

Mapeamento a partir do contrato principal: `device_id` vira `dispositivo_id`, `nivel_cm` vira `metrica: nivel_agua_cm` e `chuva_mm_h` vira outro envio com `metrica: chuva_mm_h`. O `relato` vem do app do morador. As coordenadas acima são ilustrativas (região das ilhas) e devem ser trocadas pelas dos pontos reais. O código de apoio da disciplina lê `tipo_dispositivo`, mas o enunciado usa `tipo`: a Lambda final aceita os dois.

Limiares do nível (atenção e crítico) ficam num arquivo só, valendo para o sketch e para a Lambda. Os valores saem da cota de inundação oficial, ainda por conferir.

## 4. Dados e alvo do modelo

Dados reais obrigatórios (Statistical Computing não aceita sintético).

- Base principal: INMET, Porto Alegre, 2014 a 2025 (já usada na GS1).
- Alvo, plano A: nível do Guaíba acima da cota de inundação. Estação Cais Mauá (87450004) até maio de 2024 e Gasômetro (87450020) depois, com ajuste de 1,18 m nas cotas ([nota ANA e SGB](https://www.gov.br/ana/pt-br/assuntos/noticias-e-eventos/noticias/ana-e-servico-geologico-do-brasil-fazem-readequacoes-em-estacao-de-monitoramento-do-rio-guaiba-em-porto-alegre-rs/nota-institucional-conjunta-ana-sgb-gasometro-final.pdf/@@download/file)). Dependia de o HidroWeb liberar CSV, o que não aconteceu. A cota de inundação no Gasômetro precisa ser conferida na fonte oficial antes de virar limiar.
- Alvo, plano B (adotado em 06/11): chuva acumulada em 72 h acima de um limiar, calculada do INMET. O teste do HidroWeb falhou: os downloads csv e txt da 87450004 vieram vazios e a 87450020 devolveu só o resumo de vazão. O plano A ficou como alternativa descartada.
- Registrar no relatório qual plano foi usado e por quê.

## 5. Entregáveis por matéria

| Matéria | O que entra | Dono |
|---|---|---|
| AICSS | ESP32 no Wokwi: HC-SR04 (nível), pluviômetro basculante simulado por botão com contagem por interrupção (0,2 mm por pulso), DHT22. LED e buzzer. 3 comportamentos demonstrados, JSON, fila offline | Rafael |
| Python | API FastAPI: POST validado, regras de classificação, CSV, GET, indicador (total de alertas, nível máximo), 3 cenários de teste, instruções de execução | Charles |
| Cybersecurity | Inventário de ameaças do sistema, controles, proteção aplicada à API (chave por dispositivo lida do ambiente, validação de entrada, limite de requisições, limite de tamanho), LGPD no cadastro de moradores | Rafael |
| Data Science | Modelo lógico e relacional no Oracle Data Modeler (3FN, 4+ tabelas), script `oracle.sql`, 3 consultas, MongoDB com 10+ documentos e id comum, demonstração cruzada, ZIP no formato pedido | Charles |
| Machine Learning | Baseline e 2+ modelos, tuning com validação temporal, PR-AUC, ajuste de limiar, feature importance, slides e vídeo de até 5 min | Rafael |
| Redes Neurais | Sequência das últimas horas ou dias (LSTM ou GRU) contra um MLP, early stopping e dropout, comparação de configurações, demo com dados não vistos | Rafael |
| Statistical Computing | Itens 02 a 07 do enunciado sobre a base INMET: normal, testes de hipótese (6% com n=20 e 9% com n=25), regressão simples, múltipla e logística, relatório em PDF, .csv e .py | Charles |
| AI Challenges | Vídeo de até 7 min no YouTube (não listado), com rosto, nomes e RMs, UML, Kanban, ODS e as ideias dos convidados da live | Rafael narra, Charles faz UML e Kanban |
| Cloud Computing (Plataformas e Serviços Cognitivos) | Lambda com Function URL (GET /health, GET /ocorrencias, POST /ocorrencias com 400 e 201), log no CloudWatch (payload, dados, classificação, id; WARNING para inválida e crítica), classificação local por limiar, tabela `ocorrencias` no RDS PostgreSQL, IA no relato (Hugging Face, caminho A, token em variável de ambiente, falha sem derrubar a ingestão), simulador, teste de ponta a ponta, 4 imagens, README com ODS e vídeo de até 5 min | Charles (Rafael revisa o README e o ODS) |

Balanço: Rafael fica com 5 matérias contando AI Challenges, com a narração do vídeo. Charles fica com 4 mais UML e Kanban. Com o enunciado de Cloud publicado, a carga de Charles subiu para cerca de 11h20 e a de Rafael para cerca de 10h45, e 13/11 virou dia de execução.

## 6. Lições da GS1 aplicadas

- Repositório completo desde o início: uma pasta por matéria, README em português correto, `.gitignore` no primeiro commit, sem `.pkl` nem CSVs grandes versionados (o script que gera ou baixa fica no repositório).
- Sem segredo no código. O Lambda da GS1 trazia host e senha do banco escritos no arquivo. Aqui tudo vem de variável de ambiente, com `.env.example` sem valores. Se aquele RDS ainda existir, trocar a senha.
- D1 entregue e repositório sempre iguais: uma única fonte, sem versão "corrigida" fora do Git.
- Chuva simulada como pulsos de pluviômetro, não potenciômetro tratado como mm/h.
- Métricas que resistem a crítica: alvo com mais exemplos positivos, PR-AUC, limiar ajustado, validação temporal e intervalo de confiança ou número de eventos reportado junto da métrica. Chega de F1 de 0,29 em 6 eventos.
- API REST em vez de CLI: o D4 da GS1 era um menu de terminal e a GS2 exige endpoints.
- Na Cloud, não copiar o código de apoio sem revisar: ele traz coordenadas de outra cidade, lê `tipo_dispositivo` em vez de `tipo`, responde 500 (com a mensagem de erro interna) quando `valor` não é número e deixa a Function URL sem nenhuma proteção. Os ajustes viram parte da entrega e o risco restante entra no relatório de Cyber.

## 7. Riscos e como tratar

| Risco | Tratamento |
|---|---|
| CSV do nível do Guaíba não sai do HidroWeb | Plano B (chuva 72 h do INMET), decisão até 07/11 |
| Wokwi não alcança o localhost | Wokwi-GUEST só vai à internet. Para a demo, túnel (cloudflared ou ngrok) até a API. Plano de reserva: requisições HTTP simuladas com o mesmo JSON, que o enunciado do Python aceita, mais a saída serial do Wokwi como evidência |
| Base de dados da Redes Neurais precisa de validação | O INMET não estava na lista de sugestões. Resolvido em 05/11 (pedido às 23:14, resposta às 23:27): o professor Mateus Azevedo Dalbone de Carvalho confirmou por escrito no Teams ("Ok, pode usar sim. As bases são aceitas."). Print em `docs/evidencias/rna-validacao-base-inmet-pedido-e-resposta.png`, para anexar ao relatório |
| Python não instalado nesta máquina | Rafael instala o Python 3.12 (winget) no dia 1. Notebooks rodam no Colab |
| Conta AWS sem permissão para Lambda ou RDS, ou sessão que expira | Conferir no console em 06/11. Se a sessão for limitada, anotar o que religar e deixar tudo de pé em 19/11 |
| Lambda fora da VPC exige RDS acessível pela internet | Senha forte só em variável de ambiente. O risco entra no relatório de Cyber como limitação conhecida |
| Hugging Face fora do ar ou endereço antigo (410) | Usar só router.huggingface.co. A falha da IA não derruba a ingestão: a leitura segue classificada por limiar e gravada |
| Tempo: 30 min por dia não cobre 4 matérias | Claude escreve código, notebooks e textos. Vocês revisam, rodam e tiram prints. Três dias de execução de cerca de 90 min para o que só vocês fazem |
| Ideias da live de 04/11 | Rafael ou Charles anota 3 ideias da gravação até 08/11, para entrar no vídeo e na classificação |

## 8. Cronograma em fases

Hoje é quinta, 05/11. O prazo é quinta, 19/11. Meta interna de fechamento: quarta, 18/11, com 19/11 só de reserva.

| Fase | Datas | Foco |
|---|---|---|
| 0. Fundação | 05 a 06/11 | Python instalado, repositório, contrato JSON, teste do HidroWeb, e-mail ao professor de Redes Neurais |
| 1. Dados e dispositivo | 07 a 10/11 | Nó no Wokwi, API com CSV, base INMET limpa. Dia de execução em 10/11 (Wokwi mais API) |
| 2. Modelos e armazenamento | 11 a 14/11 | Estatística, ML, rede neural, Oracle e Mongo, inventário de ameaças. RDS criado em 11/11 e tabela em 12/11. Dias de execução em 13/11 (Lambda no ar e teste de ponta a ponta com os 4 prints) e 14/11 (SQL Developer e prints) |
| 3. Integração | 15 a 16/11 | Proteção da API, relatórios finais, UML e Kanban, conferência do pacote de Cloud |
| 4. Fechamento | 17 a 18/11 | Vídeos gravados e publicados, incluindo o de 5 min da nuvem (dia de execução em 17/11), PDFs finais e conferência de cada ZIP em 18/11 |
| Reserva | 19/11 | Envio no Portal, de preferência antes das 12h |

O roadmap dia a dia, com a tarefa de cada um, sai deste desenho e vai para o dashboard.

## 9. Repositório e padrão de trabalho

Repositório novo, nome de trabalho `marca-dagua-gs2026`, estrutura:

```
docs/               desenho, contrato JSON, UML, Kanban
aicss-sensores/     sketch, diagram.json, evidências do Wokwi
python-api/         FastAPI, testes, dados de exemplo
ciberseguranca/     inventário de ameaças, controles, LGPD
dados-oracle-mongo/ .dmd, oracle.sql, mongodb.txt
estatistica/        notebook ou .py, relatório
ml/                 notebook, métricas
redes-neurais/      notebook, curvas, demo
aws/                funções, configuração, diagrama
desafio-aic/        roteiro e arquivos do vídeo
```

Commits no padrão `tipo(matéria): descrição curta`, um por entrega pequena, sem atribuição automática de ferramenta. O histórico é portfólio.

## 10. Dashboard de roadmap

HTML, CSS e JS puros, sem CDN nem fonte externa, em pasta própria fora do repositório (ferramenta da dupla). Gera um arquivo HTML único (`Dashboard GS2.html`, com `npm run build`) que abre com dois cliques, sem servidor; o servidor Node curto ficou só para desenvolvimento. Conteúdo: resumo do projeto, membros e funções por matéria e no projeto geral, linha do tempo de 05/11 a 19/11, tarefa diária de cada pessoa (cerca de 30 min, com marcação dos dias de execução), visão por matéria e uma página para copiar a tarefa do Charles de cada dia. Progresso salvo no navegador. Visual claro e sóbrio, sem padrões de interface gerada.

## 11. Fora de escopo

Dispositivo físico (usamos simulação, que o enunciado aceita), interface gráfica para o morador, integração real com a Defesa Civil, qualquer funcionalidade fora do que as matérias pedem. O que ficar como evolução futura vai identificado como tal no vídeo.

## 12. Pendências que dependem de decisão ou de ação dos dois

- Conta do GitHub para o repositório.
- Permissões da conta AWS para Lambda e RDS (conferir em 06/11).
- Token Read da Hugging Face (07/11).
- Forma de envio da entrega de Cloud no Portal (12/11).
- Anotações da live de 04/11.
- Cota de inundação oficial no Gasômetro, que também define os limiares da nuvem.

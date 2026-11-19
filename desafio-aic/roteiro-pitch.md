# Roteiro do pitch de AI Challenges (até 7 minutos)

Alvo de gravação: 6 min 40 s, para ter 20 s de margem. O vídeo passa de 7 minutos e a entrega perde valor, então corte falas antes de cortar demonstração.

Requisitos do enunciado: rosto de quem narra visível o tempo todo (um canto da tela), sem música, código ou hardware em funcionamento, nomes e matrículas na primeira ou na última tela, YouTube como não listado. Como a nota de demonstração é a maior (3,0), o centro do vídeo é o Wokwi rodando e o trecho da nuvem.

Os blocos marcados com `PREENCHER` dependem de coisa que ainda não chegou: o print do Kanban. O PNG da UML já existe em `docs/uml-sequencia.png` e as 3 ideias da live de 04/11 foram confirmadas pela equipe. Não invente conteúdo para esses espaços. Se algum não chegar, corte a frase e use o tempo na demonstração.

Atualizado em 15/11 com a entrega do Charles: a nuvem é AWS (API Gateway, Lambda, DynamoDB, CloudWatch e SNS) e os dados são Oracle e MongoDB. Os blocos de arquitetura, nuvem, dados, segurança e gestão foram reescritos em cima disso. O trecho de 1 minuto da nuvem deixou de ser obrigatório: você narra por cima dos prints de `aws/evidencias/`, o que também resolve o requisito do rosto. Se o Charles mandar um clipe, ele substitui esse bloco.

| Tempo | Bloco | Critério (pontos) |
|---|---|---|
| 0:00 a 0:20 | Abertura e identificação | Requisitos (1,5) |
| 0:20 a 1:05 | Problema, público e solução | Clareza (1,5) |
| 1:05 a 1:35 | ODS e ideias da live | Clareza (1,5) |
| 1:35 a 2:20 | Arquitetura, UML e as disciplinas | Integração (2,5) |
| 2:20 a 3:15 | Wokwi funcionando | Demonstração (3,0) |
| 3:15 a 4:20 | Nuvem na AWS | Demonstração (3,0) |
| 4:20 a 5:07 | Dados, IA e validação | Demonstração (3,0) |
| 5:07 a 5:47 | Gestão das entregas | Gestão (1,5) |
| 5:47 a 6:30 | Acessibilidade, segurança, evolução futura | Gestão e integração |
| 6:30 a 6:40 | Fecho e tela final | Requisitos (1,5) |

## 0:00 a 0:20, abertura e identificação

Na tela: slide de capa com "Marca d'Água" e, bem visíveis e grandes, Rafael Gonçalves RM 569461 e Charles Augusto RM 571908. Essa é a primeira tela, e o mesmo slide volta no fim.

> Oi, eu sou o Rafael Gonçalves, RM 569461, e este é o Marca d'Água, que fiz com o Charles Augusto, RM 571908, para a Global Solution 2026.2. É um nó comunitário que avisa sobre alagamento em Porto Alegre, mesmo quando a internet cai.

## 0:20 a 1:05, problema, público e solução

Na tela: slide com três itens (problema, público, solução). Sem foto de pessoa gerada por IA. Se usar imagem da enchente de 2024, use foto com fonte e crédito.

> Em Porto Alegre, o aviso de alagamento costuma chegar tarde, ou por um canal que quem mora em área de risco não usa. Em 2024, parte das estações de chuva do estado estava fora do ar. Quem sofre é o morador das ilhas, do Sarandi e do Humaitá, e a Defesa Civil. Na enchente a internet cai, nem todos têm smartphone e há pessoas com deficiência auditiva ou visual. A solução é um ESP32 com sensores de nível, chuva, temperatura e umidade, que avisa no local por LED e buzzer, sem rede, e envia as leituras para a nuvem.

## 1:05 a 1:35, ODS e ideias da live

Na tela: os quatro ícones de ODS (3, 10, 11 e 13) com o nome de cada um, e a seguir um slide com as 3 ideias da live (previsão de enchentes com alertas à população, soluções comunitárias para emergências, tecnologias de apoio a pessoas com deficiência), cada uma ao lado do que o projeto tem para ela. As ideias foram confirmadas por vocês na gravação de 04/11. Se souberem o nome de quem falou cada uma, ponha no slide e na fala; sem o nome confirmado, deixe sem.

> O projeto se liga a quatro ODS: o 11, cidades sustentáveis, e o 10, menos desigualdades, porque levam monitoramento a bairros com pouca infraestrutura. O 3, saúde, pelo risco de vida na enchente. E o 13, clima, pelo histórico de eventos extremos. Na live de lançamento, três ideias dos convidados batem com o que construímos. Previsão de enchentes com alertas à população: é o nosso modelo das próximas 72 horas e o aviso por LED, buzzer e e-mail. Soluções comunitárias para emergências: o nó fica no bairro e funciona sem internet. Tecnologias de apoio a pessoas com deficiência: o aviso é visual e sonoro ao mesmo tempo.

Cada ideia precisa caber em uns 5 segundos. Se ficar longo, tire palavras das ODS e não das ideias, porque as ideias entram na classificação das melhores propostas.

## 1:35 a 2:20, arquitetura, UML e as disciplinas

Na tela: primeiro o diagrama de arquitetura (nó, API em Python, nuvem na AWS, bancos, modelos), com o nome da disciplina em cada seta, e na hora de falar da UML o PNG `docs/uml-sequencia.png`. O diagrama da AWS está em `aws/roteiro-aws.md` e serve de base. O código-fonte do UML é `docs/uml-sequencia.puml`.

> O nó mede e avisa. O mesmo JSON segue para a API em Python e para a nuvem na AWS, que valida e classifica do mesmo jeito. O ML e a rede neural usam a chuva do INMET para estimar o risco das próximas 72 horas, a segurança protege a API e a nuvem, e a estatística descreveu essa base. Este é o diagrama de sequência da nuvem. A chave é conferida antes de tudo: chave errada volta 401. Leitura repetida volta 409. Só uma gravação nova no DynamoDB publica a métrica que, em alerta, dispara o e-mail. Ele deixa claro o que cada resposta significa para quem integra o nó com a nuvem.

Duração: a fala tem cerca de 115 palavras, perto de 48 s, e o bloco tem 45 s. Se estourar no ensaio, corte "e a estatística descreveu essa base" e a última frase. O que o diagrama diz foi conferido contra `aws/lambda_ingestao.py` (401 antes da validação, 409 pela gravação condicional, métrica só depois de gravar). Ele não mostra o 422 de campo inválido. Não cite o 422 como se estivesse na tela.

## 2:20 a 3:15, Wokwi funcionando

Na tela: o Wokwi com o `sketch.ino` e a saída serial ao lado. Mostre três coisas em ordem: nó em condição normal, cinco cliques no botão do pluviômetro (chuva forte) e o sensor de distância arrastado até 190 cm (nível crítico). O ponto central é LED aceso e linha `[ALERTA]` no mesmo quadro. Faça um ensaio antes: a janela de chuva é de 60 s, e os cinco cliques precisam caber nela. Passos exatos em `aicss-sensores/roteiro-cenarios.md`. Reinicie a simulação entre os cenários.

Plano B, se o Wokwi não abrir ou travar no dia: use as capturas de `aicss-sensores/evidencias/` (02-chuva-forte-led-serial.png e 03-nivel-critico-led-serial.png) e diga que são capturas da simulação. Isso vale menos que rodar ao vivo.

> Este é o nó rodando no Wokwi: ESP32, sensor de nível ultrassônico, pluviômetro simulado por botão e sensor de temperatura e umidade. Está tudo normal, LED apagado. Vou simular chuva forte: cinco pulsos em menos de um minuto passam de 50 milímetros por hora. O LED acende fixo, o buzzer toca três bipes e a serial mostra ALERTA e o JSON do contrato. Agora o nível: baixo a distância do sensor, a água sobe para 208 centímetros, e o alerta vem de novo, desta vez pelo nível. Se a rede cai, o nó guarda até 60 leituras e reenvia em ordem quando volta. O alerta local não depende de internet.

Se couber, 5 s com a captura `10-05-reenvio-em-ordem.jpg` mostrando o reenvio. Se não couber, corte a última frase.

## 3:15 a 4:20, nuvem na AWS

Na tela, em ordem, com seu rosto no canto o tempo todo: `aws/evidencias/06-teste-ponta-a-ponta.png` (saída do `testar_ingestao.py`), `08-dynamodb-itens.png`, `07-cloudwatch-alarme.png` e `10-sns-email-alerta.png`. Uns 13 s por captura. Se sobrar tempo, `04-lambda-politica-recursos.png` na hora de falar da função. Se o Charles mandar um clipe com a nuvem funcionando, ele entra no lugar das capturas, com a voz clara e sem música, e você fala só uma frase de introdução.

Aviso para não prometer demais: o que foi testado é o simulador de leituras (`testar_ingestao.py`) contra a AWS Academy, não o ESP32 do Wokwi enviando para a nuvem. Diga "simulador" e não "o nó".

> Agora a nuvem, no AWS Academy. A leitura entra por uma API do API Gateway, com HTTPS e limite de requisições, e cai numa função Lambda. A Lambda confere a chave do dispositivo, valida todos os campos, recalcula o risco no servidor e grava no DynamoDB, que fica criptografado. Aqui o simulador mandou três cenários: o teste devolveu 201 nos três, 409 para a leitura repetida e 401 para chave errada. Estes são os itens no DynamoDB, com risco normal, atenção e alerta. Quando a leitura é de alerta, a Lambda publica uma métrica no CloudWatch, o alarme passa para "em alarme" e o SNS manda este e-mail. Por enquanto o aviso vai para quem assina o tópico. O cadastro de moradores do Oracle ainda não está ligado a ele.

## 4:20 a 5:07, dados, IA e validação

Na tela: seis segundos de cada, nesta ordem. A consulta do Oracle que junta as cinco tabelas (consulta 3 do `oracle.sql`, quem foi avisado em cada alerta). Uma consulta do `mongodb.txt` no mongosh ou no Compass. O gráfico de precisão por recall do notebook de ML. A tabela de teste da rede neural. Os números são os dos notebooks salvos. Confira antes de gravar.

> Os dados ficam em dois bancos. O Oracle tem seis tabelas na terceira forma normal: áreas de risco, dispositivos, leituras, moradores, alertas e notificações. O MongoDB guarda o JSON bruto do nó e os relatos dos moradores em texto livre. O elo é o código do dispositivo. São dados de demonstração e ainda não estão ligados à nuvem. Para o modelo, usamos a estação A801 do INMET, 105 mil horas. No machine learning, a regressão logística fez 0,20 de PR-AUC no teste contra 0,083 do acaso, sem se separar da Random Forest. Na rede neural, as redes recorrentes não ganharam da regressão logística. O ganho é modesto, então o aviso imediato vem do nível medido pelo nó e o modelo é um sinal complementar, ainda não ligado à API nem à nuvem.

## 5:07 a 5:47, gestão das entregas

Na tela: o print do Kanban que o Charles manda, depois o dashboard de roadmap com a linha do tempo de 05 a 19/11.

> Somos dois e dividimos por matéria. Eu fiquei com sensores, segurança, machine learning, rede neural e este vídeo. O Charles ficou com Python, dados, estatística, nuvem, UML e Kanban. Planejamos dia a dia num roadmap e acompanhamos no quadro. Houve problemas. O CSV do nível do Guaíba não saiu do HidroWeb, e trocamos o alvo para a chuva acumulada do INMET, registrado no relatório. O Wokwi não alcança o computador local, então usamos um túnel. E no Learner Lab não dá para criar uma função de acesso própria, então a Lambda usa a LabRole que já vem pronta.

## 5:47 a 6:30, acessibilidade, segurança, evolução futura

Na tela: a lista do que está implementado ao lado da lista do que é evolução futura, com os dois títulos legíveis. Pode usar o resultado do `prova_protecao.py` (401, 403, 413, 429) em `ciberseguranca/evidencias/prova-protecao-saida.txt`, ou rodar o script ao vivo se a API estiver no ar.

> Acessibilidade: LED para quem não ouve e padrões de buzzer por nível para quem não vê. Segurança: inventariamos 15 ameaças, e a API tem chave por dispositivo e responde 401, 403, 413 e 429 nos casos certos. A nuvem também exige a chave, limita o corpo a 2 KB e a taxa de requisições. A LabRole é ampla; em produção seria uma função só com permissão de gravar na tabela. A telemetria não tem dado pessoal e o relato do morador tem rascunho de LGPD. Os modelos rodam em CPU. Ainda é evolução futura: SMS ao morador, app do morador, ligar o modelo à API e à nuvem, ligar o cadastro do Oracle ao alerta e usar previsão do tempo.

## 6:30 a 6:40, fecho e tela final

Na tela: o mesmo slide de capa com nomes e RMs, bem visível, por pelo menos 8 segundos, sem cortar a fala no meio.

> Obrigado. Rafael Gonçalves, RM 569461, e Charles Augusto, RM 571908. Marca d'Água.

## Lista de telas para deixar abertas antes de gravar

1. Slide de capa e slides de problema, ODS, arquitetura e evolução futura (na ordem do vídeo).
2. Wokwi com o projeto de `aicss-sensores/` aberto, `sketch.ino` à esquerda e a serial visível.
3. Capturas de `aws/evidencias/` (06, 08, 07 e 10, nessa ordem) abertas, e o clipe do Charles se ele mandar. Essa pasta só existia na branch `feat/aws` (não está na main) e foi trazida para a `feat/ml-final`.
4. `docs/uml-sequencia.png` e o print do Kanban. Para os dados: `oracle.sql` com a consulta 3 rodada no SQL Developer e `mongodb.txt` rodado no mongosh.
5. Notebook de ML na tabela de teste e notebook de RNA na tabela de teste.
6. `ciberseguranca/evidencias/prova-protecao-saida.txt`, ou terminal com a API no ar.
7. Dashboard de roadmap aberto na linha do tempo.

Feche e-mails, notificações e abas pessoais antes de gravar. Faça um ensaio cronometrado e corte o que passar de 6 min 40 s.

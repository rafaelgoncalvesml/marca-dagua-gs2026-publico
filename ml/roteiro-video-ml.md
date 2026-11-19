 # Roteiro do vídeo de Machine Learning (até 5 minutos)

Alvo de gravação: 4 min 40 s, para sobrar folga. O enunciado pede problema, decisões de modelagem, resultados, aplicação prática e uma demonstração do notebook ou das previsões. Link do YouTube como não listado, ou Google Drive com acesso aberto.

Os números abaixo são os das saídas salvas em `notebook_ml.ipynb` (execução com `SEED = 42`). Grave a partir do mesmo notebook que vai ser entregue. Se você rodar de novo e algum número mudar na terceira casa, troque no roteiro antes de gravar.

Antes de gravar: abra o notebook já executado, com as saídas visíveis, e deixe as seções 6, 9, 11, 12, 14 e 16 marcadas no índice lateral para pular entre elas sem procurar. Zoom do navegador em 125% para o texto ler bem na gravação. Rosto num canto durante todo o vídeo, sem música.

| Tempo | Bloco | Na tela |
|---|---|---|
| 0:00 a 0:30 | Problema e público | Capa com nomes e RMs, depois o mapa do projeto |
| 0:30 a 1:15 | Dados e preparação | Seções 3, 5 e 6 do notebook |
| 1:15 a 2:05 | Decisões de modelagem | Tabelas das seções 8, 9 e 10 |
| 2:05 a 2:55 | Resultados | Tabela e gráfico da seção 11 |
| 2:55 a 3:23 | Importância das variáveis | Gráfico da seção 12 |
| 3:23 a 4:15 | Demonstração das previsões | Seções 14 e 16 |
| 4:15 a 4:40 | Limites e evolução | Seção 17 |

## 0:00 a 0:30, problema e público

Na tela: capa com "Marca d'Água, Machine Learning", Rafael Gonçalves RM 569461 e Charles Augusto RM 571908. Aos 0:12, troque para o diagrama do projeto (ESP32, API, nuvem, modelo).

> Oi, eu sou o Rafael. Com o Charles, fizemos o Marca d'Água, um nó com sensores que avisa sobre alagamento em Porto Alegre. O modelo é um segundo sinal: a cada seis horas, ele responde se a chuva das próximas 72 horas vai passar de 50 milímetros. Para o morador, um alarme perdido custa mais que um falso, então avalio com PR-AUC e recall, não com acurácia.

## 0:30 a 1:15, dados e preparação

Na tela: seção 3 (a tabela de qualidade, 105.192 horas, nenhuma ausente na grade), seção 5 (a taxa de positivos de 6,85%) e a tabela de treino e teste da seção 6.

> Os dados são reais, da estação A801 do INMET em Porto Alegre, de 2014 a 2025: 105 mil horas. Montei 19 variáveis só com o que já se sabia na hora da previsão, como chuva acumulada, pressão, temperatura e época do ano, em amostra a cada seis horas. O alvo é positivo em cerca de 7% das linhas. A divisão é no tempo: treino até 2022, teste de 2023 a 2025, com 72 horas de folga no meio, porque o alvo olha 72 horas à frente. Imputação e padronização aprendem só no treino, e seis testes conferem que não há vazamento.

## 1:15 a 2:05, decisões de modelagem

Na tela: tabela da seção 8 (baselines), da 9 (modelos com hiperparâmetros padrão) e da 10 (depois do tuning).

> Comparei dois baselines, um que não usa informação nenhuma e a persistência, que repete a chuva das últimas 72 horas. Depois, três modelos: regressão logística, Random Forest e Gradient Boosting. Com os parâmetros padrão, a Random Forest tira 1,00 de PR-AUC no treino e 0,10 na validação. Ela decorou o treino. Fiz o tuning com GridSearchCV e RandomizedSearchCV, sempre com validação cruzada no tempo e uma folga de 72 horas entre treino e validação. Limitei a profundidade das árvores, e a nota de treino caiu para perto de 0,22. A validação ficou entre 0,11 e 0,12 nos três modelos.

## 2:05 a 2:55, resultados

Na tela: tabela e gráfico de precisão por recall da seção 11. Passe o cursor pelos intervalos de confiança.

> No teste, os três modelos ficam entre 0,18 e 0,20 de PR-AUC. O acaso dá 0,083 e a persistência 0,12. Os três ganham dos dois, mas os intervalos de confiança se sobrepõem, então não dá para dizer que um é melhor que o outro. Escolhi a regressão logística pelos critérios de desempate. Ela sobreajusta pouco, tem coeficientes que dá para ler, e as probabilidades ficam perto da frequência observada. No limiar que pega 70% dos eventos, ela dispara em 49% das linhas, contra 71% da Random Forest e 73% do Gradient Boosting. Mesmo assim, a precisão é de 13%. Esse é o custo real de não perder alarme.

## 2:55 a 3:23, importância das variáveis

Na tela: gráfico duplo da seção 12 (coeficientes e permutação por grupo).

> Pela importância por permutação, estação do ano, pressão e temperatura com umidade são as três que mais pesam. A chuva acumulada pesa praticamente zero. Isso quer dizer que boa parte do ganho vem de climatologia: em Porto Alegre as chuvas fortes se concentram em certas épocas. E a permutação mostra o que o modelo usa, não o que causa a chuva.

## 3:23 a 4:15, demonstração das previsões

Na tela: seção 14 (as faixas) e seção 16 (tabela de exemplos e a linha do tempo de abril de 2024). Esta é a parte da demonstração, então rode a célula da tabela de exemplos ao vivo se o notebook estiver aberto na sessão. Se não estiver, mostre a saída salva.

> Transformei a probabilidade em três faixas: baixo, atenção a partir de 0,054 e alerta a partir de 0,131. Agora, exemplos reais do teste, escolhidos por regra, não a dedo. Em 15 de junho de 2025 o modelo deu alerta, com probabilidade de 0,16, e vieram quase 54 milímetros. Acerto. No maior episódio do teste, abril de 2024, com 280 milímetros em 72 horas, o modelo marcou só 0,05 no início, embora tivesse chegado a 0,19 um dia antes. E em 30 de março de 2023 deu alerta com 0,46 e quase não choveu, 1,8 milímetro. Esse é o pior alarme falso. Nos 29 episódios do teste, o alerta apareceu nas 24 horas antes de 5 deles.

## 4:15 a 4:40, limites e evolução

Na tela: lista de limitações da seção 17, depois o mesmo diagrama do começo.

> O ganho sobre o acaso é modesto, o aviso falso é frequente e ele reage mais à chuva que já caiu do que à que vem. Ainda não está ligado à API nem à nuvem, e o aviso imediato vem do nível medido pelo nó. Falta usar previsão numérica do tempo, calibrar as probabilidades e incluir mais estações. Obrigado.

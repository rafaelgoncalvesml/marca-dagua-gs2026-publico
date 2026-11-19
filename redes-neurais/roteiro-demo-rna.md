# Roteiro da demonstração da rede neural

Alvo de gravação: 3 min 40 s. O enunciado de Redes Neurais pede a demonstração em vídeo com entradas que a rede não viu, as saídas produzidas, o que ela acerta, onde erra e como entraria na solução. Ele não fixa duração, então mantenha curto.

Os números são os das saídas salvas em `notebook_redes_neurais.ipynb` (`SEED = 42`, TensorFlow 2.21). Duas coisas antes de gravar:

1. A função `prever` da seção 9 só roda se os modelos estiverem na memória do Colab. A execução completa treina 57 redes e leva cerca de 30 minutos. Rode tudo uma vez, deixe a sessão aberta e grave nela. Se a sessão cair, grave com as saídas salvas e não diga "rodando agora" na parte da `prever`.
2. Se uma nova execução mudar algum número na terceira casa, troque no roteiro antes de gravar. A rede escolhida pela regra (maior PR-AUC de validação) foi a LSTM, e uma nova execução pode apontar outra.

Rosto num canto, sem música. Zoom em 125%.

| Tempo | Bloco | Na tela |
|---|---|---|
| 0:00 a 0:28 | Problema, entrada e saída | Seção 1 e a janela de exemplo da seção 4 |
| 0:28 a 1:00 | Arquiteturas e primeiro treino | Seção 5 (parâmetros) e curvas da seção 6 |
| 1:00 a 1:33 | Regularização e resultado no teste | Tabelas das seções 7 e 8 |
| 1:33 a 2:43 | Demonstração com exemplos não vistos | Seção 9, tabela e linha do tempo |
| 2:43 a 3:13 | A função `prever` e a integração | Célula final da seção 9 |
| 3:13 a 3:40 | Limites e evolução | Fim da seção 9 (e seção 11) |

## 0:00 a 0:28, problema, entrada e saída

Na tela: o título do notebook com nomes e RMs, depois o gráfico de uma janela de 72 horas (seção 4).

> Esta é a rede neural do Marca d'Água, de Rafael Gonçalves e Charles Augusto. O nó avisa no local, e a rede dá um segundo sinal. Ela recebe as últimas 72 horas, uma linha por hora, com chuva, pressão, temperatura, umidade, vento e rajada, mais a época do ano, e devolve a probabilidade de a chuva das 72 horas seguintes passar de 50 milímetros.

## 0:28 a 1:00, arquiteturas e primeiro treino

Na tela: a contagem de parâmetros da seção 5 (MLP 29.953, GRU 4.417, LSTM 5.569) e o gráfico de curvas da seção 6.

> Comparei três redes. Um MLP, que recebe a janela achatada, e duas redes recorrentes, GRU e LSTM, que leem hora por hora. No primeiro treino, com Adam, taxa de aprendizado de 0,001, lotes de 128 e 30 épocas, as três decoraram. O MLP chega a 0,99 de PR-AUC no ajuste e fica em 0,06 na validação. A perda de validação sobe depois da primeira época. É overfitting claro.

## 1:00 a 1:33, regularização e resultado no teste

Na tela: tabela de regularização da seção 7 e tabela do teste da seção 8.

> Para corrigir, usei early stopping e dropout de 0,3, cada um com três sementes, e uma busca aleatória de hiperparâmetros, com a melhor configuração retreinada com três sementes. A GRU sobe de 0,070 para 0,095 de PR-AUC só com early stopping. No teste, a regressão logística na mesma janela faz 0,194, o MLP 0,189, a GRU 0,161 e a LSTM 0,150, contra 0,084 do acaso. As redes ganham do acaso, mas não da logística, e os intervalos de confiança se sobrepõem.

## 1:33 a 2:43, demonstração com exemplos não vistos

Na tela: seção 9. Primeiro a tabela com entradas e saídas. Depois a linha do tempo de abril de 2024. Todos os exemplos são do teste, que a rede não viu no treino nem na escolha de hiperparâmetros. A regra de escolha foi: os três maiores episódios, o pior alarme falso e um momento tranquilo.

> Todos estes exemplos vêm do teste. A rede usada foi a escolhida pela validação, a LSTM, mesmo tendo ficado com a menor nota no teste, porque a regra não muda depois de ver o resultado. O limiar de atenção é 0,041 e o de alerta, 0,215. Em 15 de junho de 2025 ela deu 0,28, alerta, com apenas 2,2 milímetros nas 72 horas anteriores. A rede previu a chuva sem chuva anterior. É o acerto mais claro. No maior episódio, 25 de abril de 2024, que chegou a 280 milímetros no pico, a probabilidade fica em 0,04. A tabela mostra 50,2 porque é o início do episódio. A faixa é atenção só porque o limiar de atenção é baixo. A rede não antecipou esse evento. E em 9 de setembro de 2024 ela deu 0,51 com praticamente nenhuma chuva, o pior alarme falso. Nos 29 episódios do teste, a rede chegou ao alerta em 2, à atenção em 21 e ficou em baixo em 6.

## 2:43 a 3:13, a função `prever` e a integração

Na tela: a célula final da seção 9, com a entrada (resumo do JSON) e a saída. Rode ao vivo se a sessão estiver aberta.

> Para entrar no Marca d'Água, a rede precisa de uma função que receba as 72 horas e devolva probabilidade e faixa. Chamo essa função com um JSON do dispositivo MD-POA-001 em 25 de abril de 2024, e ela responde 0,042, atenção. Isto é uma simulação, que roda só no notebook. A ideia é a Lambda chamar a função e gravar a faixa junto da ocorrência.

## 3:13 a 3:40, limites e evolução

Na tela: a lista de "o que falta desenvolver", logo depois da célula de `prever` (fim da seção 9). Se sobrar tempo, mostre também a lista de evolução da seção 11, que cita o algoritmo genético no lugar da busca aleatória.

> O desempenho não serve de alarme sozinho. Serve como sinal complementar, e o aviso imediato vem do nível medido pelo nó. Falta o nó medir ou buscar pressão e vento, empacotar o modelo, porque o TensorFlow é pesado para uma Lambda, e guardar as 72 horas de cada nó. Nada disso está implementado. Obrigado.

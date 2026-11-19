# Statistical Computing with R and Python

Análise da base do INMET de Porto Alegre (estação A801, Jardim Botânico), de 2014 a 2025, para as questões 02 a 06 do enunciado. A entrega no Portal é a base `.csv`, o código `.py` e o relatório `.pdf`.

## Como rodar

Requer Python 3.12 ou mais novo. Na pasta `estatistica`, no PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

1. Baixe os arquivos anuais de 2014 a 2025 em https://portal.inmet.gov.br/dadoshistoricos e coloque os ZIPs em `dados/brutos/` (ou só os CSVs da A801 extraídos deles). Essa pasta não vai para o Git.
2. Monte a base diária: `python preparar_base.py`. Ela grava `dados/inmet_poa_diario.csv` e mostra quantos dias têm falha de medição em cada coluna.
3. Rode a análise: `python analise.py`. Os números de cada questão vão para `saidas/resultados.md` e os gráficos para `saidas/*.png`.
4. Testes do código: `pytest`.

## O que cada questão faz

| Questão | Variáveis | Método |
|---|---|---|
| 02, normal | Pressão média diária | Ajuste da normal, P(X < 1000 hPa), P(X > 1020 hPa), P(1000 ≤ X ≤ 1020) e percentil 5%, comparados com a frequência observada; Q-Q plot e Shapiro-Wilk |
| 03, testes de hipótese | Pressão e umidade na véspera de chuva forte (20 mm ou mais) | t de uma amostra contra a média da série: pressão menor (α = 6%, n = 20) e umidade maior (α = 9%, n = 25) |
| 04, bivariada e simples | Chuva mensal x umidade média mensal | Pearson, Spearman, dispersão, reta de mínimos quadrados, R², teste F e resíduos |
| 05, multivariada e múltipla | Chuva mensal x umidade, pressão, temperatura e vento | Matriz de correlação, regressão múltipla, R² ajustado, teste F, VIF e F parcial contra o modelo simples |
| 06, logística | Chuva forte amanhã x umidade e pressão de hoje | Regressão logística com divisão no tempo (treino até 2022, teste de 2023 em diante), equação, razão de chances, matriz de confusão, acurácia, precisão e recall |

A amostra das questões 02 e 03 é sorteada com semente fixa (42), então o resultado se repete a cada execução.

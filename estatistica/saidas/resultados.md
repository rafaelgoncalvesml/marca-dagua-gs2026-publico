# Resultados (gerado por analise.py)

Base: 4383 dias, de 01/01/2014 a 31/12/2025; 143 meses completos. Chuva forte = 20 mm ou mais no dia (328 dias).

## Questão 02: normal (pressão média diária)

| item | valor |
| --- | --- |
| variavel | pressao_media_hpa |
| n | 4361 |
| media | 1010 |
| desvio | 5.278 |
| assimetria | 0.2796 |
| curtose_excesso | -0.1391 |
| shapiro_p_amostra500 | 0.3381 |
| a | 1000 |
| b | 1020 |
| P(X<a) normal | 0.03018 |
| P(X<a) observado | 0.01972 |
| P(X>b) normal | 0.02799 |
| P(X>b) observado | 0.03554 |
| P(a<=X<=b) normal | 0.9418 |
| P(a<=X<=b) observado | 0.9447 |
| percentil_5_normal | 1001 |
| percentil_5_observado | 1002 |

## Questão 03: testes de hipótese para a média

### pressao (alfa 6%, n=20)

| item | valor |
| --- | --- |
| n | 20 |
| alfa | 0.06 |
| mu0 (media da serie) | 1010 |
| media amostral | 1007 |
| desvio amostral | 4.052 |
| H1 | mu < mu0 |
| t | -3.29 |
| gl | 19 |
| t critico | -1.628 |
| p-valor | 0.001926 |
| decisao | rejeita H0 |

### umidade (alfa 9%, n=25)

| item | valor |
| --- | --- |
| n | 25 |
| alfa | 0.09 |
| mu0 (media da serie) | 77.5 |
| media amostral | 82.39 |
| desvio amostral | 9.227 |
| H1 | mu > mu0 |
| t | 2.651 |
| gl | 24 |
| t critico | 1.381 |
| p-valor | 0.006987 |
| decisao | rejeita H0 |

## Questão 04: chuva mensal x umidade média

| item | valor |
| --- | --- |
| n_meses | 143 |
| pearson_r | 0.5029 |
| pearson_p | 1.544e-10 |
| spearman_rho | 0.5196 |
| spearman_p | 2.932e-11 |
| intercepto | -535.7 |
| inclinacao | 8.662 |
| inclinacao_p | 1.544e-10 |
| R2 | 0.2529 |
| F | 47.74 |
| F_p | 1.544e-10 |

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               chuva_mm   R-squared:                       0.253
Model:                            OLS   Adj. R-squared:                  0.248
Method:                 Least Squares   F-statistic:                     47.74
Date:                Tue, 10 Nov 2026   Prob (F-statistic):           1.54e-10
Time:                        01:20:05   Log-Likelihood:                -810.20
No. Observations:                 143   AIC:                             1624.
Df Residuals:                     141   BIC:                             1630.
Df Model:                           1                                         
Covariance Type:            nonrobust                                         
=====================================================================================
                        coef    std err          t      P>|t|      [0.025      0.975]
-------------------------------------------------------------------------------------
Intercept          -535.6806     97.358     -5.502      0.000    -728.151    -343.210
umidade_media_pct     8.6625      1.254      6.909      0.000       6.184      11.141
==============================================================================
Omnibus:                       31.445   Durbin-Watson:                   1.741
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               57.967
Skew:                           1.004   Prob(JB):                     2.59e-13
Kurtosis:                       5.387   Cond. No.                     1.28e+03
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
[2] The condition number is large, 1.28e+03. This might indicate that there are
strong multicollinearity or other numerical problems.
```

## Questão 05: regressão múltipla

Coeficientes, p-valores e IC 95%:

|                   |       coef |      p |         0 |          1 |
|:------------------|-----------:|-------:|----------:|-----------:|
| Intercept         | 16279.6    | 0.0001 | 8350.38   | 24208.8    |
| umidade_media_pct |    10.4941 | 0      |    7.4564 |    13.5317 |
| pressao_media_hpa |   -16.6455 | 0      |  -24.3428 |    -8.9482 |
| temp_media_c      |    -7.7124 | 0.0118 |  -13.6867 |    -1.7382 |
| vento_medio_ms    |     6.2611 | 0.832  |  -51.9908 |    64.513  |

| item | valor |
| --- | --- |
| R2 | 0.3745 |
| R2_ajustado | 0.3564 |
| F | 20.66 |
| F_p | 2.333e-13 |
| F_parcial | 8.942 |
| F_parcial_p | 1.872e-05 |

VIF:

| item | valor |
| --- | --- |
| umidade_media_pct | 1.755 |
| pressao_media_hpa | 4.65 |
| temp_media_c | 4.699 |
| vento_medio_ms | 1.735 |

Correlações:

|                   |   chuva_mm |   umidade_media_pct |   pressao_media_hpa |   temp_media_c |   vento_medio_ms |
|:------------------|-----------:|--------------------:|--------------------:|---------------:|-----------------:|
| chuva_mm          |      1     |               0.503 |               0.018 |         -0.216 |           -0.067 |
| umidade_media_pct |      0.503 |               1     |               0.54  |         -0.638 |           -0.455 |
| pressao_media_hpa |      0.018 |               0.54  |               1     |         -0.862 |           -0.633 |
| temp_media_c      |     -0.216 |              -0.638 |              -0.862 |          1     |            0.541 |
| vento_medio_ms    |     -0.067 |              -0.455 |              -0.633 |          0.541 |            1     |

## Questão 06: regressão logística (chuva forte amanhã ~ umidade + pressão de hoje)

| item | valor |
| --- | --- |
| n_treino | 3265 |
| n_teste | 1085 |
| eventos_treino | 232 |
| eventos_teste | 96 |
| b0 | 105.2 |
| b1_umidade | 0.03807 |
| b2_pressao | -0.1098 |
| odds_umidade_+1pp | 1.039 |
| odds_pressao_+1hPa | 0.896 |
| pseudo_R2 | 0.05309 |
| AUC_teste | 0.6725 |
| acuracia_sempre_nao | 0.9115 |

p-valores:

| item | valor |
| --- | --- |
| Intercept | 5.752e-13 |
| umidade_media_pct | 2.059e-07 |
| pressao_media_hpa | 3.463e-14 |

Teste com limiar 0,5:

| item | valor |
| --- | --- |
| limiar | 0.5 |
| VP | 0 |
| FP | 0 |
| FN | 96 |
| VN | 989 |
| acuracia | 0.9115 |
| precisao | nan |
| recall | 0 |

Teste com limiar de alerta:

| item | valor |
| --- | --- |
| limiar | 0.05 |
| VP | 75 |
| FP | 564 |
| FN | 21 |
| VN | 425 |
| acuracia | 0.4608 |
| precisao | 0.1174 |
| recall | 0.7812 |

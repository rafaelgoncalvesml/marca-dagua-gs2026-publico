"""Questões 02 a 06 de Statistical Computing sobre a base diária do INMET de Porto Alegre.

Uso: python analise.py      (antes, rode preparar_base.py)
Saídas em saidas/: resultados.md com os números de cada questão e os gráficos em PNG.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

AQUI = Path(__file__).parent
BASE = AQUI / "dados" / "inmet_poa_diario.csv"
SAIDAS = AQUI / "saidas"
SEMENTE = 42
CHUVA_FORTE_MM = 20  # dia com 20 mm ou mais conta como chuva forte


def carregar() -> pd.DataFrame:
    df = pd.read_csv(BASE, parse_dates=["data"], index_col="data").asfreq("D")
    df["chuva_forte"] = (df["chuva_mm"] >= CHUVA_FORTE_MM).astype(float).where(df["chuva_mm"].notna())
    df["chuva_forte_amanha"] = df["chuva_forte"].shift(-1)
    return df


def mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega por mês. Mês com menos de 25 dias de chuva medidos fica fora."""
    g = df.resample("MS")
    m = pd.DataFrame({
        "chuva_mm": g["chuva_mm"].sum(min_count=25),
        "umidade_media_pct": g["umidade_media_pct"].mean(),
        "pressao_media_hpa": g["pressao_media_hpa"].mean(),
        "temp_media_c": g["temp_media_c"].mean(),
        "vento_medio_ms": g["vento_medio_ms"].mean(),
    })
    return m.dropna()


# ---------- Questão 02: probabilidades na normal ----------

def questao_02(df, fig, a=1000.0, b=1020.0):
    x = df["pressao_media_hpa"].dropna()
    mu, sigma = x.mean(), x.std()
    dist = stats.norm(mu, sigma)
    amostra = x.sample(min(500, len(x)), random_state=SEMENTE)  # Shapiro perde sentido com milhares de pontos
    r = {
        "variavel": "pressao_media_hpa", "n": len(x), "media": mu, "desvio": sigma,
        "assimetria": stats.skew(x), "curtose_excesso": stats.kurtosis(x),
        "shapiro_p_amostra500": stats.shapiro(amostra).pvalue,
        "a": a, "b": b,
        "P(X<a) normal": dist.cdf(a), "P(X<a) observado": (x < a).mean(),
        "P(X>b) normal": dist.sf(b), "P(X>b) observado": (x > b).mean(),
        "P(a<=X<=b) normal": dist.cdf(b) - dist.cdf(a), "P(a<=X<=b) observado": x.between(a, b).mean(),
        "percentil_5_normal": dist.ppf(0.05), "percentil_5_observado": x.quantile(0.05),
    }
    f, (h, q) = plt.subplots(1, 2, figsize=(11, 4))
    h.hist(x, bins=40, density=True, color="#9db4c8", edgecolor="white")
    grade = np.linspace(x.min(), x.max(), 300)
    h.plot(grade, dist.pdf(grade), color="#1f4e79", lw=2, label=f"Normal({mu:.1f}; {sigma:.1f})")
    h.axvline(a, color="#c0392b", ls="--", lw=1)
    h.axvline(b, color="#c0392b", ls="--", lw=1)
    h.set(title="Pressão média diária", xlabel="hPa", ylabel="densidade")
    h.legend()
    stats.probplot(amostra, dist="norm", plot=q)
    q.set_title("Q-Q plot (amostra de 500 dias)")
    fig(f, "q02_normal_pressao.png")
    return r


# ---------- Questão 03: testes de hipótese para a média ----------

def teste_media(populacao, amostra_de, n, alfa, alternativa):
    """t de uma amostra: amostra de n dias tirada de `amostra_de` contra a média da série inteira."""
    mu0 = populacao.mean()
    amostra = amostra_de.dropna().sample(n, random_state=SEMENTE)
    t, p = stats.ttest_1samp(amostra, mu0, alternative=alternativa)
    gl = n - 1
    t_crit = stats.t.ppf(alfa, gl) if alternativa == "less" else stats.t.ppf(1 - alfa, gl)
    return {
        "n": n, "alfa": alfa, "mu0 (media da serie)": mu0, "media amostral": amostra.mean(),
        "desvio amostral": amostra.std(), "H1": f"mu {'<' if alternativa == 'less' else '>'} mu0",
        "t": t, "gl": gl, "t critico": t_crit, "p-valor": p,
        "decisao": "rejeita H0" if p < alfa else "nao rejeita H0",
    }


def questao_03(df):
    vespera = df["chuva_forte_amanha"] == 1
    return {
        # pressão cai antes de frente fria e ciclone, que trazem a chuva forte
        "pressao (alfa 6%, n=20)": teste_media(df["pressao_media_hpa"], df.loc[vespera, "pressao_media_hpa"], 20, 0.06, "less"),
        # o ar fica mais úmido na véspera da chuva forte
        "umidade (alfa 9%, n=25)": teste_media(df["umidade_media_pct"], df.loc[vespera, "umidade_media_pct"], 25, 0.09, "greater"),
    }


# ---------- Questão 04: análise bivariada e regressão simples ----------

def questao_04(m, fig):
    pearson = stats.pearsonr(m["umidade_media_pct"], m["chuva_mm"])
    spearman = stats.spearmanr(m["umidade_media_pct"], m["chuva_mm"])
    modelo = smf.ols("chuva_mm ~ umidade_media_pct", data=m).fit()
    f, (d, res) = plt.subplots(1, 2, figsize=(11, 4))
    d.scatter(m["umidade_media_pct"], m["chuva_mm"], s=18, color="#1f4e79", alpha=0.7)
    grade = np.linspace(m["umidade_media_pct"].min(), m["umidade_media_pct"].max(), 100)
    d.plot(grade, modelo.params.iloc[0] + modelo.params.iloc[1] * grade, color="#c0392b", lw=2)
    d.set(title=f"Chuva mensal x umidade média (R² = {modelo.rsquared:.2f})", xlabel="umidade média do mês (%)", ylabel="chuva no mês (mm)")
    res.scatter(modelo.fittedvalues, modelo.resid, s=18, color="#1f4e79", alpha=0.7)
    res.axhline(0, color="grey", lw=1)
    res.set(title="Resíduos x ajustados", xlabel="chuva prevista (mm)", ylabel="resíduo (mm)")
    fig(f, "q04_regressao_simples.png")
    return {
        "n_meses": int(modelo.nobs), "pearson_r": pearson.statistic, "pearson_p": pearson.pvalue,
        "spearman_rho": spearman.statistic, "spearman_p": spearman.pvalue,
        "intercepto": modelo.params.iloc[0], "inclinacao": modelo.params.iloc[1],
        "inclinacao_p": modelo.pvalues.iloc[1], "R2": modelo.rsquared,
        "F": modelo.fvalue, "F_p": modelo.f_pvalue,
        "_modelo": modelo,
    }


# ---------- Questão 05: análise multivariada e regressão múltipla ----------

PREDITORAS = ["umidade_media_pct", "pressao_media_hpa", "temp_media_c", "vento_medio_ms"]


def questao_05(m, simples, fig):
    modelo = smf.ols("chuva_mm ~ " + " + ".join(PREDITORAS), data=m).fit()
    X = sm.add_constant(m[PREDITORAS])
    vif = {c: variance_inflation_factor(X.values, i) for i, c in enumerate(X.columns) if c != "const"}
    comparacao = sm.stats.anova_lm(simples, modelo)  # F parcial: as 3 variáveis a mais ajudam?
    corr = m[["chuva_mm"] + PREDITORAS].corr()

    f, ax = plt.subplots(figsize=(6.5, 5.2))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(corr)), corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iat[i, j]:.2f}", ha="center", va="center", fontsize=9)
    f.colorbar(im)
    ax.set_title("Correlação entre as variáveis mensais")
    fig(f, "q05_correlacoes.png")
    return {
        "coeficientes": modelo.params, "p_valores": modelo.pvalues, "IC95": modelo.conf_int(),
        "R2": modelo.rsquared, "R2_ajustado": modelo.rsquared_adj, "F": modelo.fvalue, "F_p": modelo.f_pvalue,
        "VIF": vif, "F_parcial": comparacao["F"].iloc[1], "F_parcial_p": comparacao["Pr(>F)"].iloc[1],
        "correlacoes": corr,
    }


# ---------- Questão 06: regressão logística com duas variáveis ----------

def metricas(y, prob, limiar):
    prev = (prob >= limiar).astype(int)
    vp = int(((prev == 1) & (y == 1)).sum()); fp = int(((prev == 1) & (y == 0)).sum())
    fn = int(((prev == 0) & (y == 1)).sum()); vn = int(((prev == 0) & (y == 0)).sum())
    return {
        "limiar": limiar, "VP": vp, "FP": fp, "FN": fn, "VN": vn,
        "acuracia": (vp + vn) / len(y), "precisao": vp / (vp + fp) if vp + fp else float("nan"),
        "recall": vp / (vp + fn) if vp + fn else float("nan"),
    }


def questao_06(df, fig, corte="2023-01-01"):
    d = df[["umidade_media_pct", "pressao_media_hpa", "chuva_forte_amanha"]].dropna()
    treino, teste = d.loc[:corte].iloc[:-1], d.loc[corte:]  # divisão no tempo: o teste é o futuro
    modelo = smf.logit("chuva_forte_amanha ~ umidade_media_pct + pressao_media_hpa", data=treino).fit(disp=False)
    prob_treino, prob_teste = modelo.predict(treino), modelo.predict(teste)

    # limiar de alerta: o que maximiza recall + especificidade (Youden) no treino
    grade = np.linspace(0.01, 0.6, 60)
    youden = [metricas(treino["chuva_forte_amanha"], prob_treino, l) for l in grade]
    melhor = max(youden, key=lambda r: r["recall"] + r["VN"] / (r["VN"] + r["FP"]))["limiar"]

    b0, b1, b2 = modelo.params
    f, ax = plt.subplots(figsize=(7, 5))
    for classe, cor, rotulo in [(0, "#9db4c8", "sem chuva forte no dia seguinte"), (1, "#c0392b", "chuva forte no dia seguinte")]:
        s = teste[teste["chuva_forte_amanha"] == classe]
        ax.scatter(s["umidade_media_pct"], s["pressao_media_hpa"], s=14, color=cor, alpha=0.7, label=rotulo)
    u = np.linspace(d["umidade_media_pct"].min(), d["umidade_media_pct"].max(), 100)
    logit_limiar = np.log(melhor / (1 - melhor))
    ax.plot(u, (logit_limiar - b0 - b1 * u) / b2, color="#1f4e79", lw=2, label=f"fronteira (p = {melhor:.2f})")
    ax.set(title="Classificação com duas variáveis (teste, 2023 em diante)", xlabel="umidade média do dia (%)", ylabel="pressão média do dia (hPa)")
    ax.set_ylim(d["pressao_media_hpa"].min() - 1, d["pressao_media_hpa"].max() + 1)
    ax.legend(fontsize=8)
    fig(f, "q06_logistica.png")
    return {
        "n_treino": len(treino), "n_teste": len(teste),
        "eventos_treino": int(treino["chuva_forte_amanha"].sum()), "eventos_teste": int(teste["chuva_forte_amanha"].sum()),
        "b0": b0, "b1_umidade": b1, "b2_pressao": b2, "p_valores": modelo.pvalues,
        "odds_umidade_+1pp": np.exp(b1), "odds_pressao_+1hPa": np.exp(b2),
        "pseudo_R2": modelo.prsquared,
        # AUC = chance de um dia com evento ter probabilidade maior que um dia sem evento (independe do limiar)
        "AUC_teste": stats.mannwhitneyu(prob_teste[teste["chuva_forte_amanha"] == 1], prob_teste[teste["chuva_forte_amanha"] == 0]).statistic
        / (teste["chuva_forte_amanha"].sum() * (1 - teste["chuva_forte_amanha"]).sum()),
        "teste_limiar_0.5": metricas(teste["chuva_forte_amanha"], prob_teste, 0.5),
        "teste_limiar_alerta": metricas(teste["chuva_forte_amanha"], prob_teste, melhor),
        "acuracia_sempre_nao": 1 - teste["chuva_forte_amanha"].mean(),
    }


# ---------- relatório em markdown ----------

def _fmt(v):
    if isinstance(v, (float, np.floating)):
        return f"{v:.4g}"
    return str(v)


def _tabela(d: dict) -> str:
    linhas = ["| item | valor |", "| --- | --- |"]
    linhas += [f"| {k} | {_fmt(v)} |" for k, v in d.items() if not k.startswith("_")]
    return "\n".join(linhas)


def main() -> int:
    if not BASE.exists():
        print(f"Base não encontrada em {BASE}. Rode antes: python preparar_base.py")
        return 1
    SAIDAS.mkdir(exist_ok=True)

    def fig(f, nome):
        f.tight_layout()
        f.savefig(SAIDAS / nome, dpi=150)
        plt.close(f)

    df = carregar()
    m = mensal(df)
    q2, q3 = questao_02(df, fig), questao_03(df)
    q4 = questao_04(m, fig)
    q5 = questao_05(m, q4["_modelo"], fig)
    q6 = questao_06(df, fig)

    partes = [
        "# Resultados (gerado por analise.py)",
        f"Base: {len(df)} dias, de {df.index.min():%d/%m/%Y} a {df.index.max():%d/%m/%Y}; {len(m)} meses completos. "
        f"Chuva forte = {CHUVA_FORTE_MM} mm ou mais no dia ({int(df['chuva_forte'].sum())} dias).",
        "## Questão 02: normal (pressão média diária)", _tabela(q2),
        "## Questão 03: testes de hipótese para a média",
        *[f"### {nome}\n\n{_tabela(r)}" for nome, r in q3.items()],
        "## Questão 04: chuva mensal x umidade média", _tabela(q4), "```\n" + str(q4["_modelo"].summary()) + "\n```",
        "## Questão 05: regressão múltipla",
        "Coeficientes, p-valores e IC 95%:\n\n" + pd.concat([q5["coeficientes"].rename("coef"), q5["p_valores"].rename("p"), q5["IC95"]], axis=1).round(4).to_markdown(),
        _tabela({k: q5[k] for k in ["R2", "R2_ajustado", "F", "F_p", "F_parcial", "F_parcial_p"]}),
        "VIF:\n\n" + _tabela(q5["VIF"]),
        "Correlações:\n\n" + q5["correlacoes"].round(3).to_markdown(),
        "## Questão 06: regressão logística (chuva forte amanhã ~ umidade + pressão de hoje)",
        _tabela({k: v for k, v in q6.items() if not isinstance(v, (dict, pd.Series))}),
        "p-valores:\n\n" + _tabela(q6["p_valores"].to_dict()),
        "Teste com limiar 0,5:\n\n" + _tabela(q6["teste_limiar_0.5"]),
        "Teste com limiar de alerta:\n\n" + _tabela(q6["teste_limiar_alerta"]),
    ]
    (SAIDAS / "resultados.md").write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    print("\n\n".join(partes))
    return 0


if __name__ == "__main__":
    sys.exit(main())

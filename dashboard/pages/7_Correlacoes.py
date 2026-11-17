import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from common import (
    configure_page,
    correlation_strength,
    format_ptbr,
    hero,
    load_data,
    methodological_note,
    style_figure,
)

configure_page("Correlações", "📈")
_, _, _, integrated, _ = load_data()
hero(
    "Correlações exploratórias",
    "Relações estatísticas entre chuva, contexto oceânico e impactos dos eventos.",
)

LABELS = {
    "rain_same_day_mean_mm": "Chuva média no dia",
    "rain_same_day_max_mm": "Chuva máxima no dia",
    "rain_3d_mean_sum_mm": "Chuva acumulada — 3 dias",
    "rain_7d_mean_sum_mm": "Chuva acumulada — 7 dias",
    "sst_nino34_c": "TSM Niño 3.4",
    "sst_anomaly_nino34_c": "Anomalia da TSM",
    "deaths": "Óbitos",
    "injured": "Feridos",
    "displaced": "Desalojados",
    "homeless": "Desabrigados",
    "affected": "Danos humanos diretos",
    "material_damage_brl": "Danos materiais (R$)",
}
df = integrated.copy()
with st.sidebar:
    st.subheader("Filtros reativos")
    dates = st.date_input("Período", (df.event_date.min().date(), df.event_date.max().date()))
    ufs = st.multiselect("UF", sorted(df.uf.unique()), placeholder="Todas")
    types = st.multiselect("Tipologia", sorted(df.disaster_type.unique()), placeholder="Todas")
    contexts = st.multiselect(
        "Contexto oceânico", sorted(df.enso_context.unique()), placeholder="Todos"
    )
    rain_only = st.toggle("Somente eventos ligados à chuva", value=True)
    min_affected = st.number_input("Mínimo de danos humanos", min_value=0, value=0, step=10)
if len(dates) == 2:
    df = df[df.event_date.between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]
if ufs:
    df = df[df.uf.isin(ufs)]
if types:
    df = df[df.disaster_type.isin(types)]
if contexts:
    df = df[df.enso_context.isin(contexts)]
if rain_only:
    df = df[df.rain_related]
df = df[df.affected >= min_affected]

st.caption(
    f"Filtros aplicados instantaneamente · {format_ptbr(len(df))} eventos no recorte"
)
if df.empty:
    st.warning("Nenhum evento atende aos filtros atuais.")
    st.stop()
variables = list(LABELS)
c1, c2, c3 = st.columns([1, 1, 1])
x = c1.selectbox("Eixo X", variables, format_func=LABELS.get, index=3)
y = c2.selectbox("Eixo Y", variables, format_func=LABELS.get, index=10)
color = c3.selectbox(
    "Colorir por",
    ["disaster_type", "uf", "enso_context"],
    format_func={"disaster_type": "Tipologia", "uf": "UF", "enso_context": "Contexto oceânico"}.get,
)
analysis = df[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
pearson = analysis.corr(method="pearson").iloc[0, 1]
spearman = analysis.corr(method="spearman").iloc[0, 1]
m1, m2, m3 = st.columns(3)
m1.metric("Correlação de Pearson", format_ptbr(pearson, 3))
m2.metric("Correlação de Spearman", format_ptbr(spearman, 3))
m3.metric("Pares válidos", format_ptbr(len(analysis)))
methodological_note(
    f"No recorte atual, a relação linear é <b>{correlation_strength(pearson)}</b> e a relação "
    f"monotônica é <b>{correlation_strength(spearman)}</b>. Valores extremos e muitos zeros podem "
    "alterar principalmente Pearson; compare os dois coeficientes e inspecione a dispersão."
)
log_y = st.toggle(
    "Escala logarítmica no eixo Y (log1p)",
    value=False,
    help="Útil quando impactos têm muitos zeros e poucos valores muito altos.",
)
plot_df = df.copy()
plot_y = y
plot_labels = {**LABELS, "disaster_type": "Tipologia", "enso_context": "Contexto"}
if log_y:
    plot_y = f"{y}_log1p"
    plot_df[plot_y] = np.log1p(plot_df[y].clip(lower=0))
    plot_labels[plot_y] = f"log(1 + {LABELS[y]})"
fig = px.scatter(
    plot_df,
    x=x,
    y=plot_y,
    color=color,
    hover_name="municipality",
    hover_data=["uf", "event_date", "disaster_type"],
    opacity=0.65,
    trendline=None,
    labels=plot_labels,
    title=f"{LABELS[x]} × {LABELS[y]}",
)
st.plotly_chart(
    style_figure(fig, 560),
    width="stretch",
    on_select="rerun",
    selection_mode=("points", "box", "lasso"),
    key="correlation_scatter",
)

st.subheader("Matriz de correlação")
selected = st.multiselect(
    "Variáveis da matriz",
    variables,
    default=[
        "rain_3d_mean_sum_mm",
        "rain_7d_mean_sum_mm",
        "sst_anomaly_nino34_c",
        "deaths",
        "affected",
    ],
    format_func=LABELS.get,
)
if len(selected) >= 2:
    corr = (
        df[selected]
        .corr(method=st.radio("Método", ["pearson", "spearman"], horizontal=True))
        .rename(index=LABELS, columns=LABELS)
    )
    heat = px.imshow(
        corr,
        text_auto=".2f",
        zmin=-1,
        zmax=1,
        color_continuous_scale="RdBu_r",
        title="Matriz recalculada para o recorte ativo",
        aspect="auto",
    )
    st.plotly_chart(style_figure(heat, 590), width="stretch")
st.info(
    "Correlação mede associação, não causalidade. Não foi aplicado controle por sazonalidade, "
    "tipologia, população exposta ou dependência espacial. Os resultados combinam eventos "
    "municipais com chuva estadual e contexto oceânico mensal."
)

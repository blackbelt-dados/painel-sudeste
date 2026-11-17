import plotly.express as px
import streamlit as st
from common import OCEAN_COLOR, configure_page, format_ptbr, hero, load_data, style_figure

configure_page("Oceano e clima", "🌊")
*_, ocean = load_data()
hero("Oceano e clima", "Temperatura da superfície do mar e anomalia mensal na região Niño 3.4.")
latest = ocean.sort_values("date").iloc[-1]
cols = st.columns(3)
cols[0].metric("Meses disponíveis", f"{len(ocean)} de 12")
reference_month = latest.date.strftime("%m/%Y")
cols[1].metric(
    f"TSM mais recente · {reference_month}", f"{format_ptbr(latest.sst_nino34_c, 2)} °C"
)
cols[2].metric(
    f"Anomalia mais recente · {reference_month}",
    f"{format_ptbr(latest.sst_anomaly_nino34_c, 2)} °C",
    latest.enso_context,
)
left, right = st.columns(2)
fig = px.line(
    ocean,
    x="date",
    y="sst_nino34_c",
    markers=True,
    labels={"date": "Mês", "sst_nino34_c": "TSM (°C)"},
    title="TSM Niño 3.4",
    color_discrete_sequence=[OCEAN_COLOR],
)
fig.update_traces(line={"width": 3})
left.plotly_chart(style_figure(fig), width="stretch")
colors = ocean.sst_anomaly_nino34_c.apply(
    lambda v: "#F97316" if v >= 0.5 else ("#38BDF8" if v <= -0.5 else "#94A3B8")
)
fig = px.bar(
    ocean,
    x="date",
    y="sst_anomaly_nino34_c",
    labels={"date": "Mês", "sst_anomaly_nino34_c": "Anomalia (°C)"},
    title="Anomalia mensal",
)
fig.update_traces(marker_color=colors)
fig.add_hline(y=0.5, line_dash="dot", line_color="#F97316")
fig.add_hline(y=-0.5, line_dash="dot", line_color="#38BDF8")
fig.add_hline(y=0, line_color="#E2E8F0")
right.plotly_chart(style_figure(fig), width="stretch")
st.info(
    "O limiar mensal de ±0,5 °C é exploratório. O diagnóstico oficial de episódios ENSO exige persistência. A região Niño 3.4 não representa o oceano costeiro brasileiro."
)

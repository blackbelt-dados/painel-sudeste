import pandas as pd
import plotly.express as px
import streamlit as st
from common import (
    DISASTER_COLOR,
    RAIN_COLOR,
    add_uf_coordinates,
    configure_page,
    correlation_strength,
    format_ptbr,
    hero,
    load_data,
    methodological_note,
    style_figure,
)

configure_page("Análise integrada", "🔎")
_, _, _, integrated, _ = load_data()
hero(
    "Análise integrada",
    "Eventos de 2025 associados temporalmente à chuva e ao contexto oceano-climático.",
)
only_rain = st.sidebar.toggle("Somente tipologias associadas à chuva", value=True)
df = integrated[integrated.rain_related] if only_rain else integrated.copy()
dates = st.sidebar.date_input(
    "Período",
    (df.event_date.min().date(), df.event_date.max().date()),
)
ufs = st.sidebar.multiselect("UF", sorted(df.uf.unique()), placeholder="Todas")
types = st.sidebar.multiselect("Tipologia", sorted(df.disaster_type.unique()), placeholder="Todas")
contexts = st.sidebar.multiselect(
    "Contexto oceânico", sorted(df.enso_context.unique()), placeholder="Todos"
)
rain_range = st.sidebar.slider(
    "Chuva antecedente em 7 dias (mm)",
    0.0,
    float(df.rain_7d_mean_sum_mm.max()),
    (0.0, float(df.rain_7d_mean_sum_mm.max())),
)
minimum_affected = st.sidebar.number_input("Mínimo de danos humanos", min_value=0, value=0, step=10)
if len(dates) == 2:
    df = df[df.event_date.between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]
df = df[df.uf.isin(ufs)] if ufs else df
df = df[df.disaster_type.isin(types)] if types else df
df = df[df.enso_context.isin(contexts)] if contexts else df
df = df[df.rain_7d_mean_sum_mm.between(*rain_range)]
df = df[df.affected >= minimum_affected]
st.caption(f"Atualização automática · {format_ptbr(len(df))} eventos no recorte")
if df.empty:
    st.warning("Nenhum evento atende aos filtros atuais.")
    st.stop()
cols = st.columns(4)
cols[0].metric("Eventos", format_ptbr(len(df)))
cols[1].metric(
    "Com observação de chuva", f"{format_ptbr((df.reporting_stations > 0).mean() * 100, 1)}%"
)
cols[2].metric("Chuva média — 3 dias", f"{format_ptbr(df.rain_3d_mean_sum_mm.mean(), 1)} mm")
cols[3].metric("Chuva média — 7 dias", f"{format_ptbr(df.rain_7d_mean_sum_mm.mean(), 1)} mm")
methodological_note(
    "<b>Com observação de chuva</b> significa que havia ao menos uma estação reportando na UF e "
    "na data associada ao evento. Não significa que choveu no município nem que a chuva causou "
    "o desastre. A integração combina evento municipal, resumo estadual diário e contexto "
    "oceânico mensal."
)
mapped = add_uf_coordinates(
    df.groupby("uf", as_index=False).agg(
        events=("protocol", "count"),
        rain_7d=("rain_7d_mean_sum_mm", "mean"),
        affected=("affected", "sum"),
    )
)
fig = px.scatter_map(
    mapped,
    lat="latitude",
    lon="longitude",
    size="events",
    color="rain_7d",
    hover_name="uf",
    hover_data={"events": True, "affected": True, "latitude": False, "longitude": False},
    center={"lat": -14.2, "lon": -51.9},
    zoom=2.6,
    color_continuous_scale="Turbo",
    labels={
        "events": "Eventos",
        "rain_7d": "Chuva média antecedente — 7 dias (mm)",
        "affected": "Danos humanos diretos",
    },
    title="Mapa integrado — eventos e chuva antecedente",
    size_max=55,
)
fig.update_layout(map_style="carto-darkmatter")
st.plotly_chart(style_figure(fig, 560), width="stretch")
st.caption(
    "Os pontos do mapa são centroides estaduais. O mapa resume eventos municipais usando chuva "
    "agregada por UF; não indica a posição exata nem a exposição local."
)

st.subheader("Relação entre chuva e impactos")
x_metric = st.selectbox(
    "Indicador de chuva",
    ["rain_same_day_max_mm", "rain_3d_mean_sum_mm", "rain_7d_mean_sum_mm"],
    format_func={
        "rain_same_day_max_mm": "Máximo no dia",
        "rain_3d_mean_sum_mm": "Acumulado em 3 dias",
        "rain_7d_mean_sum_mm": "Acumulado em 7 dias",
    }.get,
)
y_metric = st.selectbox(
    "Indicador de impacto",
    ["affected", "deaths", "displaced", "homeless", "material_damage_brl"],
    format_func={
        "affected": "Danos humanos diretos",
        "deaths": "Óbitos",
        "displaced": "Desalojados",
        "homeless": "Desabrigados",
        "material_damage_brl": "Danos materiais (R$)",
    }.get,
)
valid = df[[x_metric, y_metric]].dropna()
correlation = valid.corr(method="spearman").iloc[0, 1]
st.metric("Correlação de Spearman no recorte", format_ptbr(correlation, 3))
st.info(
    f"Associação monotônica **{correlation_strength(correlation)}** no recorte "
    f"(**n = {format_ptbr(len(valid))}** pares válidos). Correlação não demonstra causalidade."
)
scatter = px.scatter(
    df,
    x=x_metric,
    y=y_metric,
    color="disaster_type",
    hover_name="municipality",
    hover_data=["uf", "event_date", "enso_context"],
    opacity=0.65,
    labels={
        x_metric: {
            "rain_same_day_max_mm": "Chuva máxima no dia (mm)",
            "rain_3d_mean_sum_mm": "Chuva acumulada — 3 dias (mm)",
            "rain_7d_mean_sum_mm": "Chuva acumulada — 7 dias (mm)",
        }[x_metric],
        y_metric: {
            "affected": "Danos humanos diretos",
            "deaths": "Óbitos",
            "displaced": "Desalojados",
            "homeless": "Desabrigados",
            "material_damage_brl": "Danos materiais (R$)",
        }[y_metric],
        "disaster_type": "Tipologia",
    },
    title="Dispersão interativa — selecione pontos, área ou laço",
)
st.plotly_chart(
    style_figure(scatter, 520),
    width="stretch",
    on_select="rerun",
    selection_mode=("points", "box", "lasso"),
    key="integrated_scatter",
)
left, right = st.columns(2)
box = px.box(
    df,
    x="disaster_type",
    y="rain_7d_mean_sum_mm",
    color="disaster_type",
    labels={"disaster_type": "Tipologia", "rain_7d_mean_sum_mm": "Chuva em 7 dias (mm)"},
    title="Chuva antecedente por tipologia",
    points=False,
)
box.update_layout(showlegend=False)
box.update_xaxes(tickangle=-30)
left.plotly_chart(style_figure(box, 470), width="stretch")
monthly = df.groupby("month", as_index=False).agg(
    events=("protocol", "count"), rain_7d=("rain_7d_mean_sum_mm", "mean")
)
month = px.bar(
    monthly,
    x="month",
    y="events",
    labels={"month": "Mês", "events": "Eventos"},
    title="Eventos e chuva por mês",
    color_discrete_sequence=[DISASTER_COLOR],
)
month.add_scatter(
    x=monthly.month,
    y=monthly.rain_7d,
    name="Chuva 7d (mm)",
    yaxis="y2",
    line={"color": RAIN_COLOR, "width": 3},
)
month.update_layout(yaxis2={"overlaying": "y", "side": "right", "title": "Chuva (mm)"})
right.plotly_chart(style_figure(month, 470), width="stretch")
st.dataframe(
    df.sort_values("rain_7d_mean_sum_mm", ascending=False)[
        [
            "event_date",
            "uf",
            "municipality",
            "disaster_type",
            "rain_7d_mean_sum_mm",
            "sst_anomaly_nino34_c",
            "enso_context",
            "affected",
        ]
    ].head(150).rename(
        columns={
            "event_date": "Data",
            "uf": "UF",
            "municipality": "Município",
            "disaster_type": "Tipologia",
            "rain_7d_mean_sum_mm": "Chuva acumulada — 7 dias (mm)",
            "sst_anomaly_nino34_c": "Anomalia da TSM (°C)",
            "enso_context": "Contexto oceânico",
            "affected": "Danos humanos diretos",
        }
    ),
    hide_index=True,
    width="stretch",
)

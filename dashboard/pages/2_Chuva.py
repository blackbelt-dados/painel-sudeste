import pandas as pd
import plotly.express as px
import streamlit as st
from common import (
    METRIC_LABELS,
    RAIN_COLOR,
    configure_page,
    format_ptbr,
    hero,
    load_data,
    methodological_note,
    style_figure,
)

configure_page("Chuva e estações", "🌧️")
_, stations, uf_daily, _, _ = load_data()
hero(
    "Chuva e rede meteorológica",
    "Precipitação observada e cobertura das estações automáticas do INMET em 2025.",
)
uf = st.sidebar.selectbox("UF", sorted(uf_daily.uf.unique()))
dates = st.sidebar.date_input(
    "Período",
    (uf_daily.date.min().date(), uf_daily.date.max().date()),
)
minimum_coverage = st.sidebar.slider("Cobertura mínima da estação", 0, 100, 50)
series = uf_daily[uf_daily.uf == uf]
if len(dates) == 2:
    series = series[series.date.between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))]
map_scope = st.sidebar.radio("Estações no mapa", ["Sudeste", "UF selecionada"])
line_metrics = st.multiselect(
    "Séries exibidas",
    ["mean_station_precipitation_mm", "max_station_precipitation_mm"],
    default=["mean_station_precipitation_mm", "max_station_precipitation_mm"],
    format_func={
        "mean_station_precipitation_mm": "Média entre estações",
        "max_station_precipitation_mm": "Máximo entre estações",
    }.get,
)
if not line_metrics:
    line_metrics = ["mean_station_precipitation_mm"]
st.caption(f"Atualização automática · {len(series)} dias no recorte")
cols = st.columns(3)
cols[0].metric("Estações no Sudeste", format_ptbr(stations.station_code.nunique()))
cols[1].metric(
    f"Máximo diário em {uf}", f"{format_ptbr(series.max_station_precipitation_mm.max(), 1)} mm"
)
cols[2].metric("Cobertura média", f"{format_ptbr(stations.coverage_pct.mean(), 1)}%")
fig = px.line(
    series,
    x="date",
    y=line_metrics,
    labels={
        "date": "Data",
        "value": "Precipitação (mm)",
        "variable": "Indicador",
        **METRIC_LABELS,
    },
    title=f"Precipitação diária — {uf}",
    color_discrete_sequence=[RAIN_COLOR, "#A78BFA"],
)
fig.for_each_trace(lambda trace: trace.update(name=METRIC_LABELS.get(trace.name, trace.name)))
fig.update_xaxes(tickformat="%m/%Y")
st.plotly_chart(style_figure(fig), width="stretch")
all_points = (
    stations.groupby("station_code", as_index=False)
    .agg(
        station_name=("station_name", "first"),
        uf=("uf", "first"),
        latitude=("latitude", "first"),
        longitude=("longitude", "first"),
        coverage_pct=("coverage_pct", "mean"),
        total_rain=("precipitation_mm", "sum"),
    )
    .query("latitude != 0 and longitude != 0")
)
points = all_points[all_points.coverage_pct >= minimum_coverage]
points = points[points.uf == uf] if map_scope == "UF selecionada" else points
fig = px.scatter_map(
    points,
    lat="latitude",
    lon="longitude",
    color="coverage_pct",
    size="total_rain",
    hover_name="station_name",
    hover_data={
        "uf": True,
        "station_code": True,
        "coverage_pct": ":.1f",
        "total_rain": ":.1f",
        "latitude": False,
        "longitude": False,
    },
    center={"lat": -20.1, "lon": -44.5},
    zoom=4.0,
    color_continuous_scale="Blues",
    labels=METRIC_LABELS,
    title="Mapa da rede INMET — cobertura e chuva acumulada",
    size_max=20,
)
fig.update_layout(map_style="carto-darkmatter")
st.plotly_chart(style_figure(fig, 600), width="stretch")

methodological_note(
    "O tamanho dos pontos representa a chuva acumulada e a cor representa a completude das "
    "observações. Estações usam suas coordenadas reais; baixa densidade regional reduz a "
    "representatividade do resumo estadual."
)
st.subheader("Cobertura territorial por UF")
coverage_by_uf = (
    all_points[all_points.coverage_pct >= minimum_coverage]
    .groupby("uf", as_index=False)
    .agg(
        estacoes_validas=("station_code", "nunique"),
        cobertura_media_pct=("coverage_pct", "mean"),
        chuva_acumulada_mm=("total_rain", "mean"),
    )
    .sort_values(["estacoes_validas", "cobertura_media_pct"])
)
st.dataframe(
    coverage_by_uf,
    column_config={
        "uf": "UF",
        "estacoes_validas": "Estações válidas",
        "cobertura_media_pct": st.column_config.NumberColumn("Cobertura média", format="%.1f%%"),
        "chuva_acumulada_mm": st.column_config.NumberColumn(
            "Chuva média acumulada", format="%.1f mm"
        ),
    },
    hide_index=True,
    width="stretch",
)

st.subheader("Dias mais extremos no recorte")
top_days = series.nlargest(15, "max_station_precipitation_mm")[
    ["date", "reporting_stations", "mean_station_precipitation_mm", "max_station_precipitation_mm"]
]
st.dataframe(
    top_days.rename(
        columns={
            "date": "Data",
            "reporting_stations": "Estações reportando",
            "mean_station_precipitation_mm": "Chuva média (mm)",
            "max_station_precipitation_mm": "Chuva máxima (mm)",
        }
    ),
    hide_index=True,
    width="stretch",
)

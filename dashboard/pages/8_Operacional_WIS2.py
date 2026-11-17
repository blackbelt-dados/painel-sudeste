from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st
from common import (
    RAIN_COLOR,
    configure_page,
    format_ptbr,
    hero,
    load_operational_data,
    methodological_note,
    style_figure,
)

VARIABLE_LABELS = {
    "air_temperature": "Temperatura do ar",
    "relative_humidity": "Umidade relativa",
    "total_precipitation_or_total_water_equivalent": "Precipitação reportada",
    "wind_speed": "Velocidade do vento",
    "maximum_wind_gust_speed": "Rajada máxima",
    "pressure_reduced_to_mean_sea_level": "Pressão ao nível do mar",
}

configure_page("INMET WIS2 operacional no Sudeste", "☁️")
station_variables, variables, stations, status = load_operational_data()
hero(
    "INMET WIS2 operacional - Sudeste",
    "Observações de ES, MG, RJ e SP recortadas pelas malhas oficiais do IBGE antes da camada Gold.",
)

date_label = date.fromisoformat(status["observation_date_utc"]).strftime("%d/%m/%y")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Data UTC", date_label)
m2.metric("Registros no Sudeste", format_ptbr(status["records"]))
m3.metric("Estações no Sudeste", format_ptbr(status["stations"]))
m4.metric("Duplicidades", format_ptbr(status["duplicates"]))

methodological_note(
    "A Bronze preserva a coleta nacional do INMET. A camada Gold e esta página contêm somente "
    "estações localizadas em ES, MG, RJ e SP pelas malhas do IBGE 2025, depois da conferência "
    "de contagens, duplicidades e SHA-256. Esta visão não constitui alerta meteorológico."
)

scope = status["geographic_scope"]
state_counts = scope["stations_by_state"]
st.caption(
    "Escopo geográfico: Sudeste - "
    + " | ".join(f"{uf}: {format_ptbr(state_counts[uf])} estações" for uf in scope["states"])
    + f" | Bronze nacional preservada: {format_ptbr(status['source_records'])} registros."
)

with st.sidebar:
    st.subheader("Dados operacionais")
    selected_variable = st.selectbox(
        "Variável",
        variables["variable"].tolist(),
        format_func=lambda value: VARIABLE_LABELS.get(value, value),
    )

selected = station_variables[station_variables.variable == selected_variable].copy()
summary = variables[variables.variable == selected_variable].iloc[0]
unit = summary["unit"] or "unidade informada pela fonte"
display_unit = "°C" if unit == "Celsius" else unit

st.subheader(VARIABLE_LABELS.get(selected_variable, selected_variable))
c1, c2, c3, c4 = st.columns(4)
c1.metric("Estações", format_ptbr(summary["stations"]))
c2.metric("Observações", format_ptbr(summary["observations"]))
c3.metric("Média", f"{format_ptbr(summary['mean_value'], 2)} {display_unit}")
c4.metric("Máximo", f"{format_ptbr(summary['max_value'], 2)} {display_unit}")

map_data = selected.dropna(subset=["latitude", "longitude", "mean_value"])
if not map_data.empty:
    map_figure = px.scatter_map(
        map_data,
        lat="latitude",
        lon="longitude",
        color="mean_value",
        size="observations",
        hover_name="station_wigos",
        hover_data={
            "latitude": ":.3f",
            "longitude": ":.3f",
            "observations": True,
            "min_value": ":.2f",
            "mean_value": ":.2f",
            "max_value": ":.2f",
        },
        color_continuous_scale="Blues",
        zoom=4.0,
        center={"lat": -20.3, "lon": -44.4},
        title=f"Média dos valores reportados por estação ({unit})",
    )
    map_figure.update_layout(map_style="carto-darkmatter")
    st.plotly_chart(style_figure(map_figure, 560), width="stretch")
else:
    st.info("A variável selecionada não possui coordenadas e valores válidos para o mapa.")

left, right = st.columns([1.2, 1])
distribution = px.histogram(
    selected.dropna(subset=["mean_value"]),
    x="mean_value",
    nbins=35,
    color_discrete_sequence=[RAIN_COLOR],
    labels={"mean_value": f"Média por estação ({unit})"},
    title="Distribuição entre estações",
)
left.plotly_chart(style_figure(distribution, 420), width="stretch")
right.dataframe(
    selected.sort_values("max_value", ascending=False)[
        [
            "station_wigos",
            "observations",
            "min_value",
            "mean_value",
            "max_value",
            "last_report_time_utc",
        ]
    ].head(100).rename(
        columns={
            "station_wigos": "Estação WIGOS",
            "observations": "Observações",
            "min_value": "Mínimo",
            "mean_value": "Média",
            "max_value": "Máximo",
            "last_report_time_utc": "Último reporte UTC",
        }
    ),
    hide_index=True,
    width="stretch",
)

with st.expander("Rastreabilidade da camada Gold"):
    st.json(status)
    st.dataframe(
        variables.assign(
            variavel=variables.variable.map(
                lambda value: VARIABLE_LABELS.get(value, value)
            )
        )[
            [
                "variavel",
                "unit",
                "observations",
                "valid_values",
                "stations",
                "min_value",
                "mean_value",
                "max_value",
            ]
        ],
        hide_index=True,
        width="stretch",
    )

st.caption(
    f"Fonte: INMET WIS2/OGC · Data UTC: {date_label} · "
    f"Qualidade: {status['quality']} · SHA-256 verificado."
)

import plotly.express as px
import streamlit as st
from common import (
    DISASTER_COLOR,
    add_uf_coordinates,
    configure_page,
    format_ptbr,
    hero,
    load_data,
    load_municipal_geojson,
    methodological_note,
    style_figure,
)

configure_page("Desastres", "🗺️")
atlas, *_ = load_data()
atlas = atlas.assign(
    ibge_code=atlas.ibge_code.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(7)
)
hero(
    "Desastres no Sudeste",
    "Distribuição territorial, evolução histórica e impactos registrados em ES, MG, RJ e SP.",
)
map_level = st.sidebar.radio("Nível territorial", ["UF", "Município"], horizontal=True)
years = st.sidebar.slider("Período", int(atlas.year.min()), int(atlas.year.max()), (1991, 2025))
months = st.sidebar.multiselect(
    "Meses", list(range(1, 13)), placeholder="Todos", format_func=lambda month: f"{month:02d}"
)
ufs = st.sidebar.multiselect("UF", sorted(atlas.uf.dropna().unique()), placeholder="Todas")
municipality_catalog = atlas[["ibge_code", "municipality", "uf"]].drop_duplicates()
if ufs:
    municipality_catalog = municipality_catalog[municipality_catalog.uf.isin(ufs)]
municipality_catalog = municipality_catalog.sort_values(["uf", "municipality"])
municipality_labels = {
    row.ibge_code: f"{row.municipality} — {row.uf}"
    for row in municipality_catalog.itertuples(index=False)
}
municipality_codes = st.sidebar.multiselect(
    "Município",
    municipality_catalog.ibge_code.tolist(),
    placeholder="Todos",
    format_func=lambda code: municipality_labels.get(code, code),
)
types = st.sidebar.multiselect(
    "Tipologia", sorted(atlas.disaster_type.dropna().unique()), placeholder="Todas"
)
minimum_affected = st.sidebar.number_input("Mínimo de danos humanos", min_value=0, value=0, step=10)
map_metric = st.sidebar.selectbox(
    "Métrica do mapa",
    ["events", "affected", "deaths", "losses"],
    format_func={
        "events": "Ocorrências",
        "affected": "Danos humanos diretos",
        "deaths": "Óbitos",
        "losses": "Danos e prejuízos",
    }.get,
)
map_normalization = st.sidebar.selectbox(
    "Normalização territorial",
    ["total", "per_event"] if map_level == "Município" else ["total", "per_municipality", "per_event"],
    format_func={
        "total": "Valor absoluto",
        "per_municipality": "Por município com registro",
        "per_event": "Por ocorrência",
    }.get,
)
df = atlas[atlas.year.between(*years)]
df = df[df.month.isin(months)] if months else df
df = df[df.uf.isin(ufs)] if ufs else df
df = df[df.ibge_code.isin(municipality_codes)] if municipality_codes else df
df = df[df.disaster_type.isin(types)] if types else df
df = df[df.affected >= minimum_affected]
df = df.assign(losses=df.material_damage_brl + df.public_loss_brl + df.private_loss_brl)
st.caption(f"Atualização automática · {format_ptbr(len(df))} registros no recorte")
if df.empty:
    st.warning("Nenhum registro atende aos filtros atuais.")
    st.stop()
losses = df[["material_damage_brl", "public_loss_brl", "private_loss_brl"]].sum().sum()
cols = st.columns(4)
cols[0].metric("Ocorrências", format_ptbr(len(df)))
cols[1].metric("Municípios", format_ptbr(df.ibge_code.nunique()))
cols[2].metric("Óbitos", format_ptbr(df.deaths.sum()))
cols[3].metric("Danos e prejuízos", f"R$ {format_ptbr(losses / 1e9, 1)} bi")
metric_labels = {
    "events": "Ocorrências",
    "affected": "Danos humanos diretos",
    "deaths": "Óbitos",
    "losses": "Danos e prejuízos (R$)",
}
mapped_metric = map_metric
if map_level == "UF":
    map_data = add_uf_coordinates(
        df.groupby("uf", as_index=False).agg(
            events=("protocol", "count"),
            affected=("affected", "sum"),
            deaths=("deaths", "sum"),
            losses=("losses", "sum"),
            municipalities=("ibge_code", "nunique"),
        )
    )
    if map_normalization == "per_municipality":
        mapped_metric = f"{map_metric}_normalized"
        map_data[mapped_metric] = map_data[map_metric] / map_data.municipalities.clip(lower=1)
        metric_labels[mapped_metric] = f"{metric_labels[map_metric]} por município com registro"
    elif map_normalization == "per_event":
        mapped_metric = f"{map_metric}_normalized"
        map_data[mapped_metric] = map_data[map_metric] / map_data.events.clip(lower=1)
        metric_labels[mapped_metric] = f"{metric_labels[map_metric]} por ocorrência"
    fig = px.scatter_map(
        map_data,
        lat="latitude",
        lon="longitude",
        size=mapped_metric,
        color=mapped_metric,
        hover_name="uf",
        hover_data={
            "events": True,
            "affected": True,
            "deaths": True,
            "latitude": False,
            "longitude": False,
        },
        center={"lat": -20.1, "lon": -44.5},
        zoom=4.0,
        color_continuous_scale="YlOrRd",
        labels=metric_labels,
        title=f"Mapa por UF — {metric_labels[mapped_metric]}",
        size_max=55,
    )
else:
    map_data = df.groupby(["ibge_code", "uf"], as_index=False).agg(
        municipality=("municipality", "last"),
        events=("protocol", "count"),
        affected=("affected", "sum"),
        deaths=("deaths", "sum"),
        losses=("losses", "sum"),
    )
    if map_normalization == "per_event":
        mapped_metric = f"{map_metric}_normalized"
        map_data[mapped_metric] = map_data[map_metric] / map_data.events.clip(lower=1)
        metric_labels[mapped_metric] = f"{metric_labels[map_metric]} por ocorrência"
    fig = px.choropleth_map(
        map_data,
        geojson=load_municipal_geojson(),
        locations="ibge_code",
        featureidkey="properties.CD_MUN",
        color=mapped_metric,
        hover_name="municipality",
        hover_data={
            "uf": True,
            "events": True,
            "affected": True,
            "deaths": True,
            "losses": ":,.0f",
            "ibge_code": False,
        },
        center={"lat": -20.1, "lon": -44.5},
        zoom=4.0,
        opacity=0.78,
        color_continuous_scale="YlOrRd",
        labels=metric_labels,
        title=f"Mapa por município — {metric_labels[mapped_metric]}",
    )
fig.update_layout(map_style="carto-darkmatter")
st.plotly_chart(style_figure(fig, 570), width="stretch")
if map_level == "UF":
    methodological_note(
        "Os símbolos estão posicionados nos <b>centroides das UFs</b> e não representam a "
        "localização exata dos eventos. A normalização por município usa somente municípios "
        "com registro no recorte; não equivale a uma taxa populacional ou de exposição."
    )
else:
    methodological_note(
        "Os polígonos seguem as <b>malhas municipais oficiais do IBGE 2025</b>. Os indicadores "
        "são agregados pelo código IBGE do município e não equivalem a taxas populacionais ou "
        "de exposição. A geometria foi simplificada apenas para desempenho do painel."
    )
    st.subheader("Municípios no recorte")
    ranking = map_data.sort_values(mapped_metric, ascending=False)[
        ["municipality", "uf", "events", "affected", "deaths", "losses"]
    ]
    st.dataframe(
        ranking.rename(
            columns={
                "municipality": "Município",
                "uf": "UF",
                "events": "Ocorrências",
                "affected": "Danos humanos diretos",
                "deaths": "Óbitos",
                "losses": "Danos e prejuízos (R$)",
            }
        ),
        hide_index=True,
        width="stretch",
    )
left, right = st.columns(2)
time_grain = st.radio("Agrupamento temporal", ["Ano", "Mês"], horizontal=True)
group_column = "year" if time_grain == "Ano" else "month"
yearly = df.groupby("year", as_index=False).size().rename(columns={"size": "events"})
if group_column == "month":
    yearly = df.groupby("month", as_index=False).size().rename(columns={"size": "events"})
left.plotly_chart(
    style_figure(
        px.area(
            yearly,
            x=group_column,
            y="events",
            labels={"year": "Ano", "month": "Mês", "events": "Ocorrências"},
            title=f"Ocorrências por {time_grain.lower()}",
            color_discrete_sequence=[DISASTER_COLOR],
        )
    ),
    width="stretch",
)
top = df.disaster_type.value_counts().head(10).sort_values()
right.plotly_chart(
    style_figure(
        px.bar(
            x=top.values,
            y=top.index,
            orientation="h",
            labels={"x": "Ocorrências", "y": "Tipologia"},
            title="Tipologias mais frequentes",
            color_discrete_sequence=["#FB923C"],
        )
    ),
    width="stretch",
)

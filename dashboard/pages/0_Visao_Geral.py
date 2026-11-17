import streamlit as st
from common import configure_page, hero, load_data

configure_page("Visão geral", "🌧️")
atlas, stations, _, integrated, ocean = load_data()
hero(
    "Painel de Desastres e Chuvas Extremas",
    "Aplicação multipágina para explorar desastres, precipitação e contexto oceano-climático.",
)
cols = st.columns(4)
cols[0].metric("Ocorrências históricas", f"{len(atlas):,.0f}".replace(",", "."))
cols[1].metric("Estações em 2025", f"{stations.station_code.nunique():,.0f}")
cols[2].metric("Eventos integrados", f"{len(integrated):,.0f}".replace(",", "."))
cols[3].metric("Meses oceânicos", f"{len(ocean)} de 12")
st.subheader("Navegue pelo painel")
items = [
    ("pages/1_Desastres.py", "🗺️ Desastres", "Histórico, mapa e impactos."),
    ("pages/2_Chuva.py", "🌧️ Chuva e estações", "Precipitação e rede INMET."),
    ("pages/3_Oceano_e_Clima.py", "🌊 Oceano e clima", "TSM, anomalias e ENSO."),
    ("pages/4_Analise_Integrada.py", "🔎 Análise integrada", "Eventos, chuva e clima."),
    ("pages/6_Dados_e_Metodo.py", "📚 Dados e método", "Cobertura e limitações."),
]
if not st.session_state.get("public_mode", False):
    items.insert(
        4,
        ("pages/5_Cargas_e_APIs.py", "⚙️ Cargas e APIs", "Execução, arquivos e fontes."),
    )
for path, label, caption in items:
    st.page_link(path, label=label)
    st.caption(caption)
st.info(
    "Produto analítico retrospectivo. O histórico de desastres cobre 1991–2025; chuva, oceano e "
    "integração cobrem 2025. Não constitui previsão, alerta operacional ou demonstração de "
    "causalidade."
)

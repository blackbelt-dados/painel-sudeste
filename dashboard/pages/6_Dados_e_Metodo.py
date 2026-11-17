import pandas as pd
import streamlit as st
from common import configure_page, hero, load_data

configure_page("Dados e método", "📚")
atlas, stations, _, integrated, ocean = load_data()
hero("Dados e método", "Cobertura, transformações, premissas e limites de interpretação.")
st.subheader("Cobertura carregada")
st.dataframe(
    pd.DataFrame(
        {
            "Conjunto": [
                "Atlas",
                "INMET por estação/dia",
                "NOAA/CPC Niño 3.4",
                "Eventos integrados",
            ],
            "Registros": [len(atlas), len(stations), len(ocean), len(integrated)],
            "Período": [
                f"{atlas.year.min()}–{atlas.year.max()}",
                f"{stations.date.min().date()} a {stations.date.max().date()}",
                f"{ocean.date.min().date()} a {ocean.date.max().date()}",
                "2025",
            ],
        }
    ),
    hide_index=True,
    width="stretch",
)
st.subheader("Como interpretar")
st.markdown("""- O Atlas fornece ocorrências municipais e impactos registrados administrativamente.
- A chuva horária do INMET é agregada por estação/dia e resumida por UF/dia.
- Cada evento recebe chuva estadual do dia e acumulados antecedentes de 3 e 7 dias.
- A TSM e a anomalia Niño 3.4 fornecem contexto climático de grande escala.
- Mapas por UF usam centroides estaduais; os pontos não são a localização exata do evento.
- **Com observação de chuva** indica disponibilidade de estação na UF/data, não ocorrência de chuva no município.
- A normalização por município usa somente municípios com registro no recorte e não substitui taxas por população ou exposição.
- Desastres cobrem 1991–2025; chuva, oceano e análises integradas cobrem apenas 2025.
- Correlações são sensíveis a valores extremos, excesso de zeros, sazonalidade e agregação estadual.
- As associações são descritivas, não causais, e o produto não constitui alerta ou previsão.""")
st.subheader("Compatibilidade das escalas")
st.dataframe(
    pd.DataFrame(
        {
            "Componente": ["Desastres", "Chuva", "Oceano"],
            "Escala espacial": ["Município", "UF (resumo das estações)", "Região Niño 3.4"],
            "Escala temporal": ["Data do registro", "Diária", "Mensal"],
            "Uso na integração": [
                "Unidade observacional",
                "Atribuída pela UF e data",
                "Contexto climático do mês",
            ],
        }
    ),
    hide_index=True,
    width="stretch",
)
st.subheader("Fluxo de dados")
st.code(
    "Fontes oficiais → Bronze + manifesto → transformação → CSVs analíticos → Streamlit",
    language="text",
)

"""Entrada pública do Painel para hospedagem no Streamlit Community Cloud.

A página de execução de cargas permanece disponível apenas na entrada local
``dashboard/app.py``. A versão pública expõe análises, dados e metodologia,
sem controles capazes de alterar os conjuntos processados.
"""

import importlib

import common
import streamlit as st

importlib.reload(common)

st.set_page_config(
    page_title="Painel de Desastres e Chuvas Extremas",
    page_icon="🌧️",
    layout="wide",
)

st.session_state["public_mode"] = True

pages = {
    "Painel": [
        st.Page("pages/0_Visao_Geral.py", title="Visão geral", icon="🏠", default=True),
        st.Page("pages/8_Operacional_WIS2.py", title="INMET WIS2 operacional", icon="☁️"),
    ],
    "Análises": [
        st.Page("pages/1_Desastres.py", title="Desastres", icon="🗺️"),
        st.Page("pages/2_Chuva.py", title="Chuva e estações", icon="🌧️"),
        st.Page("pages/3_Oceano_e_Clima.py", title="Oceano e clima", icon="🌊"),
        st.Page("pages/4_Analise_Integrada.py", title="Análise integrada", icon="🔎"),
        st.Page("pages/7_Correlacoes.py", title="Correlações", icon="📈"),
    ],
    "Documentação": [
        st.Page("pages/6_Dados_e_Metodo.py", title="Dados e método", icon="📚"),
    ],
}

st.navigation(pages).run()

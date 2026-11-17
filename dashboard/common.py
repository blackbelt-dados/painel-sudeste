from __future__ import annotations

import gzip
import json
from math import isnan
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed" / "dashboard"
RAIN_COLOR, DISASTER_COLOR, OCEAN_COLOR = "#38BDF8", "#F97316", "#22D3EE"
UF_CENTROIDS = {
    "AC": (-9.02, -70.81),
    "AL": (-9.57, -36.78),
    "AM": (-3.47, -65.10),
    "AP": (1.41, -51.77),
    "BA": (-12.96, -41.70),
    "CE": (-5.20, -39.53),
    "DF": (-15.78, -47.80),
    "ES": (-19.19, -40.34),
    "GO": (-15.98, -49.86),
    "MA": (-5.42, -45.44),
    "MG": (-18.51, -44.56),
    "MS": (-20.51, -54.54),
    "MT": (-12.64, -55.42),
    "PA": (-3.79, -52.48),
    "PB": (-7.28, -36.72),
    "PE": (-8.38, -37.86),
    "PI": (-6.60, -42.28),
    "PR": (-24.89, -51.55),
    "RJ": (-22.25, -42.66),
    "RN": (-5.81, -36.59),
    "RO": (-10.83, -63.34),
    "RR": (1.99, -61.33),
    "RS": (-30.17, -53.50),
    "SC": (-27.45, -50.95),
    "SE": (-10.57, -37.45),
    "SP": (-22.19, -48.79),
    "TO": (-9.46, -48.26),
}

METRIC_LABELS = {
    "events": "Ocorrências",
    "affected": "Danos humanos diretos",
    "deaths": "Óbitos",
    "losses": "Danos e prejuízos (R$)",
    "rain_7d": "Chuva média antecedente — 7 dias (mm)",
    "coverage_pct": "Cobertura da estação (%)",
    "total_rain": "Chuva acumulada (mm)",
    "mean_station_precipitation_mm": "Média entre estações",
    "max_station_precipitation_mm": "Máximo entre estações",
    "rain_same_day_max_mm": "Chuva máxima no dia (mm)",
    "rain_3d_mean_sum_mm": "Chuva acumulada — 3 dias (mm)",
    "rain_7d_mean_sum_mm": "Chuva acumulada — 7 dias (mm)",
    "disaster_type": "Tipologia",
}


def configure_page(title: str, icon: str) -> None:
    del title, icon
    st.markdown(
        """<style>
        [data-testid="stAppViewContainer"]{background:#07111f;color:#e5eef8}
        [data-testid="stSidebar"]{background:#0c1a2d}
        [data-testid="stMetric"]{background:linear-gradient(135deg,#10243c,#0b1829);border:1px solid #1f3a56;border-radius:14px;padding:14px}
        .hero{padding:1.4rem 1.7rem;border-radius:18px;margin-bottom:1rem;background:linear-gradient(120deg,#0d2b46,#123c55 55%,#164e63);border:1px solid #24536e}
        .hero h1{margin:0;color:#f8fafc;font-size:clamp(1.8rem,4vw,2.65rem);line-height:1.12}
        .hero p{margin:.45rem 0 0;color:#bae6fd}
        .method-note{padding:.8rem 1rem;border-left:4px solid #38bdf8;background:#0b1d30;border-radius:8px;margin:.6rem 0 1rem}
        @media(max-width:640px){
          .block-container{padding-left:1rem!important;padding-right:1rem!important;padding-top:1rem!important}
          .hero{padding:1rem 1.1rem;border-radius:14px}
          .hero h1{font-size:1.85rem}
          .hero p{font-size:.95rem}
          [data-testid="stMetric"]{padding:10px}
        }
        </style>""",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Fontes oficiais: Sedec/MIDR, INMET e NOAA/CPC")
    st.sidebar.caption("Análise retrospectiva — não constitui alerta.")


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True
    )


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = [
        DATA_DIR / "atlas_events.csv",
        DATA_DIR / "inmet_station_daily_2025.csv",
        DATA_DIR / "inmet_uf_daily_2025.csv",
        DATA_DIR / "integrated_events_2025.csv",
        DATA_DIR / "ocean_monthly_2025.csv",
    ]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        if st.session_state.get("public_mode", False):
            st.error("Os dados do Painel estão temporariamente indisponíveis.")
        else:
            st.error("Dados tratados ausentes. Execute as cargas em Cargas e APIs.")
        st.code("\n".join(missing))
        st.stop()
    return (
        pd.read_csv(paths[0], parse_dates=["event_date"]),
        pd.read_csv(paths[1], parse_dates=["date"]),
        pd.read_csv(paths[2], parse_dates=["date"]),
        pd.read_csv(paths[3], parse_dates=["event_date"]),
        pd.read_csv(paths[4], parse_dates=["date"]),
    )


@st.cache_data
def load_operational_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, object],
]:
    paths = [
        DATA_DIR / "inmet_wis2_station_variable_latest.csv",
        DATA_DIR / "inmet_wis2_variable_summary_latest.csv",
        DATA_DIR / "inmet_wis2_stations_latest.csv",
        DATA_DIR / "inmet_wis2_status.json",
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        if st.session_state.get("public_mode", False):
            st.info("Os dados operacionais estão temporariamente indisponíveis.")
        else:
            st.info(
                "Dados operacionais ausentes. Sincronize o WIS2 e construa a camada Gold "
                "na página Cargas e APIs."
            )
        st.code("\n".join(missing))
        st.stop()
    status = json.loads(paths[3].read_text(encoding="utf-8"))
    return (
        pd.read_csv(paths[0]),
        pd.read_csv(paths[1]),
        pd.read_csv(paths[2]),
        status,
    )


@st.cache_data
def load_municipal_geojson() -> dict[str, object]:
    path = ROOT / "data" / "reference" / "ibge" / "sudeste_municipios_ibge_2025.geojson.gz"
    if not path.exists():
        st.error("Malha municipal do IBGE ausente. Reconstrua a referência geográfica.")
        st.stop()
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def style_figure(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": 1.08},
    )
    return fig


def format_ptbr(value: float, decimals: int = 0) -> str:
    """Formata números sem depender do locale instalado no sistema."""
    if pd.isna(value):
        return "—"
    rendered = f"{value:,.{decimals}f}"
    return rendered.replace(",", "X").replace(".", ",").replace("X", ".")


def correlation_strength(value: float) -> str:
    if pd.isna(value) or isnan(float(value)):
        return "indeterminada"
    magnitude = abs(float(value))
    if magnitude < 0.10:
        return "praticamente inexistente"
    if magnitude < 0.30:
        return "fraca"
    if magnitude < 0.50:
        return "moderada"
    if magnitude < 0.70:
        return "forte"
    return "muito forte"


def methodological_note(text: str) -> None:
    st.markdown(f'<div class="method-note">{text}</div>', unsafe_allow_html=True)


def add_uf_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["latitude"] = result.uf.map(lambda u: UF_CENTROIDS.get(u, (None, None))[0])
    result["longitude"] = result.uf.map(lambda u: UF_CENTROIDS.get(u, (None, None))[1])
    return result.dropna(subset=["latitude", "longitude"])

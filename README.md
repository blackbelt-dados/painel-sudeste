# Painel Sudeste

Versão pública do **Painel de Desastres e Chuvas Extremas**, desenvolvido como
projeto aplicado da pós-graduação em Engenharia e Arquitetura de Dados.

O aplicativo reúne dados oficiais para apoiar a exploração retrospectiva de
desastres, precipitação e contexto oceano-climático em Espírito Santo, Minas
Gerais, Rio de Janeiro e São Paulo. O detalhamento territorial utiliza a malha
municipal oficial do IBGE.

## Acesso

- Painel: <https://painel-sudeste.streamlit.app>
- Guia de uso: <https://manual-painel-desastres-sudeste.netlify.app>

## Escopo e responsabilidade

O Painel é um produto analítico e demonstrativo. Ele não constitui previsão,
alerta operacional, recomendação de resposta a emergências nem demonstração de
causalidade.

## Execução local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run dashboard/public_app.py
```

As rotinas administrativas de ingestão e processamento não fazem parte desta
versão pública.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard Segurança do Trabalho", layout="wide")

SHEET_ID = "174sI6MnCUSW34Z-nptBDybP5i03oj15dgCbIcjUltXk"
GID_VISITA = "0"
GID_ESTOQUE = "300539656"
GID_TREINAMENTOS = "1439340822"

CSV_VISITA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_VISITA}"
CSV_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_ESTOQUE}"
CSV_TREINAMENTOS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_TREINAMENTOS}"

if "atualizar" not in st.session_state:
    st.session_state.atualizar = 0

if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.session_state.atualizar += 1

@st.cache_data
def carregar_dados(url):
    return pd.read_csv(url)

aba = st.sidebar.selectbox(
    "Escolha a tabela para visualizar:",
    ("Visita Técnica", "Estoque", "Treinamentos")
)

if aba == "Visita Técnica":
    df = carregar_dados(CSV_VISITA)
    df.columns = [
        "DATA", "REALIZADOR", "CONTRATO", "VISITAS", "CONFORMIDADE",
        "NÃO CONFORMIDADE", "MOTIVO DE NÃO CONFORMIDADE", "CORRIGIDO", "PENDENTE"
    ]
    st.title("📋 Visita Técnica")
    st.dataframe(df)

    # Converter DATA para datetime
    df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)

    # Métricas
    st.metric("Total de Visitas", df["VISITAS"].sum())
    st.metric("Conformidades", df["CONFORMIDADE"].sum())
    st.metric("Não Conformidades", df["NÃO CONFORMIDADE"].sum())

    # Gráfico de visitas por mês
    df["AnoMes"] = df["DATA"].dt.to_period("M").astype(str)
    visitas_mes = df.groupby("AnoMes")["VISITAS"].sum()
    st.bar_chart(visitas_mes)
elif aba == "Estoque":
    df = carregar_dados(CSV_ESTOQUE)
    df.columns = ["MATERIAL", "QUANTIDADE"]
    st.title("📦 Estoque")
    st.dataframe(df)

    st.metric("Total de Itens", df["QUANTIDADE"].sum())
    st.subheader("Materiais com menor estoque")
    st.dataframe(df.sort_values("QUANTIDADE").head(10))
    st.bar_chart(df.set_index("MATERIAL")["QUANTIDADE"])
elif aba == "Treinamentos":
    df = carregar_dados(CSV_TREINAMENTOS)
    st.title("🎓 Treinamentos")
    st.dataframe(df)
    # Aqui você pode adicionar gráficos, métricas, filtros, etc.

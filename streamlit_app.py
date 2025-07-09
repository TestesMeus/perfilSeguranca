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
    df = pd.read_csv(url)
    # Corrige o cabeçalho se vier errado
    if df.shape[0] > 0 and not all(isinstance(col, str) for col in df.columns):
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
    return df

aba = st.sidebar.selectbox(
    "Escolha a tabela para visualizar:",
    ("Visita Técnica", "Estoque", "Treinamentos")
)

if aba == "Visita Técnica":
    df = carregar_dados(CSV_VISITA)
    if not df.empty:
        df.columns = [
            "DATA", "REALIZADOR", "CONTRATO", "VISITAS", "CONFORMIDADE",
            "NÃO CONFORMIDADE", "MOTIVO DE NÃO CONFORMIDADE", "CORRIGIDO", "PENDENTE"
        ]
        st.title("📋 Visita Técnica")
        st.dataframe(df)

        # Converter DATA para datetime
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)

        # Indicadores
        total_visitas = pd.to_numeric(df["VISITAS"], errors="coerce").sum()
        total_conformidade = pd.to_numeric(df["CONFORMIDADE"], errors="coerce").sum()
        total_nao_conformidade = pd.to_numeric(df["NÃO CONFORMIDADE"], errors="coerce").sum()
        percentual_conformidade = (total_conformidade / total_visitas) * 100 if total_visitas > 0 else 0
        percentual_nao_conformidade = (total_nao_conformidade / total_visitas) * 100 if total_visitas > 0 else 0
        visitas_pendentes = pd.to_numeric(df["PENDENTE"], errors="coerce").gt(0).sum()
        visitas_corrigidas = pd.to_numeric(df["CORRIGIDO"], errors="coerce").gt(0).sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Visitas", int(total_visitas))
        col2.metric("Conformidades", int(total_conformidade))
        col3.metric("Não Conformidades", int(total_nao_conformidade))

        col4, col5 = st.columns(2)
        col4.metric("% Conformidade", f"{percentual_conformidade:.1f}%")
        col5.metric("% Não Conformidade", f"{percentual_nao_conformidade:.1f}%")

        col6, col7 = st.columns(2)
        col6.metric("Visitas Pendentes de Correção", int(visitas_pendentes))
        col7.metric("Visitas Corrigidas", int(visitas_corrigidas))

        st.divider()

        # Gráfico de visitas por mês
        df["AnoMes"] = df["DATA"].dt.to_period("M").astype(str)
        visitas_mes = df.groupby("AnoMes")["VISITAS"].apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
        st.subheader("Evolução de Visitas por Mês")
        st.bar_chart(visitas_mes)

        # Gráfico de conformidade e não conformidade por mês
        conf_mes = df.groupby("AnoMes")["CONFORMIDADE"].apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
        nconf_mes = df.groupby("AnoMes")["NÃO CONFORMIDADE"].apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
        st.subheader("Conformidade x Não Conformidade por Mês")
        st.line_chart(pd.DataFrame({"Conformidade": conf_mes, "Não Conformidade": nconf_mes}))

        # Pie chart de conformidade
        st.subheader("Distribuição de Conformidade")
        fig1, ax1 = plt.subplots()
        ax1.pie([total_conformidade, total_nao_conformidade], labels=["Conformidade", "Não Conformidade"], autopct="%1.1f%%", startangle=90)
        ax1.axis("equal")
        st.pyplot(fig1)

        # Ranking dos maiores realizadores
        st.subheader("Ranking dos Realizadores de Visitas")
        ranking_realizadores = df.groupby("REALIZADOR")["VISITAS"].apply(lambda x: pd.to_numeric(x, errors="coerce").sum()).sort_values(ascending=False).head(10)
        st.bar_chart(ranking_realizadores)

        # Gráfico de barras dos principais motivos de não conformidade
        st.subheader("Principais Motivos de Não Conformidade")
        motivos = df["MOTIVO DE NÃO CONFORMIDADE"].value_counts().head(10)
        st.bar_chart(motivos)
    else:
        st.warning("Tabela de Visita Técnica vazia ou não carregada corretamente.")

elif aba == "Estoque":
    df = carregar_dados(CSV_ESTOQUE)
    if not df.empty:
        df.columns = ["MATERIAL", "QUANTIDADE"]
        st.title("📦 Estoque")
        st.dataframe(df)

        df["QUANTIDADE"] = pd.to_numeric(df["QUANTIDADE"], errors="coerce").fillna(0)
        total_itens = df["QUANTIDADE"].sum()
        materiais_zerados = (df["QUANTIDADE"] == 0).sum()
        material_maior_estoque = df.loc[df["QUANTIDADE"].idxmax(), "MATERIAL"] if not df.empty else "-"
        material_menor_estoque = df.loc[df["QUANTIDADE"].idxmin(), "MATERIAL"] if not df.empty else "-"

        col1, col2 = st.columns(2)
        col1.metric("Total de Itens em Estoque", int(total_itens))
        col2.metric("Materiais Zerados", int(materiais_zerados))

        col3, col4 = st.columns(2)
        col3.metric("Material com Maior Estoque", material_maior_estoque)
        col4.metric("Material com Menor Estoque", material_menor_estoque)

        st.divider()

        # Gráfico de barras dos 10 materiais com menor estoque
        st.subheader("Top 10 Materiais com Menor Estoque")
        menores = df.sort_values("QUANTIDADE").head(10)
        st.bar_chart(menores.set_index("MATERIAL")["QUANTIDADE"])

        # Gráfico de barras dos 10 materiais com maior estoque
        st.subheader("Top 10 Materiais com Maior Estoque")
        maiores = df.sort_values("QUANTIDADE", ascending=False).head(10)
        st.bar_chart(maiores.set_index("MATERIAL")["QUANTIDADE"])

        # Pie chart da distribuição dos itens (opcional)
        st.subheader("Distribuição dos Itens em Estoque (Top 10)")
        fig2, ax2 = plt.subplots()
        ax2.pie(maiores["QUANTIDADE"], labels=maiores["MATERIAL"], autopct="%1.1f%%", startangle=90)
        ax2.axis("equal")
        st.pyplot(fig2)
    else:
        st.warning("Tabela de Estoque vazia ou não carregada corretamente.")

elif aba == "Treinamentos":
    df = carregar_dados(CSV_TREINAMENTOS)
    st.title("🎓 Treinamentos")
    st.dataframe(df)
    st.info("Adapte aqui os indicadores e gráficos conforme as colunas da sua aba de treinamentos.")

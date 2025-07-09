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
        # Ajustar colunas para não exigir motivo, corrigido e pendente
        colunas_base = [
            "DATA", "REALIZADOR", "CONTRATO", "VISITAS", "CONFORMIDADE",
            "NÃO CONFORMIDADE", "MOTIVO DE NÃO CONFORMIDADE", "CORRIGIDO", "PENDENTE"
        ]
        # Se faltar alguma coluna, adiciona com valor vazio
        for col in colunas_base:
            if col not in df.columns:
                df[col] = ""
        df = df[colunas_base]
        st.title("📋 Visita Técnica")
        # Converter DATA para datetime
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)
        df["AnoMes"] = df["DATA"].dt.to_period("M").astype(str)

        # PRÉ-PROCESSAMENTO ROBUSTO
        # Padronizar e limpar colunas de sim/não
        for col in ["CONFORMIDADE", "NÃO CONFORMIDADE"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip().str.lower()
            else:
                df[col] = ""
        # VISITAS: se não existir ou vier vazia, cada linha é uma visita
        if "VISITAS" in df.columns:
            df["VISITAS"] = pd.to_numeric(df["VISITAS"], errors="coerce")
            df["VISITAS"] = df["VISITAS"].fillna(1)
        else:
            df["VISITAS"] = 1
        # Tratar colunas opcionais para evitar erros
        for col in ["CORRIGIDO", "PENDENTE"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            else:
                df[col] = 0

        # Filtro de mês
        meses_disponiveis = sorted(df["AnoMes"].dropna().unique())
        mes_selecionado = st.selectbox("Selecionar Mês:", ["Todos"] + meses_disponiveis, key="mes_visita")
        if mes_selecionado != "Todos":
            df = df[df["AnoMes"] == mes_selecionado]
        # Filtro de Realizador
        realizadores = sorted(df["REALIZADOR"].dropna().unique())
        realizador_selecionado = st.selectbox("Selecionar Realizador:", ["Todos"] + realizadores, key="realizador_visita")
        if realizador_selecionado != "Todos":
            df = df[df["REALIZADOR"] == realizador_selecionado]
        st.dataframe(df)

        # Indicadores
        total_visitas = int(df["VISITAS"].sum())
        total_conformidade = (df["CONFORMIDADE"] == "sim").sum()
        total_nao_conformidade = (df["NÃO CONFORMIDADE"] == "sim").sum()
        percentual_conformidade = (total_conformidade / total_visitas) * 100 if total_visitas > 0 else 0
        percentual_nao_conformidade = (total_nao_conformidade / total_visitas) * 100 if total_visitas > 0 else 0
        visitas_pendentes = df["PENDENTE"].gt(0).sum() if "PENDENTE" in df.columns else 0
        visitas_corrigidas = df["CORRIGIDO"].gt(0).sum() if "CORRIGIDO" in df.columns else 0

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
        visitas_mes = df.groupby("AnoMes")["VISITAS"].apply(lambda x: pd.to_numeric(x, errors="coerce").sum())
        st.subheader("Evolução de Visitas por Mês")
        st.bar_chart(visitas_mes)

        # Gráfico de conformidade e não conformidade por mês
        conf_mes = df.groupby("AnoMes")["CONFORMIDADE"].apply(lambda x: (x == "sim").sum())
        nconf_mes = df.groupby("AnoMes")["NÃO CONFORMIDADE"].apply(lambda x: (x == "sim").sum())
        st.subheader("Conformidade x Não Conformidade por Mês")
        st.line_chart(pd.DataFrame({"Conformidade": conf_mes, "Não Conformidade": nconf_mes}))

        # Pie chart de conformidade
        st.subheader("Distribuição de Conformidade")
        pie_labels = []
        pie_values = []
        if total_conformidade > 0:
            pie_labels.append("Conformidade")
            pie_values.append(total_conformidade)
        if total_nao_conformidade > 0:
            pie_labels.append("Não Conformidade")
            pie_values.append(total_nao_conformidade)

        if len(pie_values) > 1:
            fig1, ax1 = plt.subplots()
            ax1.pie(pie_values, labels=pie_labels, autopct="%1.1f%%", startangle=90)
            ax1.axis("equal")
            st.pyplot(fig1)
        elif len(pie_values) == 1:
            st.info(f"Todas as visitas estão em: {pie_labels[0]}. Gráfico de pizza não exibido pois só há um tipo de status.")
        else:
            st.info("Sem dados para exibir o gráfico de conformidade.")

        # Ranking dos maiores realizadores
        st.subheader("Ranking dos Realizadores de Visitas")
        ranking_realizadores = df.groupby("REALIZADOR")["VISITAS"].apply(lambda x: pd.to_numeric(x, errors="coerce").sum()).sort_values(ascending=False).head(10)
        st.bar_chart(ranking_realizadores)

        # Gráfico de barras dos principais motivos de não conformidade
        st.subheader("Principais Motivos de Não Conformidade")
        motivos = df["MOTIVO DE NÃO CONFORMIDADE"].value_counts().head(10) if "MOTIVO DE NÃO CONFORMIDADE" in df.columns else pd.Series()
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
    if not df.empty:
        df.columns = ["DATA", "NORMA", "CONVIDADOS", "PARTICIPANTES", "PERCENTUAL"]
        st.title("🎓 Treinamentos")
        # Converter DATA para datetime e colunas numéricas
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce", dayfirst=True)
        df["CONVIDADOS"] = pd.to_numeric(df["CONVIDADOS"], errors="coerce").fillna(0)
        df["PARTICIPANTES"] = pd.to_numeric(df["PARTICIPANTES"], errors="coerce").fillna(0)
        df["PERCENTUAL"] = pd.to_numeric(df["PERCENTUAL"], errors="coerce").fillna(0)
        # Remover linhas com valores nulos ou vazios nas colunas essenciais
        df = df.dropna(subset=["DATA", "NORMA", "CONVIDADOS", "PARTICIPANTES", "PERCENTUAL"])
        df = df[df["NORMA"].astype(str).str.strip().str.lower() != "none"]
        df["AnoMes"] = df["DATA"].dt.to_period("M").astype(str)
        # Filtro de mês
        meses_disponiveis = sorted(df["AnoMes"].dropna().unique())
        mes_selecionado = st.selectbox("Selecionar Mês:", ["Todos"] + meses_disponiveis, key="mes_treinamento")
        if mes_selecionado != "Todos":
            df = df[df["AnoMes"] == mes_selecionado]
        st.dataframe(df)

        # Indicadores
        total_treinamentos = df.shape[0]
        total_convidados = df["CONVIDADOS"].sum()
        total_participantes = df["PARTICIPANTES"].sum()
        percentual_geral = (total_participantes / total_convidados) * 100 if total_convidados > 0 else 0
        norma_mais_realizada = df["NORMA"].value_counts().idxmax() if not df["NORMA"].isnull().all() else "-"

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Treinamentos", total_treinamentos)
        col2.metric("Total de Convidados", int(total_convidados))
        col3.metric("Total de Participantes", int(total_participantes))

        col4, col5 = st.columns(2)
        col4.metric("% Participação Geral", f"{percentual_geral:.1f}%")
        col5.metric("Norma Mais Realizada", norma_mais_realizada)

        st.divider()

        # Evolução de treinamentos por mês
        treinamentos_mes = df.groupby("AnoMes").size()
        st.subheader("Evolução de Treinamentos por Mês")
        st.bar_chart(treinamentos_mes)

        # Gráfico de barras das normas mais realizadas
        st.subheader("Normas Mais Realizadas")
        normas = df["NORMA"].value_counts().head(10)
        st.bar_chart(normas)

        # Gráfico de barras do percentual de participação por norma
        st.subheader("% Participação por Norma (Média)")
        percentuais_norma = df.groupby("NORMA")["PERCENTUAL"].mean().sort_values(ascending=False)
        st.bar_chart(percentuais_norma)
    else:
        st.warning("Tabela de Treinamentos vazia ou não carregada corretamente.")

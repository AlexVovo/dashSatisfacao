import streamlit as st
import pandas as pd
import plotly.express as px

# Caminho fixo do arquivo Excel
file_path = "FormPacientes.xlsx"

st.title("📊 Feedback dos Pacientes")

try:
    df = pd.read_excel(file_path)
    st.success(f"Arquivo carregado com sucesso: {file_path}")

    if "Data de preenchimento" in df.columns:
        df["Data de preenchimento"] = pd.to_datetime(df["Data de preenchimento"], errors="coerce")

        # 🔧 Remover linhas com datas inválidas (NaT)
        df = df.dropna(subset=["Data de preenchimento"])

        # Extrair ano como int e mês como nome em português
        df["Ano"] = df["Data de preenchimento"].dt.year.astype(int)
        df["Mês"] = df["Data de preenchimento"].dt.strftime("%B")

        # Traduzir os nomes dos meses
        meses_traducao = {
            "January": "Janeiro", "February": "Fevereiro", "March": "Março",
            "April": "Abril", "May": "Maio", "June": "Junho",
            "July": "Julho", "August": "Agosto", "September": "Setembro",
            "October": "Outubro", "November": "Novembro", "December": "Dezembro"
        }
        df["Mês"] = df["Mês"].map(meses_traducao)

        st.subheader("📅 Filtrar por Mês e Ano")

        # Ordenar os meses corretamente
        ordem_meses = list(meses_traducao.values())
        anos_disponiveis = sorted(df["Ano"].unique())
        meses_disponiveis = [m for m in ordem_meses if m in df["Mês"].unique()]

        ano_selecionado = st.selectbox("Selecione o Ano", anos_disponiveis)
        mes_selecionado = st.selectbox("Selecione o Mês", meses_disponiveis)

        # Aplicar filtro
        df = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]

   
    # Colunas numéricas e categóricas
    numeric_columns = df.select_dtypes(include=['number']).columns
    categorical_columns = df.select_dtypes(include=['object']).columns
    categorical_columns = [col for col in categorical_columns if col != "Data de preenchimento"]

   

    # Gráfico para categóricos
    if len(categorical_columns) > 0:
        category = st.selectbox("Selecione uma pergunta do formulário", categorical_columns)
        df_counts = df[category].value_counts().reset_index()
        df_counts.columns = ['Resposta', 'Quantidade']
        fig_cat = px.bar(df_counts, x="Resposta", y="Quantidade", title=f"Respostas de {category}")
        st.plotly_chart(fig_cat)

        st.subheader(f"🔢 Quantidade de Respostas para '{category}'")
        st.write(df_counts)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.markdown("<script>window.addEventListener('beforeunload', () => {});</script>", unsafe_allow_html=True)

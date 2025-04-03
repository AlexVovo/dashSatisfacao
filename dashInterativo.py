import streamlit as st
import pandas as pd
import plotly.express as px

# Caminho fixo do arquivo Excel
file_path = "FormPacientes.xlsx"

st.title("📊 Dashboard Interativo")

# Tenta carregar o arquivo automaticamente
try:
    df = pd.read_excel(file_path)
    st.success(f"Arquivo carregado com sucesso: {file_path}")

    # Exibir os primeiros registros
    st.subheader("📄 Visualização dos dados")
    st.write(df.head())

    # Verificar colunas disponíveis
    numeric_columns = df.select_dtypes(include=['number']).columns
    categorical_columns = df.select_dtypes(include=['object']).columns

    # Criar gráfico de distribuição para colunas numéricas
    if len(numeric_columns) > 0:
        column = st.selectbox("Selecione uma coluna numérica para visualizar", numeric_columns)
        fig = px.histogram(df, x=column, nbins=20, title=f"Distribuição de {column}")
        st.plotly_chart(fig)

    # Criar gráfico de barras para perguntas do formulário (colunas categóricas)
    if len(categorical_columns) > 0:
        category = st.selectbox("Selecione uma pergunta do formulário", categorical_columns)
        df_counts = df[category].value_counts().reset_index()
        df_counts.columns = ['Resposta', 'Quantidade']  # Renomeia as colunas corretamente

        fig_cat = px.bar(df_counts, x="Resposta", y="Quantidade", title=f"Respostas de {category}")
        st.plotly_chart(fig_cat)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")

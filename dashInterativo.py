import streamlit as st
import pandas as pd
import plotly.express as px

# Caminho fixo do arquivo Excel
file_path = "FormPacientes.xlsx"

st.title("📊 Feedback dos Pacientes")

# Tenta carregar o arquivo automaticamente
try:
    df = pd.read_excel(file_path)
    st.success(f"Arquivo carregado com sucesso: {file_path}")

    # Exibir os primeiros registros
    st.subheader("📄 Visualização dos Dados")
    st.write(df.head())

    # Verificar colunas disponíveis
    numeric_columns = df.select_dtypes(include=['number']).columns
    categorical_columns = df.select_dtypes(include=['object']).columns

    # Remover a coluna "Data de preenchimento" do filtro, se existir
    categorical_columns = [col for col in categorical_columns if col != "Data de preenchimento"]

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

        # Exibir gráfico de barras
        fig_cat = px.bar(df_counts, x="Resposta", y="Quantidade", title=f"Respostas de {category}")
        st.plotly_chart(fig_cat)

        # Exibir tabela com os valores de quantidade
        st.subheader(f"🔢 Quantidade de Respostas para '{category}'")
        st.write(df_counts)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")

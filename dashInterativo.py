import streamlit as st
import pandas as pd
import plotly.express as px

file_path = "FormPacientes.xlsx"
st.title("📊 Feedback dos Pacientes")

try:
    df = pd.read_excel(file_path)
    st.success(f"Arquivo carregado com sucesso: {file_path}")

    st.subheader("📄 Visualização dos Dados")
    st.write(df.head())

    numeric_columns = df.select_dtypes(include=['number']).columns
    categorical_columns = df.select_dtypes(include=['object']).columns
    categorical_columns = [col for col in categorical_columns if col != "Data de preenchimento"]

    if len(numeric_columns) > 0:
        column = st.selectbox("Selecione uma coluna numérica para visualizar", numeric_columns)
        fig = px.histogram(df, x=column, nbins=20, title=f"Distribuição de {column}")
        st.plotly_chart(fig)

    if len(categorical_columns) > 0:
        category = st.selectbox("Selecione uma pergunta do formulário", categorical_columns)

        container = st.empty()
        with container:
            df_counts = df[category].value_counts().reset_index()
            df_counts.columns = ['Resposta', 'Quantidade']

            st.subheader(f"📌 Pergunta Selecionada:")
            st.markdown(f"**{category}**")

            fig_cat = px.bar(df_counts, x="Resposta", y="Quantidade", title=f"Distribuição das Respostas")
            st.plotly_chart(fig_cat)

            st.subheader("🔢 Quantidade de Respostas")
            st.write(df_counts)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")

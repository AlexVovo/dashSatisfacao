import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from fpdf import FPDF
import plotly.io as pio
import os
import re

# Função para limpar nomes de arquivos
def limpar_nome_arquivo(nome):
    return re.sub(r'[^\w\s-]', '_', nome).strip().replace(' ', '_')

file_path = "FormPacientes.xlsx"

st.title("📊 Feedback dos Pacientes")

try:
    df = pd.read_excel(file_path)
    st.success(f"Arquivo carregado com sucesso: {file_path}")

    if "Data de preenchimento" in df.columns:
        df["Data de preenchimento"] = pd.to_datetime(df["Data de preenchimento"], errors="coerce")
        df = df.dropna(subset=["Data de preenchimento"])

        df["Ano"] = df["Data de preenchimento"].dt.year.astype(int)
        df["Mês"] = df["Data de preenchimento"].dt.strftime("%B")

        meses_traducao = {
            "January": "Janeiro", "February": "Fevereiro", "March": "Março",
            "April": "Abril", "May": "Maio", "June": "Junho",
            "July": "Julho", "August": "Agosto", "September": "Setembro",
            "October": "Outubro", "November": "Novembro", "December": "Dezembro"
        }
        df["Mês"] = df["Mês"].map(meses_traducao)

        st.subheader("📅 Filtrar por Mês e Ano")
        ordem_meses = list(meses_traducao.values())
        anos_disponiveis = sorted(df["Ano"].unique())
        meses_disponiveis = [m for m in ordem_meses if m in df["Mês"].unique()]

        ano_selecionado = st.selectbox("Selecione o Ano", anos_disponiveis)
        mes_selecionado = st.selectbox("Selecione o Mês", meses_disponiveis)

        df = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]

    # Obter colunas categóricas
    categorical_columns = df.select_dtypes(include=['object']).columns
    categorical_columns = [col for col in categorical_columns if col != "Data de preenchimento"]

    # Dropdown de perguntas
    opcoes = ["Todas as Perguntas"] + categorical_columns
    categoria_escolhida = st.selectbox("Selecione uma pergunta do formulário", opcoes)

    graficos_salvos = []

    def exportar_excel(df_export, nome_arquivo="respostas.xlsx"):
        output = BytesIO()
        df_export.to_excel(output, index=False)
        st.download_button(
            label="⬇️ Baixar Excel",
            data=output.getvalue(),
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def exportar_pdf_com_graficos(lista_caminhos, nome_pdf="respostas.pdf"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for caminho in lista_caminhos:
            pdf.add_page()
            titulo = os.path.basename(caminho).replace("_", " ").replace(".png", "")
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=titulo, ln=True)
            pdf.image(caminho, x=10, y=30, w=180)

        pdf_bytes = pdf.output(dest='S').encode('latin1')
        st.download_button(
            "📄 Baixar PDF com Gráficos",
            data=pdf_bytes,
            file_name=nome_pdf,
            mime="application/pdf"
        )

    if categoria_escolhida != "Todas as Perguntas":
        df_counts = df[categoria_escolhida].value_counts().reset_index()
        df_counts.columns = ['Resposta', 'Quantidade']
        df_counts['Percentual (%)'] = (df_counts['Quantidade'] / df_counts['Quantidade'].sum() * 100).round(2)

        fig_cat = px.bar(
            df_counts, x="Resposta", y="Quantidade", text="Percentual (%)",
            title=f"Respostas de {categoria_escolhida}"
        )
        fig_cat.update_traces(textposition='outside')
        st.plotly_chart(fig_cat)

        st.subheader(f"🔢 Quantidade e Percentual de Respostas para '{categoria_escolhida}'")
        st.write(df_counts)

        # Salvar gráfico
        nome_limpo = limpar_nome_arquivo(categoria_escolhida)
        caminho_imagem = f"{nome_limpo}.png"
        pio.write_image(fig_cat, caminho_imagem)
        graficos_salvos.append(caminho_imagem)

        exportar_excel(df_counts)
        exportar_pdf_com_graficos(graficos_salvos)

    else:
        st.subheader("📋 Todas as Perguntas e Respostas")
        total_geral = 0
        respostas_totais = []

        for col in categorical_columns:
            st.markdown(f"### ❓ {col}")
            respostas = df[col].value_counts().reset_index()
            respostas.columns = ['Resposta', 'Quantidade']
            respostas['Percentual (%)'] = (respostas['Quantidade'] / respostas['Quantidade'].sum() * 100).round(2)
            total_geral += respostas['Quantidade'].sum()
            respostas['Pergunta'] = col
            respostas_totais.append(respostas)

            fig = px.bar(respostas, x="Resposta", y="Quantidade", text="Percentual (%)", title=f"Respostas para: {col}")
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig)

            nome_limpo = limpar_nome_arquivo(col)
            caminho_img = f"{nome_limpo}.png"
            pio.write_image(fig, caminho_img)
            graficos_salvos.append(caminho_img)

            st.write(respostas)

        st.markdown(f"## 📊 Total Geral de Respostas: **{total_geral}**")

        if respostas_totais:
            df_geral = pd.concat(respostas_totais)
            exportar_excel(df_geral, "todas_respostas.xlsx")
            exportar_pdf_com_graficos(graficos_salvos)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")

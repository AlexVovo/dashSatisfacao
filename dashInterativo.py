import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime, timedelta
import re
from fpdf import FPDF
import os

# Autenticando com Google Sheets
@st.cache_data
def get_google_sheet(spreadsheet_url, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credenciais.json", scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(spreadsheet_url).worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def limpar_nome_arquivo(nome):
    return re.sub(r'[^\w\s-]', '_', nome).strip().replace(' ', '_')

def exportar_excel(df, nome_arquivo="resumo_areas.xlsx"):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button(
        label="\U0001F4C5 Baixar Excel",
        data=buffer.getvalue(),
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def get_color(resposta):
    cores = {
        "Excelente": "green",
        "Bom": "blue",
        "Regular": "orange",
        "Ruim": "red",
        "Não se Aplica": "gray"
    }
    return cores.get(resposta, "black")

class PDF(FPDF):
    def header(self):
        try:
            self.image("logo.png", x=0, y=5, w=200)
        except:
            pass
        self.set_font("Arial", "B", 12)
        self.ln(30)
        self.cell(0, 10, "Relatório de Satisfação dos Pacientes", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.multi_cell(0, 10, title)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_table(self, df):
        self.set_font("Arial", "", 7)
        area_width = 30
        outras_width = (self.w - area_width - 20) / (len(df.columns) - 1)
        col_widths = [area_width if i == 0 else outras_width for i in range(len(df.columns))]
        row_height = 6

        # Cabeçalho
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], row_height, str(col)[:20], border=1)
        self.ln(row_height)

        # Linhas da tabela
        for _, row in df.iterrows():
            y_start = self.get_y()
            x_start = self.get_x()

            # Primeira célula (Área) com quebra de linha
            self.set_font("Arial", "B", 7)
            self.multi_cell(col_widths[0], row_height, str(row[0]), border=1)
            y_end = self.get_y()
            linha_altura = y_end - y_start

            # Resto da linha alinhado
            self.set_xy(x_start + col_widths[0], y_start)
            self.set_font("Arial", "", 7)
            for i, item in enumerate(row[1:], start=1):
                texto = str(item)
                self.cell(col_widths[i], linha_altura, texto[:15], border=1)
            self.ln(linha_altura)

nomes_areas = {
    0: "Serviço Social", 1: "Nutrição", 2: "Psicopedagogia", 3: "Psicologia", 4: "Odontologia",
    5: "Fonoaudiologia", 6: "Fisioterapia", 7: "Psiquiatria", 8: "Farmácia", 9: "Enfermagem",
    10: "Educativas/Educação em grupo", 11: "Assistência Familiar", 12: "Copa", 13: "Recepção",
    14: "Ações Culturais e Festividades", 15: "Recreação", 16: "Atividades Interativas",
    17: "Oficinas Arte/Vida", 18: "Apoio Jurídico", 19: "Limpeza do Local",
    20: "ICI x Famílias", 21: "Terapia Ocupacioal"
}

st.set_page_config(page_title="Satisfação Pacientes", layout="wide")
st.title("\U0001F4CA Feedback dos Pacientes")

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1UMkWtlZaPrOes68tC2lTHfqyn88kmdeVzm_sqB9c6KI/edit?usp=sharing"
sheet_name = "Respostas ao formulário 1"

try:
    df = get_google_sheet(spreadsheet_url, sheet_name)
    st.success("Dados carregados com sucesso!")

    if "Carimbo de data/hora" in df.columns:
        df["Data de preenchimento"] = pd.to_datetime(df["Carimbo de data/hora"], errors="coerce")
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

        hoje = datetime.today()
        mes_anterior = hoje - timedelta(days=30)
        mes_default = meses_traducao[mes_anterior.strftime("%B")]
        ano_default = mes_anterior.year

        st.subheader("\U0001F4C5 Filtrar por Mês e Ano")
        ordem_meses = list(meses_traducao.values())
        anos_disponiveis = sorted(df["Ano"].unique())
        meses_disponiveis = [m for m in ordem_meses if m in df["Mês"].unique()]

        ano_selecionado = st.selectbox("Ano", anos_disponiveis, index=anos_disponiveis.index(ano_default))
        mes_selecionado = st.selectbox("Mês", meses_disponiveis, index=meses_disponiveis.index(mes_default) if mes_default in meses_disponiveis else 0)

        df = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]

    colunas_graficos = df.columns[2:24].tolist()
    opcoes = ["Todas as Perguntas"] + colunas_graficos
    categoria_escolhida = st.selectbox("Selecione uma pergunta", opcoes)

    pdf = PDF()
    pdf.add_page()

    if categoria_escolhida != "Todas as Perguntas":
        df_counts = df[categoria_escolhida].value_counts().reset_index()
        df_counts.columns = ['Resposta', 'Quantidade']
        df_counts['Percentual (%)'] = (df_counts['Quantidade'] / df_counts['Quantidade'].sum() * 100).round(2)

        fig = px.bar(df_counts, x="Resposta", y="Quantidade", text="Percentual (%)",
                     title=f"Respostas de {categoria_escolhida}", color="Resposta",
                     color_discrete_map={r: get_color(r) for r in df_counts['Resposta']})
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig)

        st.subheader(f"\U0001F522 Quantidade e Percentual de Respostas para '{categoria_escolhida}'")
        st.write(df_counts)
        exportar_excel(df_counts)

    else:
        st.subheader("\U0001F4D1 Áreas Atendidas - Todas as Perguntas")
        respostas_esperadas = ["Excelente", "Bom", "Regular", "Ruim", "Não se Aplica"]
        dados_areas = []

        for idx, col in enumerate(colunas_graficos):
            total_respostas = df[col].notna().sum()
            linha = {"Área": nomes_areas.get(idx, col), "Qt Respostas": total_respostas}
            for resp in respostas_esperadas:
                qtd = (df[col] == resp).sum()
                perc = round((qtd / total_respostas) * 100, 2) if total_respostas > 0 else 0
                linha[resp] = qtd
                linha[f"% {resp}"] = perc
            dados_areas.append(linha)

            df_counts = df[col].value_counts().reset_index()
            df_counts.columns = ['Resposta', 'Quantidade']
            df_counts['Percentual (%)'] = (df_counts['Quantidade'] / df_counts['Quantidade'].sum() * 100).round(2)

            fig = px.bar(df_counts, x="Resposta", y="Quantidade", text="Percentual (%)",
                         title=f"Respostas de {col}", color="Resposta",
                         color_discrete_map={r: get_color(r) for r in df_counts['Resposta']})
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig)

        df_areas = pd.DataFrame(dados_areas)
        df_areas = df_areas.drop(columns=["Qt Respostas"])
        st.dataframe(df_areas)
        exportar_excel(df_areas, nome_arquivo="areas_atendidas.xlsx")

        # Adiciona planilha ao PDF
        pdf.chapter_title("Resumo de Áreas Atendidas")
        df_areas_pdf = df_areas.drop(columns=["Não se Aplica", "% Não se Aplica"])
        pdf.add_table(df_areas_pdf)

    if "Deixe sua Sugestão:" in df.columns:
        sugestoes = df["Deixe sua Sugestão:"].dropna().reset_index(drop=True)
        if not sugestoes.empty:
            st.subheader("\U0001F4AC Sugestões")
            st.dataframe(sugestoes.to_frame(name="Sugestões"))

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer = BytesIO(pdf_bytes)

    st.download_button(
        label="\U0001F4C4 Baixar PDF",
        data=buffer,
        file_name="relatorio_satisfacao.pdf",
        mime="application/pdf"
    )

except Exception as e:
    st.error(f"Erro ao processar: {e}")

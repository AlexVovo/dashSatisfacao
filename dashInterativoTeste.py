import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime, timedelta
import re
from fpdf import FPDF
import os
import unicodedata
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Feedback dos Pacientes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Adicionar imagem no corpo da página
try:
    st.image("logo.png", caption="Instituto do Câncer Infantil")
except:
    st.markdown("**Instituto do Câncer Infantil**")

# CSS customizado para melhorar o visual
st.markdown("""
    <style>
        .main-header {
            padding: 1rem 0;
            background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #3b82f6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
        }
        
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        .stSelectbox > div > div {
            background-color: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
        }
        
        .success-message {
            background: #dcfce7;
            color: #166534;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #22c55e;
        }
        
        .section-divider {
            margin: 2rem 0;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .download-section {
            background: #f8fafc;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

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
    buffer.seek(0)
    st.download_button(
        label="Baixar Excel",
        data=buffer.getvalue(),
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def get_color_palette():
    return {
        "Excelente": "#22c55e",  # Verde
        "Bom": "#3b82f6",        # Azul
        "Regular": "#f59e0b",    # Amarelo/Laranja
        "Ruim": "#ef4444",       # Vermelho
        "Não se Aplica": "#6b7280"  # Cinza
    }

def create_enhanced_chart(df_counts, title):
    colors = get_color_palette()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_counts['Resposta'],
        y=df_counts['Quantidade'],
        text=[f"{row['Quantidade']}<br>({row['Percentual (%)']}%)" for _, row in df_counts.iterrows()],
        textposition='outside',
        marker_color=[colors.get(resp, "#6b7280") for resp in df_counts['Resposta']],
        marker_line_color='white',
        marker_line_width=2,
        hovertemplate='<b>%{x}</b><br>Quantidade: %{y}<br>Percentual: %{customdata}%<extra></extra>',
        customdata=df_counts['Percentual (%)']
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': '#1e293b'}
        },
        xaxis_title="Avaliação",
        yaxis_title="Quantidade de Respostas",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12),
        showlegend=False,
        height=400,
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor='#e2e8f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f1f5f9')
    
    return fig

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

        def check_space(altura_necessaria):
            if self.get_y() + altura_necessaria > self.h - 30:
                self.add_page()

        # Cabeçalho
        check_space(row_height)
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], row_height, str(col)[:20], border=1)
        self.ln(row_height)

        # Conteúdo
        for _, row in df.iterrows():
            y_start = self.get_y()
            x_start = self.get_x()

            self.set_font("Arial", "B", 7)
            self.multi_cell(col_widths[0], row_height, str(row[0]), border=1)
            y_end = self.get_y()
            linha_altura = y_end - y_start

            if y_end > self.h - 30:
                self.add_page()
                for i, col in enumerate(df.columns):
                    self.cell(col_widths[i], row_height, str(col)[:20], border=1)
                self.ln(row_height)
                y_start = self.get_y()
                x_start = self.get_x()
                self.set_font("Arial", "B", 7)
                self.multi_cell(col_widths[0], row_height, str(row[0]), border=1)
                y_end = self.get_y()
                linha_altura = y_end - y_start

            self.set_xy(x_start + col_widths[0], y_start)
            self.set_font("Arial", "", 7)
            for i, item in enumerate(row[1:], start=1):
                texto = str(item)
                self.cell(col_widths[i], linha_altura, texto[:15], border=1)
            self.ln(linha_altura)

    def add_assinatura(self):
        if self.get_y() > self.h - 30:
            self.add_page()
        self.ln(30)
        self.set_font("Arial", "B", 10)
        self.cell(0, 10, "Mônica Gottardi", ln=True)
        self.set_font("Arial", "", 10)
        self.cell(0, 10, "Coord. Núcleo de Atenção ao Paciente", ln=True)

# Header principal
st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard - Feedback dos Pacientes</h1>
        <p>Sistema de Análise de Satisfação | Instituto de Cardiologia</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar para filtros
with st.sidebar:
    st.markdown("### 🎯 Filtros de Análise")
    
    # Informações da conexão
    with st.expander("ℹ️ Informações da Fonte"):
        st.info("📋 Conectado ao Google Sheets\n🔄 Dados atualizados automaticamente")

spreadsheet_url = "https://docs.google.com/spreadsheets/d/1UMkWtlZaPrOes68tC2lTHfqyn88kmdeVzm_sqB9c6KI/edit?usp=sharing"
sheet_name = "Respostas ao formulário 1"

try:
    # Loading spinner
    with st.spinner("🔄 Carregando dados..."):
        df = get_google_sheet(spreadsheet_url, sheet_name)
    
    # Mensagem de sucesso
    st.markdown('<div class="success-message">✅ Dados carregados com sucesso!</div>', unsafe_allow_html=True)
    
    # Verificar se os dados foram carregados
    if df.empty:
        st.error("❌ Nenhum dado encontrado na planilha.")
        st.stop()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Respostas", len(df))
    
    with col2:
        if "Carimbo de data/hora" in df.columns:
            st.metric("📅 Período Disponível", f"{df['Carimbo de data/hora'].min()[:10]} - {df['Carimbo de data/hora'].max()[:10]}")
        else:
            st.metric("📅 Período Disponível", "N/A")
    
    with col3:
        # Contagem mais robusta das áreas
        total_colunas = len(df.columns)
        colunas_controle = 2  # Timestamp e outras colunas de controle
        areas_analisadas = max(0, total_colunas - colunas_controle)
        st.metric("🏥 Áreas Analisadas", areas_analisadas)
    
    with col4:
        st.metric("🎯 Status", "Online", delta="Ativo")

    # Processamento de datas
    if "Carimbo de data/hora" in df.columns:
        df["Data de preenchimento"] = pd.to_datetime(df["Carimbo de data/hora"], errors="coerce")
        df = df.dropna(subset=["Data de preenchimento"])
        
        if df.empty:
            st.error("❌ Nenhuma data válida encontrada.")
            st.stop()
            
        df["Ano"] = df["Data de preenchimento"].dt.year.astype(int)
        df["Mês Inglês"] = df["Data de preenchimento"].dt.strftime("%B")

        meses_traducao = {
            "January": "Janeiro", "February": "Fevereiro", "March": "Março",
            "April": "Abril", "May": "Maio", "June": "Junho",
            "July": "Julho", "August": "Agosto", "September": "Setembro",
            "October": "Outubro", "November": "Novembro", "December": "Dezembro"
        }

        df["Mês"] = df["Mês Inglês"].map(meses_traducao)

        hoje = datetime.today()
        mes_anterior = hoje - timedelta(days=30)
        mes_default = meses_traducao[mes_anterior.strftime("%B")]
        ano_default = mes_anterior.year

        # Filtros na sidebar
        with st.sidebar:
            st.markdown("### 📅 Período de Análise")
            
            anos_disponiveis = sorted(df["Ano"].unique())
            if not anos_disponiveis:
                st.error("❌ Nenhum ano disponível nos dados.")
                st.stop()
                
            ano_selecionado = st.selectbox(
                "🗓️ Selecione o Ano",
                anos_disponiveis,
                index=anos_disponiveis.index(ano_default) if ano_default in anos_disponiveis else 0
            )

            df_ano = df[df["Ano"] == ano_selecionado]
            ordem_meses = list(meses_traducao.values())
            meses_disponiveis = [m for m in ordem_meses if m in df_ano["Mês"].unique()]
            
            if not meses_disponiveis:
                st.error(f"❌ Nenhum mês disponível para o ano {ano_selecionado}.")
                st.stop()
                
            mes_default_index = meses_disponiveis.index(mes_default) if mes_default in meses_disponiveis else 0

            mes_selecionado = st.selectbox(
                "📆 Selecione o Mês",
                meses_disponiveis,
                index=mes_default_index
            )

            st.markdown("### 🔍 Tipo de Análise")
            
            # Filtro final no DataFrame
            df_filtrado = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]
            
            if df_filtrado.empty:
                st.error(f"❌ Nenhum dado disponível para {mes_selecionado}/{ano_selecionado}.")
                st.stop()
            
            # Usar o dataframe filtrado
            df = df_filtrado
    else:
        st.warning("⚠️ Coluna 'Carimbo de data/hora' não encontrada. Usando todos os dados disponíveis.")

    # Identificação das colunas de perguntas (mais robusta)
    colunas_excluir = [
        "Carimbo de data/hora", 
        "Data de preenchimento", 
        "Ano", 
        "Mês Inglês", 
        "Mês",
        "Deixe sua Sugestão:"
    ]
    
    # Filtrar colunas que são realmente perguntas
    colunas_perguntas = [col for col in df.columns if col not in colunas_excluir]
    
    # Filtrar colunas que contêm "oficinas arte/vida" (case insensitive)
    colunas_perguntas_filtradas = [
        col for col in colunas_perguntas 
        if "oficinas arte/vida" not in col.lower()
    ]
    
    if not colunas_perguntas_filtradas:
        st.error("❌ Nenhuma pergunta válida encontrada nos dados.")
        st.stop()
    
    # Opções para o selectbox
    opcoes_selectbox = ["📊 Todas as Perguntas"] + colunas_perguntas_filtradas
    
    with st.sidebar:
        pergunta_selecionada = st.selectbox(
            "Selecione uma pergunta", 
            opcoes_selectbox,
            key="pergunta_selector"
        )
        
        # Debug info (opcional - pode ser removido)
        with st.expander("🔧 Debug Info"):
            st.write(f"Total de colunas: {len(df.columns)}")
            st.write(f"Perguntas disponíveis: {len(colunas_perguntas_filtradas)}")
            st.write(f"Seleção atual: {pergunta_selecionada}")

    # Mapeamento de nomes das áreas
    nomes_areas = {
        0: "Serviço Social", 1: "Nutrição", 2: "Psicopedagogia", 3: "Psicologia", 4: "Odontologia",
        5: "Fonoaudiologia", 6: "Fisioterapia", 7: "Psiquiatria", 8: "Farmácia", 9: "Enfermagem",
        10: "Educativas/Educação em grupo", 11: "Assistência Familiar", 12: "Copa", 13: "Recepção",
        14: "Ações Culturais e Festividades", 15: "Recreação", 16: "Atividades Interativas",
        18: "Núcleo de Apoio Jurídico", 19: "Limpeza do Local", 20: "Comunicação com as famílias", 21: "Terapia Ocupacional"
    }

    # Análise baseada na seleção
    if pergunta_selecionada == "📊 Todas as Perguntas":
        # Análise geral
        st.markdown("---")
        st.markdown("## 🏥 Análise Geral por Áreas")
        
        respostas_esperadas = ["Excelente", "Bom", "Regular", "Ruim", "Não se Aplica"]
        dados_areas = []

        # Progress bar para mostrar progresso
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, col in enumerate(colunas_perguntas_filtradas):
            progress_bar.progress((idx + 1) / len(colunas_perguntas_filtradas))
            status_text.text(f"Processando: {col}")
            
            # Verificar se a coluna existe no DataFrame
            if col not in df.columns:
                continue
                
            total_respostas = df[col].notna().sum()
            
            # Usar o nome da área se disponível, senão usar o nome da coluna
            # nome_area = nomes_areas.get(idx, col)
            # Verificar se a coluna contém "apoio jurídico" (case insensitive)
            if "apoio jurídico" in col.lower():
                    nome_area = "Núcleo de Apoio Jurídico"
            else:
                    nome_area = nomes_areas.get(idx, col)
            linha = {"Área": nome_area, "Qt Respostas": total_respostas}

            for resp in respostas_esperadas:
                col_normalizada = df[col].astype(str).str.strip().str.lower()
                resp_normalizado = resp.strip().lower()
                qtd = (col_normalizada == resp_normalizado).sum()
                perc = round((qtd / total_respostas) * 100, 2) if total_respostas > 0 else 0
                linha[resp] = qtd
                linha[f"% {resp}"] = perc
            
            dados_areas.append(linha)

            # Gráfico individual
            df_counts = df[col].value_counts().reset_index()
            df_counts.columns = ['Resposta', 'Quantidade']
            df_counts['Percentual (%)'] = (df_counts['Quantidade'] / df_counts['Quantidade'].sum() * 100).round(2)

            fig = create_enhanced_chart(df_counts, f"📊 {nome_area}")
            st.plotly_chart(fig, use_container_width=True)

        # Limpar progress bar
        progress_bar.empty()
        status_text.empty()

        # Seção de comentários
        if "Deixe sua Sugestão:" in df.columns:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("## 💬 Comentários e Sugestões dos Pacientes")

            sugestoes = (
                df["Deixe sua Sugestão:"]
                .dropna()
                .astype(str)
                .str.strip()
            )
            sugestoes = sugestoes[sugestoes != ""].reset_index(drop=True)

            if not sugestoes.empty:
                st.markdown(f"**📝 Total de comentários recebidos:** {len(sugestoes)}")
                st.dataframe(sugestoes.to_frame(name="💭 Sugestão"), use_container_width=True)
            else:
                st.info("📝 Nenhuma sugestão encontrada para este período.")

        # Resumo final
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("## 📊 Resumo Executivo")
        
        if dados_areas:
            df_areas = pd.DataFrame(dados_areas)

            # Calcular totais
            somas_respostas = df_areas[respostas_esperadas].sum(numeric_only=True)
            total_geral_respostas = somas_respostas.sum()

            if total_geral_respostas > 0:
                linha_totais = {
                    f"% {resp}": round((somas_respostas[resp] / total_geral_respostas) * 100, 2)
                    for resp in respostas_esperadas
                }
                linha_totais["Área"] = "TOTAL GERAL"
                for col in df_areas.columns:
                    if col not in linha_totais:
                        linha_totais[col] = ""

                df_areas = pd.concat([df_areas, pd.DataFrame([linha_totais])], ignore_index=True)

            # Formatação das porcentagens
            for coluna in df_areas.columns:
                if coluna.startswith('% '):
                    df_areas[coluna] = df_areas[coluna].apply(lambda x: f"{x}%" if isinstance(x, (int, float)) else x)

            # Exibir tabela com estilo
            st.dataframe(df_areas, use_container_width=True)

            # Seção de downloads
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("## 📥 Downloads")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="download-section">', unsafe_allow_html=True)
                st.markdown("### 📊 Planilha Excel")
                st.markdown("Baixe os dados completos em formato Excel")
                
                if 'mes_selecionado' in locals() and 'ano_selecionado' in locals():
                    mes_arquivo = (mes_selecionado.lower()
                                .replace("ç", "c").replace("ã", "a").replace("é", "e")
                                .replace("ô", "o").replace("í", "i"))
                    nome_excel = f"areas_atendidas_{mes_arquivo}_{ano_selecionado}.xlsx"
                else:
                    nome_excel = "areas_atendidas.xlsx"
                
                exportar_excel(df_areas, nome_arquivo=nome_excel)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="download-section">', unsafe_allow_html=True)
                st.markdown("### 📄 Relatório PDF")
                st.markdown("Baixe o relatório completo em PDF")
                
                if 'mes_selecionado' in locals() and 'ano_selecionado' in locals():
                    mes_arquivo = (mes_selecionado.lower()
                                .replace("ç", "c").replace("ã", "a").replace("é", "e")
                                .replace("ô", "o").replace("í", "i"))
                    nome_pdf = f"relatorio_{mes_arquivo}_{ano_selecionado}.pdf"
                    titulo_pdf = f"Resumo de Áreas Atendidas - {mes_selecionado}/{ano_selecionado}"
                else:
                    nome_pdf = "relatorio.pdf"
                    titulo_pdf = "Resumo de Áreas Atendidas"
                
                pdf = PDF(orientation='L')
                pdf.add_page()
                pdf.chapter_title(titulo_pdf)
                pdf.add_table(df_areas)
                pdf.add_assinatura()

                pdf_bytes = pdf.output(dest='S')
                buffer = BytesIO(pdf_bytes)

                st.download_button(
                    label="📄 Baixar Relatório PDF",
                    data=buffer,
                    file_name=nome_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Nenhum dado disponível para análise.")

    else:
        # Análise individual da pergunta selecionada
        st.markdown("---")
        st.markdown(f"## 📋 Análise Detalhada: {pergunta_selecionada}")
        
        # Verificar se a pergunta selecionada existe no DataFrame
        if pergunta_selecionada not in df.columns:
            st.error(f"❌ Pergunta '{pergunta_selecionada}' não encontrada nos dados.")
            st.stop()
        
        # Análise da pergunta específica
        df_counts = df[pergunta_selecionada].value_counts().reset_index()
        df_counts.columns = ['Resposta', 'Quantidade']
        
        if df_counts.empty:
            st.warning(f"⚠️ Nenhuma resposta encontrada para '{pergunta_selecionada}'.")
        else:
            df_counts['Percentual (%)'] = (df_counts['Quantidade'] / df_counts['Quantidade'].sum() * 100).round(2)

            # Gráfico melhorado
            fig = create_enhanced_chart(df_counts, f"Distribuição de Respostas - {pergunta_selecionada}")
            st.plotly_chart(fig, use_container_width=True)

            # Tabela de resultados
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📊 Resumo Quantitativo")
                st.dataframe(df_counts, use_container_width=True)
            
            with col2:
                st.markdown("### 📈 Indicadores")
                total_respostas = df_counts['Quantidade'].sum()
                positivas = df_counts[df_counts['Resposta'].isin(['Excelente', 'Bom'])]['Quantidade'].sum()
                percentual_positivo = (positivas / total_respostas * 100) if total_respostas > 0 else 0
                
                st.metric("Total de Respostas", total_respostas)
                st.metric("Avaliações Positivas", f"{positivas} ({percentual_positivo:.1f}%)")
                
                # Download
                st.markdown('<div class="download-section">', unsafe_allow_html=True)
                exportar_excel(df_counts)
                st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ Erro ao processar os dados: {e}")
    st.markdown("### 🔧 Possíveis soluções:")
    st.markdown("- Verifique a conexão com a internet")
    st.markdown("- Confirme se o arquivo `credenciais.json` está no diretório")
    st.markdown("- Valide se a URL do Google Sheets está correta")
    st.markdown("- Verifique se a estrutura da planilha está correta")
    
    # Debug adicional
    with st.expander("🔧 Informações de Debug"):
        st.write(f"Erro detalhado: {str(e)}")
        if 'df' in locals():
            st.write(f"Colunas disponíveis: {list(df.columns)}")
            st.write(f"Shape do DataFrame: {df.shape}")
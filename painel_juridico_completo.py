
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="Painel de Perfil de Magistrado com IA e PDF", layout="wide")

st.title("📊 Painel de Perfil de Magistrado com IA e PDF")

# Função para gerar recomendação automatizada simples
def gerar_recomendacao(df):
    if (df['Tese da Defesa'] == 'Inexistência de falha').mean() > 0.3:
        return "Focar na ausência de falha comprovada e atendimento adequado."
    elif (df['Tese da Defesa'] == 'Culpa do consumidor').mean() > 0.2:
        return "Explorar a tese de culpa exclusiva do consumidor com robustez documental."
    else:
        return "Adotar abordagem documental e avaliar possibilidade de acordo em casos de dano moral reiterado."

# Função para gerar relatório em PDF
def gerar_pdf(juiz, resumo, recomendacao, tese_df, fundamentacoes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, f"Perfil do Juiz: {juiz}", ln=True, align="C")
    pdf.ln(10)
    for item in resumo:
        pdf.cell(200, 10, txt=item, ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Recomendação Estratégica:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, recomendacao)

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Teses da Defesa Mais Utilizadas:", ln=True)
    pdf.set_font("Arial", size=12)
    for index, row in tese_df.iterrows():
        pdf.cell(200, 10, f"{row['Tese da Defesa']}: {row['Frequência']}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Trechos de Fundamentações:", ln=True)
    pdf.set_font("Arial", size=12)
    for i, texto in enumerate(fundamentacoes):
        pdf.multi_cell(0, 10, f"{i+1}. {texto[:300]}...")
        pdf.ln(2)

    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    return tmp_pdf.name

# Upload do arquivo Excel
uploaded_file = st.file_uploader("📎 Envie a planilha de decisões (.csv)", type=".csv")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['Juiz'] = df['Juiz'].astype(str)
    juizes = df['Juiz'].unique()
    juiz_selecionado = st.selectbox("Selecione um juiz para análise:", sorted(juizes))

    df_juiz = df[df['Juiz'] == juiz_selecionado]

    st.subheader(f"📌 Resumo de decisões do juiz {juiz_selecionado}")
    col1, col2, col3 = st.columns(3)
    total = len(df_juiz)
    proced = round((df_juiz['Resultado'] == 'Procedente').mean() * 100, 1)
    improc = round((df_juiz['Resultado'] == 'Improcedente').mean() * 100, 1)
    col1.metric("Total de decisões", total)
    col2.metric("Procedentes (%)", proced)
    col3.metric("Improcedentes (%)", improc)

    st.markdown("---")
    st.subheader("📊 Gráficos Interativos")

    resultado_counts = df_juiz['Resultado'].value_counts().reset_index()
    resultado_counts.columns = ['Resultado', 'Contagem']
    fig_pizza = px.pie(resultado_counts, values='Contagem', names='Resultado', title='Distribuição de Resultados')
    st.plotly_chart(fig_pizza, use_container_width=True)

    tese_counts = df_juiz['Tese da Defesa'].value_counts().reset_index()
    tese_counts.columns = ['Tese da Defesa', 'Frequência']
    fig_barras = px.bar(tese_counts, x='Tese da Defesa', y='Frequência', title='Teses da Defesa Mais Utilizadas')
    st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")
    st.subheader("📚 Teses da Defesa Mais Utilizadas (Tabela)")
    st.dataframe(tese_counts)

    st.markdown("---")
    st.subheader("📝 Fundamentações (trechos extraídos)")
    fundamentacoes = df_juiz['Fundamentação da Decisão'].dropna().tolist()[:3]
    for i, texto in enumerate(fundamentacoes):
        st.markdown(f"**{i+1}.** _{texto[:300]}..._")

    st.markdown("---")
    st.subheader("💡 Recomendação Estratégica da IA")
    recomendacao = gerar_recomendacao(df_juiz)
    st.info(recomendacao)

    if st.button("📄 Gerar Relatório em PDF"):
        resumo = [
            f"Total de decisões: {total}",
            f"Procedentes (%): {proced}",
            f"Improcedentes (%): {improc}"
        ]
        caminho_pdf = gerar_pdf(juiz_selecionado, resumo, recomendacao, tese_counts, fundamentacoes)
        with open(caminho_pdf, "rb") as f:
            st.download_button("📥 Baixar Relatório PDF", f, file_name=f"perfil_{juiz_selecionado.replace(' ', '_')}.pdf")
        os.remove(caminho_pdf)

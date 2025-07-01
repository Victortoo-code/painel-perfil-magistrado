
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import tempfile
import os
from PIL import Image

st.set_page_config(page_title="Painel de Perfil de Magistrado", layout="wide")

st.title("📊 Painel de Perfil de Magistrado com Exportação e Comparação")

# Função para recomendação básica
def gerar_recomendacao(df):
    if (df['Tese da Defesa'] == 'Inexistência de falha').mean() > 0.3:
        return "Focar na ausência de falha comprovada e atendimento adequado."
    elif (df['Tese da Defesa'] == 'Culpa do consumidor').mean() > 0.2:
        return "Explorar a tese de culpa exclusiva do consumidor com robustez documental."
    else:
        return "Adotar abordagem documental e avaliar possibilidade de acordo em casos de dano moral reiterado."

# Geração de PDF com resumo
def gerar_pdf_completo(titulo, resumo, recomendacao, tese_df, fundamentacoes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, titulo, ln=True, align="C")
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
    pdf.cell(200, 10, "Teses Mais Utilizadas:", ln=True)
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

# Upload
uploaded_file = st.file_uploader("📎 Envie a planilha de decisões (.csv)", type=".csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Juiz'] = df['Juiz'].astype(str)
    juizes = sorted(df['Juiz'].unique())
    modo = st.radio("🔍 Modo de análise:", ["Análise Individual", "Comparar Juízes"])

    if modo == "Análise Individual":
        juiz = st.selectbox("Selecione um juiz:", juizes)
        df_juiz = df[df['Juiz'] == juiz]

        st.subheader(f"📌 Resumo do juiz {juiz}")
        col1, col2, col3 = st.columns(3)
        total = len(df_juiz)
        proced = round((df_juiz['Resultado'] == 'Procedente').mean() * 100, 1)
        improc = round((df_juiz['Resultado'] == 'Improcedente').mean() * 100, 1)
        col1.metric("Total de decisões", total)
        col2.metric("Procedentes (%)", proced)
        col3.metric("Improcedentes (%)", improc)

        st.subheader("📊 Gráficos")
        resultado_counts = df_juiz['Resultado'].value_counts().reset_index()
        resultado_counts.columns = ['Resultado', 'Contagem']
        fig1 = px.pie(resultado_counts, values='Contagem', names='Resultado', title='Distribuição de Resultados')
        st.plotly_chart(fig1, use_container_width=True)

        tese_counts = df_juiz['Tese da Defesa'].value_counts().reset_index()
        tese_counts.columns = ['Tese da Defesa', 'Frequência']
        fig2 = px.bar(tese_counts, x='Tese da Defesa', y='Frequência', title='Teses da Defesa Mais Utilizadas')
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📚 Teses (Tabela)")
        st.dataframe(tese_counts)

        st.subheader("📝 Fundamentações")
        fundamentos = df_juiz['Fundamentação da Decisão'].dropna().tolist()[:3]
        for i, f in enumerate(fundamentos):
            st.markdown(f"**{i+1}.** _{f[:300]}..._")

        st.subheader("💡 Recomendação da IA")
        recomendacao = gerar_recomendacao(df_juiz)
        st.info(recomendacao)

        if st.button("📄 Gerar PDF"):
            resumo = [
                f"Total de decisões: {total}",
                f"Procedentes (%): {proced}",
                f"Improcedentes (%): {improc}"
            ]
            caminho_pdf = gerar_pdf_completo(f"Juiz: {juiz}", resumo, recomendacao, tese_counts, fundamentos)
            with open(caminho_pdf, "rb") as f:
                st.download_button("📥 Baixar Relatório PDF", f, file_name=f"relatorio_{juiz}.pdf")
            os.remove(caminho_pdf)

    else:
        juiz1 = st.selectbox("Juiz 1:", juizes, key="juiz1")
        juizes2 = [j for j in juizes if j != juiz1]
        juiz2 = st.selectbox("Juiz 2:", juizes2, key="juiz2")

        df1 = df[df['Juiz'] == juiz1]
        df2 = df[df['Juiz'] == juiz2]

        col1, col2 = st.columns(2)
        col1.subheader(f"📌 {juiz1}")
        col1.metric("Total de decisões", len(df1))
        col1.metric("Procedentes (%)", round((df1['Resultado'] == 'Procedente').mean() * 100, 1))
        col1.metric("Improcedentes (%)", round((df1['Resultado'] == 'Improcedente').mean() * 100, 1))

        col2.subheader(f"📌 {juiz2}")
        col2.metric("Total de decisões", len(df2))
        col2.metric("Procedentes (%)", round((df2['Resultado'] == 'Procedente').mean() * 100, 1))
        col2.metric("Improcedentes (%)", round((df2['Resultado'] == 'Improcedente').mean() * 100, 1))

        st.subheader("📊 Teses mais usadas por juiz")
        col3, col4 = st.columns(2)
        t1 = df1['Tese da Defesa'].value_counts().reset_index()
        t1.columns = ['Tese da Defesa', 'Frequência']
        fig_t1 = px.bar(t1, x='Tese da Defesa', y='Frequência', title=f"{juiz1}")
        col3.plotly_chart(fig_t1, use_container_width=True)

        t2 = df2['Tese da Defesa'].value_counts().reset_index()
        t2.columns = ['Tese da Defesa', 'Frequência']
        fig_t2 = px.bar(t2, x='Tese da Defesa', y='Frequência', title=f"{juiz2}")
        col4.plotly_chart(fig_t2, use_container_width=True)

        st.subheader("💡 Recomendações")
        col5, col6 = st.columns(2)
        col5.markdown(f"**{juiz1}**: {gerar_recomendacao(df1)}")
        col6.markdown(f"**{juiz2}**: {gerar_recomendacao(df2)}")


import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import tempfile
import os
import openai

st.set_page_config(page_title="Painel de Perfil de Magistrado", layout="wide")
st.title("📊 Painel de Perfil de Magistrado Unificado com IA")

from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def gerar_recomendacao_ia(df_juiz):
    juiz_nome = df_juiz['Juiz'].iloc[0]
    total_dec = len(df_juiz)
    mais_usada = df_juiz['Tese da Defesa'].value_counts().idxmax()
    porcent_procedente = round((df_juiz['Resultado'] == 'Procedente').mean() * 100, 1)
    fundamentos = df_juiz['Fundamentação da Decisão'].dropna().tolist()[:2]

    prompt = f"""
    Você é um advogado especialista em contencioso de massa e direito do consumidor.
    Com base nos dados abaixo, elabore uma tese de defesa recomendada para este magistrado.

    Nome do juiz: {juiz_nome}
    Total de decisões: {total_dec}
    % de procedência: {porcent_procedente}%
    Tese da defesa mais utilizada: {mais_usada}
    Principais fundamentos extraídos:
    1. {fundamentos[0] if len(fundamentos) > 0 else 'n/a'}
    2. {fundamentos[1] if len(fundamentos) > 1 else 'n/a'}

    Gere uma recomendação objetiva e estratégica com base nesse perfil.
    """

    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=300
    )
    return resposta.choices[0].message.content.strip()


def gerar_pdf(titulo, resumo, recomendacao, tese_df, fundamentacoes):
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

uploaded_file = st.file_uploader("📎 Envie a planilha de decisões (.xlsx)", type=".xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['Juiz'] = df['Juiz'].astype(str)
    juizes = sorted(df['Juiz'].unique())
    aba = st.radio("Escolha a visualização:", ["👤 Análise Individual", "⚖️ Comparar Juízes"])

    if aba == "👤 Análise Individual":
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

        st.subheader("💡 Recomendação da IA (via ChatGPT)")
        with st.spinner("Gerando sugestão estratégica com base no perfil do juiz..."):
            recomendacao = gerar_recomendacao_ia(df_juiz)
        st.success("Recomendação gerada com sucesso!")
        st.markdown(recomendacao)

        if st.button("📄 Gerar PDF"):
            resumo = [
                f"Total de decisões: {total}",
                f"Procedentes (%): {proced}",
                f"Improcedentes (%): {improc}"
            ]
            caminho_pdf = gerar_pdf(f"Juiz: {juiz}", resumo, recomendacao, tese_counts, fundamentos)
            with open(caminho_pdf, "rb") as f:
                st.download_button("📥 Baixar Relatório PDF", f, file_name=f"relatorio_{juiz}.pdf")
            os.remove(caminho_pdf)
            
            import openai
st.write(f"Versão do openai: {openai.__version__}")




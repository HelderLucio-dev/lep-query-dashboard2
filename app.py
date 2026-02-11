import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="LEP Query Dashboard", layout="wide")

st.title("📊 LEP Study – Query Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls","xlsm"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    # Limpar espaços nos nomes das colunas
    df.columns = df.columns.str.strip()

    st.subheader("📋 Colunas encontradas no arquivo:")
    st.write(list(df.columns))

    # Usuário escolhe colunas
    ID_COL = st.selectbox("Selecione a coluna de ID:", df.columns)
    STATUS_COL = st.selectbox("Selecione a coluna de Status:", df.columns)
    DATE_COL = st.selectbox("Selecione a coluna de Data de Criação:", df.columns)

    if ID_COL and STATUS_COL and DATE_COL:

        try:
            df[DATE_COL] = pd.to_datetime(df[DATE_COL])
        except:
            st.error("⚠ Não foi possível converter a coluna de data. Verifique o formato.")
            st.stop()

        today = datetime.today()
        df["Aging"] = (today - df[DATE_COL]).dt.days

        # KPIs
        total_queries = len(df)
        open_queries = len(df[df[STATUS_COL].str.lower() == "open"])
        avg_aging = round(df["Aging"].mean(),1)

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Queries", total_queries)
        col2.metric("Open Queries", open_queries)
        col3.metric("Average Aging", avg_aging)

        # Aging Bucket
        def aging_bucket(x):
            if x <=7: return "0-7"
            elif x <=14: return "8-14"
            elif x <=30: return "15-30"
            else: return ">30"

        df["Aging Bucket"] = df["Aging"].apply(aging_bucket)

        fig = px.bar(
            df["Aging Bucket"].value_counts().reset_index(),
            x="index",
            y="Aging Bucket",
            labels={"index":"Faixa Aging","Aging Bucket":"Quantidade"},
            title="Distribuição de Aging"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Ranking por ID
        ranking = df.groupby(ID_COL).agg(
            total_queries=(ID_COL,"count"),
            open_queries=(STATUS_COL,lambda x:(x.str.lower()=="open").sum()),
            avg_aging=("Aging","mean")
        ).reset_index()

        ranking["Risk Score"] = ranking["open_queries"] + (ranking["avg_aging"]/10)

        ranking = ranking.sort_values("Risk Score",ascending=False)

        st.subheader("🏆 Ranking de Risco por ID")
        st.dataframe(ranking)

else:
    st.info("⬆ Faça upload do arquivo Excel para começar.")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="LEP Query Dashboard", layout="wide")

st.title("LEP Study - Query Monitoring Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    ID_COL = "ID"
    STATUS_COL = "Status"
    DATE_COL = "Created Date"

    today = datetime.today()
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df["Aging"] = (today - df[DATE_COL]).dt.days

    total = len(df)
    open_q = len(df[df[STATUS_COL]=="Open"])
    percent = round((open_q/total)*100,1)
    avg_aging = round(df["Aging"].mean(),1)

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total Queries", total)
    col2.metric("Open Queries", open_q)
    col3.metric("% Open", percent)
    col4.metric("Avg Aging", avg_aging)

    st.markdown("---")

    # Aging Bucket
    def aging_bucket(x):
        if x <=7: return "0-7"
        elif x <=14: return "8-14"
        elif x <=30: return "15-30"
        else: return ">30"

    df["Aging Bucket"] = df["Aging"].apply(aging_bucket)

    fig1 = px.bar(df["Aging Bucket"].value_counts(),
                  title="Distribuição de Aging")

    st.plotly_chart(fig1,use_container_width=True)

    # Ranking
    ranking = df.groupby(ID_COL).agg(
        total_queries=(ID_COL,"count"),
        open_queries=(STATUS_COL,lambda x:(x=="Open").sum()),
        avg_aging=("Aging","mean")
    ).reset_index()

    ranking["Risk Score"] = ranking["open_queries"] + (ranking["avg_aging"]/10)
    ranking = ranking.sort_values("Risk Score",ascending=False)

    st.markdown("## Ranking de Participantes Críticos")
    st.dataframe(ranking)

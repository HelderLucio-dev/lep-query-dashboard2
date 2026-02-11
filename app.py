import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="LEP Study Dashboard", layout="wide")

st.title("📊 LEP Study – Queries & Missing Pages Dashboard")

# Upload dos dois arquivos
queries_file = st.file_uploader("Upload QUERIES file (Book2.xlsx)", type=["xlsx"])
missing_file = st.file_uploader("Upload MISSING PAGES file (.xlsm)", type=["xlsm","xlsx"])

if queries_file and missing_file:

    # ==========================
    # LOAD DATA
    # ==========================
    queries = pd.read_excel(queries_file)
    missing = pd.read_excel(missing_file)

    # Limpeza básica
    queries.columns = queries.columns.str.strip()
    missing.columns = missing.columns.str.strip()

    # ==========================
    # QUERIES PROCESSING
    # ==========================
    queries["DaysNotYetClosed"] = pd.to_numeric(queries["DaysNotYetClosed"], errors="coerce")

    def aging_bucket(x):
        if x <=7: return "0-7"
        elif x <=14: return "8-14"
        elif x <=30: return "15-30"
        else: return ">30"

    queries["Aging Bucket"] = queries["DaysNotYetClosed"].apply(aging_bucket)

    # ==========================
    # KPIs
    # ==========================
    total_queries = len(queries)
    open_queries = len(queries[queries["QueryStatus"].str.contains("Open", case=False)])
    avg_aging = round(queries["DaysNotYetClosed"].mean(),1)

    total_missing = len(missing)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Queries", total_queries)
    col2.metric("Open Queries", open_queries)
    col3.metric("Average Aging", avg_aging)
    col4.metric("Total Missing Pages", total_missing)

    st.divider()

    # ==========================
    # AGING DISTRIBUTION
    # ==========================
    fig_aging = px.bar(
        queries["Aging Bucket"].value_counts().reset_index(),
        x="index",
        y="Aging Bucket",
        labels={"index":"Aging Range","Aging Bucket":"Count"},
        title="Query Aging Distribution"
    )

    st.plotly_chart(fig_aging, use_container_width=True)

    # ==========================
    # RANKING BY SUBJECT
    # ==========================
    ranking_queries = queries.groupby("Subjects").agg(
        total_queries=("Subjects","count"),
        open_queries=("QueryStatus",lambda x:(x.str.contains("Open",case=False)).sum()),
        avg_aging=("DaysNotYetClosed","mean")
    ).reset_index()

    ranking_missing = missing.groupby("Subjects").size().reset_index(name="missing_pages")

    # Merge
    ranking = ranking_queries.merge(ranking_missing, on="Subjects", how="outer").fillna(0)

    ranking["Risk Score"] = (
        ranking["open_queries"]*2 +
        ranking["avg_aging"]/10 +
        ranking["missing_pages"]
    )

    ranking = ranking.sort_values("Risk Score", ascending=False)

    st.subheader("🚨 Risk Ranking by Subject")
    st.dataframe(ranking)

    # ==========================
    # FILTER SECTION
    # ==========================
    st.divider()
    st.subheader("🔎 Detailed Query View")

    visit_filter = st.selectbox("Filter by Visit", ["All"] + sorted(queries["Visits"].unique().tolist()))
    status_filter = st.selectbox("Filter by Status", ["All"] + sorted(queries["QueryStatus"].unique().tolist()))

    filtered = queries.copy()

    if visit_filter != "All":
        filtered = filtered[filtered["Visits"] == visit_filter]

    if status_filter != "All":
        filtered = filtered[filtered["QueryStatus"] == status_filter]

    st.dataframe(filtered)

    # ==========================
    # MISSING PAGES SUMMARY
    # ==========================
    st.divider()
    st.subheader("📂 Missing Pages by Folder")

    missing_summary = missing.groupby("Folders").size().reset_index(name="Count")

    fig_missing = px.bar(
        missing_summary,
        x="Folders",
        y="Count",
        title="Missing Pages by Folder"
    )

    st.plotly_chart(fig_missing, use_container_width=True)

else:
    st.info("Upload both files to start analysis.")

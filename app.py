import duckdb
import streamlit as st

st.set_page_config(page_title="Data Job Market Tracker", layout="wide")
st.title("Data Job Market Skills Tracker")


@st.cache_data(ttl=600)
def load(query):
    con = duckdb.connect("jobs.duckdb", read_only=True)
    df = con.execute(query).df()
    con.close()
    return df


weekly = load("SELECT * FROM main.skill_demand_weekly")
jobs = load("SELECT * FROM main.int_jobs_deduped")

roles = sorted(weekly["role_family"].unique())
role = st.selectbox("Role", roles)
w = weekly[weekly["role_family"] == role]
role_jobs = jobs[jobs["role_family"] == role]

c1, c2 = st.columns(2)
c1.metric("Postings tracked", f"{len(role_jobs):,}")
c2.metric("Weeks of data", w["week"].nunique())

st.subheader("Most requested skills")
top = w.groupby("skill")["postings"].sum().sort_values(ascending=False)
st.bar_chart(top.head(15))

st.subheader("Skill trends (% of postings)")
picks = st.multiselect("Skills", top.index.tolist(), default=top.index[:5].tolist())
trend = w[w["skill"].isin(picks)].pivot_table(
    index="week", columns="skill", values="pct_of_postings"
)
st.line_chart(trend)

st.subheader("Latest postings")
st.dataframe(
    role_jobs.sort_values("posted_date", ascending=False)[
        ["posted_date", "title", "company", "location", "redirect_url"]
    ].head(25)
)
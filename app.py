import pandas as pd
import streamlit as st

st.set_page_config(page_title="Govt Service Efficiency", layout="wide")
st.title("Measuring Government Service Efficiency")


@st.cache_data
def load_data():
    return pd.read_csv("data/sample_data.csv")


def show(value):
    return "Not available" if pd.isna(value) else f"{value:g}"


df = load_data()

st.sidebar.header("Choose what to compare")
state = st.sidebar.selectbox("State", sorted(df["state"].unique()))

in_state = df[df["state"] == state]
city = st.sidebar.selectbox("City", sorted(in_state["city"].unique()))

in_city = in_state[in_state["city"] == city]
department = st.sidebar.selectbox("Department", sorted(in_city["sector"].unique()))

subset = in_city[in_city["sector"] == department]

st.subheader(f"{department} in {city}, {state}")

table = subset[["facility", "wait", "processing", "cost", "complaints", "coverage", "satisfaction"]].copy()
table.columns = ["Facility", "Wait (min)", "Processing (min)", "Cost (₹)", "Complaints", "Coverage (%)", "Satisfaction (1-5)"]
for col in table.columns[1:]:
    table[col] = table[col].map(show)

st.dataframe(table, width="stretch", hide_index=True)
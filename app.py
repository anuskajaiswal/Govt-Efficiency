import pandas as pd
import streamlit as st

st.set_page_config(page_title="Govt Service Efficiency", layout="wide")
st.title("Measuring Government Service Efficiency")

DATA_FILE = "data/bengaluru_healthcare.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)


def number(value):
    return f"{value:g}"


def single(value):
    return "Not available" if pd.isna(value) else number(value)


def span(low, high):
    values = [v for v in (low, high) if not pd.isna(v)]
    if not values:
        return "Not available"
    if len(values) == 1 or values[0] == values[1]:
        return number(values[0])
    return f"{number(values[0])}–{number(values[1])}"


df = load_data()

st.sidebar.header("Choose what to compare")
state = st.sidebar.selectbox("State", sorted(df["state"].unique()))

in_state = df[df["state"] == state]
city = st.sidebar.selectbox("City", sorted(in_state["city"].unique()))

in_city = in_state[in_state["city"] == city]
department = st.sidebar.selectbox("Department", sorted(in_city["sector"].unique()))

subset = in_city[in_city["sector"] == department].reset_index(drop=True)

st.subheader(f"{department} in {city}, {state}")

st.warning(
    "These figures are estimates, not measurements. Wait, processing and satisfaction "
    "come from public review averages, fees from official OPD rates, and coverage is "
    "given as a range that is not verified per facility. Anything missing is shown as "
    "Not available and is never guessed."
)

table = pd.DataFrame({
    "Facility": subset["facility"],
    "Wait (min)": [span(a, b) for a, b in zip(subset["wait_min"], subset["wait_max"])],
    "Processing (min)": [span(a, b) for a, b in zip(subset["processing_min"], subset["processing_max"])],
    "Cost (₹)": subset["cost"].map(single),
    "Complaints": subset["complaints"].map(single),
    "Coverage (%)": [span(a, b) for a, b in zip(subset["coverage_min"], subset["coverage_max"])],
    "Satisfaction (1-5)": subset["satisfaction"].map(single),
    "Notes": subset["notes"].fillna(""),
})

st.dataframe(table, width="stretch", hide_index=True)
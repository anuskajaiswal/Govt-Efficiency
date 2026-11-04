import pandas as pd
import streamlit as st

from src.scoring import INDICATORS, composite_score

st.set_page_config(page_title="Govt Service Efficiency", layout="wide")
st.title("Measuring Government Service Efficiency")

DATA_FILE = "data/facilities.csv"
LOCATIONS_FILE = "data/locations.csv"
DEPARTMENTS = ["Hospitals", "Public Transport", "Water Supply", "RTO and Grievance"]


@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)


@st.cache_data
def load_locations():
    return pd.read_csv(LOCATIONS_FILE)


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
locations = load_locations()

st.sidebar.header("Choose what to compare")
states = sorted(locations["state"].unique())
state = st.sidebar.selectbox(
    "State", states, index=states.index("Karnataka") if "Karnataka" in states else 0
)

cities = sorted(locations[locations["state"] == state]["city"].dropna().unique())
if not cities:
    st.subheader(state)
    st.info("No cities have been added for this state yet.")
    st.stop()

city = st.sidebar.selectbox(
    "City / District",
    cities,
    index=cities.index("Bengaluru Urban") if "Bengaluru Urban" in cities else 0,
)
department = st.sidebar.selectbox("Department", DEPARTMENTS)

subset = df[
    (df["state"] == state) & (df["city"] == city) & (df["sector"] == department)
    ].reset_index(drop=True)

st.subheader(f"{department} in {city}, {state}")

if subset.empty:
    st.info(f"No {department} facilities have been added for {city} yet.")
    st.stop()

st.sidebar.header("Indicator weights")
st.sidebar.caption("Higher means it counts more. Weights are rescaled to add up to 1.")
raw_weights = {name: st.sidebar.slider(name.capitalize(), 0, 10, 5) for name in INDICATORS}
if sum(raw_weights.values()) == 0:
    st.sidebar.error("Set at least one weight above 0.")
    st.stop()
weights = {name: value / sum(raw_weights.values()) for name, value in raw_weights.items()}

if department == "Hospitals":
    st.warning(
        "These figures are estimates, not measurements. Wait, processing and satisfaction "
        "come from public review averages, fees from official OPD rates, and coverage is "
        "given as a range that is not verified per facility. Anything missing is shown as "
        "Not available and is never guessed."
    )

scaled, score, rank, used = composite_score(subset, weights)

table = pd.DataFrame({
    "Rank": rank.map(lambda v: "Not ranked" if pd.isna(v) else str(int(v))),
    "Facility": subset["facility"],
    "Score (0-100)": score.map(lambda v: "Not available" if pd.isna(v) else f"{v:.1f}"),
    "Wait (min)": [span(a, b) for a, b in zip(subset["wait_min"], subset["wait_max"])],
    "Processing (min)": [span(a, b) for a, b in zip(subset["processing_min"], subset["processing_max"])],
    "Cost (₹)": subset["cost"].map(single),
    "Complaints": subset["complaints"].map(single),
    "Coverage (%)": [span(a, b) for a, b in zip(subset["coverage_min"], subset["coverage_max"])],
    "Satisfaction (1-5)": subset["satisfaction"].map(single),
    "Notes": subset["notes"].fillna(""),
})
table = table.loc[rank.fillna(999).sort_values(kind="stable").index]

st.dataframe(table, width="stretch", hide_index=True)

dropped = [name for name in INDICATORS if name not in used]
if dropped:
    st.caption("Not used in the score (no usable data): " + ", ".join(dropped) + ".")
st.caption(
    "Scores are relative to the facilities shown here: 100 means best in this group, "
    "0 means worst. Ranges are scored at their midpoint."
)

ranked = pd.DataFrame({"Facility": subset["facility"], "Score": score}).dropna()
if not ranked.empty:
    st.bar_chart(ranked, x="Facility", y="Score")
"""Interactive, local-first motorsport BI dashboard."""
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DB = ROOT / "data" / "motorsport_bi.sqlite"

st.set_page_config(page_title="Motorsport BI | Race intelligence", page_icon="🏁", layout="wide")
st.markdown("""<style>
  .block-container {max-width: 1350px; padding-top: 1.8rem}
  h1,h2,h3 {letter-spacing: -.03em}
  [data-testid="stMetric"] {background:#151b24; border:1px solid #2d3949; padding:16px; border-radius:12px}
  [data-testid="stMetricLabel"] {color:#b9c4d0}
</style>""", unsafe_allow_html=True)

st.title("🏁 Motorsport race intelligence")
st.caption("A portfolio case study using F1DB race results, 2015–2025 · Source: F1DB CC BY 4.0")
if not DB.exists():
    st.error("Data mart missing. Run `python src/build.py` first.")
    st.stop()


@st.cache_data
def load() -> pd.DataFrame:
    with sqlite3.connect(DB) as conn:
        return pd.read_sql_query("SELECT * FROM v_race_performance", conn, parse_dates=["race_date"])


df = load()
seasons = sorted(df.season.unique().tolist())
with st.sidebar:
    st.header("Explore")
    year_range = st.slider("Seasons", min(seasons), max(seasons), (min(seasons), max(seasons)))
    venue = st.selectbox("Circuit", ["All circuits", "Silverstone"] +
                         sorted(x for x in df.circuit_name.unique() if x != "Silverstone"))
    teams = st.multiselect("Constructors", sorted(df.constructor_name.unique()))
    st.divider()
    st.caption("Grain: one row per driver per completed Grand Prix race. Sprint and qualifying results are excluded.")

view = df[df.season.between(*year_range)].copy()
if venue != "All circuits":
    view = view[view.circuit_name == venue]
if teams:
    view = view[view.constructor_name.isin(teams)]
if view.empty:
    st.warning("No results match these filters.")
    st.stop()

race_count = view[["season", "round"]].drop_duplicates().shape[0]
metrics = st.columns(5)
for col, label, value in zip(metrics,
    ["Grand Prix races", "Driver results", "Points", "Podiums", "Retirement rate"],
    [f"{race_count:,}", f"{len(view):,}", f"{view.points.sum():,.0f}",
     f"{int(view.podium.sum()):,}", f"{view.retired.mean():.1%}"]):
    col.metric(label, value)

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Constructor performance")
    team_summary = (view.groupby("constructor_name", as_index=False)
                    .agg(points=("points", "sum"), wins=("win", "sum"), podiums=("podium", "sum"),
                         starts=("driver_id", "count"), retirements=("retired", "sum"))
                    .sort_values("points", ascending=False))
    st.bar_chart(team_summary.head(10).set_index("constructor_name")["points"], color="#e52e39")
    st.dataframe(team_summary, hide_index=True, width="stretch")
with right:
    st.subheader("Performance by season")
    season_summary = view.groupby("season", as_index=False).agg(
        points=("points", "sum"), podiums=("podium", "sum"),
        retirements=("retired", "sum"), results=("driver_id", "count"))
    season_summary["retirement_rate"] = season_summary.retirements / season_summary.results
    st.line_chart(season_summary.set_index("season")["retirement_rate"], color="#e52e39")
    st.caption("Retirement rate = results with a recorded retirement reason ÷ driver results. The source may classify some non-finishers differently.")
    st.subheader("Starting grid vs finish")
    valid = view.dropna(subset=["grid_position", "finish_position"])
    st.scatter_chart(valid, x="grid_position", y="finish_position", color="constructor_name",
                     size="points", width="stretch")

st.subheader("Race detail")
race_options = (view[["race_date", "race_name", "season", "round"]].drop_duplicates()
                .sort_values("race_date", ascending=False))
race_labels = [f"{r.season} · {r.race_name} ({r.race_date.date()})" for r in race_options.itertuples()]
race_choice = st.selectbox("Choose a race", range(len(race_labels)), format_func=lambda i: race_labels[i])
selected = race_options.iloc[race_choice]
detail = view[(view.season == selected.season) & (view.round == selected["round"])].copy()
st.dataframe(detail[["finish_position", "grid_position", "driver_name", "constructor_name", "points",
                     "positions_gained", "pit_stops", "retirement_reason"]]
             .sort_values("finish_position", na_position="last"), hide_index=True, width="stretch")
st.caption("Points use official recorded race points. Cross-era point totals are not comparable without normalisation. No commercial or customer data is included.")


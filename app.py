"""Yalnız ekran (Streamlit). Data db.py-dan, hesablamalar logic.py-dan gəlir."""

import streamlit as st

from data_loader import OUTPUT_PATH, load_csv
from db import get_asteroids, init_db, save_asteroids
from logic import daily_counts, dashboard_stats, filter_hazardous

st.set_page_config(page_title="Asteroidlər", page_icon="☄️", layout="wide")
st.title("☄️ Yerə yaxın asteroidlər")

init_db()
# Serverdə (Streamlit Cloud) asteroid.db olmur: boşdursa, CSV-dən doldururuq
if get_asteroids(7).empty and OUTPUT_PATH.exists():
    save_asteroids(load_csv())

days = st.slider("Son neçə gün?", min_value=1, max_value=7, value=7)
df = get_asteroids(days)

if df.empty:
    st.warning("Data yoxdur. Əvvəlcə `python data_loader.py` işə salın.")
    st.stop()

df = filter_hazardous(df, st.checkbox("Yalnız təhlükəlilər"))
stats = dashboard_stats(df)

col1, col2, col3 = st.columns(3)
col1.metric("Asteroid sayı", stats["count"])
col2.metric("Təhlükəli", stats["hazardous"])
closest = stats["closest_mln_km"]
col3.metric("Ən yaxın məsafə (mln km)", f"{closest:.2f}" if closest is not None else "—")

st.subheader("Hər gün neçə asteroid")
st.bar_chart(daily_counts(df))

st.subheader("Bütün asteroidlər")
st.dataframe(
    df.drop(columns="id").assign(hazardous=df["hazardous"].map({1: "Bəli", 0: "Xeyr"})),
    hide_index=True,
    width="stretch",
)

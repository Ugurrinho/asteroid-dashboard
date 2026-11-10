"""Yalnız ekran (Streamlit). Data db.py-dan, hesablamalar logic.py-dan gəlir."""

from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from data_loader import OUTPUT_PATH, load_csv
from db import get_asteroids, init_db, save_asteroids
from logic import (
    GREEN,
    MOON_DISTANCE_KM,
    RED,
    RED_DISTANCE_KM,
    YELLOW,
    YELLOW_DISTANCE_KM,
    dashboard_stats,
    filter_hazardous,
    with_status,
)

INK, MUTED, GRID, EARTH = "#1B2433", "#5B6577", "#CBD3DE", "#2F5D9E"
STATUS_COLORS = {RED: "#D64545", YELLOW: "#E0A21B", GREEN: "#2F9E74"}
STATUS_LABELS = {RED: "Təhlükəli və yaxın", YELLOW: "İzlənməli", GREEN: "Təhlükəsiz"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap');

html, body, [class*="st-"], .stMarkdown, .stDataFrame, button, input {
  font-family: 'Archivo', system-ui, sans-serif;
}
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
.block-container { max-width: 1080px; padding-top: 2.5rem; }
header[data-testid="stHeader"] { background: transparent; }

.hero h1 {
  font-family: 'Archivo', sans-serif;
  font-stretch: 125%;
  font-weight: 800;
  font-size: clamp(2rem, 5.2vw, 3.6rem);
  line-height: 1.02;
  letter-spacing: -0.02em;
  color: #1B2433;
  max-width: 18ch;
  margin: 0 0 0.75rem;
  padding: 0;
}
.hero p {
  font-size: 1.125rem;
  line-height: 1.5;
  color: #5B6577;
  max-width: 60ch;
  margin: 0 0 1.5rem;
}
.facts {
  display: flex; flex-wrap: wrap; gap: 0.5rem 2.5rem;
  margin: 0.25rem 0 0.5rem; color: #5B6577; font-size: 0.95rem;
}
.facts b {
  display: block; color: #1B2433; font-stretch: 112%;
  font-weight: 700; font-size: 1.5rem; font-variant-numeric: tabular-nums;
}
h2.section {
  font-stretch: 112%; font-weight: 700; font-size: 1.5rem;
  color: #1B2433; margin: 2.5rem 0 0.25rem; padding: 0;
}
p.section-note { color: #5B6577; margin: 0 0 1rem; max-width: 60ch; }

.watch { list-style: none; margin: 0 !important; padding: 0 !important; border-top: 1px solid #CBD3DE; }
.watch li {
  display: grid; grid-template-columns: 0.75rem 1fr auto; gap: 0 1rem;
  align-items: baseline; padding: 0.85rem 0; margin: 0 !important; border-bottom: 1px solid #CBD3DE;
}
.watch .dot { width: 0.75rem; height: 0.75rem; border-radius: 50%; align-self: center; }
.watch .name { font-weight: 600; color: #1B2433; }
.watch .note { color: #5B6577; font-size: 0.95rem; grid-column: 2 / 4; max-width: 70ch; }
.watch .date { color: #5B6577; font-size: 0.9rem; font-variant-numeric: tabular-nums; }

.key { display: flex; flex-wrap: wrap; gap: 0.4rem 1.5rem; color: #5B6577; font-size: 0.9rem; margin: -0.25rem 0 1.75rem; }
.key i { display: inline-block; width: 0.7rem; height: 0.7rem; border-radius: 50%; margin-right: 0.4rem; vertical-align: -0.05rem; }

.empty { color: #5B6577; padding: 1rem 0; border-top: 1px solid #CBD3DE; }

@media (max-width: 640px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; }
  .facts { gap: 0.75rem 1.5rem; }
}
</style>
"""


def az(value, digits):
    """Rəqəmi Azərbaycan qaydasında yazır: onluq hissə vergüllə."""
    return f"{value:.{digits}f}".replace(".", ",")


def distance_chart(df):
    """Hər asteroid: Yerdən keçdiyi məsafə (log şkala), günlərə görə sətirlərdə."""
    data = df.assign(
        distance_mln=df["distance_km"] / 1e6,
        status_label=df["status"].map(STATUS_LABELS),
        hazardous_text=df["hazardous"].map({1: "Bəli", 0: "Xeyr"}),
    )
    x_scale = alt.Scale(type="log", domain=[0.2, 100], nice=False)

    refs = pd.DataFrame([
        {"x": MOON_DISTANCE_KM / 1e6, "label": "Ay"},
        {"x": RED_DISTANCE_KM / 1e6, "label": "1 mln km"},
        {"x": YELLOW_DISTANCE_KM / 1e6, "label": "7,5 mln km"},
    ])
    ref_base = alt.Chart(refs).encode(x=alt.X("x:Q", scale=x_scale))
    rules = ref_base.mark_rule(color=EARTH, strokeDash=[4, 4], strokeWidth=1.5).encode(
        y=alt.value(0), y2=alt.value(alt.expr("height"))
    )
    rule_labels = ref_base.mark_text(
        color=EARTH, align="left", baseline="bottom", dx=4, fontSize=12, fontWeight=600
    ).encode(text="label:N", y=alt.value(-4))

    points = alt.Chart(data).mark_circle(opacity=0.85, stroke="white", strokeWidth=1).encode(
        x=alt.X(
            "distance_mln:Q",
            scale=x_scale,
            title="Yerdən məsafə, mln km (loqarifmik şkala)",
            axis=alt.Axis(values=[0.2, 1, 10, 100], format="~g", grid=False),
        ),
        y=alt.Y("date:O", title=None, sort="descending"),
        size=alt.Size("diameter_m:Q", scale=alt.Scale(range=[40, 900]), legend=None),
        color=alt.Color(
            "status:N",
            scale=alt.Scale(domain=list(STATUS_COLORS), range=list(STATUS_COLORS.values())),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("name:N", title="Ad"),
            alt.Tooltip("date:N", title="Tarix"),
            alt.Tooltip("distance_mln:Q", title="Məsafə, mln km", format=".2f"),
            alt.Tooltip("speed_kms:Q", title="Sürət, km/s", format=".1f"),
            alt.Tooltip("diameter_m:Q", title="Diametr, m", format=".0f"),
            alt.Tooltip("status_label:N", title="Qiymət"),
            alt.Tooltip("hazardous_text:N", title="NASA: təhlükəli"),
        ],
    )

    return (
        alt.layer(points, rules, rule_labels)
        .properties(height=alt.Step(44), padding={"top": 22, "left": 4, "right": 12, "bottom": 4})
        .configure(font="Archivo")
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=MUTED, titleColor=MUTED, gridColor=GRID, domainColor=GRID,
            tickColor=GRID, labelFontSize=12, titleFontSize=12, titleFontWeight=500,
        )
        .configure_axisY(grid=True, domain=False, ticks=False, labelPadding=8)
    )


def short_note(row):
    """classify() izahı adla başlayır; ad artıq qalın yazıldığı üçün onu kəsirik."""
    note = row.note.removeprefix(row.name).strip()
    return note[:1].upper() + note[1:]


def watch_list(df):
    """Qırmızı və sarı asteroidlər, ən yaxından başlayaraq."""
    flagged = df[df["status"] != GREEN].sort_values("distance_km")
    if flagged.empty:
        return '<p class="empty">Bu dövrdə izlənməli asteroid yoxdur: hamısı təhlükəsiz məsafədən keçib.</p>'
    items = "".join(
        f'<li><span class="dot" style="background:{STATUS_COLORS[r.status]}"></span>'
        f'<span class="name">{escape(r.name)}</span>'
        f'<span class="date">{escape(r.date)}</span>'
        f'<span class="note">{escape(short_note(r))}</span></li>'
        for r in flagged.itertuples()
    )
    return f'<ul class="watch">{items}</ul>'


st.set_page_config(page_title="Yerə yaxın asteroidlər", page_icon="☄️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

init_db()
# Serverdə (Streamlit Cloud) asteroid.db olmur: boşdursa, CSV-dən doldururuq
if get_asteroids(7).empty and OUTPUT_PATH.exists():
    save_asteroids(load_csv())

controls = st.columns([3, 2], vertical_alignment="bottom")
days = controls[0].slider("Neçə günə baxılsın", min_value=1, max_value=7, value=7)
only_hazardous = controls[1].toggle("Yalnız NASA-nın təhlükəli saydıqları")

df = get_asteroids(days)
if df.empty:
    st.info("Bazada asteroid yoxdur. Datanı yükləmək üçün `python data_loader.py` işə salın.")
    st.stop()

df = with_status(filter_hazardous(df, only_hazardous))
if df.empty:
    st.info("Seçilmiş günlərdə NASA-nın təhlükəli saydığı asteroid yoxdur. Filtri söndürün.")
    st.stop()

stats = dashboard_stats(df)
closest = df.loc[df["distance_km"].idxmin()]
moon_times = closest["distance_km"] / MOON_DISTANCE_KM
what = "təhlükəli asteroid" if only_hazardous else "asteroid"

st.markdown(
    f"""
<div class="hero">
  <h1>Son {days} gündə {stats['count']} {what} Yerin yanından keçdi</h1>
  <p>Ən yaxını {escape(closest['name'])} oldu: {az(stats['closest_mln_km'], 2)} mln km,
  yəni Aya olan məsafədən {moon_times:.0f} dəfə uzaq.
  Hər nöqtə bir asteroiddir; nə qədər solda, Yerə o qədər yaxın keçib.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.altair_chart(distance_chart(df), width="stretch")
st.markdown(
    '<p class="key">'
    + "".join(
        f'<span><i style="background:{STATUS_COLORS[k]}"></i>{v}</span>'
        for k, v in STATUS_LABELS.items()
    )
    + "<span>Nöqtənin ölçüsü asteroidin diametrini göstərir</span></p>",
    unsafe_allow_html=True,
)

counts = df["status"].value_counts()
st.markdown(
    f"""
<div class="facts">
  <span><b>{stats['hazardous']}</b>NASA-ya görə təhlükəli</span>
  <span><b>{counts.get(RED, 0) + counts.get(YELLOW, 0)}</b>izlənməli</span>
  <span><b>{az(df['speed_kms'].mean(), 1)} km/s</b>orta sürət</span>
  <span><b>{df['diameter_m'].max():.0f} m</b>ən böyük diametr</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<h2 class="section">İzlənməli asteroidlər</h2>'
    '<p class="section-note">Təhlükəli sayılan, 7,5 mln km-dən yaxın keçən '
    "və ya 25 km/s-dən sürətli olanlar.</p>"
    + watch_list(df),
    unsafe_allow_html=True,
)

with st.expander(f"Bütün {stats['count']} asteroidin cədvəli"):
    st.dataframe(
        df.assign(
            hazardous=df["hazardous"].map({1: "Bəli", 0: "Xeyr"}),
            status=df["status"].map(STATUS_LABELS),
            distance_km=df["distance_km"] / 1e6,
        )[["date", "name", "distance_km", "speed_kms", "diameter_m", "hazardous", "status"]],
        column_config={
            "date": "Tarix",
            "name": "Ad",
            "distance_km": st.column_config.NumberColumn("Məsafə, mln km", format="%.2f"),
            "speed_kms": st.column_config.NumberColumn("Sürət, km/s", format="%.1f"),
            "diameter_m": st.column_config.NumberColumn("Diametr, m", format="%.0f"),
            "hazardous": "NASA: təhlükəli",
            "status": "Qiymət",
        },
        hide_index=True,
        width="stretch",
    )

st.caption("Mənbə: NASA NeoWs. Qiymət qaydaları logic.py faylındadır.")

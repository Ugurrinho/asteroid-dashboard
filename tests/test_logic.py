import ast
from pathlib import Path

import pandas as pd

from data_loader import normalize
from logic import GREEN, RED, YELLOW, classify, weekly_summary
from simulator import DAYS, RED_DAY, simulate

ROOT = Path(__file__).resolve().parent.parent


def test_red_when_hazardous_and_close():
    color, text = classify({"name": "X", "distance_km": 500_000, "speed_kms": 10, "hazardous": 1})
    assert color == RED
    assert isinstance(text, str) and text


def test_yellow_when_hazardous_but_far():
    assert classify({"distance_km": 5e7, "speed_kms": 10, "hazardous": True})[0] == YELLOW


def test_yellow_when_close_not_hazardous():
    assert classify({"distance_km": 3e6, "speed_kms": 10, "hazardous": 0})[0] == YELLOW


def test_yellow_when_fast():
    assert classify({"distance_km": 5e7, "speed_kms": 28, "hazardous": 0})[0] == YELLOW


def test_green_when_far_and_slow():
    assert classify({"distance_km": 5e7, "speed_kms": 10, "hazardous": 0})[0] == GREEN


def test_csv_rows_work_after_normalize():
    csv_df = pd.DataFrame([{"name": "X", "miss_distance_km": 400_000,
                            "velocity_km_s": 12, "is_hazardous": "True"}])
    assert classify(normalize(csv_df).iloc[0])[0] == RED


def test_weekly_summary():
    df = pd.DataFrame({
        "name": ["a", "b", "c", "d"],
        "speed_kms": [5.0, 5.0, 5.0, 25.0],
        "distance_km": [9e6, 2e6, 5e6, 8e6],
    })
    s = weekly_summary(df)
    assert s["avg_speed"] == 10.0
    assert s["closest"]["name"] == "b"
    assert list(s["fast"]["name"]) == ["d"]


def test_weekly_summary_empty():
    s = weekly_summary(pd.DataFrame(columns=["name", "speed_kms", "distance_km"]))
    assert s["avg_speed"] is None and s["closest"] is None and s["fast"].empty


def _imports(filename):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_layers_stay_separate():
    assert not _imports("logic.py") & {"streamlit", "sqlite3", "db", "data_loader", "simulator", "requests"}
    assert not _imports("db.py") & {"streamlit", "logic"}
    for data_file in ("data_loader.py", "simulator.py"):
        assert not _imports(data_file) & {"streamlit", "sqlite3", "db", "logic"}
    assert not _imports("app.py") & {"sqlite3", "requests"}


def test_simulator_14_days_and_red_only_on_day_10():
    df = normalize(simulate())
    days = sorted(df["date"].unique())
    assert len(days) == DAYS

    colors = df.apply(lambda r: classify(r)[0], axis=1)
    red_days = set(df.loc[colors == RED, "date"])
    assert red_days == {days[RED_DAY - 1]}


def test_simulator_is_reproducible():
    pd.testing.assert_frame_equal(simulate(seed=1), simulate(seed=1))


def test_with_status_adds_color_and_note():
    import pandas as pd
    from logic import RED, GREEN, with_status

    df = pd.DataFrame([
        {"name": "A", "speed_kms": 10.0, "distance_km": 500_000, "hazardous": 1},
        {"name": "B", "speed_kms": 10.0, "distance_km": 50_000_000, "hazardous": 0},
    ])
    out = with_status(df)
    assert list(out["status"]) == [RED, GREEN]
    assert out["note"].str.startswith(("A", "B")).all()
    assert with_status(df.iloc[0:0]).empty

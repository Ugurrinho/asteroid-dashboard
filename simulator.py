"""14 günlük real görünən asteroid datası yaradır.

10-cu gün bilərəkdən bir "qırmızı" hadisə əlavə olunur:
təhlükəli və Yerə 1 mln km-dən yaxın keçən asteroid.

İstifadə:  python simulator.py   ->  data/simulated.csv
"""

import random
import string
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DAYS = 14
RED_DAY = 10
OUT_PATH = Path(__file__).resolve().parent / "data" / "simulated.csv"


def _fake_name(rng, year):
    letters = "".join(rng.choices(string.ascii_uppercase, k=2))
    return f"({year} {letters}{rng.randint(1, 99)})"


def _normal_asteroid(rng, day):
    diameter = round(rng.lognormvariate(4.0, 1.0), 2)  # əksəri 10-300 m
    hazardous = diameter > 140 and rng.random() < 0.4
    return {
        "name": _fake_name(rng, rng.randint(1999, 2025)),
        "date": day.isoformat(),
        "diameter_m": diameter,
        "velocity_km_s": round(rng.uniform(4, 30), 3),
        # normal günlərdə hamısı 2 mln km-dən uzaq olur ki, qırmızı yalnız 10-cu gün olsun
        "miss_distance_km": round(rng.uniform(2e6, 7.4e7), 1),
        "is_hazardous": hazardous,
    }


def simulate(start=None, seed=42):
    """14 gün üçün DataFrame qaytarır. Eyni seed -> eyni data."""
    rng = random.Random(seed)
    start = start or date.today() - timedelta(days=DAYS - 1)
    rows = []
    for i in range(DAYS):
        day = start + timedelta(days=i)
        rows += [_normal_asteroid(rng, day) for _ in range(rng.randint(5, 12))]
        if i + 1 == RED_DAY:
            rows.append({
                "name": "(2026 RD10)",
                "date": day.isoformat(),
                "diameter_m": 310.5,
                "velocity_km_s": 27.4,
                "miss_distance_km": 384_400.0,  # təxminən Ay məsafəsi
                "is_hazardous": True,
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    df = simulate()
    OUT_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"{len(df)} asteroid {DAYS} gün üçün yaradıldı -> {OUT_PATH}")

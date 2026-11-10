import csv
import os
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
OUTPUT_PATH = BASE_DIR / "data" / "asteroids.csv"

API_URL = "https://api.nasa.gov/neo/rest/v1/feed"
REQUEST_TIMEOUT_SECONDS = 30
DAYS = 7
SAMPLE_ROWS = 30
KM_PER_AU = 149_597_871

COLUMNS = [
    "name",
    "date",
    "diameter_m",
    "velocity_km_s",
    "miss_distance_km",
    "is_hazardous",
]


# CSV sütun adları -> layihədə hər yerdə istifadə olunan adlar (db, logic, app)
CSV_TO_STANDARD = {
    "velocity_km_s": "speed_kms",
    "miss_distance_km": "distance_km",
    "is_hazardous": "hazardous",
}


class ApiError(Exception):
    """The API could not provide data. Messages never contain the API key."""


def read_api_key():
    """Return NASA_API_KEY from .env, falling back to the environment."""
    if ENV_PATH.exists():
        # utf-8-sig: Windows editors often save .env with a BOM.
        for line in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip().removeprefix("export ").strip() == "NASA_API_KEY":
                return value.strip().strip("'\"")
    return os.environ.get("NASA_API_KEY", "").strip()


def date_range():
    """Return the 7 calendar days ending today, as (start, end)."""
    end = date.today()
    return end - timedelta(days=DAYS - 1), end


def parse_asteroid(asteroid, feed_date):
    """Convert one NeoWs asteroid object into a CSV row."""
    approaches = asteroid["close_approach_data"]
    approach = next(
        (a for a in approaches if a["close_approach_date"] == feed_date),
        approaches[0],
    )
    # NeoWs only gives a min/max estimate, so use the midpoint.
    diameter = asteroid["estimated_diameter"]["meters"]
    diameter_m = (
        diameter["estimated_diameter_min"] + diameter["estimated_diameter_max"]
    ) / 2

    return {
        "name": asteroid["name"].strip(),
        "date": approach["close_approach_date"],
        "diameter_m": round(diameter_m, 2),
        "velocity_km_s": round(
            float(approach["relative_velocity"]["kilometers_per_second"]), 3
        ),
        "miss_distance_km": round(float(approach["miss_distance"]["kilometers"]), 1),
        "is_hazardous": bool(asteroid["is_potentially_hazardous_asteroid"]),
    }


def fetch_asteroids(api_key):
    """Fetch rows from NeoWs, raising ApiError on any failure."""
    if not api_key:
        raise ApiError("NASA_API_KEY was not found in .env")

    start, end = date_range()
    params = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "api_key": api_key,
    }

    # Report only the exception type or status: requests puts the full URL,
    # including api_key, into its exception messages.
    try:
        response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as error:
        raise ApiError(f"request failed ({type(error).__name__})") from None

    if response.status_code != 200:
        raise ApiError(f"API returned HTTP {response.status_code}")

    try:
        feed = response.json()["near_earth_objects"]
        rows = [
            parse_asteroid(asteroid, feed_date)
            for feed_date, asteroids in feed.items()
            for asteroid in asteroids
        ]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise ApiError(f"unexpected response ({type(error).__name__})") from None

    if not rows:
        raise ApiError("API returned no asteroids")
    return rows


def generate_sample_data(count=SAMPLE_ROWS):
    """Create made-up rows. The SAMPLE names keep them from passing as real data."""
    rng = random.Random(42)
    start, _ = date_range()
    rows = []

    for number in range(1, count + 1):
        # Log-uniform ranges: small, distant objects are much more common.
        diameter_m = 10 ** rng.uniform(1, 3.2)
        miss_distance_km = 10 ** rng.uniform(5.5, 7.8)
        rows.append(
            {
                "name": f"(SAMPLE {number:03d})",
                "date": (start + timedelta(days=rng.randrange(DAYS))).isoformat(),
                "diameter_m": round(diameter_m, 2),
                "velocity_km_s": round(rng.uniform(3, 35), 3),
                "miss_distance_km": round(miss_distance_km, 1),
                # Rough version of NASA's rule: about 140 m+ and within 0.05 AU.
                "is_hazardous": diameter_m >= 140 and miss_distance_km <= 0.05 * KM_PER_AU,
            }
        )
    return rows


def write_csv(rows):
    """Write rows to OUTPUT_PATH, sorted by date and then name."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda row: (row["date"], row["name"]))
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def normalize(df):
    """CSV formatlı DataFrame-i standart sütun adlarına çevirir, hazardous -> 0/1."""
    df = df.rename(columns=CSV_TO_STANDARD).copy()
    df["hazardous"] = (
        df["hazardous"].astype(str).str.strip().str.lower().isin(["true", "1", "bəli"]).astype(int)
    )
    return df


def load_csv(path=OUTPUT_PATH):
    """CSV-ni oxuyub standart sütun adları ilə qaytarır."""
    return normalize(pd.read_csv(path))


def main():
    try:
        rows = fetch_asteroids(read_api_key())
        print(f"NASA API: {len(rows)} asteroids loaded.")
    except ApiError as error:
        rows = generate_sample_data()
        print(f"WARNING: {error}.")
        print(f"WARNING: writing {len(rows)} rows of SAMPLE data, not real NASA data.")

    write_csv(rows)
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

# Asteroid	Diametr	Tarix	Sürət	Yerə məsafə	Təhlükəli
# Ən böyük	307493 (2002 XP90)	830.89 m	1 noyabr 2026	16.094 km/s	45 865 643.9 km	Xeyr
# Orta (median)	(2019 VL3)	94.09 m	4 noyabr 2026	29.565 km/s	65 269 890.5 km	Xeyr
# Ən balaca	(2016 RN20)	9.85 m	4 noyabr 2026	6.348 km/s	28 718 966.2 km	Xeyr

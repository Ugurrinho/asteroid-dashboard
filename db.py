"""Yalnız baza (SQLite): cədvəl yaratmaq, yazmaq, oxumaq.

Burada CSV oxunmur və data təmizlənmir. save_asteroids() artıq
standart sütun adları olan DataFrame gözləyir (data_loader.normalize).
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "asteroid.db"

COLUMNS = ["name", "date", "diameter_m", "speed_kms", "distance_km", "hazardous"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS asteroids (
    id           INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    date         TEXT    NOT NULL CHECK (date(date) IS NOT NULL),
    diameter_m   REAL    CHECK (diameter_m  IS NULL OR diameter_m  >= 0),
    speed_kms    REAL    CHECK (speed_kms   IS NULL OR speed_kms   >= 0),
    distance_km  REAL    CHECK (distance_km IS NULL OR distance_km >= 0),
    hazardous    INTEGER NOT NULL DEFAULT 0 CHECK (hazardous IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_asteroids_date      ON asteroids(date);
CREATE INDEX IF NOT EXISTS idx_asteroids_hazardous ON asteroids(hazardous);
"""


def init_db():
    """Bazanı və asteroids cədvəlini yaradır (artıq varsa, toxunmur)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)


def save_asteroids(df):
    """Standart sütunlu DataFrame-i bazaya yazır. Eyni ad+tarix təkrar yazılmır."""
    added = 0
    with sqlite3.connect(DB_PATH) as conn:
        for row in df[COLUMNS].itertuples(index=False):
            cursor = conn.execute(
                """
                INSERT INTO asteroids (name, date, diameter_m, speed_kms, distance_km, hazardous)
                SELECT ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM asteroids WHERE name = ? AND date = ?)
                """,
                (*row, row.name, row.date),
            )
            added += cursor.rowcount
    return added


def get_asteroids(days=7):
    """Bazadakı ən son tarixdən geriyə doğru son `days` günün asteroidlərini qaytarır."""
    query = """
        SELECT * FROM asteroids
        WHERE date > date((SELECT MAX(date) FROM asteroids), ?)
        ORDER BY date, name
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=(f"-{days} days",))


if __name__ == "__main__":
    # CSV-ni oxumaq data_loader-in işidir; burada yalnız nəticə bazaya yazılır.
    from data_loader import load_csv

    sys.stdout.reconfigure(encoding="utf-8")  # Windows terminalında ə, ı hərfləri üçün
    init_db()
    added = save_asteroids(load_csv())
    print(f"{added} yeni asteroid bazaya yazıldı.")
    print(f"Son 7 gündə {len(get_asteroids(7))} asteroid var.")

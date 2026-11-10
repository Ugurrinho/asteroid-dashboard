"""Asteroid qərar məntiqi. Streamlit / ekran kodundan tam ayrıdır.

Burada heç bir `streamlit` importu yoxdur: funksiyalar sadəcə data alır,
nəticə qaytarır. Ona görə də pytest ilə rahat test olunur.

Standart sütun adları gözlənilir (speed_kms, distance_km, hazardous).
CSV adlarını çevirmək data_loader.normalize() funksiyasının işidir.

Qaydalar (hədlər aşağıdakı sabitlərdədir):
  qırmızı - təhlükəli (hazardous) VƏ Yerə 1 mln km-dən yaxın
  sarı    - təhlükəli, YA 7.5 mln km-dən yaxın, YA sürəti 25 km/s-dən çox
  yaşıl   - qalan hamısı
"""

import pandas as pd

RED_DISTANCE_KM = 1_000_000
YELLOW_DISTANCE_KM = 7_500_000
YELLOW_SPEED_KMS = 25.0

MOON_DISTANCE_KM = 384_400

GREEN, YELLOW, RED = "yaşıl", "sarı", "qırmızı"


def _az(value, digits):
    """Rəqəmi Azərbaycan qaydasında yazır: onluq hissə vergüllə (5,98)."""
    return f"{value:.{digits}f}".replace(".", ",")


def _get(asteroid, key):
    """Dəyəri qaytarır; yoxdursa və ya NaN-dırsa None."""
    value = asteroid.get(key) if hasattr(asteroid, "get") else None
    return None if value is None or pd.isna(value) else value


def classify(asteroid):
    """Asteroid (dict və ya pandas sətri) üçün (rəng, bir cümləlik izah) qaytarır."""
    name = _get(asteroid, "name") or "Asteroid"
    distance = _get(asteroid, "distance_km")
    speed = _get(asteroid, "speed_kms")
    hazardous = bool(_get(asteroid, "hazardous"))

    distance = float(distance) if distance is not None else float("inf")
    speed = float(speed) if speed is not None else 0.0
    dist_mln = distance / 1e6

    if hazardous and distance < RED_DISTANCE_KM:
        return RED, f"{name} təhlükəlidir və Yerə cəmi {_az(dist_mln, 2)} mln km yaxınlaşır."
    if hazardous:
        return YELLOW, f"{name} təhlükəli sayılır, amma {_az(dist_mln, 2)} mln km uzaqdan keçir."
    if distance < YELLOW_DISTANCE_KM:
        return YELLOW, f"{name} Yerə {_az(dist_mln, 2)} mln km yaxınlaşır, izləmək lazımdır."
    if speed > YELLOW_SPEED_KMS:
        return YELLOW, f"{name} çox sürətlidir ({_az(speed, 1)} km/s), izləmək lazımdır."
    return GREEN, f"{name} təhlükəsizdir: {_az(dist_mln, 2)} mln km uzaqdan, {_az(speed, 1)} km/s sürətlə keçir."


def weekly_summary(df):
    """Orta sürət, ən yaxın asteroid və ortadan 2 dəfə sürətli olanları qaytarır."""
    if df.empty:
        return {"avg_speed": None, "closest": None, "fast": df.iloc[0:0]}

    avg_speed = float(df["speed_kms"].mean())
    closest = df.loc[df["distance_km"].idxmin()]
    fast = df[df["speed_kms"] > 2 * avg_speed].reset_index(drop=True)

    return {"avg_speed": avg_speed, "closest": closest, "fast": fast}


def filter_hazardous(df, only_hazardous=True):
    """Yalnız təhlükəli asteroidləri saxlayır (only_hazardous=False olsa, hamısını)."""
    return df[df["hazardous"] == 1] if only_hazardous else df


def dashboard_stats(df):
    """Ekrandakı göstəricilər: say, təhlükəli sayı, ən yaxın məsafə (mln km)."""
    return {
        "count": len(df),
        "hazardous": int(df["hazardous"].sum()),
        "closest_mln_km": float(df["distance_km"].min()) / 1e6 if len(df) else None,
    }


def with_status(df):
    """Hər sətrə classify() nəticəsini əlavə edir: `status` (rəng) və `note` (izah)."""
    pairs = [classify(row) for _, row in df.iterrows()]
    return df.assign(
        status=[p[0] for p in pairs],
        note=[p[1] for p in pairs],
    )


def daily_counts(df):
    """Hər gün neçə asteroid olduğunu qaytarır (tarix -> say)."""
    return df.groupby("date").size().rename("say")

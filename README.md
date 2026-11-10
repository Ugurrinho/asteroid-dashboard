# ☄️ Yerə yaxın asteroidlər

NASA NeoWs datası əsasında Streamlit dashboard.

| Fayl | Vəzifə |
|---|---|
| `app.py` | yalnız ekran (Streamlit) |
| `logic.py` | yalnız qaydalar (rəng təsnifatı, statistika) |
| `db.py` | yalnız baza (SQLite) |
| `data_loader.py`, `simulator.py` | yalnız data (NASA API / simulyasiya) |

```bash
pip install -r requirements.txt
python data_loader.py   # .env-də NASA_API_KEY lazımdır, yoxdursa SAMPLE data yazır
streamlit run app.py
pytest
```

import os
import sqlite3
import pandas as pd

# ==========================
# Setup
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database", "f1_data.db")


# ==========================
# Helper Functions
# ==========================
def ensure_predictions_table():
    """Create Race_Predictions table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Race_Predictions (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            gp_name TEXT NOT NULL,
            driver_code TEXT NOT NULL,
            driver_name TEXT,
            qualifying_time REAL,
            qualifying_position INTEGER,
            predicted_race_position INTEGER,
            tire_deg_rate REAL,
            prediction_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_all_races(year: int):
    """Return all race names for the given year."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT name FROM Race WHERE year = ? ORDER BY round ASC", conn, params=(year,)
    )
    conn.close()
    return df["name"].tolist()


def get_race_data_from_db(year: int, gp_name: str):
    """Retrieve qualifying + degradation data for a race from the DB."""
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT 
            d.code AS DriverCode,
            d.first_name,
            d.last_name,
            dr.Q1, dr.Q2, dr.Q3,
            dr.qualifying_position,
            dr.avg_tire_deg_per_lap
        FROM Driver_Race dr
        JOIN Driver d ON dr.driver_id = d.driver_id
        JOIN Race r ON dr.race_id = r.race_id
        WHERE r.year = ? AND r.name = ?
        ORDER BY dr.qualifying_position
    """
    df = pd.read_sql_query(query, conn, params=(year, gp_name))
    conn.close()

    if df.empty:
        print(f"⚠️  No qualifying data found for {gp_name} {year}")
        return None

    # Construct driver display name with fallbacks
    def build_name(row):
        if pd.notna(row["first_name"]) and pd.notna(row["last_name"]):
            return f"{row['first_name']} {row['last_name']}"
        elif pd.notna(row["first_name"]):
            return row["first_name"]
        elif pd.notna(row["DriverCode"]):
            return row["DriverCode"]
        return "Unknown Driver"

    df["Driver"] = df.apply(build_name, axis=1)

    # Derive best qualifying time
    def best_time(row):
        for q in ["Q3", "Q2", "Q1"]:
            if row[q] and row[q] != "None":
                try:
                    return pd.to_timedelta(row[q]).total_seconds()
                except Exception:
                    pass
        return None

    df["QualifyingTime (s)"] = df.apply(best_time, axis=1)
    df = df.dropna(subset=["QualifyingTime (s)"])
    return df


# ==========================
# Prediction Logic
# ==========================
def predict_race_positions(df: pd.DataFrame):
    """Predict finishing positions based on qualifying + tyre degradation."""
    predictions = df.copy()

    predictions["HasDegData"] = predictions["avg_tire_deg_per_lap"].notna()
    median_deg = predictions["avg_tire_deg_per_lap"].median(skipna=True)

    # Relative degradation (negative = better)
    predictions["RelativeDeg"] = predictions["avg_tire_deg_per_lap"] - median_deg

    # Adjust positions: better degradation → move up, worse → move down
    def adjust(row):
        if not row["HasDegData"]:
            return 0
        if row["RelativeDeg"] < 0:
            return -1  # better tyre life
        elif row["RelativeDeg"] > 0:
            return 1   # worse tyre life
        return 0

    predictions["PositionAdjustment"] = predictions.apply(adjust, axis=1)
    predictions["PredictedRacePosition"] = predictions["qualifying_position"] + predictions["PositionAdjustment"]
    predictions["PredictedRacePosition"] = predictions["PredictedRacePosition"].clip(1, len(predictions))
    predictions = predictions.sort_values("PredictedRacePosition").reset_index(drop=True)
    predictions["PredictedRacePosition"] = predictions.index + 1
    predictions["PredictionMethod"] = predictions.apply(
        lambda r: "qualifying_and_tire_deg" if r["HasDegData"] else "qualifying_only", axis=1
    )
    return predictions


# ==========================
# Store in DB
# ==========================
def store_predictions(year: int, gp_name: str, df: pd.DataFrame):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO Race_Predictions (
                year, gp_name, driver_code, driver_name,
                qualifying_time, qualifying_position,
                predicted_race_position, tire_deg_rate, prediction_method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            year, gp_name, row["DriverCode"], row["Driver"],
            row["QualifyingTime (s)"], row["qualifying_position"],
            row["PredictedRacePosition"], row["avg_tire_deg_per_lap"], row["PredictionMethod"]
        ))
    conn.commit()
    conn.close()


# ==========================
# Main
# ==========================
def generate_predictions_for_all_2025():
    YEAR = 2025
    ensure_predictions_table()
    races = get_all_races(YEAR)

    print(f"=== Generating predictions for all {YEAR} races ===")
    for gp_name in races:
        print(f"\n🏁 {gp_name}")
        df = get_race_data_from_db(YEAR, gp_name)
        if df is None or df.empty:
            continue
        predictions = predict_race_positions(df)
        store_predictions(YEAR, gp_name, predictions)
        print(f"✅ Predictions stored for {gp_name}")

    print(f"\n🎯 All predictions for {YEAR} completed and saved to Race_Predictions.")


if __name__ == "__main__":
    generate_predictions_for_all_2025()

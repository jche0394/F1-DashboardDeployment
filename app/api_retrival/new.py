import sqlite3
import pandas as pd
from datetime import datetime
import fastf1
from get_deg import calculate_tire_degradation  # import your function

# ==============================
# CONFIGURATION
# ==============================
DB_FILE = "app/api_retrival/database/f1_data.db"
YEAR = 2025
import os
os.makedirs("fastf1_cache", exist_ok=True)
fastf1.Cache.enable_cache("fastf1_cache")



# ==============================
# Ensure column exists
# ==============================
def ensure_deg_column():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(Driver_Race);")
    cols = [c[1] for c in cur.fetchall()]
    if "avg_tire_deg_per_lap" not in cols:
        cur.execute("ALTER TABLE Driver_Race ADD COLUMN avg_tire_deg_per_lap REAL;")
        print("✅ Added column avg_tire_deg_per_lap.")
    else:
        print("ℹ️ Column already exists.")
    conn.commit()
    conn.close()


# ==============================
# Get all rounds for a season
# ==============================
def get_rounds(year):
    schedule = fastf1.get_event_schedule(year)
    # skip only pre-season or testing
    schedule = schedule[~schedule["EventName"].str.contains("Testing", case=False, na=False)]
    return schedule[["RoundNumber", "EventName", "EventDate"]].reset_index(drop=True)



# ==============================
# Update degradation values
# ==============================
def update_tire_deg_for_year(year):
    ensure_deg_column()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    rounds = get_rounds(year)
    print(f"\n=== Updating tyre degradation for {year} season ===")

    for _, event in rounds.iterrows():
        rnd = int(event["RoundNumber"])
        name = event["EventName"]

        print(f"\n🏁 Round {rnd}: {name}")
        try:
            deg_df, source = calculate_tire_degradation(year, rnd)
        except Exception as e:
            print(f"❌ Error calculating degradation for round {rnd}: {e}")
            continue

        if deg_df.empty:
            print("⚠️ No usable degradation data.")
            continue

        for _, row in deg_df.iterrows():
            first = str(row["FirstName"]).strip() if row["FirstName"] else None
            last = str(row["LastName"]).strip() if row["LastName"] else None
            deg = row["AvgDegPerLap"]

            if not first or not last or pd.isna(deg):
                continue

            cur.execute("""
                UPDATE Driver_Race
                SET avg_tire_deg_per_lap = ?
                WHERE race_id = (
                    SELECT race_id FROM Race WHERE year = ? AND round = ?
                )
                AND driver_id = (
                    SELECT driver_id FROM Driver WHERE lower(first_name) = lower(?) AND lower(last_name) = lower(?)
                );
            """, (deg, year, rnd, first, last))

        conn.commit()
        print(f"✅ Updated degradation for {len(deg_df)} drivers (source: {source})")

    conn.close()
    print("\n🎯 All 2024 races updated.")


# ==============================
# Run script
# ==============================
if __name__ == "__main__":
    update_tire_deg_for_year(2025)

import fastf1
import pandas as pd
import os

CACHE_DIR = "fastf1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


def load_session(year, round_num, kind):
    """Load a FastF1 session by round number."""
    sess = fastf1.get_session(year, round_num, kind)
    sess.load()
    return sess


def calculate_deg_from_session(session, is_sprint=False):
    """Compute average tyre degradation per driver from a given session."""
    laps = session.laps.copy()
    drivers = session.results[["Abbreviation", "FirstName", "LastName"]].drop_duplicates()

    # ✅ only use race compounds
    race_compounds = ["MEDIUM", "HARD"]
    laps = laps[laps["Compound"].isin(race_compounds)]
    laps = laps[pd.notna(laps["LapTime"])].copy()
    laps.loc[:, "LapTime (s)"] = laps["LapTime"].dt.total_seconds()

    deg_data = []
    min_stint_length = 3  # lenient to include most drivers

    for driver in laps["Driver"].unique():
        driver_laps = laps[laps["Driver"] == driver]
        all_deg = []

        for stint in driver_laps["Stint"].unique():
            stint_laps = driver_laps[driver_laps["Stint"] == stint].sort_values("LapNumber")
            if len(stint_laps) < min_stint_length:
                continue

            usable = stint_laps.iloc[1:]  # skip out lap
            if len(usable) < 2:
                continue

            # short stints → start vs end; long stints → average window method
            if len(usable) >= 6:
                early = usable.iloc[:3]["LapTime (s)"].mean()
                late = usable.iloc[-3:]["LapTime (s)"].mean()
                num_laps = len(usable) - 3
            else:
                early = usable.iloc[0]["LapTime (s)"]
                late = usable.iloc[-1]["LapTime (s)"]
                num_laps = len(usable) - 1

            deg_per_lap = (late - early) / num_laps if num_laps > 0 else 0
            all_deg.append(deg_per_lap)

        if all_deg:
            deg_data.append({
                "Driver": driver,
                "AvgDegPerLap": sum(all_deg) / len(all_deg)
            })

    if not deg_data:
        return pd.DataFrame(columns=["Driver", "FirstName", "LastName", "AvgDegPerLap"])

    df = pd.DataFrame(deg_data)
    merged = df.merge(drivers, left_on="Driver", right_on="Abbreviation", how="left")
    merged = merged[["Driver", "FirstName", "LastName", "AvgDegPerLap"]].sort_values("AvgDegPerLap")
    return merged


def calculate_tire_degradation(year, round_num):
    """Get tyre degradation data for a race weekend (priority: Sprint > FP2 > FP3)."""
    for kind, is_sprint in [("S", True), ("FP2", False), ("FP3", False)]:
        try:
            session = load_session(year, round_num, kind)
            print(f"✅ Using {kind} session")
            deg = calculate_deg_from_session(session, is_sprint)
            if not deg.empty:
                return deg, kind
        except Exception as e:
            print(f"⚠️ Failed to load {kind}: {e}")

    print("❌ No usable session data found for this round.")
    return pd.DataFrame(columns=["Driver", "FirstName", "LastName", "AvgDegPerLap"]), None


# -----------------------------
# Run for a given round number
# -----------------------------
if __name__ == "__main__":
    year = 2025
    round_num = 19  # e.g. Bahrain GP 2024
    deg, source = calculate_tire_degradation(year, round_num)

    if source:
        print(f"\nTire degradation per driver (s/lap) — source: {source}")
    else:
        print("\nNo tire degradation data available — prediction fallback: qualifying_only")

    if deg.empty:
        print("(no usable stints found)")
    else:
        for _, row in deg.iterrows():
            sign = "▲" if row["AvgDegPerLap"] > 0 else "▼"
            print(f"{row['FirstName']} {row['LastName']} ({row['Driver']}): "
                  f"{row['AvgDegPerLap']:.5f} s/lap {sign}")

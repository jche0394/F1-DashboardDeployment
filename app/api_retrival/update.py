import os
import sqlite3
import fastf1
import pandas as pd
from datetime import datetime, timezone

from races import getRaces
from round_elo import add_elo_rating
from get_deg import calculate_tire_degradation
from session_retrival import get_session  # loads one FastF1 session (single round)

# ==========================
# Setup
# ==========================
CACHE_DIR = "fastf1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

DB_FILE = "app/api_retrival/database/f1_data.db"


def safe_int(val):
    if val is None or pd.isna(val):
        return None
    try:
        return int(val)
    except Exception:
        return None


def format_quali_time(val):
    if val is None or pd.isna(val):
        return None
    return str(val)


def safe_date(val):
    if val is None or pd.isna(val):
        return None
    return pd.to_datetime(val).strftime("%Y-%m-%d")


def ensure_deg_column(cur):
    cur.execute("PRAGMA table_info(Driver_Race);")
    cols = [c[1] for c in cur.fetchall()]
    if "avg_tire_deg_per_lap" not in cols:
        cur.execute("ALTER TABLE Driver_Race ADD COLUMN avg_tire_deg_per_lap REAL;")


# ============================================================
# Retrieve existing Elo tables (pivoted by CODE/NAME, not names)
# ============================================================
def get_existing_elos(conn, year):
    # Driver Elo (by driver code)
    driver_df = pd.read_sql_query(
        """
        SELECT dr.elo AS DriverElo,
               dr.combined_elo AS CombinedElo,
               r.round AS Round,
               d.code AS DriverId,
               d.first_name AS FirstName,
               d.last_name AS LastName,
               c.name AS ConstructorName
        FROM Driver_Race dr
        JOIN Race r ON dr.race_id = r.race_id
        JOIN Driver d ON dr.driver_id = d.driver_id
        JOIN Constructor c ON dr.constructor_id = c.constructor_id
        WHERE r.year = ?
        ORDER BY r.round
        """,
        conn,
        params=(year,),
    )

    # Constructor Elo (by constructor name)
    constructor_df = pd.read_sql_query(
        """
        SELECT cr.elo AS ConstructorElo,
               r.round AS Round,
               c.name AS ConstructorName
        FROM Constructor_Race cr
        JOIN Race r ON cr.race_id = r.race_id
        JOIN Constructor c ON cr.constructor_id = c.constructor_id
        WHERE r.year = ?
        ORDER BY r.round
        """,
        conn,
        params=(year,),
    )

    if not driver_df.empty:
        prev_driver = (
            driver_df.pivot_table(index="DriverId", columns="Round", values="DriverElo")
            .reset_index()
        )
        prev_combined = (
            driver_df.pivot_table(index="DriverId", columns="Round", values="CombinedElo")
            .reset_index()
        )
    else:
        prev_driver = pd.DataFrame(columns=["DriverId"])
        prev_combined = pd.DataFrame(columns=["DriverId"])

    if not constructor_df.empty:
        prev_constr = (
            constructor_df.pivot_table(index="ConstructorName", columns="Round", values="ConstructorElo")
            .reset_index()
        )
    else:
        prev_constr = pd.DataFrame(columns=["ConstructorName"])

    return prev_driver, prev_combined, prev_constr


# ============================================================
# Main update process
# ============================================================
def update_round(year: int, rnd: int, event_row, conn) -> bool:
    """Update a single round. Returns True if round was added/updated."""
    circuit = event_row.get("Location")
    date_val = safe_date(event_row.get("EventDate"))
    name = event_row.get("EventName", f"Round {rnd}")

    # Ensure race row exists
    cur = conn.cursor()
    cur.execute("SELECT race_id FROM Race WHERE year=? AND round=?", (year, rnd))
    row = cur.fetchone()
    if not row:
        print("🆕 Inserting race metadata...")
        cur.execute(
            "INSERT OR IGNORE INTO Race (year, round, name, circuit, date) VALUES (?, ?, ?, ?, ?)",
            (year, rnd, name, circuit, date_val),
        )
        conn.commit()
        cur.execute("SELECT race_id FROM Race WHERE year=? AND round=?", (year, rnd))
        row = cur.fetchone()
    race_id = row[0]

    # If already populated, skip
    cur.execute("SELECT COUNT(*) FROM Driver_Race WHERE race_id=?", (race_id,))
    if cur.fetchone()[0] > 0:
        return False

    # Load session data for this round
    print(f"📡 Loading FastF1 session data for Round {rnd} ({name})...")
    round_df = get_session(year, rnd)
    if round_df is None or round_df.empty:
        print(f"✖ No session data found for Round {rnd}.")
        return False

    # ----------------------------------------------------------
    # Insert/ensure driver, constructor
    # ----------------------------------------------------------
    for _, r in round_df.iterrows():
        # Driver code (must be NOT NULL in schema)
        code_raw = (r.get("DriverId") or "").strip()
        if not code_raw:
            # fallback: build a pseudo-code from name (still unique-ish)
            first = (r.get("FirstName") or "").strip()
            last = (r.get("LastName") or "").strip()
            code_raw = (last[:3] or first[:3] or "UNK").upper()

        first = (r.get("FirstName") or "").strip() or None
        last = (r.get("LastName") or "").strip() or None
        headshot = r.get("DriverUrl")
        country = r.get("CountryName")

        # Upsert driver by code
        cur.execute("SELECT driver_id FROM Driver WHERE code=?", (code_raw,))
        drv_row = cur.fetchone()
        if not drv_row:
            cur.execute(
                """
                INSERT INTO Driver (code, first_name, last_name, headshot, country)
                VALUES (?, ?, ?, ?, ?)
                """,
                (code_raw, first, last, headshot, country),
            )
            driver_id = cur.lastrowid
        else:
            driver_id = drv_row[0]

        # Constructor
        cname = r.get("ConstructorName")
        cur.execute("INSERT OR IGNORE INTO Constructor (name) VALUES (?)", (cname,))
        cur.execute("SELECT constructor_id FROM Constructor WHERE name=?", (cname,))
        constructor_id = cur.fetchone()[0]

        # Constructor_Race placeholder (Elo to be updated later)
        cur.execute(
            """
            INSERT OR IGNORE INTO Constructor_Race (constructor_id, race_id, elo)
            VALUES (?, ?, ?)
            """,
            (constructor_id, race_id, None),
        )

        # Driver_Race
        cur.execute(
            """
            INSERT OR IGNORE INTO Driver_Race (
                driver_id, constructor_id, race_id,
                GridPosition, Laps, RaceTime, Status,
                Q1, Q2, Q3, qualifying_position,
                position, points, elo, combined_elo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                driver_id,
                constructor_id,
                race_id,
                safe_int(r.get("GridPosition")),
                safe_int(r.get("Laps")),
                format_quali_time(r.get("RaceTime")),
                r.get("Status"),
                format_quali_time(r.get("Q1")),
                format_quali_time(r.get("Q2")),
                format_quali_time(r.get("Q3")),
                safe_int(r.get("QualifyingPosition")),
                safe_int(r.get("RacePosition")),
                safe_int(r.get("Points")),
                None,
                None,
            ),
        )

    conn.commit()

    # =======================================================
    # ELO UPDATES (keyed by DriverId / ConstructorName)
    # =======================================================
    print(f"⚙️ Calculating Elo for Round {rnd}...")
    prev_driver, prev_combined, prev_constr = get_existing_elos(conn, year)

    # driver elo
    new_driver_elo = add_elo_rating(year, rnd, prev_driver.copy(), "DriverId", None, round_df)

    # constructor elo
    new_constr_elo = add_elo_rating(year, rnd, prev_constr.copy(), "ConstructorName", None, round_df)

    # combined driver elo uses constructor K-modifiers
    new_combined_elo = add_elo_rating(
        year, rnd, prev_combined.copy(), "DriverId", new_constr_elo[["ConstructorName", rnd]], round_df
    )

    # Write Elo back
    for _, row_d in new_driver_elo.reset_index().iterrows():
        code = row_d.get("DriverId")
        if not code:
            continue
        cur.execute(
            """
            UPDATE Driver_Race
            SET elo = ?
            WHERE race_id = ?
              AND driver_id = (SELECT driver_id FROM Driver WHERE code = ?)
            """,
            (safe_int(row_d.get(rnd)), race_id, code),
        )

    for _, row_c in new_constr_elo.reset_index().iterrows():
        cname = row_c.get("ConstructorName")
        if not cname:
            continue
        cur.execute(
            """
            UPDATE Constructor_Race
            SET elo = ?
            WHERE race_id = ?
              AND constructor_id = (SELECT constructor_id FROM Constructor WHERE name = ?)
            """,
            (safe_int(row_c.get(rnd)), race_id, cname),
        )

    for _, row_cmb in new_combined_elo.reset_index().iterrows():
        code = row_cmb.get("DriverId")
        if not code:
            continue
        cur.execute(
            """
            UPDATE Driver_Race
            SET combined_elo = ?
            WHERE race_id = ?
              AND driver_id = (SELECT driver_id FROM Driver WHERE code = ?)
            """,
            (safe_int(row_cmb.get(rnd)), race_id, code),
        )

    conn.commit()
    print("✅ Elo ratings updated.")

    # =======================================================
    # TYRE DEGRADATION (match by driver code)
    # =======================================================
    print(f"🛞 Calculating tyre degradation for Round {rnd}...")
    try:
        ensure_deg_column(cur)
        try:
            deg_df, source = calculate_tire_degradation(year, rnd)
        except Exception as e:
            print(f"❌ Error calculating degradation for round {rnd}: {e}")
            return True  # Race was still added

        if deg_df is None or deg_df.empty:
            print("⚠️ No usable degradation data.")
        else:
            updated = 0
            for _, row in deg_df.iterrows():
                first = str(row.get("FirstName") or "").strip()
                last = str(row.get("LastName") or "").strip()
                deg = row.get("AvgDegPerLap")

                if not first or not last or pd.isna(deg):
                    continue

                cur.execute(
                    """
                    UPDATE Driver_Race
                    SET avg_tire_deg_per_lap = ?
                    WHERE race_id = ?
                      AND driver_id = (
                          SELECT driver_id FROM Driver
                          WHERE lower(first_name)=lower(?) AND lower(last_name)=lower(?)
                      )
                    """,
                    (float(deg), race_id, first, last),
                )
                updated += cur.rowcount

            conn.commit()
            print(f"✅ Updated degradation for {updated} drivers (source: {source})")

    except Exception as e:
        print(f"❌ Tyre degradation failed: {e}")

    print(f"🎯 Update complete for Round {rnd} – {name}")
    return True


def update_all_missing_rounds(year: int):
    """Find and add all missing rounds for the year (backfills gaps)."""
    print(f"\n=== Checking {year} season for missing rounds ===")

    schedule = getRaces(year)
    # Make EventDate tz-aware (UTC) to compare with 'now' safely in CI
    event_dates = pd.to_datetime(schedule["EventDate"], utc=True)
    now = datetime.now(timezone.utc)

    past_rounds = schedule[(schedule["RoundNumber"] > 0) & (event_dates <= now)]
    if past_rounds.empty:
        print("No past races yet this season.")
        return

    # Sort by round number - process in order for correct ELO chaining
    past_rounds = past_rounds.sort_values("RoundNumber").reset_index(drop=True)
    conn = sqlite3.connect(DB_FILE)

    added = 0
    for _, event_row in past_rounds.iterrows():
        rnd = int(event_row["RoundNumber"])
        name = event_row.get("EventName", f"Round {rnd}")

        # Quick check if round already has data
        cur = conn.cursor()
        cur.execute(
            "SELECT race_id FROM Race WHERE year=? AND round=?",
            (year, rnd),
        )
        race_row = cur.fetchone()
        if race_row:
            cur.execute("SELECT COUNT(*) FROM Driver_Race WHERE race_id=?", (race_row[0],))
            if cur.fetchone()[0] > 0:
                continue  # Already populated, skip

        print(f"\n🔎 Processing Round {rnd} – {name}")
        if update_round(year, rnd, event_row, conn):
            added += 1

    conn.close()
    if added > 0:
        print(f"\n✅ Added {added} missing round(s) for {year}.")
    else:
        print(f"\n✔ All {len(past_rounds)} past rounds for {year} already populated.")


def update_latest_round(year: int):
    """Legacy: update only the most recent round. Use update_all_missing_rounds for backfill."""
    print(f"\n=== Checking latest {year} round ===")

    schedule = getRaces(year)
    # Make EventDate tz-aware (UTC) to compare with 'now' safely in CI
    event_dates = pd.to_datetime(schedule["EventDate"], utc=True)
    now = datetime.now(timezone.utc)

    past_rounds = schedule[(schedule["RoundNumber"] > 0) & (event_dates <= now)]
    if past_rounds.empty:
        print("No past races yet this season.")
        return

    latest_event = past_rounds.iloc[-1]
    rnd = int(latest_event["RoundNumber"])
    circuit = latest_event.get("Location")
    date_val = safe_date(latest_event["EventDate"])
    name = latest_event.get("EventName", f"Round {rnd}")

    print(f"🔎 Latest race: Round {rnd} – {name} ({circuit}, {date_val})")

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Ensure race row exists
    cur.execute("SELECT race_id FROM Race WHERE year=? AND round=?", (year, rnd))
    row = cur.fetchone()
    if not row:
        print("🆕 Inserting race metadata...")
        cur.execute(
            "INSERT OR IGNORE INTO Race (year, round, name, circuit, date) VALUES (?, ?, ?, ?, ?)",
            (year, rnd, name, circuit, date_val),
        )
        conn.commit()
        cur.execute("SELECT race_id FROM Race WHERE year=? AND round=?", (year, rnd))
        row = cur.fetchone()
    race_id = row[0]

    # If already populated, skip
    cur.execute("SELECT COUNT(*) FROM Driver_Race WHERE race_id=?", (race_id,))
    if cur.fetchone()[0] > 0:
        print(f"✔ Round {rnd} already populated.")
        conn.close()
        return

    # Load session data for this round
    print("📡 Loading latest FastF1 session data...")
    round_df = get_session(year, rnd)
    if round_df is None or round_df.empty:
        print("✖ No session data found.")
        conn.close()
        return

    # ----------------------------------------------------------
    # Insert/ensure driver, constructor
    # ----------------------------------------------------------
    for _, r in round_df.iterrows():
        # Driver code (must be NOT NULL in schema)
        code_raw = (r.get("DriverId") or "").strip()
        if not code_raw:
            # fallback: build a pseudo-code from name (still unique-ish)
            first = (r.get("FirstName") or "").strip()
            last = (r.get("LastName") or "").strip()
            code_raw = (last[:3] or first[:3] or "UNK").upper()

        first = (r.get("FirstName") or "").strip() or None
        last = (r.get("LastName") or "").strip() or None
        headshot = r.get("DriverUrl")
        country = r.get("CountryName")

        # Upsert driver by code
        cur.execute("SELECT driver_id FROM Driver WHERE code=?", (code_raw,))
        drv_row = cur.fetchone()
        if not drv_row:
            cur.execute(
                """
                INSERT INTO Driver (code, first_name, last_name, headshot, country)
                VALUES (?, ?, ?, ?, ?)
                """,
                (code_raw, first, last, headshot, country),
            )
            driver_id = cur.lastrowid
        else:
            driver_id = drv_row[0]

        # Constructor
        cname = r.get("ConstructorName")
        cur.execute("INSERT OR IGNORE INTO Constructor (name) VALUES (?)", (cname,))
        cur.execute("SELECT constructor_id FROM Constructor WHERE name=?", (cname,))
        constructor_id = cur.fetchone()[0]

        # Constructor_Race placeholder (Elo to be updated later)
        cur.execute(
            """
            INSERT OR IGNORE INTO Constructor_Race (constructor_id, race_id, elo)
            VALUES (?, ?, ?)
            """,
            (constructor_id, race_id, None),
        )

        # Driver_Race
        cur.execute(
            """
            INSERT OR IGNORE INTO Driver_Race (
                driver_id, constructor_id, race_id,
                GridPosition, Laps, RaceTime, Status,
                Q1, Q2, Q3, qualifying_position,
                position, points, elo, combined_elo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                driver_id,
                constructor_id,
                race_id,
                safe_int(r.get("GridPosition")),
                safe_int(r.get("Laps")),
                format_quali_time(r.get("RaceTime")),
                r.get("Status"),
                format_quali_time(r.get("Q1")),
                format_quali_time(r.get("Q2")),
                format_quali_time(r.get("Q3")),
                safe_int(r.get("QualifyingPosition")),
                safe_int(r.get("RacePosition")),
                safe_int(r.get("Points")),
                None,
                None,
            ),
        )

    conn.commit()

    # =======================================================
    # ELO UPDATES (keyed by DriverId / ConstructorName)
    # =======================================================
    print(f"⚙️ Calculating Elo for Round {rnd}...")
    prev_driver, prev_combined, prev_constr = get_existing_elos(conn, year)

    # driver elo
    new_driver_elo = add_elo_rating(year, rnd, prev_driver.copy(), "DriverId", None, round_df)

    # constructor elo
    new_constr_elo = add_elo_rating(year, rnd, prev_constr.copy(), "ConstructorName", None, round_df)

    # combined driver elo uses constructor K-modifiers
    new_combined_elo = add_elo_rating(
        year, rnd, prev_combined.copy(), "DriverId", new_constr_elo[["ConstructorName", rnd]], round_df
    )

    # Write Elo back
    for _, row_d in new_driver_elo.reset_index().iterrows():
        code = row_d.get("DriverId")
        if not code:
            continue
        cur.execute(
            """
            UPDATE Driver_Race
            SET elo = ?
            WHERE race_id = ?
              AND driver_id = (SELECT driver_id FROM Driver WHERE code = ?)
            """,
            (safe_int(row_d.get(rnd)), race_id, code),
        )

    for _, row_c in new_constr_elo.reset_index().iterrows():
        cname = row_c.get("ConstructorName")
        if not cname:
            continue
        cur.execute(
            """
            UPDATE Constructor_Race
            SET elo = ?
            WHERE race_id = ?
              AND constructor_id = (SELECT constructor_id FROM Constructor WHERE name = ?)
            """,
            (safe_int(row_c.get(rnd)), race_id, cname),
        )

    for _, row_cmb in new_combined_elo.reset_index().iterrows():
        code = row_cmb.get("DriverId")
        if not code:
            continue
        cur.execute(
            """
            UPDATE Driver_Race
            SET combined_elo = ?
            WHERE race_id = ?
              AND driver_id = (SELECT driver_id FROM Driver WHERE code = ?)
            """,
            (safe_int(row_cmb.get(rnd)), race_id, code),
        )

    conn.commit()
    print("✅ Elo ratings updated.")

    # =======================================================
    # TYRE DEGRADATION (match by driver code)
    # =======================================================
    print(f"🛞 Calculating tyre degradation for Round {rnd}...")
    try:
        ensure_deg_column(cur)
        try:
            deg_df, source = calculate_tire_degradation(year, rnd)
        except Exception as e:
            print(f"❌ Error calculating degradation for round {rnd}: {e}")
            conn.close()
            return

        if deg_df is None or deg_df.empty:
            print("⚠️ No usable degradation data.")
            conn.close()
            return

        updated = 0
        for _, row in deg_df.iterrows():
            first = str(row.get("FirstName") or "").strip()
            last = str(row.get("LastName") or "").strip()
            deg = row.get("AvgDegPerLap")

            if not first or not last or pd.isna(deg):
                continue

            cur.execute(
                """
                UPDATE Driver_Race
                SET avg_tire_deg_per_lap = ?
                WHERE race_id = ?
                  AND driver_id = (
                      SELECT driver_id FROM Driver
                      WHERE lower(first_name)=lower(?) AND lower(last_name)=lower(?)
                  )
                """,
                (float(deg), race_id, first, last),
            )
            updated += cur.rowcount

        conn.commit()
        print(f"✅ Updated degradation for {updated} drivers (source: {source})")

    except Exception as e:
        print(f"❌ Tyre degradation failed: {e}")

    conn.close()
    print(f"🎯 Update complete for Round {rnd} – {name}")


def clear_year(year: int):
    """Delete all race data for a given year (Driver_Race, Constructor_Race, Race)."""
    print(f"\n=== Clearing all data for {year} ===")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Get race_ids for this year
    cur.execute("SELECT race_id FROM Race WHERE year = ?", (year,))
    race_ids = [r[0] for r in cur.fetchall()]

    if not race_ids:
        print(f"No {year} data found in database.")
        conn.close()
        return

    placeholders = ",".join("?" * len(race_ids))

    cur.execute(f"DELETE FROM Driver_Race WHERE race_id IN ({placeholders})", race_ids)
    dr_deleted = cur.rowcount

    cur.execute(f"DELETE FROM Constructor_Race WHERE race_id IN ({placeholders})", race_ids)
    cr_deleted = cur.rowcount

    cur.execute("DELETE FROM Race WHERE year = ?", (year,))
    race_deleted = cur.rowcount

    conn.commit()
    conn.close()
    print(f"✅ Deleted {dr_deleted} Driver_Race, {cr_deleted} Constructor_Race, {race_deleted} Race rows for {year}.")


if __name__ == "__main__":
    import sys
    current_year = datetime.now().year

    if "--clear-year" in sys.argv:
        idx = sys.argv.index("--clear-year")
        if idx + 1 < len(sys.argv):
            year = int(sys.argv[idx + 1])
            clear_year(year)
            print(f"\nRepopulating {year}...")
            update_all_missing_rounds(year)
        else:
            print("Usage: python app/api_retrival/update.py --clear-year 2026")
    else:
        update_all_missing_rounds(current_year)

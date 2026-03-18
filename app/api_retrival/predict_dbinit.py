import os
import sqlite3
from datetime import datetime

# ==========================
# Setup
# ==========================
DB_PATH = "app/api_retrival/database"
os.makedirs(DB_PATH, exist_ok=True)
DB_FILE = os.path.join(DB_PATH, "f1_data.db")


def create_all_tables():
    """Create the core F1 tables and prediction table if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.executescript("""
    -- ==========================
    -- Core F1 Schema
    -- ==========================

    CREATE TABLE IF NOT EXISTS Driver (
        driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        headshot TEXT,
        country TEXT
    );

    CREATE TABLE IF NOT EXISTS Constructor (
        constructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Race (
        race_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        year INTEGER NOT NULL,
        round INTEGER NOT NULL,
        name TEXT NOT NULL,
        circuit TEXT,
        date DATE
    );

    CREATE TABLE IF NOT EXISTS Constructor_Race (
        constructor_race_id INTEGER PRIMARY KEY AUTOINCREMENT,
        constructor_id INTEGER NOT NULL,
        race_id INTEGER NOT NULL,
        elo INTEGER,
        UNIQUE(constructor_id, race_id),
        FOREIGN KEY (constructor_id) REFERENCES Constructor(constructor_id),
        FOREIGN KEY (race_id) REFERENCES Race(race_id)
    );

    CREATE TABLE IF NOT EXISTS Driver_Race (
        driver_race_id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        constructor_id INTEGER NOT NULL,
        race_id INTEGER NOT NULL,
        GridPosition INTEGER,
        Laps INTEGER,
        RaceTime TEXT,
        Status TEXT,
        Q1 TEXT,
        Q2 TEXT,
        Q3 TEXT,
        qualifying_position INTEGER,
        position INTEGER,
        points INTEGER,
        elo INTEGER,
        combined_elo INTEGER,
        avg_tire_deg_per_lap REAL,
        FOREIGN KEY (driver_id) REFERENCES Driver(driver_id),
        FOREIGN KEY (constructor_id) REFERENCES Constructor(constructor_id),
        FOREIGN KEY (race_id) REFERENCES Race(race_id)
    );

    CREATE TABLE IF NOT EXISTS Advanced (
        advanced_race_id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_race_id INTEGER NOT NULL,
        avg_lap_time TEXT,
        qualifying_time REAL,
        sector1 REAL,
        sector2 REAL,
        sector3 REAL,
        model_used TEXT,
        FOREIGN KEY (driver_race_id) REFERENCES Driver_Race(driver_race_id)
    );

    -- ==========================
    -- Predictions Table
    -- ==========================

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
    );

    """)

    conn.commit()
    conn.close()
    print(f"✅ Database schema created at {DB_FILE}")


if __name__ == "__main__":
    print("Initializing F1 database structure...")
    create_all_tables()
    print("✔ All tables created successfully.")

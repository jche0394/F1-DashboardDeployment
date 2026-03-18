import sqlite3
from flask import Flask, jsonify
from flask_cors import CORS
import os
import pandas as pd



app = Flask(__name__)
# Enable CORS to allow your React app to make requests to this backend
CORS(app) 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Join that path with the relative path to the database

DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'f1_data.db')

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    # This makes the database return rows as dictionary-like objects
    conn.row_factory = sqlite3.Row 
    return conn

# --- API Endpoint to Get All Drivers ---
@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    """Fetches all drivers from the Driver table and returns them as JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Execute a query to select all drivers
        cursor.execute("SELECT * FROM Driver")
        drivers = cursor.fetchall()
        conn.close()
        
        # Convert the database rows to a list of dictionaries
        # This makes it easy to convert to JSON
        drivers_list = [dict(row) for row in drivers]
        
        return jsonify(drivers_list)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Return an error response
        return jsonify({"error": "Failed to retrieve data from the database"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/driver_race/<int:year>', methods=['GET'])
def get_driver_race(year):
    """Fetches all driver race from the Driver table and returns them as JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * From Driver_Race INNER JOIN Race ON Driver_Race.race_id = Race.race_id WHERE year = ?;"
        cursor.execute(query, (year,))

        drivers = cursor.fetchall()
        conn.close()
        
        # Convert the database rows to a list of dictionaries
        # This makes it easy to convert to JSON
        drivers_list = [dict(row) for row in drivers]
        
        return jsonify(drivers_list)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Return an error response
        return jsonify({"error": "Failed to retrieve data from the database"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    



@app.route('/api/constructor_race/<int:year>', methods=['GET'])
def get_constructor_race(year):
    """Fetches all driver race from the Driver table and returns them as JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * From Constructor_Race INNER JOIN Race ON Constructor_Race.race_id = Race.race_id WHERE year = ?;"
        cursor.execute(query, (year,))
        
        drivers = cursor.fetchall()
        conn.close()
        
        # Convert the database rows to a list of dictionaries
        # This makes it easy to convert to JSON
        drivers_list = [dict(row) for row in drivers]
        
        return jsonify(drivers_list)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Return an error response
        return jsonify({"error": "Failed to retrieve data from the database"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    

from flask import Flask, jsonify, request
import sqlite3

# Assume app is defined, e.g., app = Flask(__name__)
# Assume get_db_connection is defined to connect to your DB

# --- Helper function to convert cursor results to list of dicts ---
def rows_to_dict_list(cursor_rows):
    """Converts a list of sqlite3.Row objects to a list of dictionaries."""
    return [dict(row) for row in cursor_rows]

# ========================================
# Comparison Endpoints
# ========================================

@app.route('/api/drivers/compare/<int:driver1_id>/<int:driver2_id>', methods=['GET'])
def compare_drivers(driver1_id, driver2_id):
    """Fetches career stats and latest Elo for two drivers to compare them."""
    try:
        conn = get_db_connection()
        
        # Fetch basic info and latest race stats for each driver
        query = """
            SELECT
                d.first_name,
                d.last_name,
                d.country,
                dr.elo,
                dr.combined_elo,
                dr.position,
                dr.points,
                r.year,
                r.round,
                r.name as race_name
            FROM Driver d
            JOIN Driver_Race dr ON d.driver_id = dr.driver_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE d.driver_id = ?
            ORDER BY r.year DESC, r.round DESC
            LIMIT 1;
        """
        
        driver1_data = conn.execute(query, (driver1_id,)).fetchone()
        driver2_data = conn.execute(query, (driver2_id,)).fetchone()
        
        conn.close()

        if not driver1_data or not driver2_data:
            return jsonify({"error": "One or both drivers not found"}), 404

        response = {
            "driver1": dict(driver1_data),
            "driver2": dict(driver2_data)
        }
        
        return jsonify(response)
        
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/constructors/compare/<int:constructor1_id>/<int:constructor2_id>', methods=['GET'])
def compare_constructors(constructor1_id, constructor2_id):
    """Fetches latest Elo for two constructors to compare them."""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT
                c.name,
                cr.elo,
                r.year,
                r.round,
                r.name as race_name
            FROM Constructor c
            JOIN Constructor_Race cr ON c.constructor_id = cr.constructor_id
            JOIN Race r ON cr.race_id = r.race_id
            WHERE c.constructor_id = ?
            ORDER BY r.year DESC, r.round DESC
            LIMIT 1;
        """
        
        constructor1_data = conn.execute(query, (constructor1_id,)).fetchone()
        constructor2_data = conn.execute(query, (constructor2_id,)).fetchone()
        
        conn.close()

        if not constructor1_data or not constructor2_data:
            return jsonify({"error": "One or both constructors not found"}), 404

        response = {
            "constructor1": dict(constructor1_data),
            "constructor2": dict(constructor2_data)
        }
        
        return jsonify(response)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# ========================================
# Ranking & History Endpoints
# ========================================

@app.route('/api/rankings/drivers/elo', methods=['GET'])
def get_driver_elo_rankings():
    """
    Returns the latest Elo score for every driver, ranked highest to lowest.
    Can be filtered by season using query parameter: ?season=2023
    Can be filtered by specific race using: ?season=2023&race=5
    """
    try:
        year = request.args.get('season', type=int)
        round_num = request.args.get('race', type=int)
        
        conn = get_db_connection()
        
        if year and round_num:
            # Get rankings for a specific race
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name, d.code,
                    c.constructor_id, c.name as constructor_name, dr.elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN Race r ON dr.race_id = r.race_id
                WHERE r.year = ? AND r.round = ?
                ORDER BY dr.elo DESC;
            """
            drivers = conn.execute(query, (year, round_num)).fetchall()
        elif year:
            # Get rankings for a specific year (latest race of that year)
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name, d.code,
                    c.constructor_id, c.name as constructor_name, dr.elo
                FROM
                    Driver d
                JOIN
                    (SELECT
                        dr.driver_id, dr.constructor_id, dr.elo,
                        ROW_NUMBER() OVER(PARTITION BY dr.driver_id ORDER BY r.round DESC) as rn
                     FROM Driver_Race dr
                     JOIN Race r ON dr.race_id = r.race_id
                     WHERE r.year = ?) dr ON d.driver_id = dr.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                WHERE
                    dr.rn = 1
                ORDER BY
                    dr.elo DESC;
            """
            drivers = conn.execute(query, (year,)).fetchall()
        else:
            # Get latest rankings across all years
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name, d.code,
                    c.constructor_id, c.name as constructor_name, dr.elo
                FROM
                    Driver d
                JOIN
                    (SELECT
                        driver_id, constructor_id, elo,
                        ROW_NUMBER() OVER(PARTITION BY driver_id ORDER BY race_id DESC) as rn
                     FROM Driver_Race) dr ON d.driver_id = dr.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                WHERE
                    dr.rn = 1
                ORDER BY
                    dr.elo DESC;
            """
            drivers = conn.execute(query).fetchall()
        
        conn.close()
        
        return jsonify(rows_to_dict_list(drivers))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
        
@app.route('/api/rankings/drivers/elo/history/<int:driver_id>', methods=['GET'])
def get_driver_elo_history(driver_id):
    """
    Returns the full Elo history for a specific driver.
    Can be filtered by season using a query parameter, e.g., ?season=2023
    """
    try:
        year_filter = request.args.get('season', type=int)
        
        conn = get_db_connection()
        
        base_query = """
            SELECT
                r.year, r.round, r.name AS race_name, r.date, dr.elo
            FROM Driver_Race dr
            JOIN Race r ON dr.race_id = r.race_id
            WHERE dr.driver_id = ?
        """
        params = [driver_id]

        if year_filter:
            base_query += " AND r.year = ?"
            params.append(year_filter)
        
        base_query += " ORDER BY r.year, r.round;"

        history = conn.execute(base_query, tuple(params)).fetchall()
        conn.close()
        
        return jsonify(rows_to_dict_list(history))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@app.route('/api/rankings/constructors/elo/history/<int:constructor_id>', methods=['GET'])
def get_constructor_elo_history(constructor_id):
    """
    Returns the full Elo history for a specific constructor.
    Can be filtered by season using a query parameter, e.g., ?season=2023
    """
    try:
        year_filter = request.args.get('season', type=int)
        
        conn = get_db_connection()
        
        base_query = """
            SELECT
                r.year, r.round, r.name AS race_name, r.date, cr.elo
            FROM Constructor_Race cr
            JOIN Race r ON cr.race_id = r.race_id
            WHERE cr.constructor_id = ?
        """
        params = [constructor_id]

        if year_filter:
            base_query += " AND r.year = ?"
            params.append(year_filter)
        
        base_query += " ORDER BY r.year, r.round;"

        history = conn.execute(base_query, tuple(params)).fetchall()
        conn.close()
        
        return jsonify(rows_to_dict_list(history))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


@app.route('/api/rankings/combined', methods=['GET'])
def get_combined_elo_rankings():
    """
    Returns the latest combined driver-constructor Elo scores, ranked.
    Can be filtered by season using query parameter: ?season=2023
    Can be filtered by specific race using: ?season=2023&race=5
    """
    try:
        year = request.args.get('season', type=int)
        round_num = request.args.get('race', type=int)
        
        conn = get_db_connection()
        
        if year and round_num:
            # Get combined rankings for a specific race
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name,
                    c.constructor_id, c.name as constructor_name,
                    dr.combined_elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN Race r ON dr.race_id = r.race_id
                WHERE r.year = ? AND r.round = ?
                ORDER BY dr.combined_elo DESC;
            """
            rankings = conn.execute(query, (year, round_num)).fetchall()
        elif year:
            # Get combined rankings for a specific year (latest race of that year)
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name,
                    c.constructor_id, c.name as constructor_name,
                    dr.combined_elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN Race r ON dr.race_id = r.race_id
                JOIN (
                    SELECT dr.driver_id, MAX(r.round) as max_round
                    FROM Driver_Race dr
                    JOIN Race r ON dr.race_id = r.race_id
                    WHERE r.year = ?
                    GROUP BY dr.driver_id
                ) latest ON dr.driver_id = latest.driver_id AND r.round = latest.max_round
                WHERE r.year = ?
                ORDER BY dr.combined_elo DESC;
            """
            rankings = conn.execute(query, (year, year)).fetchall()
        else:
            # Get latest combined rankings across all years
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name,
                    c.constructor_id, c.name as constructor_name,
                    dr.combined_elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN (
                    SELECT driver_id, MAX(race_id) as max_race_id
                    FROM Driver_Race
                    GROUP BY driver_id
                ) latest ON dr.driver_id = latest.driver_id AND dr.race_id = latest.max_race_id
                ORDER BY dr.combined_elo DESC;
            """
            rankings = conn.execute(query).fetchall()
        
        conn.close()
        
        return jsonify(rows_to_dict_list(rankings))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# ========================================
# Utility Endpoints
# ========================================

@app.route('/api/years', methods=['GET'])
def get_available_years():
    """Returns all available years in the database."""
    try:
        conn = get_db_connection()
        query = "SELECT DISTINCT year FROM Race ORDER BY year DESC;"
        years = conn.execute(query).fetchall()
        conn.close()
        
        years_list = [row['year'] for row in years]
        return jsonify(years_list)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# ========================================
# Specific Race Elo Endpoints
# ========================================

@app.route('/api/rankings/constructors/elo', methods=['GET'])
def get_constructor_elo_by_race_query():
    """
    Returns constructor Elo for a specific race via query params.
    e.g., /api/rankings/constructors/elo?season=2023&race=5
    """
    year = request.args.get('season', type=int)
    round_num = request.args.get('race', type=int)
    
    if not year or not round_num:
        return jsonify({"error": "Both 'season' and 'race' query parameters are required."}), 400
        
    return get_elo_for_constructors_in_race(year, round_num)

# ========================================
# Path-based Elo Endpoints
# ========================================

@app.route('/api/elo/drivers/<int:year>/<int:round_num>', methods=['GET'])
def get_elo_for_drivers_in_race(year, round_num):
    """Returns the Elo for all drivers in a specific race."""
    try:
        conn = get_db_connection()
        query = """
            SELECT
                d.driver_id, d.first_name, d.last_name, d.code, dr.elo
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE r.year = ? AND r.round = ?
            ORDER BY dr.elo DESC;
        """
        drivers = conn.execute(query, (year, round_num)).fetchall()
        conn.close()
        
        return jsonify(rows_to_dict_list(drivers))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/elo/constructors/<int:year>/<int:round_num>', methods=['GET'])
def get_elo_for_constructors_in_race(year, round_num):
    """Returns the Elo for all constructors in a specific race."""
    try:
        conn = get_db_connection()
        query = """
            SELECT
                c.constructor_id, c.name, cr.elo
            FROM Constructor_Race cr
            JOIN Constructor c ON cr.constructor_id = c.constructor_id
            JOIN Race r ON cr.race_id = r.race_id
            WHERE r.year = ? AND r.round = ?
            ORDER BY cr.elo DESC;
        """
        constructors = conn.execute(query, (year, round_num)).fetchall()
        conn.close()
        
        return jsonify(rows_to_dict_list(constructors))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/elo/combined/<int:year>/<int:round_num>', methods=['GET'])
def get_combined_elo_for_race(year, round_num):
    """Returns the combined driver-constructor Elo for a specific race."""
    try:
        conn = get_db_connection()
        query = """
            SELECT
                d.driver_id, d.first_name, d.last_name,
                c.constructor_id, c.name as constructor_name,
                dr.combined_elo
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Constructor c ON dr.constructor_id = c.constructor_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE r.year = ? AND r.round = ?
            ORDER BY dr.combined_elo DESC;
        """
        results = conn.execute(query, (year, round_num)).fetchall()
        conn.close()
        
        return jsonify(rows_to_dict_list(results))

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# ========================================
# Race Predictions Endpoint (DB-based)
# ========================================
@app.route("/api/race_predict", methods=["GET"])
def race_predict_from_db():
    """Generate race predictions using stored qualifying + degradation data."""
    try:
        year = int(request.args.get("year", 2025))
        gp_name = request.args.get("gp_name")
        if not gp_name:
            return jsonify({"error": "Missing gp_name parameter"}), 400

        # --- Normalize the GP name ---
        def normalize_gp_name(name: str) -> str:
            mapping = {
                "Australia": "Australian Grand Prix",
                "China": "Chinese Grand Prix",
                "Japan": "Japanese Grand Prix",
                "Bahrain": "Bahrain Grand Prix",
                "Saudi Arabia": "Saudi Arabian Grand Prix",
                "Emilia Romagna": "Emilia Romagna Grand Prix",
                "Monaco": "Monaco Grand Prix",
                "Spain": "Spanish Grand Prix",
                "Canada": "Canadian Grand Prix",
                "Austria": "Austrian Grand Prix",
                "Great Britain": "British Grand Prix",
                "Belgium": "Belgian Grand Prix",
                "Hungary": "Hungarian Grand Prix",
                "Netherlands": "Dutch Grand Prix",
                "Italy": "Italian Grand Prix",
                "Azerbaijan": "Azerbaijan Grand Prix",
                "Singapore": "Singapore Grand Prix",
                "United States": "United States Grand Prix",
                "Mexico": "Mexico City Grand Prix",
                "Brazil": "São Paulo Grand Prix",
                "Qatar": "Qatar Grand Prix",
                "Abu Dhabi": "Abu Dhabi Grand Prix",
            }
            return mapping.get(name.strip(), name)

        normalized_name = normalize_gp_name(gp_name)

        # --- Query DB for qualifying + degradation data ---
        conn = get_db_connection()
        query = """
            SELECT 
                d.code AS DriverCode,
                d.first_name,
                d.last_name,
                c.name AS ConstructorName,
                dr.Q1, dr.Q2, dr.Q3,
                dr.qualifying_position,
                dr.avg_tire_deg_per_lap
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Constructor c ON dr.constructor_id = c.constructor_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE r.year = ? AND LOWER(r.name) LIKE LOWER(?)
            ORDER BY dr.qualifying_position
        """
        df = pd.read_sql_query(query, conn, params=(year, f"%{normalized_name}%"))
        conn.close()

        if df.empty:
            return jsonify({"detail": f"No qualifying data found for '{gp_name}' ({normalized_name}) {year}"}), 404

        # --- Combine names for display ---
        df["Driver"] = df.apply(lambda r: f"{r['first_name']} {r['last_name']}".strip(), axis=1)

        # --- Derive best qualifying time ---
        def best_time(row):
            for q in ["Q3", "Q2", "Q1"]:
                val = row.get(q)
                if val and val != "None":
                    try:
                        return pd.to_timedelta(val).total_seconds()
                    except Exception:
                        pass
            return None

        df["QualifyingTime (s)"] = df.apply(best_time, axis=1)
        df = df.dropna(subset=["QualifyingTime (s)"])

        # --- Prediction logic ---
        df["HasDegData"] = df["avg_tire_deg_per_lap"].notna()
        median_deg = df["avg_tire_deg_per_lap"].median(skipna=True)
        df["RelativeDeg"] = df["avg_tire_deg_per_lap"] - median_deg

        def adjust(row):
            if not row["HasDegData"]:
                return 0
            if row["RelativeDeg"] < 0:
                return -1  # better tyre management
            elif row["RelativeDeg"] > 0:
                return 1   # worse tyre management
            return 0

        df["PositionAdjustment"] = df.apply(adjust, axis=1)
        df["PredictedRacePosition"] = (
            df["qualifying_position"] + df["PositionAdjustment"]
        ).clip(1, len(df))
        df = df.sort_values("PredictedRacePosition").reset_index(drop=True)
        df["PredictedRacePosition"] = df.index + 1
        df["PredictionMethod"] = df.apply(
            lambda r: "qualifying_and_tire_deg" if r["HasDegData"] else "qualifying_only",
            axis=1,
        )

        # --- Save to Race_Predictions (optional) ---
        conn = sqlite3.connect(DATABASE_PATH)
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
                row["PredictedRacePosition"], row["avg_tire_deg_per_lap"],
                row["PredictionMethod"]
            ))
        conn.commit()
        conn.close()

        # --- JSON Response ---
        import math
        predictions = []
        for i, row in df.iterrows():
            tire_deg = row["avg_tire_deg_per_lap"]
            if isinstance(tire_deg, float) and (math.isnan(tire_deg) or math.isinf(tire_deg)):
                tire_deg = None
            predictions.append({
                "position": int(i + 1),
                "driver": row["Driver"],
                "driver_code": row["DriverCode"],
                "constructor_name": row["ConstructorName"],
                "qualifying_time": round(row["QualifyingTime (s)"], 3),
                "qualifying_position": int(row["qualifying_position"]),
                "predicted_race_position": int(row["PredictedRacePosition"]),
                "tire_deg_rate": round(tire_deg, 4) if tire_deg is not None else None,
                "prediction_method": row["PredictionMethod"],
            })

        return jsonify({
            "year": year,
            "gp_name": normalized_name,
            "predictions": predictions
        })

    except Exception as e:
        return jsonify({"error": f"Prediction generation failed: {e}"}), 500


@app.route("/api/available_races/<int:year>", methods=["GET"])
def get_available_races(year):
    """Return all race names for the given year that have qualifying data in the database."""
    try:
        conn = get_db_connection()
        query = """
            SELECT DISTINCT r.name AS race_name
            FROM Race r
            JOIN Driver_Race dr ON r.race_id = dr.race_id
            WHERE r.year = ?
              AND dr.qualifying_position IS NOT NULL
            ORDER BY r.round ASC;
        """
        df = pd.read_sql_query(query, conn, params=(year,))
        conn.close()

        races = df["race_name"].tolist()
        return jsonify(races)
    except Exception as e:
        return jsonify({"error": f"Failed to load available races: {e}"}), 500


# --- Run the Flask App ---
if __name__ == '__main__':
    # The host='0.0.0.0' makes the server accessible on your local network
    # The port can be any available port, 5000 is common for Flask
    app.run(host='0.0.0.0', port=5001, debug=True)

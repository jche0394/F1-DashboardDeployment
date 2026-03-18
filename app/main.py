from flask import Flask, jsonify, request
from flask_cors import CORS
import fastf1
import fastf1.ergast
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3

# Setup FastF1 cache
os.makedirs("f1_cache", exist_ok=True)
fastf1.Cache.enable_cache("f1_cache")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Ergast API
ergast = fastf1.ergast.Ergast()

# Database configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'api_retrival', 'database', 'f1_data.db')

# 2025 F1 grid for race predictions
drivers_2025 = {
    "Max Verstappen": "VER",
    "Charles Leclerc": "LEC",
    "Carlos Sainz Jr.": "SAI",
    "Lewis Hamilton": "HAM",
    "George Russell": "RUS",
    "Lando Norris": "NOR",
    "Oscar Piastri": "PIA",
    "Fernando Alonso": "ALO",
    "Lance Stroll": "STR",
    "Esteban Ocon": "OCO",
    "Pierre Gasly": "GAS",
    "Yuki Tsunoda": "TSU",
    "Alexander Albon": "ALB",
    "Nico Hülkenberg": "HUL",
    "Andrea Kimi Antonelli": "ANT",
    "Oliver Bearman": "BEA",
    "Franco Colapinto": "COL",
    "Gabriel Bortoleto": "BOR",
    "Isack Hadjar": "HAD",
    "Liam Lawson": "LAW"
}

# Reverse mapping: driver code -> full name (fallback for when FastF1 doesn't provide FullName)
driver_code_to_name = {v: k for k, v in drivers_2025.items()}

# Race predictions only supported for current season
def get_current_year():
    return datetime.now().year

# ========================================
# Dynamic race validation (multi-year support)
# ========================================
def _gp_name_matches(gp_name: str, valid_races: list) -> bool:
    """Check if gp_name matches any valid race (exact or common variants like 'X Grand Prix')."""
    if not gp_name or not valid_races:
        return False
    gp = gp_name.strip()
    valid_set = {str(v).strip() for v in valid_races}
    if gp in valid_set:
        return True
    # "Bahrain Grand Prix" matches valid "Bahrain"
    normalized = gp.replace(" Grand Prix", "").strip()
    if normalized in valid_set:
        return True
    # "Bahrain" matches valid "Bahrain Grand Prix"
    for v in valid_set:
        if v + " Grand Prix" == gp or v == gp:
            return True
    return False


def get_valid_race_names_for_year(year: int):
    """Fetch valid race/event names. Returns EventName only, one per round. Never Location or Country."""
    try:
        schedule = fastf1.get_event_schedule(year)
        schedule = schedule[~schedule["EventName"].str.contains("Testing", case=False, na=False)]
        if "RoundNumber" in schedule.columns:
            schedule = schedule.sort_values("RoundNumber")
            # One row per round: take EventName from first row of each round (avoids any session duplicates)
            schedule = schedule.drop_duplicates(subset=["RoundNumber"], keep="first")
        names = schedule["EventName"].tolist()
        # Ensure only EventName format (excludes Location/Country if ever present)
        return [str(n).strip() for n in names if n and "Grand Prix" in str(n)]
    except Exception:
        return []


# ========================================
# Database Helper Functions
# ========================================
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def rows_to_dict_list(cursor_rows):
    """Converts a list of sqlite3.Row objects to a list of dictionaries."""
    return [dict(row) for row in cursor_rows]

# ========================================
# Race Prediction Helper Functions
# ========================================
def load_session(year: int, gp_name: str, kind: str):
    """Load a FastF1 session"""
    sess = fastf1.get_session(year, gp_name, kind)
    sess.load()
    return sess

def get_qualifying_times_for_prediction(year: int, gp_name: str):
    """Fetch qualifying times from FastF1"""
    try:
        sess = load_session(year, gp_name, "Q")
        results = sess.results
        
        if results is None or len(results) == 0:
            return None, "Qualifying data is not available yet. The qualifying session may not have occurred."
        
        qual_data = []
        for _, row in results.iterrows():
            driver_code = row.get("Abbreviation")
            q3_time = row.get("Q3")
            q2_time = row.get("Q2")
            q1_time = row.get("Q1")
            
            best_time = q3_time if pd.notna(q3_time) else (q2_time if pd.notna(q2_time) else q1_time)
            
            if pd.notna(best_time) and driver_code:
                driver_name = row.get("FullName") if pd.notna(row.get("FullName")) else driver_code_to_name.get(driver_code, driver_code)
                team_name = row.get("TeamName") if pd.notna(row.get("TeamName")) else None
                qual_data.append({
                    "Driver": driver_name,
                    "DriverCode": driver_code,
                    "QualifyingTime (s)": best_time.total_seconds(),
                    "TeamName": team_name
                })
        
        if len(qual_data) == 0:
            return None, "No valid qualifying times found. The qualifying session may not have occurred yet."
        
        df = pd.DataFrame(qual_data)
        df = df.sort_values("QualifyingTime (s)").reset_index(drop=True)
        df["QualifyingPosition"] = df.index + 1
        
        return df, None
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "cannot find" in error_msg or "no round" in error_msg or "invalid event" in error_msg or "not found" in error_msg or "no session" in error_msg:
            return None, f"Circuit or race '{gp_name}' does not exist in {year}. Please check the race name is correct."
        else:
            return None, f"Unable to load qualifying data: {str(e)}"

def calculate_tire_degradation(year: int, gp_name: str):
    """Calculate tire degradation rate from practice sessions or sprint race"""
    # Try sprint race first
    try:
        sprint = load_session(year, gp_name, "S")
        return calculate_deg_from_session(sprint, is_sprint=True)
    except:
        pass
    
    # Try FP2
    try:
        fp2 = load_session(year, gp_name, "FP2")
        return calculate_deg_from_session(fp2, is_sprint=False)
    except:
        pass
    
    # Fall back to FP3
    try:
        fp3 = load_session(year, gp_name, "FP3")
        return calculate_deg_from_session(fp3, is_sprint=False)
    except:
        return pd.DataFrame(columns=['DriverCode', 'AvgDegPerLap'])

def calculate_deg_from_session(session, is_sprint: bool):
    """Calculate degradation from a session (practice or sprint)"""
    laps = session.laps.copy()
    
    # Build driver number/id -> abbreviation map so deg_data uses same codes as qualifying
    driver_to_abbr = {}
    if hasattr(session, "results") and session.results is not None and len(session.results) > 0:
        for _, row in session.results.iterrows():
            num = row.get("DriverNumber")
            abbr = row.get("Abbreviation")
            if pd.notna(num) and pd.notna(abbr):
                driver_to_abbr[str(num)] = str(abbr)
                driver_to_abbr[int(num)] = str(abbr)
    
    def to_driver_code(driver_id):
        if driver_id in driver_to_abbr:
            return driver_to_abbr[driver_id]
        if str(driver_id) in driver_to_abbr:
            return driver_to_abbr[str(driver_id)]
        return driver_id  # fallback: already abbreviation in some FastF1 versions
    
    if not is_sprint:
        race_compounds = ['MEDIUM', 'HARD']
        laps = laps[laps['Compound'].isin(race_compounds)]
    
    laps = laps[pd.notna(laps['LapTime'])]
    laps['LapTime (s)'] = laps['LapTime'].dt.total_seconds()
    
    # Prefer DriverNumber (reliable) over Driver (may be number or abbreviation depending on FastF1 version)
    driver_col = "DriverNumber" if "DriverNumber" in laps.columns else "Driver"
    
    deg_data = []
    min_stint_length = 5 if is_sprint else 7
    
    for driver_id in laps[driver_col].unique():
        driver_code = to_driver_code(driver_id)
        driver_laps = laps[laps[driver_col] == driver_id].copy()
        
        for stint in driver_laps['Stint'].unique():
            stint_laps = driver_laps[driver_laps['Stint'] == stint].sort_values('LapNumber')
            
            if len(stint_laps) >= min_stint_length:
                if is_sprint:
                    usable_laps = stint_laps.iloc[1:]
                else:
                    usable_laps = stint_laps.iloc[1:-1]
                
                if len(usable_laps) >= 6:
                    early_laps = usable_laps.iloc[:3]['LapTime (s)'].mean()
                    late_laps = usable_laps.iloc[-3:]['LapTime (s)'].mean()
                    
                    num_laps = len(usable_laps) - 3
                    deg_per_lap = (late_laps - early_laps) / num_laps if num_laps > 0 else 0
                    
                    deg_data.append({
                        'DriverCode': driver_code,
                        'DegPerLap': deg_per_lap,
                        'StintLength': len(usable_laps),
                        'Compound': stint_laps.iloc[0]['Compound'] if 'Compound' in stint_laps.columns else 'UNKNOWN'
                    })
    
    if len(deg_data) == 0:
        return pd.DataFrame(columns=['DriverCode', 'AvgDegPerLap'])
    
    deg_df = pd.DataFrame(deg_data)
    avg_deg = deg_df.groupby('DriverCode')['DegPerLap'].mean().reset_index()
    avg_deg.columns = ['DriverCode', 'AvgDegPerLap']
    
    return avg_deg

def predict_race_positions(year: int, gp_name: str, qualifying_times: pd.DataFrame):
    """Predict race finishing positions based on qualifying + tire degradation"""
    deg_data = calculate_tire_degradation(year, gp_name)
    
    predictions = qualifying_times.merge(deg_data, on='DriverCode', how='left')
    predictions['HasDegData'] = predictions['DriverCode'].isin(deg_data['DriverCode'])
    
    if len(deg_data) > 0 and predictions['HasDegData'].sum() > 0:
        drivers_with_deg = predictions[predictions['HasDegData']].copy()
        median_deg = drivers_with_deg['AvgDegPerLap'].median()
        
        predictions['RelativeDeg'] = predictions['AvgDegPerLap'] - median_deg
        
        if predictions['HasDegData'].sum() >= 4:
            deg_25th = drivers_with_deg['AvgDegPerLap'].quantile(0.25)
            deg_75th = drivers_with_deg['AvgDegPerLap'].quantile(0.75)
            
            def calculate_position_adjustment(row):
                if not row['HasDegData']:
                    return 0
                
                deg = row['AvgDegPerLap']
                
                if deg <= deg_25th:
                    improvement = (deg_25th - deg) / (median_deg - deg_25th) if median_deg != deg_25th else 1
                    return -min(3, max(1, int(improvement * 3)))
                
                elif deg >= deg_75th:
                    decline = (deg - deg_75th) / (deg_75th - median_deg) if deg_75th != median_deg else 1
                    return min(3, max(1, int(decline * 3)))
                
                else:
                    return 0
            
            predictions['PositionAdjustment'] = predictions.apply(calculate_position_adjustment, axis=1)
        else:
            predictions['PositionAdjustment'] = 0
            predictions.loc[predictions['HasDegData'], 'PositionAdjustment'] = predictions.loc[
                predictions['HasDegData'], 'RelativeDeg'
            ].apply(lambda x: min(2, max(-2, int(x * 10))))
    else:
        predictions['AvgDegPerLap'] = None
        predictions['RelativeDeg'] = 0
        predictions['PositionAdjustment'] = 0
    
    predictions['PredictedRacePosition'] = predictions['QualifyingPosition'] + predictions['PositionAdjustment']
    predictions['PredictedRacePosition'] = predictions['PredictedRacePosition'].clip(
        lower=predictions['QualifyingPosition'] - 3,
        upper=predictions['QualifyingPosition'] + 3
    )
    
    predictions['PredictedRacePosition'] = predictions['PredictedRacePosition'].clip(1, len(predictions))
    
    predictions = predictions.sort_values(['PredictedRacePosition', 'QualifyingPosition']).reset_index(drop=True)
    
    seen_positions = {}
    for idx, row in predictions.iterrows():
        pos = int(row['PredictedRacePosition'])
        if pos in seen_positions:
            while pos in seen_positions and pos <= len(predictions):
                pos += 1
            predictions.at[idx, 'PredictedRacePosition'] = pos
        seen_positions[pos] = True
    
    predictions = predictions.sort_values('PredictedRacePosition').reset_index(drop=True)
    predictions['PredictedRacePosition'] = predictions.index + 1
    
    predictions['PredictionMethod'] = predictions.apply(
        lambda row: 'qualifying_and_tire_deg' if row['HasDegData'] else 'qualifying_only',
        axis=1
    )
    
    return predictions

# ========================================
# Health Check
# ========================================
# Build identifier - increment when deploying; verify at /api/health to confirm latest code is live
API_BUILD_ID = '2026-03-predictions'

@app.route('/', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'build': API_BUILD_ID,
        'timestamp': datetime.now().isoformat(),
        'message': 'F1 Dashboard API - Combined Backend',
        'endpoints': {
            'ergast': ['/api/driver-standings', '/api/constructor-standings', '/api/season-schedule'],
            'database': ['/api/drivers', '/api/rankings/drivers/elo', '/api/comparisons'],
            'predictions': ['/api/available_races/<year>', '/api/race_predict']
        }
    })

# ========================================
# Ergast API Endpoints (from main.py)
# ========================================
@app.route('/api/driver-standings', methods=['GET'])
def get_driver_standings():
    try:
        year = request.args.get('year', 'current')
        response = ergast.get_driver_standings(year)
        
        if response.content and len(response.content) > 0:
            df = response.content[0]
            
            formatted_standings = []
            for _, row in df.iterrows():
                formatted_standings.append({
                    'position': int(row.get('position', 0)),
                    'points': float(row.get('points', 0)),
                    'Driver': {
                        'driverId': row.get('driverId', ''),
                        'givenName': row.get('givenName', ''),
                        'familyName': row.get('familyName', '')
                    },
                    'Constructor': {
                        'constructorId': row.get('constructorId', ''),
                        'name': row.get('constructorNames', [''])[0] if row.get('constructorNames') else ''
                    }
                })
            
            return jsonify({
                'MRData': {
                    'StandingsTable': {
                        'StandingsLists': [{
                            'DriverStandings': formatted_standings
                        }]
                    }
                }
            })
        else:
            return jsonify({'error': 'No data available'}), 404
            
    except Exception as e:
        print(f"Error in driver standings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/constructor-standings', methods=['GET'])
def get_constructor_standings():
    try:
        year = request.args.get('year', 'current')
        response = ergast.get_constructor_standings(year)
        
        if response.content and len(response.content) > 0:
            df = response.content[0]
            
            formatted_standings = []
            for _, row in df.iterrows():
                formatted_standings.append({
                    'position': int(row.get('position', 0)),
                    'points': float(row.get('points', 0)),
                    'Constructor': {
                        'constructorId': row.get('constructorId', ''),
                        'name': row.get('constructorName', '')
                    }
                })
            
            return jsonify({
                'MRData': {
                    'StandingsTable': {
                        'StandingsLists': [{
                            'ConstructorStandings': formatted_standings
                        }]
                    }
                }
            })
        else:
            return jsonify({'error': 'No data available'}), 404
            
    except Exception as e:
        print(f"Error in constructor standings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/season-schedule', methods=['GET'])
def get_season_schedule():
    try:
        year = request.args.get('year', 'current')
        response = ergast.get_race_schedule(year)
        
        if hasattr(response, 'content'):
            df = response.content
        else:
            df = response
            
        formatted_races = []
        for _, row in df.iterrows():
            formatted_races.append({
                'round': int(row.get('round', 0)),
                'Circuit': {
                    'Location': {
                        'country': row.get('country', '')
                    }
                },
                'date': str(row.get('raceDate', '')),
                'raceName': row.get('raceName', '')
            })
        
        return jsonify({
            'MRData': {
                'RaceTable': {
                    'Races': formatted_races
                }
            }
        })
            
    except Exception as e:
        print(f"Error in season schedule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/race-results', methods=['GET'])
def get_race_results():
    try:
        year = request.args.get('year', 'current')
        round_num = request.args.get('round')
        
        if not round_num:
            return jsonify({'error': 'Round parameter is required'}), 400
        
        response = ergast.get_race_results(year, round_num)
        
        if response.content and len(response.content) > 0:
            df = response.content[0]
            
            formatted_results = []
            for _, row in df.iterrows():
                formatted_results.append({
                    'position': int(row.get('position', 0)),
                    'Driver': {
                        'givenName': row.get('givenName', ''),
                        'familyName': row.get('familyName', '')
                    },
                    'Constructor': {
                        'name': row.get('constructorNames', [''])[0] if row.get('constructorNames') else ''
                    },
                    'points': float(row.get('points', 0))
                })
            
            return jsonify({
                'MRData': {
                    'RaceTable': {
                        'Races': [{
                            'Results': formatted_results
                        }]
                    }
                }
            })
        else:
            return jsonify({'error': 'No data available'}), 404
            
    except Exception as e:
        print(f"Error in race results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/qualifying-results', methods=['GET'])
def get_qualifying_results():
    try:
        year = request.args.get('year', 'current')
        round_num = request.args.get('round')
        
        if not round_num:
            return jsonify({'error': 'Round parameter is required'}), 400
        
        response = ergast.get_qualifying_results(year, round_num)
        
        if response.content and len(response.content) > 0:
            df = response.content[0]
            
            formatted_results = []
            for _, row in df.iterrows():
                formatted_results.append({
                    'position': int(row.get('position', 0)),
                    'Driver': {
                        'givenName': row.get('givenName', ''),
                        'familyName': row.get('familyName', '')
                    },
                    'Constructor': {
                        'name': row.get('constructorNames', [''])[0] if row.get('constructorNames') else ''
                    },
                    'Q1': str(row.get('Q1', '')),
                    'Q2': str(row.get('Q2', '')),
                    'Q3': str(row.get('Q3', ''))
                })
            
            return jsonify({
                'MRData': {
                    'RaceTable': {
                        'Races': [{
                            'QualifyingResults': formatted_results
                        }]
                    }
                }
            })
        else:
            return jsonify({'error': 'No data available'}), 404
            
    except Exception as e:
        print(f"Error in qualifying results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/circuits', methods=['GET'])
def get_circuits():
    try:
        year = request.args.get('year', 'current')
        response = ergast.get_circuits(year)
        
        if hasattr(response, 'content'):
            df = response.content
        else:
            df = response
            
        formatted_circuits = []
        for _, row in df.iterrows():
            formatted_circuits.append({
                'circuitId': row.get('circuitId', ''),
                'name': row.get('circuitName', ''),
                'Location': {
                    'country': row.get('country', ''),
                    'locality': row.get('locality', '')
                }
            })
        
        return jsonify({
            'MRData': {
                'CircuitTable': {
                    'Circuits': formatted_circuits
                }
            }
        })
            
    except Exception as e:
        print(f"Error in circuits: {e}")
        return jsonify({'error': str(e)}), 500

# ========================================
# Database Endpoints (from apis.py)
# ========================================
@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    """Fetches all drivers from the Driver table and returns them as JSON."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Driver")
        drivers = cursor.fetchall()
        conn.close()
        
        drivers_list = [dict(row) for row in drivers]
        
        return jsonify(drivers_list)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to retrieve data from the database"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/constructors', methods=['GET'])
def get_constructors():
    """Fetches all constructors."""
    try:
        year = request.args.get('year')
        
        # If year is provided, use ergast
        if year:
            response = ergast.get_constructor_info(year)
            
            if response.content and len(response.content) > 0:
                df = response.content[0]
                
                formatted_constructors = []
                for _, row in df.iterrows():
                    formatted_constructors.append({
                        'constructorId': row.get('constructorId', ''),
                        'name': row.get('constructorName', ''),
                        'nationality': row.get('nationality', '')
                    })
                
                return jsonify({
                    'MRData': {
                        'ConstructorTable': {
                            'Constructors': formatted_constructors
                        }
                    }
                })
            else:
                return jsonify({'error': 'No data available'}), 404
        else:
            # Otherwise use database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Constructor")
            constructors = cursor.fetchall()
            conn.close()
            
            return jsonify([dict(row) for row in constructors])
            
    except Exception as e:
        print(f"Error in constructors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/driver_race/<int:year>', methods=['GET'])
def get_driver_race(year):
    """Fetches all driver race data for a specific year."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * From Driver_Race INNER JOIN Race ON Driver_Race.race_id = Race.race_id WHERE year = ?;"
        cursor.execute(query, (year,))

        drivers = cursor.fetchall()
        conn.close()
        
        drivers_list = [dict(row) for row in drivers]
        
        return jsonify(drivers_list)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to retrieve data from the database"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/constructor_race/<int:year>', methods=['GET'])
def get_constructor_race(year):
    """Fetches all constructor race data for a specific year."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * From Constructor_Race INNER JOIN Race ON Constructor_Race.race_id = Race.race_id WHERE year = ?;"
        cursor.execute(query, (year,))
        
        drivers = cursor.fetchall()
        conn.close()
        
        drivers_list = [dict(row) for row in drivers]
        
        return jsonify(drivers_list)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to retrieve data from the database"}), 500
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# ========================================
# Comparison Endpoints
# ========================================
@app.route('/api/drivers/compare/<int:driver1_id>/<int:driver2_id>', methods=['GET'])
def compare_drivers(driver1_id, driver2_id):
    """Fetches career stats and latest Elo for two drivers to compare them."""
    try:
        conn = get_db_connection()
        
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
    """Returns the latest Elo score for every driver, ranked highest to lowest."""
    try:
        year = request.args.get('season', type=int)
        round_num = request.args.get('race', type=int)
        
        conn = get_db_connection()
        
        if year and round_num:
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
    """Returns the full Elo history for a specific driver."""
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

@app.route('/api/rankings/combined', methods=['GET'])
def get_combined_elo_rankings():
    """Returns the latest combined driver-constructor Elo scores, ranked."""
    try:
        year = request.args.get('season', type=int)
        round_num = request.args.get('race', type=int)
        
        conn = get_db_connection()
        
        if year and round_num:
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
    """Returns constructor Elo for a specific race via query params."""
    year = request.args.get('season', type=int)
    round_num = request.args.get('race', type=int)
    
    if not year or not round_num:
        return jsonify({"error": "Both 'season' and 'race' query parameters are required."}), 400
        
    return get_elo_for_constructors_in_race(year, round_num)

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
# Available Races (multi-year)
# ========================================
@app.route('/api/available_races/<int:year>', methods=['GET'])
def get_available_races(year):
    """Return race/event names for the current year from FastF1 schedule."""
    try:
        current_year = get_current_year()
        if year != current_year:
            return jsonify({"error": f"Race predictions are only available for the current season ({current_year})"}), 400
        races = get_valid_race_names_for_year(year)
        return jsonify(races)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================
# Race Prediction Endpoints (from predict_race.py)
# ========================================
@app.route('/api/race_predict', methods=['GET'])
def race_predict():
    """
    Predict race finishing positions for a given Grand Prix
    
    Query Parameters:
    - year: The year of the race (e.g., 2025)
    - gp_name: The name of the Grand Prix (e.g., "Monaco", "Silverstone")
    
    Methodology:
    1. Fetches qualifying times and positions
    2. Analyzes tire degradation (Priority: Sprint Race > FP2 > FP3)
    3. Calculates tire degradation rate per driver from long runs
    4. Predicts race positions by adjusting qualifying order based on tire management
    """
    try:
        year = request.args.get('year', type=int)
        gp_name = request.args.get('gp_name')
        
        if not year or not gp_name:
            return jsonify({"error": "Both 'year' and 'gp_name' parameters are required"}), 400
        
        # Only current year supported
        current_year = get_current_year()
        if year != current_year:
            return jsonify({
                "error": f"Race predictions are only available for the current season ({current_year})"
            }), 400
        
        # Validate race name against schedule for this year
        valid_races = get_valid_race_names_for_year(year)
        if not valid_races:
            return jsonify({"error": f"Could not load schedule for {year}. Year may be unsupported."}), 400
        
        if not _gp_name_matches(gp_name, valid_races):
            return jsonify({
                "error": f"Invalid race name '{gp_name}'. Valid {year} races: {', '.join(valid_races)}"
            }), 400
        
        # Fetch qualifying times
        qualifying_times, error = get_qualifying_times_for_prediction(year, gp_name)
        
        if error:
            return jsonify({"error": error}), 404
        
        if len(qualifying_times) == 0:
            return jsonify({
                "error": f"No qualifying data found for {year} {gp_name}. Please try a different race or check if the race has occurred."
            }), 404
        
        # Generate predictions
        predictions_df = predict_race_positions(year, gp_name, qualifying_times)
        
        # Format response
        predictions_list = []
        for idx, row in predictions_df.iterrows():
            predictions_list.append({
                "position": idx + 1,
                "driver": row["Driver"],
                "driver_code": row["DriverCode"],
                "qualifying_time": round(row["QualifyingTime (s)"], 3),
                "qualifying_position": int(row["QualifyingPosition"]),
                "predicted_race_position": int(row["PredictedRacePosition"]),
                "tire_deg_rate": round(row["AvgDegPerLap"], 4) if pd.notna(row["AvgDegPerLap"]) else None,
                "prediction_method": row["PredictionMethod"],
                "constructor_name": row.get("TeamName") if pd.notna(row.get("TeamName")) else None
            })
        
        return jsonify({
            "year": year,
            "gp_name": gp_name,
            "predictions": predictions_list
        })
    
    except Exception as e:
        print(f"Error in race prediction: {e}")
        return jsonify({"error": f"Error generating predictions: {str(e)}"}), 500

# ========================================
# Run the Flask App
# ========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

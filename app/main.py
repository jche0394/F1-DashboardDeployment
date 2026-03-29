from flask import Flask, jsonify, request
from flask_cors import CORS
import fastf1
import fastf1.ergast
import os
from datetime import datetime
import sqlite3

try:
    from app.repositories.driver_repository import DriverRepository
    from app.repositories.race_repository import RaceRepository
    from app.repositories.rankings_repository import RankingsRepository
    from app.repositories.prediction_repository import PredictionRepository
    from app.repositories.constructor_repository import ConstructorRepository
    from app.services.comparison_service import ComparisonService
    from app.services.prediction_service import PredictionService
    from app.services.race_service import RaceService
    from app.services.rankings_service import RankingsService
except ImportError:
    from repositories.driver_repository import DriverRepository
    from repositories.race_repository import RaceRepository
    from repositories.rankings_repository import RankingsRepository
    from repositories.prediction_repository import PredictionRepository
    from repositories.constructor_repository import ConstructorRepository
    from services.comparison_service import ComparisonService
    from services.prediction_service import PredictionService
    from services.race_service import RaceService
    from services.rankings_service import RankingsService

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


driver_repository = DriverRepository(DATABASE_PATH)
constructor_repository = ConstructorRepository(DATABASE_PATH)
race_repository = RaceRepository(DATABASE_PATH)
rankings_repository = RankingsRepository(DATABASE_PATH)
prediction_repository = PredictionRepository(
    DATABASE_PATH,
    available_races_provider=get_valid_race_names_for_year,
)

rankings_service = RankingsService(rankings_repository)
race_service = RaceService(race_repository)
comparison_service = ComparisonService(driver_repository, constructor_repository)
prediction_service = PredictionService(
    prediction_repository,
    driver_code_to_name=driver_code_to_name,
    get_current_year=get_current_year,
    valid_races_provider=get_valid_race_names_for_year,
)


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
            'database': [
                '/api/drivers',
                '/api/rankings/drivers/elo',
                '/api/drivers/compare/<id1>/<id2>',
                '/api/constructors/compare/<id1>/<id2>',
            ],
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
        return jsonify(driver_repository.get_all_drivers())
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
            return jsonify(constructor_repository.get_all_constructors())
            
    except Exception as e:
        print(f"Error in constructors: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/driver_race/<int:year>', methods=['GET'])
def get_driver_race(year):
    """Fetches all driver race data for a specific year."""
    try:
        return jsonify(race_service.get_driver_race_by_year(year))
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
        return jsonify(race_service.get_constructor_race_by_year(year))
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
        response = comparison_service.compare_drivers(driver1_id, driver2_id)
        if not response:
            return jsonify({"error": "One or both drivers not found"}), 404
        return jsonify(response)
        
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/constructors/compare/<int:constructor1_id>/<int:constructor2_id>', methods=['GET'])
def compare_constructors(constructor1_id, constructor2_id):
    """Fetches latest Elo for two constructors to compare them."""
    try:
        response = comparison_service.compare_constructors(constructor1_id, constructor2_id)
        if not response:
            return jsonify({"error": "One or both constructors not found"}), 404
        return jsonify(response)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# ========================================
# Ranking & History Endpoints
# ========================================
def _ranking_query_kwargs():
    """Optional filters: min_elo, q|search, sort (elo|name|code), order (asc|desc)."""
    min_elo = request.args.get("min_elo", type=int)
    search = request.args.get("q") or request.args.get("search")
    sort_by = request.args.get("sort", "elo")
    descending = request.args.get("order", "desc").lower() != "asc"
    return {
        "min_elo": min_elo,
        "search": search,
        "sort_by": sort_by,
        "descending": descending,
    }


@app.route('/api/rankings/drivers/elo', methods=['GET'])
def get_driver_elo_rankings():
    """Returns the latest Elo score for every driver, ranked highest to lowest."""
    try:
        year = request.args.get('season', type=int)
        round_num = request.args.get('race', type=int)
        drivers = rankings_service.get_driver_elo_rankings(year, round_num, **_ranking_query_kwargs())
        return jsonify(drivers)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/rankings/drivers/elo/history/<int:driver_id>', methods=['GET'])
def get_driver_elo_history(driver_id):
    """Returns the full Elo history for a specific driver."""
    try:
        year_filter = request.args.get('season', type=int)
        history = rankings_service.get_driver_elo_history(driver_id, year_filter)
        return jsonify(history)

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
        kw = _ranking_query_kwargs()
        if kw.get("sort_by") == "elo":
            kw = {**kw, "sort_by": "combined_elo"}
        rankings = rankings_service.get_combined_rankings(year, round_num, **kw)
        return jsonify(rankings)

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
        return jsonify(race_service.get_available_years())

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
        drivers = rankings_service.get_driver_elo_for_race(
            year, round_num, **_ranking_query_kwargs()
        )
        return jsonify(drivers)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/elo/constructors/<int:year>/<int:round_num>', methods=['GET'])
def get_elo_for_constructors_in_race(year, round_num):
    """Returns the Elo for all constructors in a specific race."""
    try:
        constructors = rankings_service.get_constructor_elo_rankings(
            year, round_num, **_ranking_query_kwargs()
        )
        return jsonify(constructors)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/elo/combined/<int:year>/<int:round_num>', methods=['GET'])
def get_combined_elo_for_race(year, round_num):
    """Returns the combined driver-constructor Elo for a specific race."""
    try:
        kw = _ranking_query_kwargs()
        if kw.get("sort_by") == "elo":
            kw = {**kw, "sort_by": "combined_elo"}
        results = rankings_service.get_combined_elo_for_race(year, round_num, **kw)
        return jsonify(results)

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
        races, err = prediction_service.get_available_races(year)
        if err:
            return jsonify({"error": err}), 400
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
    year = request.args.get('year', type=int)
    gp_name = request.args.get('gp_name')
    flask_debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    body, err, status, detail = prediction_service.get_predictions_payload_safe(
        year, gp_name, flask_debug=flask_debug
    )
    if err:
        resp = {"error": err}
        if detail:
            resp["detail"] = detail
        return jsonify(resp), status
    return jsonify(body)

# ========================================
# 404 Handler - Return JSON so frontend doesn't get "Unexpected token '<'"
# ========================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "path": request.path}), 404

# ========================================
# Run the Flask App
# ========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

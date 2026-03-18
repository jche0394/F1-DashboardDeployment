from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import pandas as pd
import os

# ==========================
# Setup
# ==========================
app = FastAPI(title="F1 Race Prediction API (DB-based)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database", "f1_data.db")

# ==========================
# Models
# ==========================
class DriverPrediction(BaseModel):
    position: int
    driver: str
    driver_code: str
    qualifying_time: Optional[float]
    qualifying_position: Optional[int]
    predicted_race_position: Optional[int]
    tire_deg_rate: Optional[float]
    prediction_method: Optional[str]


class RacePredictionResponse(BaseModel):
    year: int
    gp_name: str
    predictions: List[DriverPrediction]


# ==========================
# Database helpers
# ==========================
def get_predictions_from_db(year: int, gp_name: str):
    """Fetch stored predictions from the Race_Predictions table."""
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT driver_code, driver_name, qualifying_time,
               qualifying_position, predicted_race_position,
               tire_deg_rate, prediction_method
        FROM Race_Predictions
        WHERE year = ? AND gp_name LIKE ?
        ORDER BY predicted_race_position ASC
    """
    df = pd.read_sql_query(query, conn, params=(year, f"%{gp_name}%"))
    conn.close()
    return df


# ==========================
# API Endpoints
# ==========================
@app.get("/")
def read_root():
    return {
        "message": "F1 Race Prediction API (Database-Backed)",
        "endpoints": {
            "/api/race_predict": "GET - Retrieve stored predictions for a given race",
            "/api/update_predictions": "POST - Regenerate all predictions for 2025",
        },
        "source": "Data fetched from local SQLite database (no FastF1 calls)."
    }


@app.get("/api/race_predict", response_model=RacePredictionResponse)
def race_predict(year: int, gp_name: str):
    """Fetch stored predictions for a given race (already in DB)."""
    try:
        df = get_predictions_from_db(year, gp_name)
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No stored predictions found for {gp_name} {year}. "
                       f"Try regenerating using /api/update_predictions."
            )

        predictions = []
        for i, row in df.iterrows():
            predictions.append(
                DriverPrediction(
                    position=i + 1,
                    driver=row["driver_name"],
                    driver_code=row["driver_code"],
                    qualifying_time=row["qualifying_time"],
                    qualifying_position=row["qualifying_position"],
                    predicted_race_position=row["predicted_race_position"],
                    tire_deg_rate=row["tire_deg_rate"],
                    prediction_method=row["prediction_method"]
                )
            )

        return RacePredictionResponse(
            year=year,
            gp_name=gp_name,
            predictions=predictions
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/update_predictions")
def update_predictions(year: int = 2025):
    """Regenerate all predictions for the 2025 season."""
    try:
        import subprocess
        script_path = os.path.join(BASE_DIR, "populate_predictions_all_2025.py")
        subprocess.run(["python", script_path], check=True)
        return {"message": f"✅ Predictions updated for {year} season."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update predictions: {e}")

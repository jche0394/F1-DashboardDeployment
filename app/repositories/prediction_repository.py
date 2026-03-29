import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .base_repository import BaseRepository


class PredictionRepository(BaseRepository):
    def __init__(
        self,
        db_path: str,
        available_races_provider: Optional[Callable[[int], List[str]]] = None,
    ):
        super().__init__(db_path)
        self.available_races_provider = available_races_provider
        self._ensure_prediction_table()

    def _ensure_prediction_table(self) -> None:
        query = """
            CREATE TABLE IF NOT EXISTS Prediction_Cache (
                year INTEGER NOT NULL,
                gp_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (year, gp_name)
            );
        """
        self._execute(query)

    def get_predictions(self, year: int, gp_name: str) -> Optional[Dict[str, Any]]:
        row = self._fetch_one(
            """
            SELECT year, gp_name, payload, updated_at
            FROM Prediction_Cache
            WHERE year = ? AND lower(gp_name) = lower(?);
            """,
            (year, gp_name),
        )
        if not row:
            return None
        return {
            "year": row["year"],
            "gp_name": row["gp_name"],
            "predictions": json.loads(row["payload"]),
            "updated_at": row["updated_at"],
        }

    def save_predictions(self, year: int, gp_name: str, predictions: List[Dict[str, Any]]) -> None:
        query = """
            INSERT INTO Prediction_Cache (year, gp_name, payload, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(year, gp_name)
            DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at;
        """
        self._execute(
            query,
            (year, gp_name, json.dumps(predictions), datetime.now(timezone.utc).isoformat()),
        )

    def get_available_races(self, year: int) -> List[str]:
        if not self.available_races_provider:
            return []
        return self.available_races_provider(year)

    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        return self._fetch_all(
            "SELECT year, gp_name, updated_at FROM Prediction_Cache ORDER BY updated_at DESC;"
        )

    def create(self, data: Dict[str, Any]) -> int:
        year = data.get("year")
        gp_name = data.get("gp_name")
        predictions = data.get("predictions", [])
        self.save_predictions(year, gp_name, predictions)
        return 0

    def update(self, entity_id: int, data: Dict[str, Any]) -> bool:
        self.create(data)
        return True

    def delete(self, entity_id: int) -> bool:
        raise NotImplementedError("Use year + gp_name for deleting cached predictions.")


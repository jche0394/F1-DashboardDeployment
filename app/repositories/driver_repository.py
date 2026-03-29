from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository


class DriverRepository(BaseRepository):
    def get_all_drivers(self) -> List[Dict[str, Any]]:
        return self._fetch_all("SELECT * FROM Driver ORDER BY driver_id;")

    def get_driver_by_id(self, driver_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one("SELECT * FROM Driver WHERE driver_id = ?;", (driver_id,))

    def get_driver_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        return self._fetch_one("SELECT * FROM Driver WHERE code = ?;", (code,))

    def get_driver_comparison_snapshot(self, driver_id: int) -> Optional[Dict[str, Any]]:
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
        return self._fetch_one(query, (driver_id,))

    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        return self.get_driver_by_id(entity_id)

    def get_all(self) -> List[Dict[str, Any]]:
        return self.get_all_drivers()

    def create(self, data: Dict[str, Any]) -> int:
        query = """
            INSERT INTO Driver (code, first_name, last_name, headshot, country)
            VALUES (?, ?, ?, ?, ?);
        """
        return self._execute(
            query,
            (
                data.get("code"),
                data.get("first_name"),
                data.get("last_name"),
                data.get("headshot"),
                data.get("country"),
            ),
        )

    def update(self, entity_id: int, data: Dict[str, Any]) -> bool:
        query = """
            UPDATE Driver
            SET code = ?, first_name = ?, last_name = ?, headshot = ?, country = ?
            WHERE driver_id = ?;
        """
        self._execute(
            query,
            (
                data.get("code"),
                data.get("first_name"),
                data.get("last_name"),
                data.get("headshot"),
                data.get("country"),
                entity_id,
            ),
        )
        return True

    def delete(self, entity_id: int) -> bool:
        self._execute("DELETE FROM Driver WHERE driver_id = ?;", (entity_id,))
        return True


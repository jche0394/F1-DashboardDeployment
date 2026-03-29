from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository


class RaceRepository(BaseRepository):
    def get_races_by_year(self, year: int) -> List[Dict[str, Any]]:
        return self._fetch_all(
            "SELECT * FROM Race WHERE year = ? ORDER BY round ASC;",
            (year,),
        )

    def get_race_results(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        query = """
            SELECT
                dr.position,
                d.first_name,
                d.last_name,
                d.code,
                c.name AS constructor_name,
                dr.points
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Constructor c ON dr.constructor_id = c.constructor_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE r.year = ? AND r.round = ?
            ORDER BY dr.position ASC;
        """
        return self._fetch_all(query, (year, round_num))

    def get_available_years(self) -> List[int]:
        rows = self._fetch_all("SELECT DISTINCT year FROM Race ORDER BY year DESC;")
        return [row["year"] for row in rows]

    def get_driver_race_by_year(self, year: int) -> List[Dict[str, Any]]:
        query = """
            SELECT *
            FROM Driver_Race
            INNER JOIN Race ON Driver_Race.race_id = Race.race_id
            WHERE year = ?;
        """
        return self._fetch_all(query, (year,))

    def get_constructor_race_by_year(self, year: int) -> List[Dict[str, Any]]:
        query = """
            SELECT *
            FROM Constructor_Race
            INNER JOIN Race ON Constructor_Race.race_id = Race.race_id
            WHERE year = ?;
        """
        return self._fetch_all(query, (year,))

    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one("SELECT * FROM Race WHERE race_id = ?;", (entity_id,))

    def get_all(self) -> List[Dict[str, Any]]:
        return self._fetch_all("SELECT * FROM Race ORDER BY year DESC, round DESC;")

    def create(self, data: Dict[str, Any]) -> int:
        query = """
            INSERT INTO Race (year, round, name, circuit, date)
            VALUES (?, ?, ?, ?, ?);
        """
        return self._execute(
            query,
            (
                data.get("year"),
                data.get("round"),
                data.get("name"),
                data.get("circuit"),
                data.get("date"),
            ),
        )

    def update(self, entity_id: int, data: Dict[str, Any]) -> bool:
        query = """
            UPDATE Race
            SET year = ?, round = ?, name = ?, circuit = ?, date = ?
            WHERE race_id = ?;
        """
        self._execute(
            query,
            (
                data.get("year"),
                data.get("round"),
                data.get("name"),
                data.get("circuit"),
                data.get("date"),
                entity_id,
            ),
        )
        return True

    def delete(self, entity_id: int) -> bool:
        self._execute("DELETE FROM Race WHERE race_id = ?;", (entity_id,))
        return True


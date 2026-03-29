from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository


class RankingsRepository(BaseRepository):
    def get_driver_elo_rankings(
        self,
        season: Optional[int] = None,
        race: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if season and race:
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name, d.code,
                    c.constructor_id, c.name AS constructor_name, dr.elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN Race r ON dr.race_id = r.race_id
                WHERE r.year = ? AND r.round = ?
                ORDER BY dr.elo DESC;
            """
            return self._fetch_all(query, (season, race))

        if season:
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name, d.code,
                    c.constructor_id, c.name AS constructor_name, dr.elo
                FROM Driver d
                JOIN (
                    SELECT
                        dr.driver_id, dr.constructor_id, dr.elo,
                        ROW_NUMBER() OVER(PARTITION BY dr.driver_id ORDER BY r.round DESC) AS rn
                    FROM Driver_Race dr
                    JOIN Race r ON dr.race_id = r.race_id
                    WHERE r.year = ?
                ) dr ON d.driver_id = dr.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                WHERE dr.rn = 1
                ORDER BY dr.elo DESC;
            """
            return self._fetch_all(query, (season,))

        query = """
            SELECT
                d.driver_id, d.first_name, d.last_name, d.code,
                c.constructor_id, c.name AS constructor_name, dr.elo
            FROM Driver d
            JOIN (
                SELECT
                    driver_id, constructor_id, elo,
                    ROW_NUMBER() OVER(PARTITION BY driver_id ORDER BY race_id DESC) AS rn
                FROM Driver_Race
            ) dr ON d.driver_id = dr.driver_id
            JOIN Constructor c ON dr.constructor_id = c.constructor_id
            WHERE dr.rn = 1
            ORDER BY dr.elo DESC;
        """
        return self._fetch_all(query)

    def get_constructor_elo_rankings(
        self,
        season: Optional[int] = None,
        race: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if season and race:
            query = """
                SELECT
                    c.constructor_id, c.name, cr.elo
                FROM Constructor_Race cr
                JOIN Constructor c ON cr.constructor_id = c.constructor_id
                JOIN Race r ON cr.race_id = r.race_id
                WHERE r.year = ? AND r.round = ?
                ORDER BY cr.elo DESC;
            """
            return self._fetch_all(query, (season, race))

        if season:
            query = """
                SELECT
                    c.constructor_id, c.name, cr.elo
                FROM Constructor_Race cr
                JOIN Constructor c ON cr.constructor_id = c.constructor_id
                JOIN Race r ON cr.race_id = r.race_id
                JOIN (
                    SELECT cr.constructor_id, MAX(r.round) AS max_round
                    FROM Constructor_Race cr
                    JOIN Race r ON cr.race_id = r.race_id
                    WHERE r.year = ?
                    GROUP BY cr.constructor_id
                ) latest ON cr.constructor_id = latest.constructor_id AND r.round = latest.max_round
                WHERE r.year = ?
                ORDER BY cr.elo DESC;
            """
            return self._fetch_all(query, (season, season))

        query = """
            SELECT
                c.constructor_id, c.name, cr.elo
            FROM Constructor_Race cr
            JOIN Constructor c ON cr.constructor_id = c.constructor_id
            JOIN (
                SELECT constructor_id, MAX(race_id) AS max_race_id
                FROM Constructor_Race
                GROUP BY constructor_id
            ) latest
              ON cr.constructor_id = latest.constructor_id
             AND cr.race_id = latest.max_race_id
            ORDER BY cr.elo DESC;
        """
        return self._fetch_all(query)

    def get_combined_rankings(
        self,
        season: Optional[int] = None,
        race: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if season and race:
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name,
                    c.constructor_id, c.name AS constructor_name,
                    dr.combined_elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN Race r ON dr.race_id = r.race_id
                WHERE r.year = ? AND r.round = ?
                ORDER BY dr.combined_elo DESC;
            """
            return self._fetch_all(query, (season, race))

        if season:
            query = """
                SELECT
                    d.driver_id, d.first_name, d.last_name,
                    c.constructor_id, c.name AS constructor_name,
                    dr.combined_elo
                FROM Driver_Race dr
                JOIN Driver d ON dr.driver_id = d.driver_id
                JOIN Constructor c ON dr.constructor_id = c.constructor_id
                JOIN Race r ON dr.race_id = r.race_id
                JOIN (
                    SELECT dr.driver_id, MAX(r.round) AS max_round
                    FROM Driver_Race dr
                    JOIN Race r ON dr.race_id = r.race_id
                    WHERE r.year = ?
                    GROUP BY dr.driver_id
                ) latest ON dr.driver_id = latest.driver_id AND r.round = latest.max_round
                WHERE r.year = ?
                ORDER BY dr.combined_elo DESC;
            """
            return self._fetch_all(query, (season, season))

        query = """
            SELECT
                d.driver_id, d.first_name, d.last_name,
                c.constructor_id, c.name AS constructor_name,
                dr.combined_elo
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Constructor c ON dr.constructor_id = c.constructor_id
            JOIN (
                SELECT driver_id, MAX(race_id) AS max_race_id
                FROM Driver_Race
                GROUP BY driver_id
            ) latest ON dr.driver_id = latest.driver_id AND dr.race_id = latest.max_race_id
            ORDER BY dr.combined_elo DESC;
        """
        return self._fetch_all(query)

    def get_driver_elo_history(
        self,
        driver_id: int,
        season: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        base_query = """
            SELECT
                r.year, r.round, r.name AS race_name, r.date, dr.elo
            FROM Driver_Race dr
            JOIN Race r ON dr.race_id = r.race_id
            WHERE dr.driver_id = ?
        """
        params: List[Any] = [driver_id]
        if season:
            base_query += " AND r.year = ?"
            params.append(season)
        base_query += " ORDER BY r.year, r.round;"
        return self._fetch_all(base_query, tuple(params))

    def get_driver_elo_for_race(self, season: int, race: int) -> List[Dict[str, Any]]:
        query = """
            SELECT
                d.driver_id, d.first_name, d.last_name, d.code, dr.elo
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE r.year = ? AND r.round = ?
            ORDER BY dr.elo DESC;
        """
        return self._fetch_all(query, (season, race))

    def get_combined_elo_for_race(self, season: int, race: int) -> List[Dict[str, Any]]:
        query = """
            SELECT
                d.driver_id, d.first_name, d.last_name,
                c.constructor_id, c.name AS constructor_name,
                dr.combined_elo
            FROM Driver_Race dr
            JOIN Driver d ON dr.driver_id = d.driver_id
            JOIN Constructor c ON dr.constructor_id = c.constructor_id
            JOIN Race r ON dr.race_id = r.race_id
            WHERE r.year = ? AND r.round = ?
            ORDER BY dr.combined_elo DESC;
        """
        return self._fetch_all(query, (season, race))

    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        return self.get_driver_elo_rankings()

    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError("RankingsRepository does not support direct create.")

    def update(self, entity_id: int, data: Dict[str, Any]) -> bool:
        raise NotImplementedError("RankingsRepository does not support direct update.")

    def delete(self, entity_id: int) -> bool:
        raise NotImplementedError("RankingsRepository does not support direct delete.")


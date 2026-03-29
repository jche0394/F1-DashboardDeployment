from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository


class ConstructorRepository(BaseRepository):
    def get_all_constructors(self) -> List[Dict[str, Any]]:
        return self._fetch_all("SELECT * FROM Constructor ORDER BY constructor_id;")

    def get_constructor_by_id(self, constructor_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch_one(
            "SELECT * FROM Constructor WHERE constructor_id = ?;",
            (constructor_id,),
        )

    def get_constructor_comparison_snapshot(self, constructor_id: int) -> Optional[Dict[str, Any]]:
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
        return self._fetch_one(query, (constructor_id,))

    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        return self.get_constructor_by_id(entity_id)

    def get_all(self) -> List[Dict[str, Any]]:
        return self.get_all_constructors()

    def create(self, data: Dict[str, Any]) -> int:
        return self._execute(
            "INSERT INTO Constructor (name) VALUES (?);",
            (data.get("name"),),
        )

    def update(self, entity_id: int, data: Dict[str, Any]) -> bool:
        self._execute(
            "UPDATE Constructor SET name = ? WHERE constructor_id = ?;",
            (data.get("name"), entity_id),
        )
        return True

    def delete(self, entity_id: int) -> bool:
        self._execute("DELETE FROM Constructor WHERE constructor_id = ?;", (entity_id,))
        return True


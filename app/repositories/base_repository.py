import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepository(ABC):
    """Abstract base repository with common SQLite helpers."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def _execute(self, query: str, params: tuple = ()) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Fetch one entity by primary key."""

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Fetch all entities for this repository."""

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        """Create and return primary key for a new entity."""

    @abstractmethod
    def update(self, entity_id: int, data: Dict[str, Any]) -> bool:
        """Update an entity by id and return success."""

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an entity by id and return success."""


from typing import Any, Dict, List

try:
    from app.repositories.race_repository import RaceRepository
except ImportError:
    from repositories.race_repository import RaceRepository


class RaceService:
    """Business logic for race schedules and results via RaceRepository."""

    def __init__(self, race_repository: RaceRepository):
        self._repo = race_repository

    def get_available_years(self) -> List[int]:
        return self._repo.get_available_years()

    def get_races_by_year(self, year: int) -> List[Dict[str, Any]]:
        return self._repo.get_races_by_year(year)

    def get_race_results(self, year: int, round_num: int) -> List[Dict[str, Any]]:
        return self._repo.get_race_results(year, round_num)

    def get_driver_race_by_year(self, year: int) -> List[Dict[str, Any]]:
        return self._repo.get_driver_race_by_year(year)

    def get_constructor_race_by_year(self, year: int) -> List[Dict[str, Any]]:
        return self._repo.get_constructor_race_by_year(year)

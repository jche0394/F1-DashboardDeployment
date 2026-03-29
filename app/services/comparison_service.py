from typing import Any, Dict, Optional

try:
    from app.repositories.constructor_repository import ConstructorRepository
    from app.repositories.driver_repository import DriverRepository
except ImportError:
    from repositories.constructor_repository import ConstructorRepository
    from repositories.driver_repository import DriverRepository


class ComparisonService:
    """Driver and constructor comparison using DriverRepository and ConstructorRepository."""

    def __init__(
        self,
        driver_repository: DriverRepository,
        constructor_repository: ConstructorRepository,
    ):
        self._drivers = driver_repository
        self._constructors = constructor_repository

    def compare_drivers(
        self,
        driver1_id: int,
        driver2_id: int,
    ) -> Optional[Dict[str, Any]]:
        driver1_data = self._drivers.get_driver_comparison_snapshot(driver1_id)
        driver2_data = self._drivers.get_driver_comparison_snapshot(driver2_id)
        if not driver1_data or not driver2_data:
            return None
        return {"driver1": driver1_data, "driver2": driver2_data}

    def compare_constructors(
        self,
        constructor1_id: int,
        constructor2_id: int,
    ) -> Optional[Dict[str, Any]]:
        c1 = self._constructors.get_constructor_comparison_snapshot(constructor1_id)
        c2 = self._constructors.get_constructor_comparison_snapshot(constructor2_id)
        if not c1 or not c2:
            return None
        return {"constructor1": c1, "constructor2": c2}

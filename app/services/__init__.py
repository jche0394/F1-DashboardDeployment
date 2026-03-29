try:
    from app.services.comparison_service import ComparisonService
    from app.services.race_service import RaceService
    from app.services.rankings_service import RankingsService
except ImportError:
    from services.comparison_service import ComparisonService
    from services.race_service import RaceService
    from services.rankings_service import RankingsService

__all__ = [
    "ComparisonService",
    "PredictionService",
    "RaceService",
    "RankingsService",
]


def __getattr__(name):
    if name == "PredictionService":
        try:
            from app.services.prediction_service import PredictionService
        except ImportError:
            from services.prediction_service import PredictionService
        return PredictionService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

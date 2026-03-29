from typing import Any, Dict, List, Optional

try:
    from app.repositories.rankings_repository import RankingsRepository
except ImportError:
    from repositories.rankings_repository import RankingsRepository


class RankingsService:
    """Business logic for Elo rankings: optional filtering and sorting on repository data."""

    def __init__(self, rankings_repository: RankingsRepository):
        self._repo = rankings_repository

    def get_driver_elo_rankings(
        self,
        season: Optional[int] = None,
        race: Optional[int] = None,
        *,
        min_elo: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "elo",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        rows = self._repo.get_driver_elo_rankings(season, race)
        return self._post_process_driver_elo(rows, min_elo, search, sort_by, descending)

    def get_constructor_elo_rankings(
        self,
        season: Optional[int] = None,
        race: Optional[int] = None,
        *,
        min_elo: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "elo",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        rows = self._repo.get_constructor_elo_rankings(season, race)
        return self._post_process_constructor_elo(rows, min_elo, search, sort_by, descending)

    def get_combined_rankings(
        self,
        season: Optional[int] = None,
        race: Optional[int] = None,
        *,
        min_elo: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "combined_elo",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        rows = self._repo.get_combined_rankings(season, race)
        return self._post_process_combined(rows, min_elo, search, sort_by, descending)

    def get_driver_elo_history(
        self,
        driver_id: int,
        season: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return self._repo.get_driver_elo_history(driver_id, season)

    def get_driver_elo_for_race(
        self,
        season: int,
        race: int,
        *,
        min_elo: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "elo",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        rows = self._repo.get_driver_elo_for_race(season, race)
        return self._post_process_driver_elo(rows, min_elo, search, sort_by, descending)

    def get_combined_elo_for_race(
        self,
        season: int,
        race: int,
        *,
        min_elo: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "combined_elo",
        descending: bool = True,
    ) -> List[Dict[str, Any]]:
        rows = self._repo.get_combined_elo_for_race(season, race)
        return self._post_process_combined(rows, min_elo, search, sort_by, descending)

    def _post_process_driver_elo(
        self,
        rows: List[Dict[str, Any]],
        min_elo: Optional[int],
        search: Optional[str],
        sort_by: str,
        descending: bool,
    ) -> List[Dict[str, Any]]:
        return self._filter_sort(
            rows,
            score_key="elo",
            min_score=min_elo,
            search=search,
            search_keys=("first_name", "last_name", "code", "constructor_name"),
            sort_by=sort_by,
            descending=descending,
            name_sort_keys=("last_name", "first_name"),
        )

    def _post_process_constructor_elo(
        self,
        rows: List[Dict[str, Any]],
        min_elo: Optional[int],
        search: Optional[str],
        sort_by: str,
        descending: bool,
    ) -> List[Dict[str, Any]]:
        return self._filter_sort(
            rows,
            score_key="elo",
            min_score=min_elo,
            search=search,
            search_keys=("name",),
            sort_by=sort_by,
            descending=descending,
            name_sort_keys=("name",),
        )

    def _post_process_combined(
        self,
        rows: List[Dict[str, Any]],
        min_elo: Optional[int],
        search: Optional[str],
        sort_by: str,
        descending: bool,
    ) -> List[Dict[str, Any]]:
        effective_sort = "combined_elo" if sort_by == "elo" else sort_by
        return self._filter_sort(
            rows,
            score_key="combined_elo",
            min_score=min_elo,
            search=search,
            search_keys=("first_name", "last_name", "constructor_name"),
            sort_by=effective_sort,
            descending=descending,
            name_sort_keys=("last_name", "first_name"),
        )

    def _filter_sort(
        self,
        rows: List[Dict[str, Any]],
        *,
        score_key: str,
        min_score: Optional[int],
        search: Optional[str],
        search_keys: tuple,
        sort_by: str,
        descending: bool,
        name_sort_keys: tuple,
    ) -> List[Dict[str, Any]]:
        out = list(rows)
        if min_score is not None:
            out = [
                r
                for r in out
                if r.get(score_key) is not None and int(r[score_key]) >= min_score
            ]
        if search and search.strip():
            q = search.lower().strip()

            def matches(row: Dict[str, Any]) -> bool:
                return any(q in str(row.get(k, "")).lower() for k in search_keys)

            out = [r for r in out if matches(r)]

        reverse = descending
        if sort_by in (score_key, "elo", "combined_elo"):
            out.sort(
                key=lambda r: (r.get(score_key) is None, r.get(score_key) if r.get(score_key) is not None else 0),
                reverse=reverse,
            )
        elif sort_by == "name":
            out.sort(
                key=lambda r: tuple(str(r.get(k) or "").lower() for k in name_sort_keys),
                reverse=not reverse,
            )
        elif sort_by == "code":
            out.sort(key=lambda r: str(r.get("code") or "").lower(), reverse=reverse)
        else:
            out.sort(
                key=lambda r: (r.get(score_key) is None, r.get(score_key) if r.get(score_key) is not None else 0),
                reverse=reverse,
            )
        return out

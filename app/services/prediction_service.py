from __future__ import annotations

import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

import fastf1
import pandas as pd

try:
    from app.repositories.prediction_repository import PredictionRepository
except ImportError:
    from repositories.prediction_repository import PredictionRepository


class PredictionService:
    """
    Race prediction workflow: validate GP name, cache via PredictionRepository,
    qualifying + tire degradation model (extracted from route handlers).
    """

    def __init__(
        self,
        prediction_repository: PredictionRepository,
        *,
        driver_code_to_name: Dict[str, str],
        get_current_year: Callable[[], int],
        valid_races_provider: Callable[[int], List[str]],
    ):
        self._repo = prediction_repository
        self._driver_code_to_name = driver_code_to_name
        self._get_current_year = get_current_year
        self._valid_races_provider = valid_races_provider

    @staticmethod
    def gp_name_matches(gp_name: str, valid_races: List[str]) -> bool:
        if not gp_name or not valid_races:
            return False
        gp = gp_name.strip()
        valid_set = {str(v).strip() for v in valid_races}
        if gp in valid_set:
            return True
        normalized = gp.replace(" Grand Prix", "").strip()
        if normalized in valid_set:
            return True
        for v in valid_set:
            if v + " Grand Prix" == gp or v == gp:
                return True
        return False

    def get_valid_race_names_for_year(self, year: int) -> List[str]:
        return self._valid_races_provider(year)

    def get_available_races(self, year: int) -> Tuple[Optional[List[str]], Optional[str]]:
        current_year = self._get_current_year()
        if year != current_year:
            return None, f"Race predictions are only available for the current season ({current_year})"
        return self._repo.get_available_races(year), None

    def get_predictions_payload(
        self,
        year: int,
        gp_name: str,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int, Optional[str]]:
        """
        Returns (json_body, error_message, http_status, optional_detail_tb).
        On success, error_message is None and status 200.
        """
        if not year or not gp_name:
            return None, "Both 'year' and 'gp_name' parameters are required", 400, None

        current_year = self._get_current_year()
        if year != current_year:
            return (
                None,
                f"Race predictions are only available for the current season ({current_year})",
                400,
                None,
            )

        valid_races = self.get_valid_race_names_for_year(year)
        if not valid_races:
            return None, f"Could not load schedule for {year}. Year may be unsupported.", 400, None

        if not self.gp_name_matches(gp_name, valid_races):
            return (
                None,
                f"Invalid race name '{gp_name}'. Valid {year} races: {', '.join(valid_races)}",
                400,
                None,
            )

        cached = self._repo.get_predictions(year, gp_name)
        if cached:
            return (
                {
                    "year": cached["year"],
                    "gp_name": cached["gp_name"],
                    "predictions": cached["predictions"],
                },
                None,
                200,
                None,
            )

        qualifying_times, error = self._get_qualifying_times_for_prediction(year, gp_name)
        if error:
            return None, error, 404, None

        if len(qualifying_times) == 0:
            return (
                None,
                f"No qualifying data found for {year} {gp_name}. Please try a different race or check if the race has occurred.",
                404,
                None,
            )

        predictions_df = self._predict_race_positions(year, gp_name, qualifying_times)
        predictions_list = self._format_predictions_list(predictions_df)

        self._repo.save_predictions(year, gp_name, predictions_list)

        return ({"year": year, "gp_name": gp_name, "predictions": predictions_list}, None, 200, None)

    def _load_session(self, year: int, gp_name: str, kind: str):
        sess = fastf1.get_session(year, gp_name, kind)
        sess.load()
        return sess

    def _get_qualifying_times_for_prediction(
        self, year: int, gp_name: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        try:
            sess = self._load_session(year, gp_name, "Q")
            results = sess.results

            if results is None or len(results) == 0:
                return None, "Qualifying data is not available yet. The qualifying session may not have occurred."

            qual_data = []
            for _, row in results.iterrows():
                driver_code = row.get("Abbreviation")
                q3_time = row.get("Q3")
                q2_time = row.get("Q2")
                q1_time = row.get("Q1")

                best_time = q3_time if pd.notna(q3_time) else (q2_time if pd.notna(q2_time) else q1_time)

                if pd.notna(best_time) and driver_code:
                    driver_name = (
                        row.get("FullName")
                        if pd.notna(row.get("FullName"))
                        else self._driver_code_to_name.get(driver_code, driver_code)
                    )
                    team_name = row.get("TeamName") if pd.notna(row.get("TeamName")) else None
                    qual_data.append(
                        {
                            "Driver": driver_name,
                            "DriverCode": driver_code,
                            "QualifyingTime (s)": best_time.total_seconds(),
                            "TeamName": team_name,
                        }
                    )

            if len(qual_data) == 0:
                return None, "No valid qualifying times found. The qualifying session may not have occurred yet."

            df = pd.DataFrame(qual_data)
            df = df.sort_values("QualifyingTime (s)").reset_index(drop=True)
            df["QualifyingPosition"] = df.index + 1

            return df, None

        except Exception as e:
            error_msg = str(e).lower()

            if (
                "cannot find" in error_msg
                or "no round" in error_msg
                or "invalid event" in error_msg
                or "not found" in error_msg
                or "no session" in error_msg
            ):
                return None, f"Circuit or race '{gp_name}' does not exist in {year}. Please check the race name is correct."
            return None, f"Unable to load qualifying data: {str(e)}"

    def _calculate_tire_degradation(self, year: int, gp_name: str) -> pd.DataFrame:
        try:
            sprint = self._load_session(year, gp_name, "S")
            return self._calculate_deg_from_session(sprint, is_sprint=True)
        except Exception:
            pass

        try:
            fp2 = self._load_session(year, gp_name, "FP2")
            return self._calculate_deg_from_session(fp2, is_sprint=False)
        except Exception:
            pass

        try:
            fp3 = self._load_session(year, gp_name, "FP3")
            return self._calculate_deg_from_session(fp3, is_sprint=False)
        except Exception:
            return pd.DataFrame(columns=["DriverCode", "AvgDegPerLap"])

    def _calculate_deg_from_session(self, session, is_sprint: bool) -> pd.DataFrame:
        laps = session.laps.copy()

        driver_to_abbr = {}
        if hasattr(session, "results") and session.results is not None and len(session.results) > 0:
            for _, row in session.results.iterrows():
                num = row.get("DriverNumber")
                abbr = row.get("Abbreviation")
                if pd.notna(num) and pd.notna(abbr):
                    driver_to_abbr[str(num)] = str(abbr)
                    driver_to_abbr[int(num)] = str(abbr)

        def to_driver_code(driver_id):
            if driver_id in driver_to_abbr:
                return driver_to_abbr[driver_id]
            if str(driver_id) in driver_to_abbr:
                return driver_to_abbr[str(driver_id)]
            return driver_id

        if not is_sprint:
            race_compounds = ["MEDIUM", "HARD"]
            laps = laps[laps["Compound"].isin(race_compounds)]

        laps = laps[pd.notna(laps["LapTime"])]
        laps["LapTime (s)"] = laps["LapTime"].dt.total_seconds()

        driver_col = "DriverNumber" if "DriverNumber" in laps.columns else "Driver"

        deg_data = []
        min_stint_length = 5 if is_sprint else 7

        for driver_id in laps[driver_col].unique():
            driver_code = to_driver_code(driver_id)
            driver_laps = laps[laps[driver_col] == driver_id].copy()

            for stint in driver_laps["Stint"].unique():
                stint_laps = driver_laps[driver_laps["Stint"] == stint].sort_values("LapNumber")

                if len(stint_laps) >= min_stint_length:
                    if is_sprint:
                        usable_laps = stint_laps.iloc[1:]
                    else:
                        usable_laps = stint_laps.iloc[1:-1]

                    if len(usable_laps) >= 6:
                        early_laps = usable_laps.iloc[:3]["LapTime (s)"].mean()
                        late_laps = usable_laps.iloc[-3:]["LapTime (s)"].mean()

                        num_laps = len(usable_laps) - 3
                        deg_per_lap = (late_laps - early_laps) / num_laps if num_laps > 0 else 0

                        deg_data.append(
                            {
                                "DriverCode": driver_code,
                                "DegPerLap": deg_per_lap,
                                "StintLength": len(usable_laps),
                                "Compound": stint_laps.iloc[0]["Compound"] if "Compound" in stint_laps.columns else "UNKNOWN",
                            }
                        )

        if len(deg_data) == 0:
            return pd.DataFrame(columns=["DriverCode", "AvgDegPerLap"])

        deg_df = pd.DataFrame(deg_data)
        avg_deg = deg_df.groupby("DriverCode")["DegPerLap"].mean().reset_index()
        avg_deg.columns = ["DriverCode", "AvgDegPerLap"]

        return avg_deg

    def _predict_race_positions(
        self, year: int, gp_name: str, qualifying_times: pd.DataFrame
    ) -> pd.DataFrame:
        deg_data = self._calculate_tire_degradation(year, gp_name)

        predictions = qualifying_times.merge(deg_data, on="DriverCode", how="left")
        predictions["HasDegData"] = predictions["DriverCode"].isin(deg_data["DriverCode"])

        if len(deg_data) > 0 and predictions["HasDegData"].sum() > 0:
            drivers_with_deg = predictions[predictions["HasDegData"]].copy()
            median_deg = drivers_with_deg["AvgDegPerLap"].median()

            predictions["RelativeDeg"] = predictions["AvgDegPerLap"] - median_deg

            if predictions["HasDegData"].sum() >= 4:
                deg_25th = drivers_with_deg["AvgDegPerLap"].quantile(0.25)
                deg_75th = drivers_with_deg["AvgDegPerLap"].quantile(0.75)

                def calculate_position_adjustment(row):
                    if not row["HasDegData"]:
                        return 0

                    deg = row["AvgDegPerLap"]

                    if deg <= deg_25th:
                        improvement = (deg_25th - deg) / (median_deg - deg_25th) if median_deg != deg_25th else 1
                        return -min(3, max(1, int(improvement * 3)))

                    if deg >= deg_75th:
                        decline = (deg - deg_75th) / (deg_75th - median_deg) if deg_75th != median_deg else 1
                        return min(3, max(1, int(decline * 3)))

                    return 0

                predictions["PositionAdjustment"] = predictions.apply(calculate_position_adjustment, axis=1)
            else:
                predictions["PositionAdjustment"] = 0
                predictions.loc[predictions["HasDegData"], "PositionAdjustment"] = predictions.loc[
                    predictions["HasDegData"], "RelativeDeg"
                ].apply(lambda x: min(2, max(-2, int(x * 10))))
        else:
            predictions["AvgDegPerLap"] = None
            predictions["RelativeDeg"] = 0
            predictions["PositionAdjustment"] = 0

        predictions["PredictedRacePosition"] = predictions["QualifyingPosition"] + predictions["PositionAdjustment"]
        predictions["PredictedRacePosition"] = predictions["PredictedRacePosition"].clip(
            lower=predictions["QualifyingPosition"] - 3,
            upper=predictions["QualifyingPosition"] + 3,
        )

        predictions["PredictedRacePosition"] = predictions["PredictedRacePosition"].clip(1, len(predictions))

        predictions = predictions.sort_values(["PredictedRacePosition", "QualifyingPosition"]).reset_index(drop=True)

        seen_positions = {}
        for idx, row in predictions.iterrows():
            pos = int(row["PredictedRacePosition"])
            if pos in seen_positions:
                while pos in seen_positions and pos <= len(predictions):
                    pos += 1
                predictions.at[idx, "PredictedRacePosition"] = pos
            seen_positions[pos] = True

        predictions = predictions.sort_values("PredictedRacePosition").reset_index(drop=True)
        predictions["PredictedRacePosition"] = predictions.index + 1

        predictions["PredictionMethod"] = predictions.apply(
            lambda row: "qualifying_and_tire_deg" if row["HasDegData"] else "qualifying_only",
            axis=1,
        )

        return predictions

    def _format_predictions_list(self, predictions_df: pd.DataFrame) -> List[Dict[str, Any]]:
        predictions_list = []
        for idx, row in predictions_df.iterrows():
            q_time = row.get("QualifyingTime (s)")
            pred_pos = row.get("PredictedRacePosition")
            deg = row.get("AvgDegPerLap")
            predictions_list.append(
                {
                    "position": int(idx) + 1,
                    "driver": str(row.get("Driver", "")),
                    "driver_code": str(row.get("DriverCode", "")),
                    "qualifying_time": round(float(q_time), 3) if pd.notna(q_time) else None,
                    "qualifying_position": int(row.get("QualifyingPosition", 0)),
                    "predicted_race_position": int(pred_pos) if pd.notna(pred_pos) else int(idx) + 1,
                    "tire_deg_rate": round(float(deg), 4) if pd.notna(deg) else None,
                    "prediction_method": str(row.get("PredictionMethod", "qualifying_only")),
                    "constructor_name": str(row.get("TeamName")) if pd.notna(row.get("TeamName")) else None,
                }
            )
        return predictions_list

    def get_predictions_payload_safe(
        self,
        year: int,
        gp_name: str,
        *,
        flask_debug: bool,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], int, Optional[str]]:
        try:
            body, err, status, _detail = self.get_predictions_payload(year, gp_name)
            return body, err, status, None
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error in race prediction: {e}\n{tb}")
            detail = tb if flask_debug else None
            return None, f"Error generating predictions: {str(e)}", 500, detail

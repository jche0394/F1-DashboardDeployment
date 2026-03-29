import os
import sqlite3
import tempfile
import unittest

from app.repositories.constructor_repository import ConstructorRepository
from app.repositories.driver_repository import DriverRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.race_repository import RaceRepository
from app.repositories.rankings_repository import RankingsRepository
from app.services.comparison_service import ComparisonService
from app.services.race_service import RaceService
from app.services.rankings_service import RankingsService

try:
    from app.services.prediction_service import PredictionService
except ModuleNotFoundError:
    PredictionService = None  # optional: requires fastf1


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_services.db")
        self._create_schema()
        self._seed_data()

        self.driver_repo = DriverRepository(self.db_path)
        self.constructor_repo = ConstructorRepository(self.db_path)
        self.race_repo = RaceRepository(self.db_path)
        self.rankings_repo = RankingsRepository(self.db_path)
        self.prediction_repo = PredictionRepository(
            self.db_path,
            available_races_provider=lambda year: [f"Sample GP {year}"],
        )

        self.rankings_service = RankingsService(self.rankings_repo)
        self.race_service = RaceService(self.race_repo)
        self.comparison_service = ComparisonService(self.driver_repo, self.constructor_repo)
        self.prediction_service = (
            PredictionService(
                self.prediction_repo,
                driver_code_to_name={"VER": "Max Verstappen"},
                get_current_year=lambda: 2025,
                valid_races_provider=lambda year: ["Bahrain Grand Prix"],
            )
            if PredictionService
            else None
        )

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            pass

    def _create_schema(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE Driver (
                driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                first_name TEXT,
                last_name TEXT,
                headshot TEXT,
                country TEXT
            );

            CREATE TABLE Constructor (
                constructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE Race (
                race_id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                round INTEGER NOT NULL,
                name TEXT NOT NULL,
                circuit TEXT,
                date TEXT
            );

            CREATE TABLE Driver_Race (
                driver_race_id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                constructor_id INTEGER NOT NULL,
                race_id INTEGER NOT NULL,
                position INTEGER,
                points INTEGER,
                elo INTEGER,
                combined_elo INTEGER
            );

            CREATE TABLE Constructor_Race (
                constructor_race_id INTEGER PRIMARY KEY AUTOINCREMENT,
                constructor_id INTEGER NOT NULL,
                race_id INTEGER NOT NULL,
                elo INTEGER
            );
            """
        )
        conn.commit()
        conn.close()

    def _seed_data(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Driver (code, first_name, last_name, country) VALUES (?,?,?,?);",
            ("AAA", "Alpha", "Apple", "CountryA"),
        )
        cur.execute(
            "INSERT INTO Driver (code, first_name, last_name, country) VALUES (?,?,?,?);",
            ("BBB", "Beta", "Banana", "CountryB"),
        )
        cur.execute("INSERT INTO Constructor (name) VALUES ('Team A');")
        cur.execute("INSERT INTO Constructor (name) VALUES ('Team B');")
        cur.execute(
            "INSERT INTO Race (year, round, name, circuit, date) VALUES (2024, 1, 'Test GP', 'C', '2024-03-01');"
        )
        race_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO Driver_Race (driver_id, constructor_id, race_id, position, points, elo, combined_elo)
            VALUES (1, 1, ?, 1, 25, 1200, 1180);
            """,
            (race_id,),
        )
        cur.execute(
            """
            INSERT INTO Driver_Race (driver_id, constructor_id, race_id, position, points, elo, combined_elo)
            VALUES (2, 2, ?, 2, 18, 900, 950);
            """,
            (race_id,),
        )
        cur.execute(
            "INSERT INTO Constructor_Race (constructor_id, race_id, elo) VALUES (1, ?, 1100);",
            (race_id,),
        )
        cur.execute(
            "INSERT INTO Constructor_Race (constructor_id, race_id, elo) VALUES (2, ?, 800);",
            (race_id,),
        )
        conn.commit()
        conn.close()

    def test_rankings_service_filter_min_elo(self):
        rows = self.rankings_service.get_driver_elo_rankings(
            2024, 1, min_elo=1000, search=None, sort_by="elo", descending=True
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["code"], "AAA")

    def test_rankings_service_search(self):
        rows = self.rankings_service.get_driver_elo_rankings(
            2024, 1, search="ban", sort_by="name", descending=False
        )
        self.assertTrue(any("Banana" in str(r.get("last_name")) for r in rows))

    def test_race_service_results_and_years(self):
        years = self.race_service.get_available_years()
        self.assertIn(2024, years)
        res = self.race_service.get_race_results(2024, 1)
        self.assertEqual(len(res), 2)

    def test_comparison_service_drivers(self):
        payload = self.comparison_service.compare_drivers(1, 2)
        self.assertIsNotNone(payload)
        self.assertIn("driver1", payload)
        self.assertIn("driver2", payload)

    def test_comparison_service_missing_driver(self):
        self.assertIsNone(self.comparison_service.compare_drivers(1, 99))

    @unittest.skipUnless(PredictionService, "fastf1 not installed")
    def test_prediction_service_gp_match(self):
        self.assertTrue(
            PredictionService.gp_name_matches("Bahrain", ["Bahrain Grand Prix"])
        )

    @unittest.skipUnless(PredictionService, "fastf1 not installed")
    def test_prediction_service_available_races_year_gate(self):
        races, err = self.prediction_service.get_available_races(2024)
        self.assertIsNone(races)
        self.assertIn("only available for the current season", err or "")

    @unittest.skipUnless(PredictionService, "fastf1 not installed")
    def test_prediction_service_available_races_current_year(self):
        races, err = self.prediction_service.get_available_races(2025)
        self.assertIsNone(err)
        self.assertEqual(races, ["Sample GP 2025"])


if __name__ == "__main__":
    unittest.main()

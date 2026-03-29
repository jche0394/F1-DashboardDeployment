import os
import sqlite3
import tempfile
import unittest

from app.repositories.constructor_repository import ConstructorRepository
from app.repositories.driver_repository import DriverRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.race_repository import RaceRepository
from app.repositories.rankings_repository import RankingsRepository


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_repo.db")
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

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            # Windows can occasionally keep SQLite temp handles briefly.
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
        cur.executescript(
            """
            INSERT INTO Driver (driver_id, code, first_name, last_name, country)
            VALUES
                (1, 'VER', 'Max', 'Verstappen', 'Netherlands'),
                (2, 'HAM', 'Lewis', 'Hamilton', 'United Kingdom');

            INSERT INTO Constructor (constructor_id, name)
            VALUES
                (1, 'Red Bull'),
                (2, 'Mercedes');

            INSERT INTO Race (race_id, year, round, name, circuit, date)
            VALUES
                (1, 2024, 1, 'Bahrain Grand Prix', 'Bahrain', '2024-03-01'),
                (2, 2024, 2, 'Saudi Arabian Grand Prix', 'Jeddah', '2024-03-08'),
                (3, 2025, 1, 'Australian Grand Prix', 'Melbourne', '2025-03-16');

            INSERT INTO Driver_Race (driver_id, constructor_id, race_id, position, points, elo, combined_elo)
            VALUES
                (1, 1, 1, 1, 25, 1500, 1600),
                (2, 2, 1, 2, 18, 1400, 1500),
                (1, 1, 2, 2, 18, 1490, 1590),
                (2, 2, 2, 1, 25, 1510, 1610),
                (1, 1, 3, 1, 25, 1515, 1620),
                (2, 2, 3, 2, 18, 1420, 1520);

            INSERT INTO Constructor_Race (constructor_id, race_id, elo)
            VALUES
                (1, 1, 1450),
                (2, 1, 1440),
                (1, 2, 1460),
                (2, 2, 1470),
                (1, 3, 1480),
                (2, 3, 1465);
            """
        )
        conn.commit()
        conn.close()

    def test_driver_repository_crud_and_lookup(self):
        drivers = self.driver_repo.get_all_drivers()
        self.assertEqual(len(drivers), 2)
        self.assertEqual(self.driver_repo.get_driver_by_code("VER")["first_name"], "Max")

        new_id = self.driver_repo.create(
            {
                "code": "NOR",
                "first_name": "Lando",
                "last_name": "Norris",
                "headshot": None,
                "country": "United Kingdom",
            }
        )
        self.assertIsNotNone(self.driver_repo.get_driver_by_id(new_id))

        self.driver_repo.update(
            new_id,
            {
                "code": "NOR",
                "first_name": "Lando",
                "last_name": "Norris",
                "headshot": None,
                "country": "UK",
            },
        )
        self.assertEqual(self.driver_repo.get_driver_by_id(new_id)["country"], "UK")

        self.driver_repo.delete(new_id)
        self.assertIsNone(self.driver_repo.get_driver_by_id(new_id))

    def test_constructor_repository_comparison_and_crud(self):
        all_constructors = self.constructor_repo.get_all_constructors()
        self.assertEqual(len(all_constructors), 2)

        snapshot = self.constructor_repo.get_constructor_comparison_snapshot(1)
        self.assertEqual(snapshot["name"], "Red Bull")
        self.assertEqual(snapshot["year"], 2025)

        new_id = self.constructor_repo.create({"name": "McLaren"})
        self.constructor_repo.update(new_id, {"name": "McLaren F1"})
        self.assertEqual(
            self.constructor_repo.get_constructor_by_id(new_id)["name"], "McLaren F1"
        )
        self.constructor_repo.delete(new_id)
        self.assertIsNone(self.constructor_repo.get_constructor_by_id(new_id))

    def test_race_repository_year_and_join_queries(self):
        self.assertEqual(self.race_repo.get_available_years(), [2025, 2024])
        self.assertEqual(len(self.race_repo.get_races_by_year(2024)), 2)
        self.assertEqual(len(self.race_repo.get_driver_race_by_year(2024)), 4)
        self.assertEqual(len(self.race_repo.get_constructor_race_by_year(2024)), 4)
        self.assertEqual(len(self.race_repo.get_race_results(2024, 1)), 2)

    def test_rankings_repository_queries(self):
        all_time = self.rankings_repo.get_driver_elo_rankings()
        self.assertEqual(all_time[0]["driver_id"], 1)

        season_latest = self.rankings_repo.get_driver_elo_rankings(season=2024)
        self.assertEqual(season_latest[0]["driver_id"], 2)

        race_rank = self.rankings_repo.get_driver_elo_rankings(season=2024, race=1)
        self.assertEqual(len(race_rank), 2)

        constructors = self.rankings_repo.get_constructor_elo_rankings(season=2024, race=2)
        self.assertEqual(constructors[0]["constructor_id"], 2)

        combined = self.rankings_repo.get_combined_rankings(season=2025, race=1)
        self.assertEqual(combined[0]["driver_id"], 1)

        history = self.rankings_repo.get_driver_elo_history(driver_id=1, season=2024)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["round"], 1)

        race_drivers = self.rankings_repo.get_driver_elo_for_race(2025, 1)
        self.assertEqual(len(race_drivers), 2)

        race_combined = self.rankings_repo.get_combined_elo_for_race(2025, 1)
        self.assertEqual(race_combined[0]["driver_id"], 1)

    def test_prediction_repository_cache_and_provider(self):
        self.assertEqual(self.prediction_repo.get_available_races(2025), ["Sample GP 2025"])
        self.assertIsNone(self.prediction_repo.get_predictions(2025, "Bahrain Grand Prix"))

        payload = [{"driver_code": "VER", "predicted_race_position": 1}]
        self.prediction_repo.save_predictions(2025, "Bahrain Grand Prix", payload)
        cached = self.prediction_repo.get_predictions(2025, "bahrain grand prix")

        self.assertIsNotNone(cached)
        self.assertEqual(cached["year"], 2025)
        self.assertEqual(cached["predictions"][0]["driver_code"], "VER")


if __name__ == "__main__":
    unittest.main()


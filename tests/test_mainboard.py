import unittest
from unittest.mock import mock_open, patch
from mainboard.mainboard import Mainboard

# Python

class TestLoadFixtures(unittest.TestCase):
    def test_load_fixtures_with_fixtures_key(self):
        mock_json = '{"fixtures": [{"id": 1, "name": "FixtureA"}, {"id": 2, "name": "FixtureB"}]}'
        with patch("builtins.open", mock_open(read_data=mock_json)):
            mainboard = Mainboard("dummy/path.json")
            fixtures = mainboard.load_fixtures()
            print("Loaded fixtures:", fixtures)
            self.assertIsInstance(fixtures, list)
            self.assertEqual(len(fixtures), 2)
            self.assertEqual(fixtures[0]["name"], "FixtureA")

    def test_load_fixtures_without_fixtures_key(self):
        mock_json = '{"other_key": []}'
        with patch("builtins.open", mock_open(read_data=mock_json)):
            mainboard = Mainboard("dummy/path.json")
            fixtures = mainboard.load_fixtures()
            print("Loaded fixtures:", fixtures)
            self.assertIsInstance(fixtures, list)
            self.assertEqual(fixtures, [])

    def test_load_fixtures_with_empty_fixtures(self):
        mock_json = '{"fixtures": []}'
        with patch("builtins.open", mock_open(read_data=mock_json)):
            mainboard = Mainboard("dummy/path.json")
            fixtures = mainboard.load_fixtures()
            print("Loaded fixtures:", fixtures)
            self.assertIsInstance(fixtures, list)
            self.assertEqual(fixtures, [])

if __name__ == "__main__":
    unittest.main()
import json

class Mainboard:
    def __init__(self, json_path="fixtures/fixtures.json"):
        self.json_path = json_path
        self.fixtures = self.load_fixtures()

    def load_fixtures(self):
        with open(self.json_path, "r") as f:
            data = json.load(f)
        return data.get("fixtures", [])
        
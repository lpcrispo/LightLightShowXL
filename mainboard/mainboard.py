import json

class MainBoard:
    def __init__(self):
        with open('fixtures/fixtures.json', 'r') as f:
            fixtures_file = json.load(f)

        self.fixtures = [] #création du tableau vide
        for fixture in fixtures_file["fixtures"]: #parcours du fichier JSON
            self.fixtures.append({"name": fixture["name"]}) #ajout de chaque fixture au tableau
            print(f"Loaded fixture: {fixture['name']}")

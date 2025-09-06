import json
from time import time

class MainBoard:
    def __init__(self):
        self.board = [] #création du tableau vide
        self.fixtures_file = {} #initialisation du dictionnaire de fixtures vide
        
        with open('fixtures/fixtures.json', 'r') as f:
            self.fixtures_file = json.load(f)

        for fixture in self.fixtures_file["fixtures"]: #parcours du fichier JSON
            self.board.append({"name": fixture["name"],
                               "channels": {"red": self.get_channel(fixture["name"], "red"),
                                            "green": self.get_channel(fixture["name"], "green"),
                                            "blue": self.get_channel(fixture["name"], "blue")},
                               "current_color": "black",
                               "next_color": "black",
                               "current_priority": 0,
                               "start_time": time(),
                               "color_duration": 1000, #durée par défaut en milisecondes
                               "step_time": time()
                               }
                            ) #ajout de chaque fixture au tableau
            print(f"Loaded fixture: {fixture['name']}")

    def get_channel(self, p_fixture_name, p_channel_name):
        # Cherche le fixture correspondant
        for fixture in self.fixtures_file["fixtures"]:
            if fixture["name"] == p_fixture_name:
                # Cherche le numéro de channel associé au nom
                for channel_num, channel_info in fixture["channels"].items():
                    if channel_info["name"] == p_channel_name:
                        # Calcule le numéro DMX absolu
                        return fixture["dmx_address"] + int(channel_num) - 1
        return None  # Si non trouvé
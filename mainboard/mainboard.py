import json
from time import time

class MainBoard:
    def __init__(self):
        self.board = [] #création du tableau vide
        self.last_update_time = time()  # Initialisation du temps de la dernière mise à jour

        self.available_fixtures = {} #initialisation du dictionnaire de fixtures vide
        self.available_colors = {} #initialisation du dictionnaire de couleurs vide
        self.available_themes = {} #initialisation du dictionnaire de thèmes vide
        self.sequence_colors = {} #initialisation de la séquence de couleurs vide
        self.current_theme = "startup" #thème par défaut
        
        #load definitions from JSON files
        with open('fixtures/fixtures.json', 'r') as f:
            self.available_fixtures = json.load(f)
            print(self.available_fixtures)
        with open('themes/colors.json', 'r') as f:
            self.available_colors = json.load(f)
            print(self.available_colors)
        with open('themes/themes.json', 'r') as f:
            self.available_themes = json.load(f)
            print(self.available_themes)
         # Initialiser sequence_colors selon le current_theme
        self.sequence_colors = self.available_themes["startup"]["sequence"]
        

        #populate the board with fixtures and their channels
        for fixture_name, fixture in self.available_fixtures.items(): #parcours du fichier JSON
            self.board.append({
                                "name": fixture_name,
                                "red": {"id": self.get_channel(fixture_name, "red"), "value": 255},
                                "green": {"id": self.get_channel(fixture_name, "green"), "value": 255},
                                "blue": {"id": self.get_channel(fixture_name, "blue"), "value": 255},
                                "startup_sequence": "white",
                                "current_seq_color": "white",
                                "next_seq_color": "black",
                                "current_priority": 0,
                                "last_kick_color": "yellow",
                                "start_time": self.last_update_time,
                                "color_duration": 1000, #durée par défaut en milisecondes
                                "last_step_time": self.last_update_time
                              })
        for fixture in self.board:
            print(f"Loaded fixture: {fixture['name']} at DMX addresses {fixture['red']}, {fixture['green']}, {fixture['blue']}")

    def get_channel(self, p_fixture_name, p_channel_name):
       return self.available_fixtures[p_fixture_name]["channels"][p_channel_name]["id"]+self.available_fixtures[p_fixture_name]["dmx_address"]-1
    
    def get_color_r(self, p_color_name):
        return self.available_colors[p_color_name]["red"]
    def get_color_g(self, p_color_name):
        return self.available_colors[p_color_name]["green"]
    def get_color_b(self, p_color_name):
        return self.available_colors[p_color_name]["blue"]

    def get_next_color_in_theme_by_type(self, p_theme, p_type, p_current_color):
        sequence = self.available_themes[p_theme][p_type]
        idx = sequence.index(p_current_color)
        next_idx = (idx + 1) % len(sequence)
        return sequence[next_idx]

    
    def update_board(self):
        current_time = time()
        passed_time = (current_time - self.last_update_time) * 1000  # Convertir en millisecondes
        # print(f"Time since last update: {passed_time} ms")
        for fixture in self.board:
            # Logique de mise à jour des couleurs basée sur le temps écoulé
            if current_time - fixture["last_step_time"] >= fixture["color_duration"] / 1000:
                # Passer à la couleur suivante dans la séquence
                if fixture["current_seq_color"] == fixture["next_seq_color"]:
                    # Si on est à la fin de la séquence, revenir au début
                    fixture["current_seq_color"] = fixture["next_seq_color"]
                    fixture["start_time"] = current_time
                else:
                    # Avancer à la couleur suivante
                    fixture["current_seq_color"] = fixture["next_seq_color"]
                    fixture["start_time"] = current_time
                
                # Mettre à jour le temps du dernier changement de couleur
                fixture["last_step_time"] = current_time
                
                # Ici, tu peux ajouter le code pour envoyer la nouvelle couleur au matériel DMX
                print(f"Fixture {fixture['name']} changed to color {fixture['current_seq_color']}")
        self.last_update_time = current_time
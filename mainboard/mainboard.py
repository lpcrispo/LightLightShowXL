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
                                "current_type": "sequence", #type de couleur actuelle (sequence, kick)
                                "current_sequence_color": "white", #couleur actuelle dans la séquence
                                "current_color_intensity_prc": 1, #intensité actuelle dans la séquence (0-100%)
                                "next_sequence_color": "black", #couleur suivante dans la séquence
                                "current_kick_color": "yellow", #couleur actuelle de kick
                                "current_priority": 0, #priorité actuelle (0=sequence, 1=kick)
                                "last_kick_color": "yellow", #dernière couleur de kick
                                "color_start_time": self.last_update_time, #temps de début de la couleur actuelle
                                "color_duration": 1000, #durée par défaut en milisecondes
                                "fade_duration": 500, #durée de fondu par défaut en milisecondes
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
    
    def update_new_color_sequence(self, p_fixture, p_new_color, p_current_time):
        p_fixture["current_seq_color"] = p_new_color
        p_fixture["red"]["value"] = self.get_color_r(p_new_color) 
        p_fixture["green"]["value"] = self.get_color_g(p_new_color) 
        p_fixture["blue"]["value"] = self.get_color_b(p_new_color)
        p_fixture["color_start_time"] = p_current_time

    def apply_intensity_modulation(self, p_fixture):
        intensity = p_fixture["current_color_intensity_prc"]
        p_fixture["red"]["value"] = int(p_fixture["red"]["value"] * intensity)
        p_fixture["green"]["value"] = int(p_fixture["green"]["value"] * intensity)
        p_fixture["blue"]["value"] = int(p_fixture["blue"]["value"] * intensity)
    
    def update_color_to_next(self, p_fixture, p_current_color, p_new_color, p_percent):
        p_fixture["red"]["value"] = int(self.get_color_r(p_current_color) + (self.get_color_r(p_new_color) - self.get_color_r(p_current_color)) * p_percent)
        p_fixture["green"]["value"] = int(self.get_color_g(p_current_color) + (self.get_color_g(p_new_color) - self.get_color_g(p_current_color)) * p_percent)
        p_fixture["blue"]["value"] = int(self.get_color_b(p_current_color) + (self.get_color_b(p_new_color) - self.get_color_b(p_current_color)) * p_percent)

    def update_board(self):
        current_time = time()
        # Parcours de chaque fixture pour mettre à jour sa couleur
        for fixture in self.board:
            elapsed = current_time - fixture["color_start_time"]
            color_duration_s = fixture["color_duration"] / 1000
            fade_duration_s = fixture["fade_duration"] / 1000
            begin_fade_percent = (fixture["color_duration"] - fixture["fade_duration"]) / fixture["color_duration"]
            fade_start = color_duration_s * begin_fade_percent
            fade_end = fade_start + fade_duration_s
            # Met à jour la couleur de chaque fixture en fonction du temps écoulé
            # Vérifie si la durée de la couleur actuelle est écoulée
            if elapsed >= color_duration_s: 
                # Passer à la couleur suivante dans la séquence
                fixture["current_sequence_color"] = fixture["next_sequence_color"]
                fixture["next_sequence_color"] = self.get_next_color_in_theme_by_type(self.current_theme, fixture["current_type"], fixture["next_sequence_color"])
                self.update_new_color_sequence(fixture, fixture["current_sequence_color"], current_time)
                # Ici, tu peux ajouter le code pour envoyer la nouvelle couleur au matériel DMX
                print(f"Fixture {fixture['name']} changed to color {fixture['current_sequence_color']}")
            # Vérifie si la durée de la couleur actuelle est à moitié écoulée
            elif fade_start <= elapsed < fade_end:
                percent = min((elapsed - fade_start) / fade_duration_s, 1)
                self.update_color_to_next(fixture, fixture["current_sequence_color"], fixture["next_sequence_color"], percent)
                print(f"Fading fixture {fixture['name']} to color {fixture['next_sequence_color']} at {percent*100:.1f}%")
            else:
                pass
            self.apply_intensity_modulation(fixture)
            fixture["last_step_time"] = current_time
        self.last_update_time = current_time
        
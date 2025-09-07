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
        self.current_theme = "sunset" #thème par défaut
        
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
        self.sequence_colors = self.available_themes[self.current_theme]["sequence"]
        self.kick_colors = self.available_themes[self.current_theme]["kick"]

        #populate the board with fixtures and their channels
        for fixture_name, fixture in self.available_fixtures.items(): #parcours du fichier JSON
            self.board.append({
                                "name": fixture_name,
                                "current_type": "sequence", #type de couleur actuelle (sequence, kick)
                                "dimmer": {"id": self.get_channel(fixture_name, "dimmer"),"value": 255 }, #canal dimmer
                                "sequence_red": {"id": self.get_channel(fixture_name, "red"), "value": 255},
                                "sequence_green": {"id": self.get_channel(fixture_name, "green"), "value": 255},
                                "sequence_blue": {"id": self.get_channel(fixture_name, "blue"), "value": 255},
                                "sequence_current_color": self.sequence_colors[0], # première couleur du thème
                                "sequence_intensity": 1, #intensité actuelle dans la séquence (0-100%)
                                "sequence_color_start_time": self.last_update_time, #temps de début de la couleur actuelle
                                "sequence_color_duration": 1, #durée par défaut en milisecondes
                                "sequence_fade_duration": 0.5, #durée de fondu par défaut en milisecondes
                                "sequence_next_color": self.sequence_colors[1] if len(self.sequence_colors) > 1 else self.sequence_colors[0],
                                "kick_respond": fixture["kick_respond"], #indique si le kick est activé pour cette fixture
                                "kick_current_color": self.kick_colors[0], # première couleur du thème
                                "kick_activated": False, #indique si le kick est activé
                                "kick_duration": 0.2, #durée du kick en milisecondes
                                "kick_red": {"id": self.get_channel(fixture_name, "red"), "value": 0},
                                "kick_green": {"id": self.get_channel(fixture_name, "green"), "value": 0},
                                "kick_blue": {"id": self.get_channel(fixture_name, "blue"), "value": 0},
                              })
        for fixture in self.board:
            print(f"Loaded fixture: {fixture['name']} at DMX addr dim:{fixture['dimmer']['id']}, red:{fixture['sequence_red']['id']}, green:{fixture['sequence_green']['id']}, blue:{fixture['sequence_blue']['id']}")

    def get_channel(self, p_fixture_name, p_channel_name):
        channels = self.available_fixtures[p_fixture_name]["channels"]
        if p_channel_name not in channels:
            return "NA"
        return channels[p_channel_name]["id"] + self.available_fixtures[p_fixture_name]["dmx_address"] - 1
    
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
        p_fixture["sequence_current_color"] = p_new_color
        p_fixture["sequence_red"]["value"] = self.get_color_r(p_new_color) 
        p_fixture["sequence_green"]["value"] = self.get_color_g(p_new_color) 
        p_fixture["sequence_blue"]["value"] = self.get_color_b(p_new_color)
        p_fixture["sequence_color_start_time"] = p_current_time

    def apply_intensity_modulation(self, p_fixture):
        intensity = p_fixture["sequence_intensity"]
        p_fixture["sequence_red"]["value"] = int(p_fixture["sequence_red"]["value"] * intensity)
        p_fixture["sequence_green"]["value"] = int(p_fixture["sequence_green"]["value"] * intensity)
        p_fixture["sequence_blue"]["value"] = int(p_fixture["sequence_blue"]["value"] * intensity)

    def update_sequence_color_to_next(self, p_fixture, p_current_color, p_new_color, p_percent):
        p_fixture["sequence_red"]["value"] = int(self.get_color_r(p_current_color) + (self.get_color_r(p_new_color) - self.get_color_r(p_current_color)) * p_percent)
        p_fixture["sequence_green"]["value"] = int(self.get_color_g(p_current_color) + (self.get_color_g(p_new_color) - self.get_color_g(p_current_color)) * p_percent)
        p_fixture["sequence_blue"]["value"] = int(self.get_color_b(p_current_color) + (self.get_color_b(p_new_color) - self.get_color_b(p_current_color)) * p_percent)

    def update_kick_color_to_next(self, p_fixture, p_current_color, p_seq_r, p_seq_g, p_seq_b, p_percent):
        p_fixture["kick_red"]["value"] = int(self.get_color_r(p_current_color) + (p_seq_r - self.get_color_r(p_current_color)) * p_percent)
        p_fixture["kick_green"]["value"] = int(self.get_color_g(p_current_color) + (p_seq_g - self.get_color_g(p_current_color)) * p_percent)
        p_fixture["kick_blue"]["value"] = int(self.get_color_b(p_current_color) + (p_seq_b - self.get_color_b(p_current_color)) * p_percent)

    def activate_kick(self):
        current_time = time()
        for fixture in self.board:
            if fixture["kick_respond"]:
                fixture["kick_activated"] = True
                fixture["kick_start_time"] = current_time
                fixture["kick_current_color"] = self.get_next_color_in_theme_by_type(self.current_theme, "kick", fixture["kick_current_color"])
                fixture["kick_red"]["value"] = self.get_color_r(fixture["kick_current_color"])
                fixture["kick_green"]["value"] = self.get_color_g(fixture["kick_current_color"])
                fixture["kick_blue"]["value"] = self.get_color_b(fixture["kick_current_color"])

    def update_board(self):
        current_time = time()
        # Parcours de chaque fixture pour mettre à jour sa couleur
        for fixture in self.board:
            elapsed = current_time - fixture["sequence_color_start_time"]
            color_duration = fixture["sequence_color_duration"] 
            fade_duration = fixture["sequence_fade_duration"]
            begin_fade_percent = (color_duration - fade_duration) / color_duration
            fade_start = color_duration * begin_fade_percent
            fade_end = fade_start + fade_duration
            # Met à jour la couleur de chaque fixture en fonction du temps écoulé
            # Vérifie si la durée de la couleur actuelle est écoulée
            if elapsed >= color_duration: 
                # Passer à la couleur suivante dans la séquence
                fixture["sequence_current_color"] = fixture["sequence_next_color"]
                fixture["sequence_next_color"] = self.get_next_color_in_theme_by_type(self.current_theme, "sequence", fixture["sequence_next_color"])
                self.update_new_color_sequence(fixture, fixture["sequence_current_color"], current_time)
            # Vérifie si la durée de la couleur actuelle est à moitié écoulée
            elif fade_start <= elapsed < fade_end:
                percent = min((elapsed - fade_start) / fade_duration, 1)
                self.update_sequence_color_to_next(fixture, fixture["sequence_current_color"], fixture["sequence_next_color"], percent)
            else:
                pass
            self.apply_intensity_modulation(fixture)
        for fixture in self.board:
            if fixture["kick_activated"]:
                kick_elapsed = current_time - fixture["kick_start_time"]
                if kick_elapsed >= fixture["kick_duration"]:
                    fixture["kick_activated"] = False
                else:
                    # Appliquer l'interpolation vers la couleur de la sequence active
                    self.update_kick_color_to_next(fixture, fixture["kick_current_color"], fixture["sequence_red"]["value"], fixture["sequence_green"]["value"], fixture["sequence_blue"]["value"], kick_elapsed / fixture["kick_duration"])
        self.last_update_time = current_time
        
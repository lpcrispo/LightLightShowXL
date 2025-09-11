import json
from time import time
import random

class MainBoard:
    def __init__(self, p_theme="random", p_style="random"):
        self.board = [] #création du tableau vide
        self.last_update_time = time()  # Initialisation du temps de la dernière mise à jour
        self.available_fixtures = {} #initialisation du dictionnaire de fixtures vide
        self.available_colors = {} #initialisation du dictionnaire de couleurs vide
        self.available_themes = {} #initialisation du dictionnaire de thèmes vide
        self.sequence_colors = {} #initialisation de la séquence de couleurs vide
        
        self.transition_beats = 5
        self.energy_levels = {
            'bass': "faible",
            'mid': "faible",
            'high': "faible",
            'timestamp': time(),
            'intensity': 0,
        }
        
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
         
        self.change_theme(p_theme, p_style) #thème par défaut
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
                                "repos_activated": False, #indique si le mode repos est activé
                                "repos_red": {"id": self.get_channel(fixture_name, "red"), "value": 10},
                                "repos_green": {"id": self.get_channel(fixture_name, "green"), "value": 10},
                                "repos_blue": {"id": self.get_channel(fixture_name, "blue"), "value": 10},
                              })
        for fixture in self.board:
            print(f"Loaded fixture: {fixture['name']} at DMX addr dim:{fixture['dimmer']['id']}, red:{fixture['sequence_red']['id']}, green:{fixture['sequence_green']['id']}, blue:{fixture['sequence_blue']['id']}")
        self.change_theme(p_theme, p_style) #applique le thème initial


    def get_channel(self, p_fixture_name, p_channel_name):
        channels = self.available_fixtures[p_fixture_name]["channels"]
        if p_channel_name not in channels:
            return "NA"
        return channels[p_channel_name]["id"] + self.available_fixtures[p_fixture_name]["dmx_address"] - 1

    def assign_starting_color_to_fixtures(self, p_style="random", p_theme="default"):
        # assigne une couleur de départ selon le style (random, same, alternate, gradient left-right, gradient right-left, sides to center, center to sides)
        if p_theme not in self.available_themes:
            print(f"Theme {p_theme} not found. No changes made.")
            return
        if p_style not in ["random", "same", "alternate", "gradient left-right", "gradient right-left", "sides to center", "center to sides"]:
            print(f"Style {p_style} not recognized. No changes made.")
            return
        if p_style == "random":
            p_style = random.choice(["same", "alternate", "gradient left-right", "gradient right-left", "sides to center", "center to sides"])
            print(f"Randomly selected style: {p_style}")
            
        self.sequence_colors = self.available_themes[p_theme]["sequence"]
        self.kick_colors = self.available_themes[p_theme]["kick"]
        
        num_colors = len(self.sequence_colors)
        num_fixtures = len(self.board)
        
        
        if num_colors == 0 or num_fixtures == 0:
            print("No colors or fixtures available. No changes made.")
            return
        if p_style == "same": #toutes les fixtures ont la même couleur de départ
            starting_color = self.sequence_colors[0]
            for fixture in self.board:
                fixture["sequence_current_color"] = starting_color
                fixture["sequence_next_color"] = self.sequence_colors[1] if num_colors > 1 else self.sequence_colors[0]
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
        elif p_style == "alternate": #les fixtures alternent les couleurs de départ
            for i, fixture in enumerate(self.board):
                starting_color = self.sequence_colors[i % num_colors]
                fixture["sequence_current_color"] = starting_color
                fixture["sequence_next_color"] = self.sequence_colors[(i + 1) % num_colors]
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
        elif p_style == "gradient left-right": #gradient de gauche à droite
            for i, fixture in enumerate(self.board):
                color_index = int((i / (num_fixtures - 1)) * (num_colors - 1)) if num_fixtures > 1 else 0
                starting_color = self.sequence_colors[color_index]
                fixture["sequence_current_color"] = starting_color
                fixture["sequence_next_color"] = self.sequence_colors[(color_index + 1) % num_colors]
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
        elif p_style == "gradient right-left": #gradient de droite à gauche
            for i, fixture in enumerate(self.board):
                color_index = int(((num_fixtures - 1 - i) / (num_fixtures - 1)) * (num_colors - 1)) if num_fixtures > 1 else 0
                starting_color = self.sequence_colors[color_index]
                fixture["sequence_current_color"] = starting_color
                fixture["sequence_next_color"] = self.sequence_colors[(color_index + 1) % num_colors]
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
        elif p_style == "sides to center": #gradient des côtés vers le centre
            center_index = (num_fixtures - 1) / 2
            for i, fixture in enumerate(self.board):
                distance_to_center = abs(i - center_index)
                max_distance = center_index if center_index != 0 else 1
                color_index = int(((max_distance - distance_to_center) / max_distance) * (num_colors - 1))
                starting_color = self.sequence_colors[color_index]
                fixture["sequence_current_color"] = starting_color
                fixture["sequence_next_color"] = self.sequence_colors[(color_index + 1) % num_colors]
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
        elif p_style == "center to sides": #gradient du centre vers les côtés
            center_index = (num_fixtures - 1) / 2
            for i, fixture in enumerate(self.board):
                distance_to_center = abs(i - center_index)
                max_distance = center_index if center_index != 0 else 1
                color_index = int((distance_to_center / max_distance) * (num_colors - 1))
                starting_color = self.sequence_colors[color_index]
                fixture["sequence_current_color"] = starting_color
                fixture["sequence_next_color"] = self.sequence_colors[(color_index + 1) % num_colors]
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * fixture["sequence_intensity"])
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * fixture["sequence_intensity"])

        #kick sera tjrs la première couleur du thème
        for fixture in self.board:
            fixture["kick_current_color"] = self.kick_colors[0]
            fixture["kick_red"]["value"] = self.get_color_r(fixture["kick_current_color"])
            fixture["kick_green"]["value"] = self.get_color_g(fixture["kick_current_color"])
            fixture["kick_blue"]["value"] = self.get_color_b(fixture["kick_current_color"])


    def change_theme(self, p_theme="random", p_style="random"):
        if p_theme == "random":
            p_theme = random.choice(list(self.available_themes.keys()))
        if p_theme not in self.available_themes:
            print(f"Theme {p_theme} not found. Keeping current theme {self.current_theme}.")
            return
        self.current_theme = p_theme
        self.assign_starting_color_to_fixtures(p_style=p_style, p_theme=p_theme)
        print(f"Changing to theme: {self.current_theme} with sequence colors: {self.sequence_colors} and kick colors: {self.kick_colors}")

    
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
        intensity = p_fixture["sequence_intensity"]
        p_fixture["sequence_current_color"] = p_new_color
        p_fixture["sequence_red"]["value"] = self.get_color_r(p_new_color) * intensity
        p_fixture["sequence_green"]["value"] = self.get_color_g(p_new_color) * intensity
        p_fixture["sequence_blue"]["value"] = self.get_color_b(p_new_color) * intensity
        p_fixture["sequence_color_start_time"] = p_current_time

    def apply_intensity_modulation(self, p_fixture):
        intensity = p_fixture["sequence_intensity"]
        p_fixture["sequence_red"]["value"] = int(p_fixture["sequence_red"]["value"]) #* intensity)
        p_fixture["sequence_green"]["value"] = int(p_fixture["sequence_green"]["value"]) #* intensity)
        p_fixture["sequence_blue"]["value"] = int(p_fixture["sequence_blue"]["value"]) #* intensity)

    def update_sequence_color_to_next(self, p_fixture, p_current_color, p_new_color, p_percent):
        # Appliquer l'intensité IMMÉDIATEMENT lors de la transition
        intensity = p_fixture["sequence_intensity"]
        
        # Calculer les valeurs RGB avec intensité déjà appliquée
        current_r = int(self.get_color_r(p_current_color) * intensity)
        current_g = int(self.get_color_g(p_current_color) * intensity)
        current_b = int(self.get_color_b(p_current_color) * intensity)
        
        new_r = int(self.get_color_r(p_new_color) * intensity)
        new_g = int(self.get_color_g(p_new_color) * intensity)
        new_b = int(self.get_color_b(p_new_color) * intensity)
        
        # Interpolation entre les couleurs déjà modulées par l'intensité
        p_fixture["sequence_red"]["value"] = int(current_r + ((new_r - current_r) * p_percent))
        p_fixture["sequence_green"]["value"] = int(current_g + ((new_g - current_g) * p_percent))
        p_fixture["sequence_blue"]["value"] = int(current_b + ((new_b - current_b) * p_percent))

    def update_kick_color_to_next(self, p_fixture, p_current_color, p_seq_r, p_seq_g, p_seq_b, p_percent):
        p_fixture["kick_red"]["value"] = int(self.get_color_r(p_current_color)  + (p_seq_r - self.get_color_r(p_current_color)) * p_percent)
        p_fixture["kick_green"]["value"] = int(self.get_color_g(p_current_color)  + (p_seq_g - self.get_color_g(p_current_color)) * p_percent)
        p_fixture["kick_blue"]["value"] = int(self.get_color_b(p_current_color)  + (p_seq_b - self.get_color_b(p_current_color)) * p_percent)

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

    # Met à jour la durée des séquences et des fondus en fonction du BPM
    # la duration dure 2 beats, le fade 1 beat  
    def update_sequence_duration_and_fade_from_bpm(self, p_bpm, p_last_beat_timestamp=None):
        #print(f"Updating sequence durations from BPM: {p_bpm}")
        if p_bpm <= 0:
            return
        beat_duration = 60.0 / p_bpm
        for fixture in self.board:
            fixture["sequence_color_duration"] = beat_duration
            fixture["sequence_fade_duration"] = beat_duration / 2
        self.sync_sequence_to_beat_start(p_bpm, p_last_beat_timestamp) # Optionnel: synchroniser immédiatement les séquences au début du beat

    def sync_sequence_to_beat_start(self, p_bpm, p_last_beat_timestamp=None):
        current_time = time()
        # Si on a un timestamp de beat, calculer le prochain beat prédit
        if p_last_beat_timestamp and p_bpm > 0:
            beat_interval = 60.0 / p_bpm

            # Calculer combien de beats se sont écoulés depuis le dernier beat détecté
            time_since_last_beat = current_time - p_last_beat_timestamp
            beats_elapsed = time_since_last_beat / beat_interval
            
            # Calculer le temps jusqu'au prochain beat
            time_to_next_beat = beat_interval - (time_since_last_beat % beat_interval)
            next_beat_time = current_time + time_to_next_beat
            
            #print(f"Beat sync: {beats_elapsed:.2f} beats elapsed, next beat in {time_to_next_beat:.2f}s")
            
            # Nombre de beats pour la transition graduelle
            self.transition_beats = 3  # Glisser sur 3 beats
            
            # Synchroniser toutes les fixtures sur le prochain beat
        for fixture in self.board:
            color_duration = fixture["sequence_color_duration"]
            elapsed = current_time - fixture["sequence_color_start_time"]
            
            # Calculer quand cette couleur va se terminer naturellement
            natural_end_time = fixture["sequence_color_start_time"] + color_duration
            
            # Calculer l'écart avec le prochain beat idéal
            time_diff = natural_end_time - next_beat_time
            
            if elapsed < color_duration:
                # Ajustement graduel sur plusieurs beats
                # Réduire l'écart d'un tiers à chaque cycle
                adjustment_factor = 1.0 / self.transition_beats
                time_adjustment = time_diff * adjustment_factor
                
                # Appliquer l'ajustement en modifiant le start_time
                new_start_time = fixture["sequence_color_start_time"] - time_adjustment
                fixture["sequence_color_start_time"] = new_start_time
                
                progress_percent = elapsed / color_duration
                #print(f"Beat sync {fixture['name']}: progress {progress_percent:.1%}, gradual sync (adj: {time_adjustment:.2f}s)")
            else:
                # Si la couleur est déjà finie, programmer le changement sur le prochain beat
                # mais avec un léger ajustement graduel
                adjustment_factor = 1.0 / self.transition_beats
                time_adjustment = time_diff * adjustment_factor
                
                adjusted_start_time = next_beat_time - time_adjustment
                fixture["sequence_color_start_time"] = adjusted_start_time
                fixture["sequence_current_color"] = fixture["sequence_next_color"]
                fixture["sequence_next_color"] = self.get_next_color_in_theme_by_type(
                    self.current_theme, "sequence", fixture["sequence_next_color"]
                )
                self.update_new_color_sequence(fixture, fixture["sequence_current_color"], adjusted_start_time)
                #print(f"Beat sync {fixture['name']}: scheduled color change with gradual sync (adj: {time_adjustment:.2f}s)")
        

    def update_board(self):
        current_time = time()
        # Parcours de chaque fixture pour mettre à jour sa couleur et son état
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
        
        
    def update_energy_levels_detailed(self, energy_levels):
        """Met à jour les données du mainboard avec analyse détaillée"""
        
        # Convertir les niveaux en scores numériques
        level_scores = {
            'très_faible': 1,
            'faible': 2,
            'moyenne': 3,
            'haute': 4,
            'très_haute': 5
        }
        
        # Calculer le score global pondéré
        total_score = (
            level_scores[energy_levels['bass']] * 3 +           # Bass très important
            level_scores[energy_levels['sub_bass']] * 2 +       # Sub-bass important  
            level_scores[energy_levels['mid']] * 2 +            # Mid important
            level_scores[energy_levels['low_mid']] * 1.5 +      # Low-mid modéré
            level_scores[energy_levels['high']] * 1 +           # High moins important
            level_scores[energy_levels['presence']] * 0.5       # Presence subtil
        ) / 10  # Normaliser sur 10
        
        # Utiliser l'intensité globale pour détecter refrain/couplet
        global_intensity_score = level_scores[energy_levels['global_intensity']]
        
        print(f"Global intensity: {energy_levels['global_intensity']} (score: {global_intensity_score})")
        
        # Ajuster l'intensité (plage plus large pour plus de contraste)
        if global_intensity_score == 1:  # Très faible
            for fixture in self.board:
                if fixture["repos_activated"] == False:
                    fixture["repos_activated"] = True
                    self.change_theme(p_theme="random", p_style="random")
        else:
            for fixture in self.board:
                if fixture["repos_activated"] == True:
                    fixture["repos_activated"] = False
        if global_intensity_score == 2:  # Très faible/faible
            intensity = 0.1 + (total_score / 5.0) * 0.4  # 0.1 à 0.5
        elif global_intensity_score == 3:  # Moyenne
            intensity = 0.4 + (total_score / 5.0) * 0.4  # 0.4 à 0.8
        else:  # Haute/très haute (refrain)
            intensity = 0.6 + (total_score / 5.0) * 0.4  # 0.6 à 1.0
        
        # Détecter les changements d'ambiance importants
        previous_global = getattr(self, 'previous_global_intensity', 'moyenne')
        
        # Transition couplet -> refrain
        if (previous_global in ['très_faible', 'faible'] and 
            energy_levels['global_intensity'] in ['haute', 'très_haute']):
            print("🎵 REFRAIN DÉTECTÉ - Changement de thème")
            self.change_theme(p_theme="random", p_style="random")
            
        # Transition refrain -> couplet
        elif (previous_global in ['haute', 'très_haute'] and 
            energy_levels['global_intensity'] in ['très_faible', 'faible']):
            print("🎵 COUPLET DÉTECTÉ - Mode calme")
            #self.change_theme(p_theme="random", p_style="random")
        
        # Appliquer aux fixtures
        for fixture in self.board:
            old_intensity = fixture["sequence_intensity"]
            fixture["sequence_intensity"] = intensity
             # Si l'intensité a changé, mettre à jour immédiatement les valeurs RGB actuelles
            if old_intensity != intensity:
                # Recalculer les valeurs avec la nouvelle intensité
                fixture["sequence_red"]["value"] = int(self.get_color_r(fixture["sequence_current_color"]) * intensity)
                fixture["sequence_green"]["value"] = int(self.get_color_g(fixture["sequence_current_color"]) * intensity)
                fixture["sequence_blue"]["value"] = int(self.get_color_b(fixture["sequence_current_color"]) * intensity)
            
        # Stocker pour la prochaine analyse
        self.previous_global_intensity = energy_levels['global_intensity']
        
        # Stocker les détails pour monitoring
        if not hasattr(self, 'detailed_energy_levels'):
            self.detailed_energy_levels = {}
        
        self.detailed_energy_levels.update({
            **energy_levels,
            'total_score': total_score,
            'intensity': intensity,
            'timestamp': time()
        })
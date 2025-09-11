import tkinter as tk
from views.audiodevice_view import AudioDeviceSelector
from views.start_view import StartButton
from views.fixtures_view import FixturesView

class MainView(tk.Tk):
    def __init__(self, start_callback):
        super().__init__()
        self.title("LightLightShowXL")
        self.geometry("1200x600")
        
        # frame horizontal pour les deux sections en haut
        top_frame = tk.Frame(self)
        top_frame.pack(anchor='nw', padx=10, pady=10, fill='x')
        
        # Section audio en haut à gauche
        self.audio_selector = AudioDeviceSelector(top_frame)
        self.audio_selector.pack(side='left')
    

        # Passe une lambda qui fournit l'index input choisi
        start_btn = StartButton(
            top_frame,
            start_callback=lambda: start_callback(
                self.audio_selector.get_selected_input_device_index(),
                self.audio_selector.get_selected_output_device_index()
            )
        )
        start_btn.pack(side='left', padx=10)
        
        # Bouton pour ouvrir une fenêtre séparée de monitoring (optionnel)
        fixtures_window_btn = tk.Button(
            top_frame,
            text="Fixtures Window",
            command=self.show_fixtures_monitor
        )
        fixtures_window_btn.pack(side='left', padx=10)
        
        # Bouton pour configurer les fixtures
        fixtures_config_btn = tk.Button(
            top_frame,
            text="Config Fixtures",
            command=self.show_fixtures_config
        )
        fixtures_config_btn.pack(side='left', padx=10)
        
        # Bouton pour configurer les thèmes et couleurs
        themes_config_btn = tk.Button(
            top_frame,
            text="Config Thèmes",
            command=self.show_themes_config
        )
        themes_config_btn.pack(side='left', padx=10)
        
        # Espace vide pour pousser le contenu vers le haut
        middle_frame = tk.Frame(self)
        middle_frame.pack(fill='both', expand=True)

        # Stocker la référence du mainboard pour l'utiliser plus tard
        self.mainboard = None
        self.fixtures_inline_view = None
    
    def set_mainboard(self, mainboard):
        """Méthode pour définir le mainboard après sa création"""
        self.mainboard = mainboard
    
    def show_fixtures_monitor(self):
        """Affiche la fenêtre de monitoring des fixtures"""
        if not hasattr(self, 'mainboard') or not self.mainboard:
            print("MainBoard not available yet")
            return
        from views.fixtures_view import create_fixtures_monitor
        create_fixtures_monitor(self, self.mainboard)
        
    def show_fixtures_config(self):
        """Affiche la fenêtre de configuration des fixtures"""
        from views.Fixtures_config import create_fixtures_config_window
        create_fixtures_config_window(self)
        
    def show_themes_config(self):
        """Affiche la fenêtre de configuration des thèmes et couleurs"""
        from views.Themes_and_colors_config import create_themes_colors_config_window
        create_themes_colors_config_window(self)
import tkinter as tk
from tkinter import ttk
import threading
import time

class FixturesView:
    def __init__(self, parent, mainboard):
        self.parent = parent
        self.mainboard = mainboard
        self.running = False
        self.update_thread = None
        
        # Frame principal pour la vue des fixtures
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ttk.Label(self.frame, text="Fixtures Monitor", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Frame pour contenir les carrés des fixtures
        self.fixtures_frame = ttk.Frame(self.frame)
        self.fixtures_frame.pack(fill="both", expand=True)
        
        # Dictionnaire pour stocker les widgets de chaque fixture
        self.fixture_widgets = {}
        
        # Créer les carrés pour chaque fixture
        self.create_fixture_squares()
        
        # Démarrer la mise à jour automatique
        self.start_monitoring()
    
    def create_fixture_squares(self):
        """Crée un carré coloré pour chaque fixture"""
        # Calculer le nombre de colonnes (par exemple 4 fixtures par ligne)
        columns = 4
        
        for index, fixture in enumerate(self.mainboard.board):
            row = index // columns
            col = index % columns
            
            # Frame pour chaque fixture (sans bordure)
            fixture_frame = ttk.Frame(self.fixtures_frame)
            fixture_frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # Nom de la fixture
            name_label = ttk.Label(fixture_frame, text=fixture["name"], 
                                 font=("Arial", 9, "bold"))
            name_label.pack(pady=(0, 2))
            
            # Carré couleur unique
            color_canvas = tk.Canvas(fixture_frame, width=80, height=80, 
                                   bg="black", highlightthickness=0, bd=0)
            color_canvas.pack()
            color_rect = color_canvas.create_rectangle(1, 1, 79, 79, fill="black", outline="gray", width=1)
            
            # Status indicator (petit point coloré en haut à droite du carré)
            status_indicator = color_canvas.create_oval(65, 5, 75, 15, fill="gray", outline="white")
            
            # RGB info (compact)
            rgb_label = ttk.Label(fixture_frame, text="0,0,0", font=("Arial", 8))
            rgb_label.pack(pady=(2, 0))
            
            # Stocker les widgets pour cette fixture
            self.fixture_widgets[fixture["name"]] = {
                'frame': fixture_frame,
                'canvas': color_canvas,
                'rect': color_rect,
                'status_indicator': status_indicator,
                'rgb_label': rgb_label,
                'name': fixture["name"]
            }
        
        # Configurer les colonnes pour qu'elles s'étalent uniformément
        for i in range(columns):
            self.fixtures_frame.grid_columnconfigure(i, weight=1)
    
    def start_monitoring(self):
        """Démarre le thread de surveillance des couleurs"""
        self.running = True
        self.update_thread = threading.Thread(target=self.update_colors_loop, daemon=True)
        self.update_thread.start()
    
    def stop_monitoring(self):
        """Arrête la surveillance"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
    
    def update_colors_loop(self):
        """Boucle de mise à jour des couleurs (thread séparé)"""
        while self.running:
            try:
                # Programmer la mise à jour dans le thread principal
                self.parent.after(0, self.update_fixture_colors)
                time.sleep(0.05)  # Mise à jour 20 fois par seconde
            except Exception as e:
                print(f"Erreur dans update_colors_loop: {e}")
    
    def update_fixture_colors(self):
        """Met à jour les couleurs des fixtures (thread principal)"""
        try:
            for fixture in self.mainboard.board:
                fixture_name = fixture["name"]
                
                if fixture_name in self.fixture_widgets:
                    widgets = self.fixture_widgets[fixture_name]
                    
                    # Déterminer quelle couleur afficher (kick ou sequence)
                    if fixture["kick_activated"]:
                        # Couleur de kick
                        r = fixture["kick_red"]["value"]
                        g = fixture["kick_green"]["value"]
                        b = fixture["kick_blue"]["value"]
                        
                        # Indicateur de status (rouge pour kick actif)
                        widgets['canvas'].itemconfig(widgets['status_indicator'], fill="red")
                    else:
                        # Couleur de sequence
                        r = fixture["sequence_red"]["value"]
                        g = fixture["sequence_green"]["value"]
                        b = fixture["sequence_blue"]["value"]
                        
                        # Indicateur de status
                        if fixture["kick_respond"]:
                            widgets['canvas'].itemconfig(widgets['status_indicator'], fill="green")  # Vert si prêt pour kick
                        else:
                            widgets['canvas'].itemconfig(widgets['status_indicator'], fill="gray")   # Gris si pas de kick
                    
                    # Mettre à jour le carré de couleur
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    widgets['canvas'].itemconfig(widgets['rect'], fill=hex_color)
                    
                    # Mettre à jour le label RGB
                    widgets['rgb_label'].config(text=f"{r},{g},{b}")
                    
        except Exception as e:
            print(f"Erreur dans update_fixture_colors: {e}")
    
    def destroy(self):
        """Nettoie la vue"""
        self.stop_monitoring()
        if hasattr(self, 'frame'):
            self.frame.destroy()


class FixturesInlineView:
    """Version compacte des fixtures pour intégration dans MainView"""
    def __init__(self, parent, mainboard):
        self.parent = parent
        self.mainboard = mainboard
        self.running = False
        self.update_thread = None
        
        # Dictionnaire pour stocker les widgets de chaque fixture
        self.fixture_widgets = {}
        
        # Créer la zone de scroll avec les fixtures
        self.create_scroll_area()
        
        # Créer les carrés pour chaque fixture
        self.create_fixture_squares()
        
        # Démarrer la mise à jour automatique
        self.start_monitoring()
    
    def create_scroll_area(self):
        """Crée la zone de scroll horizontal"""
        # Frame container
        self.container_frame = tk.Frame(self.parent)
        self.container_frame.pack(side='bottom', fill='x', padx=10, pady=(0, 10))
        
        # Label titre
        title_label = tk.Label(self.container_frame, text="Fixtures Monitor", 
                              font=("Arial", 12, "bold"))
        title_label.pack(anchor='w', pady=(0, 5))
        
        # Canvas avec scrollbar horizontal
        self.canvas = tk.Canvas(self.container_frame, height=120, bg='lightgray')
        self.scrollbar = ttk.Scrollbar(self.container_frame, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        # Pack les éléments
        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="bottom", fill="x")
        
        # Bind scroll de la souris
        def _on_mousewheel(event):
            self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def create_fixture_squares(self):
        """Crée un carré coloré compact pour chaque fixture en ligne horizontale"""
        for index, fixture in enumerate(self.mainboard.board):
            # Frame pour chaque fixture (très compact, sans bordure)
            fixture_frame = tk.Frame(self.scrollable_frame, bg='white')
            fixture_frame.pack(side='left', padx=1, pady=2)
            
            # Nom de la fixture (très petit)
            name_label = tk.Label(fixture_frame, text=fixture["name"], 
                                font=("Arial", 8, "bold"), bg='white')
            name_label.pack()
            
            # Carré couleur unique (plus petit)
            color_canvas = tk.Canvas(fixture_frame, width=50, height=50, 
                                   bg="black", highlightthickness=0, bd=0)
            color_canvas.pack(pady=1)
            color_rect = color_canvas.create_rectangle(1, 1, 49, 49, fill="black", outline="gray", width=1)
            
            # Status indicator (petit point)
            status_indicator = color_canvas.create_oval(40, 3, 47, 10, fill="gray", outline="white")
            
            # RGB info (très compact)
            rgb_label = tk.Label(fixture_frame, text="0,0,0", font=("Arial", 7), bg='white')
            rgb_label.pack()
            
            # Stocker les widgets pour cette fixture
            self.fixture_widgets[fixture["name"]] = {
                'frame': fixture_frame,
                'canvas': color_canvas,
                'rect': color_rect,
                'status_indicator': status_indicator,
                'rgb_label': rgb_label,
                'name': fixture["name"]
            }
    
    def start_monitoring(self):
        """Démarre le thread de surveillance des couleurs"""
        self.running = True
        self.update_thread = threading.Thread(target=self.update_colors_loop, daemon=True)
        self.update_thread.start()
    
    def stop_monitoring(self):
        """Arrête la surveillance"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1)
    
    def update_colors_loop(self):
        """Boucle de mise à jour des couleurs (thread séparé)"""
        while self.running:
            try:
                # Programmer la mise à jour dans le thread principal
                self.parent.after(0, self.update_fixture_colors)
                time.sleep(0.1)  # Mise à jour 10 fois par seconde
            except Exception as e:
                print(f"Erreur dans update_colors_loop inline: {e}")
    
    def update_fixture_colors(self):
        """Met à jour les couleurs des fixtures (thread principal)"""
        try:
            for fixture in self.mainboard.board:
                fixture_name = fixture["name"]
                
                if fixture_name in self.fixture_widgets:
                    widgets = self.fixture_widgets[fixture_name]
                    
                    # Déterminer quelle couleur afficher (kick ou sequence)
                    if fixture["kick_activated"]:
                        # Couleur de kick
                        r = fixture["kick_red"]["value"]
                        g = fixture["kick_green"]["value"]
                        b = fixture["kick_blue"]["value"]
                        
                        # Indicateur de status (rouge pour kick actif)
                        widgets['canvas'].itemconfig(widgets['status_indicator'], fill="red")
                    else:
                        # Couleur de sequence
                        r = fixture["sequence_red"]["value"]
                        g = fixture["sequence_green"]["value"]
                        b = fixture["sequence_blue"]["value"]
                        
                        # Indicateur de status
                        if fixture["kick_respond"]:
                            widgets['canvas'].itemconfig(widgets['status_indicator'], fill="green")  # Vert si prêt pour kick
                        else:
                            widgets['canvas'].itemconfig(widgets['status_indicator'], fill="gray")   # Gris si pas de kick
                    
                    # Mettre à jour le carré de couleur
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    widgets['canvas'].itemconfig(widgets['rect'], fill=hex_color)
                    
                    # Mettre à jour le label RGB
                    widgets['rgb_label'].config(text=f"{r},{g},{b}")
                    
        except Exception as e:
            print(f"Erreur dans update_fixture_colors inline: {e}")
    
    def destroy(self):
        """Nettoie la vue"""
        self.stop_monitoring()
        if hasattr(self, 'container_frame'):
            self.container_frame.destroy()


# Fonction pour créer une fenêtre de monitoring des fixtures
def create_fixtures_monitor(parent_window, mainboard):
    """Crée une fenêtre de monitoring des fixtures"""
    monitor_window = tk.Toplevel(parent_window)
    monitor_window.title("Fixtures Monitor - LightLightShowXL")
    monitor_window.geometry("900x700")
    
    fixtures_view = FixturesView(monitor_window, mainboard)
    
    # Gérer la fermeture de la fenêtre
    def on_closing():
        fixtures_view.destroy()
        monitor_window.destroy()
    
    monitor_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    return fixtures_view
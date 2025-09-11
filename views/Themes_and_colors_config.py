import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os
from copy import deepcopy

class ThemesAndColorsConfigView:
    def __init__(self, parent):
        self.parent = parent
        self.colors_data = {}
        self.themes_data = {}
        self.selected_color = None
        self.selected_theme = None
        self.colors_file_path = "themes/colors.json"
        self.themes_file_path = "themes/themes.json"
        
        # Charger les données existantes
        self.load_colors()
        self.load_themes()
        
        # Créer l'interface
        self.create_widgets()
        self.populate_lists()
    
    def load_colors(self):
        """Charge les couleurs depuis le fichier JSON"""
        try:
            if os.path.exists(self.colors_file_path):
                with open(self.colors_file_path, 'r', encoding='utf-8') as f:
                    self.colors_data = json.load(f)
            else:
                self.colors_data = {}
                messagebox.showwarning("Attention", f"Fichier {self.colors_file_path} non trouvé. Un nouveau sera créé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des couleurs: {e}")
            self.colors_data = {}
    
    def load_themes(self):
        """Charge les thèmes depuis le fichier JSON"""
        try:
            if os.path.exists(self.themes_file_path):
                with open(self.themes_file_path, 'r', encoding='utf-8') as f:
                    self.themes_data = json.load(f)
            else:
                self.themes_data = {}
                messagebox.showwarning("Attention", f"Fichier {self.themes_file_path} non trouvé. Un nouveau sera créé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des thèmes: {e}")
            self.themes_data = {}
    
    def save_colors(self):
        """Sauvegarde les couleurs dans le fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.colors_file_path), exist_ok=True)
            with open(self.colors_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.colors_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Succès", "Couleurs sauvegardées avec succès!")
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde des couleurs: {e}")
            return False
    
    def save_themes(self):
        """Sauvegarde les thèmes dans le fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.themes_file_path), exist_ok=True)
            with open(self.themes_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.themes_data, f, indent=6, ensure_ascii=False)
            messagebox.showinfo("Succès", "Thèmes sauvegardés avec succès!")
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde des thèmes: {e}")
            return False
    
    def create_widgets(self):
        """Crée l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Configuration Thèmes et Couleurs", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Notebook pour séparer couleurs et thèmes
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # ===== ONGLET COULEURS =====
        colors_frame = ttk.Frame(self.notebook)
        self.notebook.add(colors_frame, text="Couleurs")
        self.create_colors_tab(colors_frame)
        
        # ===== ONGLET THÈMES =====
        themes_frame = ttk.Frame(self.notebook)
        self.notebook.add(themes_frame, text="Thèmes")
        self.create_themes_tab(themes_frame)
    
    def create_colors_tab(self, parent_frame):
        """Crée l'onglet de gestion des couleurs"""
        # Frame pour la disposition horizontale
        content_frame = ttk.Frame(parent_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== PARTIE GAUCHE: Liste des couleurs =====
        left_frame = ttk.LabelFrame(content_frame, text="Liste des Couleurs", padding=10)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_frame.configure(width=350)
        
        # Boutons d'action pour les couleurs
        colors_buttons_frame = ttk.Frame(left_frame)
        colors_buttons_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(colors_buttons_frame, text="Nouvelle", command=self.new_color).pack(side="left", padx=(0, 5))
        ttk.Button(colors_buttons_frame, text="Dupliquer", command=self.duplicate_color).pack(side="left", padx=(0, 5))
        ttk.Button(colors_buttons_frame, text="Supprimer", command=self.delete_color).pack(side="left")
        
        # Liste des couleurs avec aperçu
        colors_list_frame = ttk.Frame(left_frame)
        colors_list_frame.pack(fill="both", expand=True)
        
        # Treeview pour afficher les couleurs avec aperçu
        columns = ("RGB", "Hex")
        self.colors_tree = ttk.Treeview(colors_list_frame, columns=columns, show="tree headings", height=15)
        
        self.colors_tree.heading("#0", text="Nom")
        self.colors_tree.heading("RGB", text="RGB")
        self.colors_tree.heading("Hex", text="Hex")
        
        self.colors_tree.column("#0", width=120)
        self.colors_tree.column("RGB", width=80)
        self.colors_tree.column("Hex", width=80)
        
        colors_scroll = ttk.Scrollbar(colors_list_frame, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=colors_scroll.set)
        
        self.colors_tree.pack(side="left", fill="both", expand=True)
        colors_scroll.pack(side="right", fill="y")
        
        self.colors_tree.bind('<<TreeviewSelect>>', self.on_color_select)
        
        # ===== PARTIE DROITE: Édition de couleur =====
        right_frame = ttk.LabelFrame(content_frame, text="Édition de Couleur", padding=10)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Informations de couleur
        color_info_frame = ttk.LabelFrame(right_frame, text="Informations", padding=10)
        color_info_frame.pack(fill="x", pady=(0, 10))
        
        # Nom de la couleur
        ttk.Label(color_info_frame, text="Nom:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.color_name_var = tk.StringVar()
        ttk.Entry(color_info_frame, textvariable=self.color_name_var, width=30).grid(row=0, column=1, sticky="ew", pady=2)
        
        # Valeurs RGB
        ttk.Label(color_info_frame, text="Rouge (0-255):").grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.red_var = tk.StringVar()
        red_spinbox = ttk.Spinbox(color_info_frame, textvariable=self.red_var, from_=0, to=255, width=28)
        red_spinbox.grid(row=1, column=1, sticky="ew", pady=2)
        red_spinbox.bind('<KeyRelease>', self.on_color_change)
        red_spinbox.bind('<<Increment>>', self.on_color_change)
        red_spinbox.bind('<<Decrement>>', self.on_color_change)
        
        ttk.Label(color_info_frame, text="Vert (0-255):").grid(row=2, column=0, sticky="w", padx=(0, 10))
        self.green_var = tk.StringVar()
        green_spinbox = ttk.Spinbox(color_info_frame, textvariable=self.green_var, from_=0, to=255, width=28)
        green_spinbox.grid(row=2, column=1, sticky="ew", pady=2)
        green_spinbox.bind('<KeyRelease>', self.on_color_change)
        green_spinbox.bind('<<Increment>>', self.on_color_change)
        green_spinbox.bind('<<Decrement>>', self.on_color_change)
        
        ttk.Label(color_info_frame, text="Bleu (0-255):").grid(row=3, column=0, sticky="w", padx=(0, 10))
        self.blue_var = tk.StringVar()
        blue_spinbox = ttk.Spinbox(color_info_frame, textvariable=self.blue_var, from_=0, to=255, width=28)
        blue_spinbox.grid(row=3, column=1, sticky="ew", pady=2)
        blue_spinbox.bind('<KeyRelease>', self.on_color_change)
        blue_spinbox.bind('<<Increment>>', self.on_color_change)
        blue_spinbox.bind('<<Decrement>>', self.on_color_change)
        
        color_info_frame.columnconfigure(1, weight=1)
        
        # Aperçu de couleur et sélecteur
        preview_frame = ttk.LabelFrame(right_frame, text="Aperçu", padding=10)
        preview_frame.pack(fill="x", pady=(0, 10))
        
        # Canvas pour l'aperçu
        self.color_preview = tk.Canvas(preview_frame, width=200, height=100, bg="black")
        self.color_preview.pack(pady=5)
        self.color_rect = self.color_preview.create_rectangle(2, 2, 198, 98, fill="black", outline="gray")
        
        # Bouton sélecteur de couleur
        ttk.Button(preview_frame, text="Sélectionner Couleur", command=self.choose_color).pack(pady=5)
        
        # Boutons de sauvegarde pour les couleurs
        colors_save_frame = ttk.Frame(right_frame)
        colors_save_frame.pack(fill="x", pady=10)
        
        ttk.Button(colors_save_frame, text="Sauvegarder Couleur", command=self.save_current_color).pack(side="left", padx=(0, 10))
        ttk.Button(colors_save_frame, text="Sauvegarder Tout", command=self.save_colors).pack(side="left", padx=(0, 10))
        ttk.Button(colors_save_frame, text="Recharger", command=self.reload_colors).pack(side="left")
    
    def create_themes_tab(self, parent_frame):
        """Crée l'onglet de gestion des thèmes"""
        # Frame pour la disposition horizontale
        content_frame = ttk.Frame(parent_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== PARTIE GAUCHE: Liste des thèmes =====
        left_frame = ttk.LabelFrame(content_frame, text="Liste des Thèmes", padding=10)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_frame.configure(width=300)
        
        # Boutons d'action pour les thèmes
        themes_buttons_frame = ttk.Frame(left_frame)
        themes_buttons_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(themes_buttons_frame, text="Nouveau", command=self.new_theme).pack(side="left", padx=(0, 5))
        ttk.Button(themes_buttons_frame, text="Dupliquer", command=self.duplicate_theme).pack(side="left", padx=(0, 5))
        ttk.Button(themes_buttons_frame, text="Supprimer", command=self.delete_theme).pack(side="left")
        
        # Liste des thèmes
        themes_list_frame = ttk.Frame(left_frame)
        themes_list_frame.pack(fill="both", expand=True)
        
        self.themes_listbox = tk.Listbox(themes_list_frame, height=20)
        themes_scrollbar = ttk.Scrollbar(themes_list_frame, orient="vertical", command=self.themes_listbox.yview)
        self.themes_listbox.configure(yscrollcommand=themes_scrollbar.set)
        
        self.themes_listbox.pack(side="left", fill="both", expand=True)
        themes_scrollbar.pack(side="right", fill="y")
        
        self.themes_listbox.bind('<<ListboxSelect>>', self.on_theme_select)
        
        # ===== PARTIE DROITE: Édition de thème =====
        right_frame = ttk.LabelFrame(content_frame, text="Édition de Thème", padding=10)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Nom du thème
        theme_name_frame = ttk.Frame(right_frame)
        theme_name_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(theme_name_frame, text="Nom du thème:").pack(side="left", padx=(0, 10))
        self.theme_name_var = tk.StringVar()
        ttk.Entry(theme_name_frame, textvariable=self.theme_name_var, width=30).pack(side="left", fill="x", expand=True)
        
        # Couleurs de séquence
        sequence_frame = ttk.LabelFrame(right_frame, text="Couleurs de Séquence", padding=10)
        sequence_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Boutons pour gérer la séquence
        sequence_buttons_frame = ttk.Frame(sequence_frame)
        sequence_buttons_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(sequence_buttons_frame, text="Ajouter", command=self.add_sequence_color).pack(side="left", padx=(0, 5))
        ttk.Button(sequence_buttons_frame, text="Supprimer", command=self.remove_sequence_color).pack(side="left", padx=(0, 5))
        ttk.Button(sequence_buttons_frame, text="↑", command=self.move_sequence_up).pack(side="left", padx=(0, 5))
        ttk.Button(sequence_buttons_frame, text="↓", command=self.move_sequence_down).pack(side="left")
        
        # Liste des couleurs de séquence
        self.sequence_listbox = tk.Listbox(sequence_frame, height=8)
        sequence_scroll = ttk.Scrollbar(sequence_frame, orient="vertical", command=self.sequence_listbox.yview)
        self.sequence_listbox.configure(yscrollcommand=sequence_scroll.set)
        
        self.sequence_listbox.pack(side="left", fill="both", expand=True)
        sequence_scroll.pack(side="right", fill="y")
        
        # Couleurs de kick
        kick_frame = ttk.LabelFrame(right_frame, text="Couleurs de Kick", padding=10)
        kick_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Boutons pour gérer les kicks
        kick_buttons_frame = ttk.Frame(kick_frame)
        kick_buttons_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(kick_buttons_frame, text="Ajouter", command=self.add_kick_color).pack(side="left", padx=(0, 5))
        ttk.Button(kick_buttons_frame, text="Supprimer", command=self.remove_kick_color).pack(side="left", padx=(0, 5))
        ttk.Button(kick_buttons_frame, text="↑", command=self.move_kick_up).pack(side="left", padx=(0, 5))
        ttk.Button(kick_buttons_frame, text="↓", command=self.move_kick_down).pack(side="left")
        
        # Liste des couleurs de kick
        self.kick_listbox = tk.Listbox(kick_frame, height=5)
        kick_scroll = ttk.Scrollbar(kick_frame, orient="vertical", command=self.kick_listbox.yview)
        self.kick_listbox.configure(yscrollcommand=kick_scroll.set)
        
        self.kick_listbox.pack(side="left", fill="both", expand=True)
        kick_scroll.pack(side="right", fill="y")
        
        # Boutons de sauvegarde pour les thèmes
        themes_save_frame = ttk.Frame(right_frame)
        themes_save_frame.pack(fill="x", pady=10)
        
        ttk.Button(themes_save_frame, text="Sauvegarder Thème", command=self.save_current_theme).pack(side="left", padx=(0, 10))
        ttk.Button(themes_save_frame, text="Sauvegarder Tout", command=self.save_themes).pack(side="left", padx=(0, 10))
        ttk.Button(themes_save_frame, text="Recharger", command=self.reload_themes).pack(side="left")
    
    def populate_lists(self):
        """Remplit les listes de couleurs et thèmes"""
        self.populate_colors_list()
        self.populate_themes_list()
    
    def populate_colors_list(self):
        """Remplit la liste des couleurs"""
        # Vider le treeview
        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)
        
        # Ajouter les couleurs triées
        for color_name in sorted(self.colors_data.keys()):
            color_data = self.colors_data[color_name]
            r = color_data.get("red", 0)
            g = color_data.get("green", 0)
            b = color_data.get("blue", 0)
            rgb_text = f"{r},{g},{b}"
            hex_text = f"#{r:02x}{g:02x}{b:02x}"
            
            item = self.colors_tree.insert("", "end", text=color_name, values=(rgb_text, hex_text))
            
            # Essayer de colorer la ligne (peut ne pas fonctionner sur tous les systèmes)
            try:
                self.colors_tree.set(item, "RGB", rgb_text)
                self.colors_tree.set(item, "Hex", hex_text)
            except:
                pass
    
    def populate_themes_list(self):
        """Remplit la liste des thèmes"""
        self.themes_listbox.delete(0, tk.END)
        for theme_name in sorted(self.themes_data.keys()):
            self.themes_listbox.insert(tk.END, theme_name)
    
    def on_color_select(self, event):
        """Gère la sélection d'une couleur"""
        selection = self.colors_tree.selection()
        if selection:
            item = selection[0]
            color_name = self.colors_tree.item(item)["text"]
            self.selected_color = color_name
            self.load_color_data(color_name)
    
    def on_theme_select(self, event):
        """Gère la sélection d'un thème"""
        selection = self.themes_listbox.curselection()
        if selection:
            theme_name = self.themes_listbox.get(selection[0])
            self.selected_theme = theme_name
            self.load_theme_data(theme_name)
    
    def load_color_data(self, color_name):
        """Charge les données d'une couleur dans l'interface"""
        if color_name not in self.colors_data:
            return
        
        color_data = self.colors_data[color_name]
        self.color_name_var.set(color_name)
        self.red_var.set(str(color_data.get("red", 0)))
        self.green_var.set(str(color_data.get("green", 0)))
        self.blue_var.set(str(color_data.get("blue", 0)))
        
        self.update_color_preview()
    
    def load_theme_data(self, theme_name):
        """Charge les données d'un thème dans l'interface"""
        if theme_name not in self.themes_data:
            return
        
        theme_data = self.themes_data[theme_name]
        self.theme_name_var.set(theme_name)
        
        # Charger les couleurs de séquence
        self.sequence_listbox.delete(0, tk.END)
        for color in theme_data.get("sequence", []):
            self.sequence_listbox.insert(tk.END, color)
        
        # Charger les couleurs de kick
        self.kick_listbox.delete(0, tk.END)
        for color in theme_data.get("kick", []):
            self.kick_listbox.insert(tk.END, color)
    
    def on_color_change(self, event=None):
        """Met à jour l'aperçu quand les valeurs RGB changent"""
        self.update_color_preview()
    
    def update_color_preview(self):
        """Met à jour l'aperçu de couleur"""
        try:
            r = int(self.red_var.get() or 0)
            g = int(self.green_var.get() or 0)
            b = int(self.blue_var.get() or 0)
            
            # S'assurer que les valeurs sont dans la plage valide
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            self.color_preview.itemconfig(self.color_rect, fill=hex_color)
            
        except (ValueError, tk.TclError):
            # Si les valeurs ne sont pas valides, utiliser noir
            self.color_preview.itemconfig(self.color_rect, fill="black")
    
    def choose_color(self):
        """Ouvre le sélecteur de couleur"""
        try:
            r = int(self.red_var.get() or 0)
            g = int(self.green_var.get() or 0)
            b = int(self.blue_var.get() or 0)
            initial_color = (r, g, b)
        except ValueError:
            initial_color = (0, 0, 0)
        
        color = colorchooser.askcolor(color=initial_color, title="Choisir une couleur")
        if color[0]:  # Si une couleur a été sélectionnée
            r, g, b = [int(x) for x in color[0]]
            self.red_var.set(str(r))
            self.green_var.set(str(g))
            self.blue_var.set(str(b))
            self.update_color_preview()
    
    def new_color(self):
        """Crée une nouvelle couleur"""
        name = f"nouvelle_couleur_{len(self.colors_data) + 1}"
        self.colors_data[name] = {"red": 255, "green": 255, "blue": 255}
        self.populate_colors_list()
        self.select_color_in_list(name)
    
    def duplicate_color(self):
        """Duplique la couleur sélectionnée"""
        if not self.selected_color:
            messagebox.showwarning("Attention", "Veuillez sélectionner une couleur à dupliquer")
            return
        
        original_color = self.colors_data[self.selected_color]
        new_name = f"{self.selected_color}_copie"
        
        counter = 1
        while new_name in self.colors_data:
            new_name = f"{self.selected_color}_copie_{counter}"
            counter += 1
        
        self.colors_data[new_name] = deepcopy(original_color)
        self.populate_colors_list()
        self.select_color_in_list(new_name)
    
    def delete_color(self):
        """Supprime la couleur sélectionnée"""
        if not self.selected_color:
            messagebox.showwarning("Attention", "Veuillez sélectionner une couleur à supprimer")
            return
        
        if messagebox.askyesno("Confirmer", f"Êtes-vous sûr de vouloir supprimer '{self.selected_color}' ?"):
            del self.colors_data[self.selected_color]
            self.selected_color = None
            self.populate_colors_list()
            self.clear_color_form()
    
    def select_color_in_list(self, color_name):
        """Sélectionne une couleur dans la liste"""
        for item in self.colors_tree.get_children():
            if self.colors_tree.item(item)["text"] == color_name:
                self.colors_tree.selection_set(item)
                self.colors_tree.focus(item)
                self.colors_tree.see(item)
                self.selected_color = color_name
                self.load_color_data(color_name)
                break
    
    def save_current_color(self):
        """Sauvegarde la couleur actuellement éditée"""
        if not self.validate_color_data():
            return
        
        old_name = self.selected_color
        new_name = self.color_name_var.get().strip()
        
        if old_name != new_name and new_name in self.colors_data:
            messagebox.showerror("Erreur", f"Le nom '{new_name}' est déjà utilisé")
            return
        
        color_data = {
            "red": int(self.red_var.get()),
            "green": int(self.green_var.get()),
            "blue": int(self.blue_var.get())
        }
        
        if old_name and old_name != new_name and old_name in self.colors_data:
            del self.colors_data[old_name]
        
        self.colors_data[new_name] = color_data
        self.selected_color = new_name
        
        self.populate_colors_list()
        self.select_color_in_list(new_name)
        messagebox.showinfo("Succès", f"Couleur '{new_name}' sauvegardée!")
    
    def validate_color_data(self):
        """Valide les données de couleur"""
        try:
            name = self.color_name_var.get().strip()
            if not name:
                messagebox.showerror("Erreur", "Le nom de la couleur est requis")
                return False
            
            r = int(self.red_var.get())
            g = int(self.green_var.get())
            b = int(self.blue_var.get())
            
            if not (0 <= r <= 255) or not (0 <= g <= 255) or not (0 <= b <= 255):
                messagebox.showerror("Erreur", "Les valeurs RGB doivent être entre 0 et 255")
                return False
            
            return True
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
            return False
    
    def new_theme(self):
        """Crée un nouveau thème"""
        name = f"nouveau_theme_{len(self.themes_data) + 1}"
        self.themes_data[name] = {
            "sequence": ["white"],
            "kick": ["white"]
        }
        self.populate_themes_list()
        self.select_theme_in_list(name)
    
    def duplicate_theme(self):
        """Duplique le thème sélectionné"""
        if not self.selected_theme:
            messagebox.showwarning("Attention", "Veuillez sélectionner un thème à dupliquer")
            return
        
        original_theme = self.themes_data[self.selected_theme]
        new_name = f"{self.selected_theme}_copie"
        
        counter = 1
        while new_name in self.themes_data:
            new_name = f"{self.selected_theme}_copie_{counter}"
            counter += 1
        
        self.themes_data[new_name] = deepcopy(original_theme)
        self.populate_themes_list()
        self.select_theme_in_list(new_name)
    
    def delete_theme(self):
        """Supprime le thème sélectionné"""
        if not self.selected_theme:
            messagebox.showwarning("Attention", "Veuillez sélectionner un thème à supprimer")
            return
        
        if messagebox.askyesno("Confirmer", f"Êtes-vous sûr de vouloir supprimer '{self.selected_theme}' ?"):
            del self.themes_data[self.selected_theme]
            self.selected_theme = None
            self.populate_themes_list()
            self.clear_theme_form()
    
    def select_theme_in_list(self, theme_name):
        """Sélectionne un thème dans la liste"""
        self.themes_listbox.selection_clear(0, tk.END)
        for i in range(self.themes_listbox.size()):
            if self.themes_listbox.get(i) == theme_name:
                self.themes_listbox.selection_set(i)
                self.themes_listbox.see(i)
                self.selected_theme = theme_name
                self.load_theme_data(theme_name)
                break
    
    def add_sequence_color(self):
        """Ajoute une couleur à la séquence"""
        dialog = ColorSelectorDialog(self.parent, "Sélectionner couleur pour la séquence", self.colors_data)
        if dialog.result:
            self.sequence_listbox.insert(tk.END, dialog.result)
    
    def remove_sequence_color(self):
        """Supprime la couleur sélectionnée de la séquence"""
        selection = self.sequence_listbox.curselection()
        if selection:
            self.sequence_listbox.delete(selection[0])
    
    def move_sequence_up(self):
        """Déplace la couleur sélectionnée vers le haut dans la séquence"""
        selection = self.sequence_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            item = self.sequence_listbox.get(idx)
            self.sequence_listbox.delete(idx)
            self.sequence_listbox.insert(idx - 1, item)
            self.sequence_listbox.selection_set(idx - 1)
    
    def move_sequence_down(self):
        """Déplace la couleur sélectionnée vers le bas dans la séquence"""
        selection = self.sequence_listbox.curselection()
        if selection and selection[0] < self.sequence_listbox.size() - 1:
            idx = selection[0]
            item = self.sequence_listbox.get(idx)
            self.sequence_listbox.delete(idx)
            self.sequence_listbox.insert(idx + 1, item)
            self.sequence_listbox.selection_set(idx + 1)
    
    def add_kick_color(self):
        """Ajoute une couleur de kick"""
        dialog = ColorSelectorDialog(self.parent, "Sélectionner couleur de kick", self.colors_data)
        if dialog.result:
            self.kick_listbox.insert(tk.END, dialog.result)
    
    def remove_kick_color(self):
        """Supprime la couleur de kick sélectionnée"""
        selection = self.kick_listbox.curselection()
        if selection:
            self.kick_listbox.delete(selection[0])
    
    def move_kick_up(self):
        """Déplace la couleur de kick vers le haut"""
        selection = self.kick_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            item = self.kick_listbox.get(idx)
            self.kick_listbox.delete(idx)
            self.kick_listbox.insert(idx - 1, item)
            self.kick_listbox.selection_set(idx - 1)
    
    def move_kick_down(self):
        """Déplace la couleur de kick vers le bas"""
        selection = self.kick_listbox.curselection()
        if selection and selection[0] < self.kick_listbox.size() - 1:
            idx = selection[0]
            item = self.kick_listbox.get(idx)
            self.kick_listbox.delete(idx)
            self.kick_listbox.insert(idx + 1, item)
            self.kick_listbox.selection_set(idx + 1)
    
    def save_current_theme(self):
        """Sauvegarde le thème actuellement édité"""
        old_name = self.selected_theme
        new_name = self.theme_name_var.get().strip()
        
        if not new_name:
            messagebox.showerror("Erreur", "Le nom du thème est requis")
            return
        
        if old_name != new_name and new_name in self.themes_data:
            messagebox.showerror("Erreur", f"Le nom '{new_name}' est déjà utilisé")
            return
        
        # Récupérer les couleurs des listes
        sequence_colors = [self.sequence_listbox.get(i) for i in range(self.sequence_listbox.size())]
        kick_colors = [self.kick_listbox.get(i) for i in range(self.kick_listbox.size())]
        
        if not sequence_colors:
            messagebox.showerror("Erreur", "Au moins une couleur de séquence est requise")
            return
        
        if not kick_colors:
            messagebox.showerror("Erreur", "Au moins une couleur de kick est requise")
            return
        
        theme_data = {
            "sequence": sequence_colors,
            "kick": kick_colors
        }
        
        if old_name and old_name != new_name and old_name in self.themes_data:
            del self.themes_data[old_name]
        
        self.themes_data[new_name] = theme_data
        self.selected_theme = new_name
        
        self.populate_themes_list()
        self.select_theme_in_list(new_name)
        messagebox.showinfo("Succès", f"Thème '{new_name}' sauvegardé!")
    
    def clear_color_form(self):
        """Vide le formulaire de couleur"""
        self.color_name_var.set("")
        self.red_var.set("0")
        self.green_var.set("0")
        self.blue_var.set("0")
        self.update_color_preview()
    
    def clear_theme_form(self):
        """Vide le formulaire de thème"""
        self.theme_name_var.set("")
        self.sequence_listbox.delete(0, tk.END)
        self.kick_listbox.delete(0, tk.END)
    
    def reload_colors(self):
        """Recharge les couleurs depuis le fichier"""
        self.load_colors()
        self.populate_colors_list()
        self.clear_color_form()
        self.selected_color = None
        messagebox.showinfo("Info", "Couleurs rechargées depuis le fichier")
    
    def reload_themes(self):
        """Recharge les thèmes depuis le fichier"""
        self.load_themes()
        self.populate_themes_list()
        self.clear_theme_form()
        self.selected_theme = None
        messagebox.showinfo("Info", "Thèmes rechargés depuis le fichier")


class ColorSelectorDialog:
    def __init__(self, parent, title, colors_data):
        self.result = None
        self.colors_data = colors_data
        
        # Créer la fenêtre de dialogue
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        self.dialog.wait_window()
    
    def create_widgets(self):
        """Crée les widgets du dialogue"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Liste des couleurs avec aperçu
        ttk.Label(main_frame, text="Sélectionner une couleur:").pack(pady=(0, 10))
        
        # Frame pour la liste et preview
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Treeview pour les couleurs
        columns = ("Preview", "RGB")
        self.colors_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)
        
        self.colors_tree.heading("#0", text="Nom")
        self.colors_tree.heading("Preview", text="Aperçu")
        self.colors_tree.heading("RGB", text="RGB")
        
        self.colors_tree.column("#0", width=120)
        self.colors_tree.column("Preview", width=80)
        self.colors_tree.column("RGB", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=scrollbar.set)
        
        self.colors_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Remplir la liste
        for color_name in sorted(self.colors_data.keys()):
            color_data = self.colors_data[color_name]
            r = color_data.get("red", 0)
            g = color_data.get("green", 0)
            b = color_data.get("blue", 0)
            rgb_text = f"{r},{g},{b}"
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            
            self.colors_tree.insert("", "end", text=color_name, values=(hex_color, rgb_text))
        
        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        ttk.Button(buttons_frame, text="OK", command=self.ok_clicked).pack(side="left", padx=(0, 10))
        ttk.Button(buttons_frame, text="Annuler", command=self.cancel_clicked).pack(side="left")
        
        # Double-clic pour sélectionner
        self.colors_tree.bind('<Double-1>', lambda e: self.ok_clicked())
    
    def ok_clicked(self):
        """Valide la sélection"""
        selection = self.colors_tree.selection()
        if selection:
            item = selection[0]
            color_name = self.colors_tree.item(item)["text"]
            self.result = color_name
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Annule la sélection"""
        self.dialog.destroy()


def create_themes_colors_config_window(parent):
    """Crée une fenêtre de configuration des thèmes et couleurs"""
    config_window = tk.Toplevel(parent)
    config_window.title("Configuration Thèmes et Couleurs - LightLightShowXL")
    config_window.geometry("1400x900")
    
    themes_colors_config = ThemesAndColorsConfigView(config_window)
    
    return themes_colors_config
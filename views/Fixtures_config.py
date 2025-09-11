import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from copy import deepcopy

class FixturesConfigView:
    def __init__(self, parent):
        self.parent = parent
        self.fixtures_data = {}
        self.selected_fixture = None
        self.fixtures_file_path = "fixtures/fixtures.json"
        
        # Charger les fixtures existantes
        self.load_fixtures()
        
        # Créer l'interface
        self.create_widgets()
        self.populate_fixtures_list()
    
    def load_fixtures(self):
        """Charge les fixtures depuis le fichier JSON"""
        try:
            if os.path.exists(self.fixtures_file_path):
                with open(self.fixtures_file_path, 'r', encoding='utf-8') as f:
                    self.fixtures_data = json.load(f)
            else:
                self.fixtures_data = {}
                messagebox.showwarning("Attention", f"Fichier {self.fixtures_file_path} non trouvé. Un nouveau sera créé.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des fixtures: {e}")
            self.fixtures_data = {}
    
    def save_fixtures(self):
        """Sauvegarde les fixtures dans le fichier JSON"""
        try:
            # Créer le dossier fixtures s'il n'existe pas
            os.makedirs(os.path.dirname(self.fixtures_file_path), exist_ok=True)
            
            with open(self.fixtures_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.fixtures_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Succès", "Fixtures sauvegardées avec succès!")
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def create_widgets(self):
        """Crée l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Configuration des Fixtures", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame pour la disposition horizontale
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # ===== PARTIE GAUCHE: Liste des fixtures =====
        left_frame = ttk.LabelFrame(content_frame, text="Liste des Fixtures", padding=10)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        left_frame.configure(width=300)
        
        # Boutons d'action
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Nouvelle", command=self.new_fixture).pack(side="left", padx=(0, 5))
        ttk.Button(buttons_frame, text="Dupliquer", command=self.duplicate_fixture).pack(side="left", padx=(0, 5))
        ttk.Button(buttons_frame, text="Supprimer", command=self.delete_fixture).pack(side="left")
        
        # Liste des fixtures
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill="both", expand=True)
        
        self.fixtures_listbox = tk.Listbox(list_frame, height=20)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.fixtures_listbox.yview)
        self.fixtures_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.fixtures_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.fixtures_listbox.bind('<<ListboxSelect>>', self.on_fixture_select)
        
        # ===== PARTIE DROITE: Édition de fixture =====
        right_frame = ttk.LabelFrame(content_frame, text="Édition de Fixture", padding=10)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Informations générales
        general_frame = ttk.LabelFrame(right_frame, text="Informations Générales", padding=10)
        general_frame.pack(fill="x", pady=(0, 10))
        
        # Nom
        ttk.Label(general_frame, text="Nom:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(general_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=2)
        
        # Type
        ttk.Label(general_frame, text="Type:").grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(general_frame, textvariable=self.type_var, 
                                 values=["par", "moving_head", "wash", "beam", "spot", "strobe", "laser", "smoke"], width=28)
        type_combo.grid(row=1, column=1, sticky="ew", pady=2)
        
        # Fabricant
        ttk.Label(general_frame, text="Fabricant:").grid(row=2, column=0, sticky="w", padx=(0, 10))
        self.manufacturer_var = tk.StringVar()
        ttk.Entry(general_frame, textvariable=self.manufacturer_var, width=30).grid(row=2, column=1, sticky="ew", pady=2)
        
        # Adresse DMX
        ttk.Label(general_frame, text="Adresse DMX:").grid(row=3, column=0, sticky="w", padx=(0, 10))
        self.dmx_address_var = tk.StringVar()
        ttk.Entry(general_frame, textvariable=self.dmx_address_var, width=30).grid(row=3, column=1, sticky="ew", pady=2)
        
        # Nombre de canaux
        ttk.Label(general_frame, text="Nombre de canaux:").grid(row=4, column=0, sticky="w", padx=(0, 10))
        self.channel_count_var = tk.StringVar()
        ttk.Entry(general_frame, textvariable=self.channel_count_var, width=30).grid(row=4, column=1, sticky="ew", pady=2)
        
        # Kick respond
        self.kick_respond_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="Répond au kick", 
                       variable=self.kick_respond_var).grid(row=5, column=1, sticky="w", pady=5)
        
        general_frame.columnconfigure(1, weight=1)
        
        # Canaux
        channels_frame = ttk.LabelFrame(right_frame, text="Canaux", padding=10)
        channels_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Frame pour les boutons de canaux
        channels_buttons_frame = ttk.Frame(channels_frame)
        channels_buttons_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(channels_buttons_frame, text="Ajouter Canal", command=self.add_channel).pack(side="left", padx=(0, 5))
        ttk.Button(channels_buttons_frame, text="Supprimer Canal", command=self.remove_channel).pack(side="left")
        
        # Treeview pour les canaux
        columns = ("ID", "Défaut", "Min", "Max")
        self.channels_tree = ttk.Treeview(channels_frame, columns=columns, show="tree headings", height=10)
        
        self.channels_tree.heading("#0", text="Nom du Canal")
        for col in columns:
            self.channels_tree.heading(col, text=col)
            self.channels_tree.column(col, width=80)
        
        channels_scroll = ttk.Scrollbar(channels_frame, orient="vertical", command=self.channels_tree.yview)
        self.channels_tree.configure(yscrollcommand=channels_scroll.set)
        
        self.channels_tree.pack(side="left", fill="both", expand=True)
        channels_scroll.pack(side="right", fill="y")
        
        self.channels_tree.bind('<Double-1>', self.edit_channel)
        
        # Boutons de sauvegarde
        save_frame = ttk.Frame(right_frame)
        save_frame.pack(fill="x", pady=10)
        
        ttk.Button(save_frame, text="Sauvegarder Fixture", command=self.save_current_fixture).pack(side="left", padx=(0, 10))
        ttk.Button(save_frame, text="Sauvegarder Tout", command=self.save_fixtures).pack(side="left", padx=(0, 10))
        ttk.Button(save_frame, text="Recharger", command=self.reload_fixtures).pack(side="left")
    
    def populate_fixtures_list(self):
        """Remplit la liste des fixtures triée par adresse DMX"""
        self.fixtures_listbox.delete(0, tk.END)
        
        # Trier les fixtures par adresse DMX
        fixtures_sorted = sorted(
            self.fixtures_data.items(), 
            key=lambda x: x[1].get("dmx_address", 999)  # 999 comme valeur par défaut pour les fixtures sans adresse
        )
        
        for fixture_name, fixture_data in fixtures_sorted:
            dmx_addr = fixture_data.get("dmx_address", "?")
            display_text = f"[{dmx_addr:03d}] {fixture_name}"
            self.fixtures_listbox.insert(tk.END, display_text)

    def on_fixture_select(self, event):
        """Gère la sélection d'une fixture"""
        selection = self.fixtures_listbox.curselection()
        if selection:
            # Extraire le nom de la fixture depuis le texte affiché
            display_text = self.fixtures_listbox.get(selection[0])
            # Le nom de la fixture est après "] "
            fixture_name = display_text.split("] ", 1)[1] if "] " in display_text else display_text
            self.selected_fixture = fixture_name
            self.load_fixture_data(fixture_name)
    
    def load_fixture_data(self, fixture_name):
        """Charge les données d'une fixture dans l'interface"""
        if fixture_name not in self.fixtures_data:
            return
        
        fixture = self.fixtures_data[fixture_name]
        
        # Charger les informations générales
        self.name_var.set(fixture.get("name", ""))
        self.type_var.set(fixture.get("type", ""))
        self.manufacturer_var.set(fixture.get("manufacturer", ""))
        self.dmx_address_var.set(str(fixture.get("dmx_address", 1)))
        self.channel_count_var.set(str(fixture.get("channel_count", 1)))
        self.kick_respond_var.set(fixture.get("kick_respond", False))
        
        # Charger les canaux
        self.load_channels_data(fixture.get("channels", {}))
    
    def load_channels_data(self, channels_data):
        """Charge les données des canaux dans le treeview"""
        # Vider le treeview
        for item in self.channels_tree.get_children():
            self.channels_tree.delete(item)
        
        # Ajouter les canaux
        for channel_name, channel_data in channels_data.items():
            self.channels_tree.insert("", "end", text=channel_name,
                                    values=(channel_data.get("id", 1),
                                           channel_data.get("default", 0),
                                           channel_data.get("min", 0),
                                           channel_data.get("max", 255)))
    
    def new_fixture(self):
        """Crée une nouvelle fixture"""
        name = f"Nouvelle_Fixture_{len(self.fixtures_data) + 1}"
        
        new_fixture = {
            "name": name,
            "type": "par",
            "manufacturer": "Generic",
            "dmx_address": self.get_next_dmx_address(),
            "channel_count": 4,
            "channels": {
                "red": {"id": 1, "default": 0, "min": 0, "max": 255},
                "green": {"id": 2, "default": 0, "min": 0, "max": 255},
                "blue": {"id": 3, "default": 0, "min": 0, "max": 255},
                "white": {"id": 4, "default": 0, "min": 0, "max": 255}
            },
            "kick_respond": False
        }
        
        self.fixtures_data[name] = new_fixture
        self.populate_fixtures_list()
        
        # Sélectionner la nouvelle fixture dans la liste triée
        self.select_fixture_in_list(name)
        self.selected_fixture = name
        self.load_fixture_data(name)
    
    def duplicate_fixture(self):
        """Duplique la fixture sélectionnée"""
        if not self.selected_fixture:
            messagebox.showwarning("Attention", "Veuillez sélectionner une fixture à dupliquer")
            return
        
        original_fixture = self.fixtures_data[self.selected_fixture]
        new_name = f"{self.selected_fixture}_Copie"
        
        # S'assurer que le nom est unique
        counter = 1
        while new_name in self.fixtures_data:
            new_name = f"{self.selected_fixture}_Copie_{counter}"
            counter += 1
        
        # Créer une copie profonde
        new_fixture = deepcopy(original_fixture)
        new_fixture["name"] = new_name
        new_fixture["dmx_address"] = self.get_next_dmx_address()
        
        self.fixtures_data[new_name] = new_fixture
        self.populate_fixtures_list()
        
        # Sélectionner la nouvelle fixture dans la liste triée
        self.select_fixture_in_list(new_name)
        self.selected_fixture = new_name
        self.load_fixture_data(new_name)
    
    def delete_fixture(self):
        """Supprime la fixture sélectionnée"""
        if not self.selected_fixture:
            messagebox.showwarning("Attention", "Veuillez sélectionner une fixture à supprimer")
            return
        
        if messagebox.askyesno("Confirmer", f"Êtes-vous sûr de vouloir supprimer '{self.selected_fixture}' ?"):
            del self.fixtures_data[self.selected_fixture]
            self.selected_fixture = None
            self.populate_fixtures_list()
            self.clear_form()
    
    def select_fixture_in_list(self, fixture_name):
        """Sélectionne une fixture dans la liste par son nom"""
        self.fixtures_listbox.selection_clear(0, tk.END)
        for i in range(self.fixtures_listbox.size()):
            display_text = self.fixtures_listbox.get(i)
            # Extraire le nom de la fixture depuis le texte affiché
            list_fixture_name = display_text.split("] ", 1)[1] if "] " in display_text else display_text
            if list_fixture_name == fixture_name:
                self.fixtures_listbox.selection_set(i)
                self.fixtures_listbox.see(i)  # S'assurer que l'élément est visible
                break
    
    def get_next_dmx_address(self):
        """Trouve la prochaine adresse DMX disponible"""
        used_addresses = set()
        for fixture in self.fixtures_data.values():
            dmx_addr = fixture.get("dmx_address", 1)
            channel_count = fixture.get("channel_count", 1)
            for i in range(channel_count):
                used_addresses.add(dmx_addr + i)
        
        # Trouver la première adresse libre
        addr = 1
        while addr in used_addresses:
            addr += 1
        return addr
    
    def save_current_fixture(self):
        """Sauvegarde la fixture actuellement éditée"""
        if not self.validate_fixture_data():
            return
        
        old_name = self.selected_fixture
        new_name = self.name_var.get().strip()
        
        # Vérifier si le nom a changé et s'il est déjà utilisé
        if old_name != new_name and new_name in self.fixtures_data:
            messagebox.showerror("Erreur", f"Le nom '{new_name}' est déjà utilisé")
            return
        
        # Créer les données de la fixture
        fixture_data = {
            "name": new_name,
            "type": self.type_var.get(),
            "manufacturer": self.manufacturer_var.get(),
            "dmx_address": int(self.dmx_address_var.get()),
            "channel_count": int(self.channel_count_var.get()),
            "channels": self.get_channels_data(),
            "kick_respond": self.kick_respond_var.get()
        }
        
        # Supprimer l'ancienne entrée si le nom a changé
        if old_name and old_name != new_name and old_name in self.fixtures_data:
            del self.fixtures_data[old_name]
        
        # Sauvegarder la nouvelle/modifiée fixture
        self.fixtures_data[new_name] = fixture_data
        self.selected_fixture = new_name
        
        # Repeupler la liste (qui sera automatiquement triée)
        self.populate_fixtures_list()
        
        # Resélectionner la fixture sauvegardée
        self.select_fixture_in_list(new_name)
        
        messagebox.showinfo("Succès", f"Fixture '{new_name}' sauvegardée!")
    
    def get_channels_data(self):
        """Récupère les données des canaux depuis le treeview"""
        channels = {}
        for item in self.channels_tree.get_children():
            channel_name = self.channels_tree.item(item)["text"]
            values = self.channels_tree.item(item)["values"]
            channels[channel_name] = {
                "id": int(values[0]),
                "default": int(values[1]),
                "min": int(values[2]),
                "max": int(values[3])
            }
        return channels
    
    def validate_fixture_data(self):
        """Valide les données de la fixture"""
        try:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Erreur", "Le nom de la fixture est requis")
                return False
            
            dmx_address = int(self.dmx_address_var.get())
            if dmx_address < 1 or dmx_address > 512:
                messagebox.showerror("Erreur", "L'adresse DMX doit être entre 1 et 512")
                return False
            
            channel_count = int(self.channel_count_var.get())
            if channel_count < 1 or channel_count > 32:
                messagebox.showerror("Erreur", "Le nombre de canaux doit être entre 1 et 32")
                return False
            
            # Vérifier que l'adresse + nombre de canaux ne dépasse pas 512
            if dmx_address + channel_count - 1 > 512:
                messagebox.showerror("Erreur", "L'adresse DMX + nombre de canaux dépasse 512")
                return False
            
            return True
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
            return False
    
    def add_channel(self):
        """Ajoute un nouveau canal"""
        dialog = ChannelDialog(self.parent)
        if dialog.result:
            channel_name, channel_data = dialog.result
            self.channels_tree.insert("", "end", text=channel_name,
                                    values=(channel_data["id"],
                                           channel_data["default"],
                                           channel_data["min"],
                                           channel_data["max"]))
    
    def remove_channel(self):
        """Supprime le canal sélectionné"""
        selected = self.channels_tree.selection()
        if selected:
            self.channels_tree.delete(selected[0])
    
    def edit_channel(self, event):
        """Édite le canal sélectionné"""
        selected = self.channels_tree.selection()
        if selected:
            item = selected[0]
            channel_name = self.channels_tree.item(item)["text"]
            values = self.channels_tree.item(item)["values"]
            
            current_data = {
                "id": int(values[0]),
                "default": int(values[1]),
                "min": int(values[2]),
                "max": int(values[3])
            }
            
            dialog = ChannelDialog(self.parent, channel_name, current_data)
            if dialog.result:
                new_name, new_data = dialog.result
                self.channels_tree.item(item, text=new_name,
                                      values=(new_data["id"],
                                             new_data["default"],
                                             new_data["min"],
                                             new_data["max"]))
    
    def clear_form(self):
        """Vide le formulaire"""
        self.name_var.set("")
        self.type_var.set("")
        self.manufacturer_var.set("")
        self.dmx_address_var.set("1")
        self.channel_count_var.set("1")
        self.kick_respond_var.set(False)
        
        for item in self.channels_tree.get_children():
            self.channels_tree.delete(item)
    
    def reload_fixtures(self):
        """Recharge les fixtures depuis le fichier"""
        self.load_fixtures()
        self.populate_fixtures_list()
        self.clear_form()
        self.selected_fixture = None
        messagebox.showinfo("Info", "Fixtures rechargées depuis le fichier")


class ChannelDialog:
    def __init__(self, parent, channel_name="", channel_data=None):
        self.result = None
        
        if channel_data is None:
            channel_data = {"id": 1, "default": 0, "min": 0, "max": 255}
        
        # Créer la fenêtre de dialogue
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuration du Canal")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Variables
        self.name_var = tk.StringVar(value=channel_name)
        self.id_var = tk.StringVar(value=str(channel_data["id"]))
        self.default_var = tk.StringVar(value=str(channel_data["default"]))
        self.min_var = tk.StringVar(value=str(channel_data["min"]))
        self.max_var = tk.StringVar(value=str(channel_data["max"]))
        
        self.create_widgets()
        
        # Attendre la fermeture
        self.dialog.wait_window()
    
    def create_widgets(self):
        """Crée les widgets du dialogue"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Nom du canal
        ttk.Label(main_frame, text="Nom du canal:").grid(row=0, column=0, sticky="w", pady=5)
        name_combo = ttk.Combobox(main_frame, textvariable=self.name_var, width=30)
        name_combo['values'] = ("red", "green", "blue", "white", "amber", "uv", "dimmer", 
                               "pan", "tilt", "color_wheel", "gobo_wheel", "prism", 
                               "focus", "zoom", "iris", "shutter", "reset", "strobe", "flashfx",
                               "fadefx", "colorchange")
        name_combo.grid(row=0, column=1, sticky="ew", pady=5)
        
        # ID du canal
        ttk.Label(main_frame, text="ID du canal:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.id_var, width=30).grid(row=1, column=1, sticky="ew", pady=5)
        
        # Valeur par défaut
        ttk.Label(main_frame, text="Valeur par défaut:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.default_var, width=30).grid(row=2, column=1, sticky="ew", pady=5)
        
        # Valeur minimum
        ttk.Label(main_frame, text="Valeur minimum:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.min_var, width=30).grid(row=3, column=1, sticky="ew", pady=5)
        
        # Valeur maximum
        ttk.Label(main_frame, text="Valeur maximum:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.max_var, width=30).grid(row=4, column=1, sticky="ew", pady=5)
        
        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="OK", command=self.ok_clicked).pack(side="left", padx=10)
        ttk.Button(buttons_frame, text="Annuler", command=self.cancel_clicked).pack(side="left")
        
        main_frame.columnconfigure(1, weight=1)
    
    def ok_clicked(self):
        """Valide et ferme le dialogue"""
        try:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Erreur", "Le nom du canal est requis")
                return
            
            channel_data = {
                "id": int(self.id_var.get()),
                "default": int(self.default_var.get()),
                "min": int(self.min_var.get()),
                "max": int(self.max_var.get())
            }
            
            # Validation
            if channel_data["id"] < 1:
                messagebox.showerror("Erreur", "L'ID du canal doit être >= 1")
                return
            
            if not (0 <= channel_data["default"] <= 255):
                messagebox.showerror("Erreur", "La valeur par défaut doit être entre 0 et 255")
                return
            
            if not (0 <= channel_data["min"] <= 255):
                messagebox.showerror("Erreur", "La valeur minimum doit être entre 0 et 255")
                return
            
            if not (0 <= channel_data["max"] <= 255):
                messagebox.showerror("Erreur", "La valeur maximum doit être entre 0 et 255")
                return
            
            if channel_data["min"] > channel_data["max"]:
                messagebox.showerror("Erreur", "La valeur minimum ne peut pas être supérieure à la valeur maximum")
                return
            
            self.result = (name, channel_data)
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
    
    def cancel_clicked(self):
        """Annule et ferme le dialogue"""
        self.dialog.destroy()


def create_fixtures_config_window(parent):
    """Crée une fenêtre de configuration des fixtures"""
    config_window = tk.Toplevel(parent)
    config_window.title("Configuration des Fixtures - LightLightShowXL")
    config_window.geometry("1200x800")
    
    fixtures_config = FixturesConfigView(config_window)
    
    return fixtures_config
import tkinter as tk
from views.audiodevice_view import AudioDeviceSelector
from views.start_view import StartButton

class MainView(tk.Tk):
    def __init__(self, start_callback):
        super().__init__()
        self.title("LightLightShowXL")
        self.geometry("400x300")
        
        # frame horizontal pour les deux sections en haut
        top_frame = tk.Frame(self)
        top_frame.pack(anchor='nw', padx=10, pady=10, fill='x')
        
        # Section audio en haut à gauche
        audio_selector = AudioDeviceSelector(top_frame)
        audio_selector.pack(side='left')

        # Bouton Start en haut juste à droite de l'autre bloc
        start_btn = StartButton(top_frame, start_callback)
        start_btn.pack(side='left')
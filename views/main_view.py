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
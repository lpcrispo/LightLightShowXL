import tkinter as tk
import threading

class MainView(tk.Tk):
    def __init__(self, start_callback):
        super().__init__()
        self.title("LightLightShowXL")
        self.geometry("400x300")
        self.start_callback = start_callback
        self.start_button = tk.Button(self, text="Start", command=self.start_app)
        self.start_button.pack(expand=True)

    def start_app(self):
        # Démarre l'application principale dans un thread séparé
        threading.Thread(target=self.start_callback, daemon=True).start()
        self.start_button.config(state=tk.DISABLED)
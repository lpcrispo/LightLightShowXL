import tkinter as tk
import threading

class StartButton(tk.Frame):
    def __init__(self, master=None, start_callback=None):
        super().__init__(master)
        self.start_callback = start_callback
        self.button = tk.Button(self, text="Start", command=self.start_app)
        self.button.pack(anchor='nw', padx=10, pady=10)

    def start_app(self):
        if self.start_callback:
            threading.Thread(target=self.start_callback, daemon=True).start()
        self.button.config(state=tk.DISABLED)
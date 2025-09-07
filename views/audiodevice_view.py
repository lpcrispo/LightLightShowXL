import tkinter as tk
from tkinter import ttk
import sounddevice as sd

class AudioDeviceSelector(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        devices = sd.query_devices()
        input_devices = [d['name'] for d in devices if d['max_input_channels'] > 0]
        output_devices = [d['name'] for d in devices if d['max_output_channels'] > 0]

        tk.Label(self, text="Input:").grid(row=0, column=0, sticky='e')
        self.input_combo = ttk.Combobox(self, values=input_devices, state="readonly")
        self.input_combo.grid(row=0, column=1)
        if input_devices:
            self.input_combo.current(0)

        tk.Label(self, text="Output:").grid(row=1, column=0, sticky='e')
        self.output_combo = ttk.Combobox(self, values=output_devices, state="readonly")
        self.output_combo.grid(row=1, column=1)
        if output_devices:
            self.output_combo.current(0)
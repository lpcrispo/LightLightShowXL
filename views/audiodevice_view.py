import tkinter as tk
from tkinter import ttk
import sounddevice as sd

class AudioDeviceSelector(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        devices = sd.query_devices()
        self.input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        self.output_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_output_channels'] > 0]

        tk.Label(self, text="Input:").grid(row=0, column=0, sticky='e')
        self.input_combo = ttk.Combobox(
            self,
            values=[name for _, name in self.input_devices],
            state="readonly",
            width=35
        )
        self.input_combo.grid(row=0, column=1)
        if self.input_devices:
            self.input_combo.current(0)

        tk.Label(self, text="Output:").grid(row=1, column=0, sticky='e')
        self.output_combo = ttk.Combobox(
            self,
            values=[name for _, name in self.output_devices],
            state="readonly",
            width=35
        )
        self.output_combo.grid(row=1, column=1)
        if self.output_devices:
            self.output_combo.current(0)
            
    def get_selected_input_device_index(self):
        idx = self.input_combo.current()
        if idx >= 0:
            return self.input_devices[idx][0]
        return None

    def get_selected_output_device_index(self):
        idx = self.output_combo.current()
        if idx >= 0:
            return self.output_devices[idx][0]
        return None
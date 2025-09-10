import numpy as np
import threading
import time
import librosa
import sounddevice as sd
from collections import deque

class EnergyDetector(threading.Thread):
    def __init__(self, mainboard, input_device_index=None):
        super().__init__(daemon=True)
        self.mainboard = mainboard
        
        # Paramètres audio
        self.input_device_index = input_device_index
        self.sample_rate = 22050
        self.record_duration = 2  # Buffer de 2 secondes
        self.audio_buffer = deque(maxlen=int(self.sample_rate * self.record_duration))
        self.analysis_interval = 1  # Analyse toutes les 1 seconde
        self.last_analysis_time = time.time()
        
        # Paramètres des bandes de fréquences
        self.bass_range = (20, 250)      # Bass: 20-250 Hz
        self.mid_range = (250, 4000)     # Mid: 250-4000 Hz     
        self.high_range = (4000, 11000)  # High: 4000-11000 Hz
        
        # Historique pour seuils adaptatifs
        self.energy_history = {
            'bass': deque(maxlen=2),
            'mid': deque(maxlen=2),
            'high': deque(maxlen=2)
        }
        
        # Seuils pour classification (percentiles)
        self.low_threshold = 30    # En dessous = "faible"
        self.high_threshold = 70   # Au-dessus = "haute"
        
        self._running = False
        self.audio_stream = None
        
        # Dernières valeurs détectées
        self.current_levels = {
            'bass': 'faible',
            'mid': 'faible', 
            'high': 'faible'
        }
        
        print("EnergyDetector initialized")
    
    def run(self):
        """Méthode principale du thread"""
        self._running = True
        print("EnergyDetector thread started...")
        
        # Démarrer l'enregistrement audio
        if self.input_device_index is not None:
            self.start_audio_recording()
        
        while self._running:
            current_time = time.time()
            
            # Analyse des bandes d'énergie toutes les 2 secondes
            if (current_time - self.last_analysis_time > self.analysis_interval and 
                len(self.audio_buffer) > self.sample_rate * 1.5):  # Au moins 1.5 secondes d'audio
                
                self.last_analysis_time = current_time
                self.analyze_frequency_bands()
                
            time.sleep(0.1)
        
        print("EnergyDetector thread stopped.")
    
    def stop(self):
        """Arrête le thread proprement"""
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
        self._running = False
    
    def start_audio_recording(self):
        """Démarre l'enregistrement audio en arrière-plan"""
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"EnergyDetector audio status: {status}")
            # Ajouter les nouvelles données au buffer circulaire
            audio_data = indata[:, 0] if indata.ndim > 1 else indata  # Mono
            self.audio_buffer.extend(audio_data)
        
        try:
            self.audio_stream = sd.InputStream(
                device=self.input_device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=1024,
                callback=audio_callback
            )
            self.audio_stream.start()
            print(f"EnergyDetector audio recording started on device {self.input_device_index}")
        except Exception as e:
            print(f"Failed to start EnergyDetector audio recording: {e}")
            self.audio_stream = None
    
    def analyze_frequency_bands(self):
        """Analyse l'énergie dans les 3 bandes de fréquences"""
        try:
            if len(self.audio_buffer) < self.sample_rate:
                return
            
            # Convertir le buffer en array numpy
            audio_array = np.array(list(self.audio_buffer), dtype=np.float32)
            
            # Calculer la FFT
            fft = np.fft.rfft(audio_array * np.hanning(len(audio_array)))
            magnitude = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio_array), 1 / self.sample_rate)
            
            # Calculer l'énergie pour chaque bande
            bass_energy = self._calculate_band_energy(magnitude, freqs, *self.bass_range)
            mid_energy = self._calculate_band_energy(magnitude, freqs, *self.mid_range)
            high_energy = self._calculate_band_energy(magnitude, freqs, *self.high_range)
            
            # Ajouter à l'historique
            self.energy_history['bass'].append(bass_energy)
            self.energy_history['mid'].append(mid_energy)
            self.energy_history['high'].append(high_energy)
            
            # Classifier les niveaux
            bass_level = self._classify_energy_level('bass', bass_energy)
            mid_level = self._classify_energy_level('mid', mid_energy)
            high_level = self._classify_energy_level('high', high_energy)
            
            # Stocker les niveaux actuels
            self.current_levels = {
                'bass': bass_level,
                'mid': mid_level,
                'high': high_level
            }
            
            #print(f"Energy levels - Bass: {bass_level} ({bass_energy:.1f}), "
            #      f"Mid: {mid_level} ({mid_energy:.1f}), "
            #      f"High: {high_level} ({high_energy:.1f})")
            
            # Envoyer au mainboard
            self.send_energy_levels_to_mainboard(bass_level, mid_level, high_level)
            
        except Exception as e:
            print(f"Error in frequency band analysis: {e}")
    
    def _calculate_band_energy(self, magnitude, freqs, low_freq, high_freq):
        """Calcule l'énergie dans une bande de fréquences donnée"""
        band_mask = (freqs >= low_freq) & (freqs <= high_freq)
        band_energy = np.sum(magnitude[band_mask] ** 2)
        
        # Normalisation logarithmique pour une meilleure plage dynamique
        if band_energy > 0:
            return np.log10(band_energy + 1) * 10
        return 0
    
    def _classify_energy_level(self, band_name, current_energy):
        """Classifie le niveau d'énergie en faible/moyenne/haute"""
        history = list(self.energy_history[band_name])
        
        if len(history) < 3:
            # Pas assez d'historique, utiliser des seuils fixes
            if current_energy < 20:
                return 'faible'
            elif current_energy < 40:
                return 'moyenne'
            else:
                return 'haute'
        
        # Utiliser les percentiles de l'historique pour des seuils adaptatifs
        low_percentile = np.percentile(history, self.low_threshold)
        high_percentile = np.percentile(history, self.high_threshold)
        
        if current_energy <= low_percentile:
            return 'faible'
        elif current_energy >= high_percentile:
            return 'haute'
        else:
            return 'moyenne'
    
    def send_energy_levels_to_mainboard(self, bass_level, mid_level, high_level):
        """Envoie les niveaux d'énergie au mainboard"""
        try:
            # Placeholder pour l'appel au mainboard
            # Le mainboard devra implémenter cette méthode
            if hasattr(self.mainboard, 'update_energy_levels'):
                self.mainboard.update_energy_levels(bass_level, mid_level, high_level)
            else:
                print(f"MainBoard placeholder - Energy levels: Bass={bass_level}, Mid={mid_level}, High={high_level}")
                
        except Exception as e:
            print(f"Error sending energy levels to mainboard: {e}")
    
    def get_current_levels(self):
        """Retourne les niveaux d'énergie actuels"""
        return self.current_levels.copy()
    
    def get_energy_history(self):
        """Retourne l'historique des énergies pour debug/monitoring"""
        return {
            band: list(history) for band, history in self.energy_history.items()
        }
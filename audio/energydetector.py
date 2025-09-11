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
        self.record_duration = 3  # Buffer de 3 secondes
        self.audio_buffer = deque(maxlen=int(self.sample_rate * self.record_duration))
        self.analysis_interval = 1  # Analyse toutes les 1 seconde
        self.last_analysis_time = time.time()
        
         # Paramètres des bandes de fréquences (plus précises)
        self.sub_bass_range = (20, 60)       # Sub-bass: 20-60 Hz (très profond)
        self.bass_range = (60, 250)          # Bass: 60-250 Hz (kick, basse)
        self.low_mid_range = (250, 1000)     # Low-mid: 250-1000 Hz (voix grave, instruments)
        self.mid_range = (1000, 4000)        # Mid: 1000-4000 Hz (voix, guitare)
        self.high_range = (4000, 8000)       # High: 4000-8000 Hz (cymbales, détails)
        self.presence_range = (8000, 16000)  # Presence: 8000-16000 Hz (air, brillance)
        
       # Historique plus long pour meilleure adaptation
        self.energy_history = {
            'sub_bass': deque(maxlen=20),
            'bass': deque(maxlen=20),
            'low_mid': deque(maxlen=20),
            'mid': deque(maxlen=20),
            'high': deque(maxlen=20),
            'presence': deque(maxlen=20)
        }
        
        # Historique pour détecter les changements d'énergie globale
        self.total_energy_history = deque(maxlen=10)
        
        # Seuils pour classification (plus de niveaux)
        self.very_low_threshold = 20     # très faible
        self.low_threshold = 40          # faible  
        self.medium_threshold = 60       # moyenne
        self.high_threshold = 80         # haute
        # Au-dessus = très haute
        
        self._running = False
        self.audio_stream = None
        
        # Dernières valeurs détectées (avec plus de niveaux)
        self.current_levels = {
            'sub_bass': 'très_faible',
            'bass': 'très_faible',
            'low_mid': 'très_faible',
            'mid': 'très_faible', 
            'high': 'très_faible',
            'presence': 'très_faible',
            'global_intensity': 'très_faible'
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
            
            # Analyse plus fréquente
            if (current_time - self.last_analysis_time > self.analysis_interval and 
                len(self.audio_buffer) > self.sample_rate * 1.0):  # Au moins 1 seconde d'audio
                
                self.last_analysis_time = current_time
                self.analyze_frequency_bands()
                
            time.sleep(0.05)  # Plus réactif
        
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
                blocksize=512,  # Plus petit pour plus de réactivité
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
            sub_bass_energy = self._calculate_band_energy(magnitude, freqs, *self.sub_bass_range)
            bass_energy = self._calculate_band_energy(magnitude, freqs, *self.bass_range)
            low_mid_energy = self._calculate_band_energy(magnitude, freqs, *self.low_mid_range)
            mid_energy = self._calculate_band_energy(magnitude, freqs, *self.mid_range)
            high_energy = self._calculate_band_energy(magnitude, freqs, *self.high_range)
            presence_energy = self._calculate_band_energy(magnitude, freqs, *self.presence_range)
            
            # Calculer l'énergie totale pondérée (refrain vs couplet)
            total_energy = (sub_bass_energy * 1.5 + bass_energy * 2.0 + 
                          low_mid_energy * 1.2 + mid_energy * 1.0 + 
                          high_energy * 0.8 + presence_energy * 0.6)
            
            # Ajouter à l'historique
            self.energy_history['sub_bass'].append(sub_bass_energy)
            self.energy_history['bass'].append(bass_energy)
            self.energy_history['low_mid'].append(low_mid_energy)
            self.energy_history['mid'].append(mid_energy)
            self.energy_history['high'].append(high_energy)
            self.energy_history['presence'].append(presence_energy)
            self.total_energy_history.append(total_energy)
            
            # Classifier les niveaux avec 5 niveaux
            sub_bass_level = self._classify_energy_level_detailed('sub_bass', sub_bass_energy)
            bass_level = self._classify_energy_level_detailed('bass', bass_energy)
            low_mid_level = self._classify_energy_level_detailed('low_mid', low_mid_energy)
            mid_level = self._classify_energy_level_detailed('mid', mid_energy)
            high_level = self._classify_energy_level_detailed('high', high_energy)
            presence_level = self._classify_energy_level_detailed('presence', presence_energy)
            
            # Classifier l'intensité globale (refrain vs couplet)
            global_intensity = self._classify_global_intensity(total_energy)
            
            # Stocker les niveaux actuels
            self.current_levels = {
                'sub_bass': sub_bass_level,
                'bass': bass_level,
                'low_mid': low_mid_level,
                'mid': mid_level,
                'high': high_level,
                'presence': presence_level,
                'global_intensity': global_intensity
            }
            
            #print(f"Energy: Sub={sub_bass_level[:1]}, Bass={bass_level[:1]}, LMid={low_mid_level[:1]}, "
            #      f"Mid={mid_level[:1]}, High={high_level[:1]}, Pres={presence_level[:1]}, "
            #      f"Global={global_intensity}")
            
            # Envoyer au mainboard
            self.send_energy_levels_to_mainboard()
            
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
    
    def _classify_energy_level_detailed(self, band_name, current_energy):
        """Classifie le niveau d'énergie avec 5 niveaux"""
        history = list(self.energy_history[band_name])
        
        # Seuils fixes absolus BEAUCOUP plus stricts pour "très_faible"
        absolute_thresholds = {
            'sub_bass': [2, 8, 20, 40],      # très_faible (quasi silence), faible, moyenne, haute
            'bass': [3, 12, 25, 50],
            'low_mid': [4, 15, 30, 60],
            'mid': [5, 18, 35, 70],
            'high': [3, 12, 25, 50],
            'presence': [1, 6, 15, 30]
        }

        thresholds = absolute_thresholds.get(band_name, [3, 12, 25, 50])
        
        if len(history) < 8:  
            # Utiliser les seuils fixes absolus
            if current_energy <= thresholds[0]:  # Changé < en <= pour inclure exactement le seuil
                return 'très_faible'
            elif current_energy <= thresholds[1]:
                return 'faible'
            elif current_energy <= thresholds[2]:
                return 'moyenne'
            elif current_energy <= thresholds[3]:
                return 'haute'
            else:
                return 'très_haute'
        
        # Avec assez d'historique, utiliser des seuils adaptatifs MAIS avec des minimums STRICTS
        very_low_p = max(np.percentile(history, self.very_low_threshold), thresholds[0])
        low_p = max(np.percentile(history, self.low_threshold), thresholds[1])
        medium_p = max(np.percentile(history, self.medium_threshold), thresholds[2])
        high_p = max(np.percentile(history, self.high_threshold), thresholds[3])
        
        # Forcer "très_faible" uniquement pour de vraies valeurs très basses
        if current_energy <= thresholds[0]:  # Force "très_faible" si en dessous du seuil absolu
            return 'très_faible'
        elif current_energy <= low_p:
            return 'faible'
        elif current_energy <= medium_p:
            return 'moyenne'
        elif current_energy <= high_p:
            return 'haute'
        else:
            return 'très_haute'
    
    def _classify_global_intensity(self, total_energy):
        """Classifie l'intensité globale pour détecter refrain vs couplet"""
        history = list(self.total_energy_history)
        
        # Seuils fixes absolus BEAUCOUP plus stricts pour "très_faible"
        absolute_thresholds = [15, 60, 150, 350]  # très_faible (quasi silence), faible, moyenne, haute
        
        if len(history) < 8:  
            if total_energy <= absolute_thresholds[0]:  # Vraiment très faible
                return 'très_faible'
            elif total_energy <= absolute_thresholds[1]:
                return 'faible'
            elif total_energy <= absolute_thresholds[2]:
                return 'moyenne'
            elif total_energy <= absolute_thresholds[3]:
                return 'haute'
            else:
                return 'très_haute'
        
        # Seuils adaptatifs avec des minimums de sécurité STRICTS
        very_low_p = max(np.percentile(history, 10), absolute_thresholds[0])  # Percentile plus bas (10 au lieu de 15)
        low_p = max(np.percentile(history, 30), absolute_thresholds[1])       # Percentile plus bas (30 au lieu de 35)
        medium_p = max(np.percentile(history, 50), absolute_thresholds[2])    # Percentile plus bas (50 au lieu de 55)
        high_p = max(np.percentile(history, 70), absolute_thresholds[3])      # Percentile plus bas (70 au lieu de 75)
        
        # Forcer "très_faible" uniquement pour de vraies valeurs très basses
        if total_energy <= absolute_thresholds[0]:  # Force "très_faible" si vraiment très bas
            return 'très_faible'
        elif total_energy <= low_p:
            return 'faible'
        elif total_energy <= medium_p:
            return 'moyenne'
        elif total_energy <= high_p:
            return 'haute'
        else:
            return 'très_haute'
    
    def send_energy_levels_to_mainboard(self):
        """Envoie les niveaux d'énergie au mainboard"""
        try:
            if hasattr(self.mainboard, 'update_energy_levels_detailed'):
                self.mainboard.update_energy_levels_detailed(self.current_levels)
            else:
                print(f"Energy levels: {self.current_levels}")
                
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
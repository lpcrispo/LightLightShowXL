import numpy as np
import threading
import time
import librosa
import sounddevice as sd
from collections import deque
import io

class BeatCalculator(threading.Thread):
    def __init__(self, mainboard, input_device_index=None):
        super().__init__(daemon=True)  # Initialiser le thread parent
        self.mainboard = mainboard
        
         # Paramètres pour l'enregistrement audio
        self.input_device_index = input_device_index
        self.sample_rate = 22050  # Réduit pour librosa (plus rapide)
        self.record_duration = 4  # secondes d'enregistrement
        self.audio_buffer = deque(maxlen=int(self.sample_rate * self.record_duration))
        self.librosa_update_interval = 5  # Analyse librosa toutes les 5 secondes
        self.last_librosa_update = time.time()
        
        self.current_bpm = 0
        
        self.kick_timestamps = []
        self.beat_per_minute = 0
        self.beat_history = deque(maxlen=10)
        self._running = False
        self.last_update_time = time.time()
        self.update_interval = 3  # secondes
        self.keep_last_kick_time = 10  # secondes
        
    def run(self):
        """Méthode principale du thread"""
        self._running = True
        print("BeatCalculator thread started...")
        
        # Démarrer l'enregistrement audio en arrière-plan si un device est fourni
        if self.input_device_index is not None:
            self.start_audio_recording()
        
        while self._running:
            current_time = time.time()
            
            # Mise à jour BPM basée sur les kicks
            if current_time - self.last_update_time > self.update_interval:
                self.last_update_time = current_time
                self.put_kick_timestamp_if_no_kick()
                self.send_beat_to_mainboard()
            
            # Analyse BPM avec librosa (moins fréquente car plus coûteuse)
            if (current_time - self.last_librosa_update > self.librosa_update_interval and 
                len(self.audio_buffer) > self.sample_rate * 2):  # Au moins 2 secondes d'audio
                self.last_librosa_update = current_time
                self.get_beat_per_minute_from_librosa()
                
            # Le thread reste en vie pour traiter les timestamps
            time.sleep(0.1)
        print("BeatCalculator thread stopped.")
    
    def stop(self):
        """Arrête le thread proprement"""
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
        self._running = False
        
    def send_beat_to_mainboard(self):
            self.beat_per_minute = self.get_beat_per_minute_from_kicks(self.kick_timestamps)
            print(f"Detected BPM: {self.beat_per_minute}")
            #self.mainboard.update_sequence_duration_and_fade_from_bpm(self.beat_per_minute)

    def put_kick_timestamp(self):
        #ajoute le timestamp actuel à la liste des kicks
        self.kick_timestamps.append(time.time())
        #si le plus vieux timestamp a plus de 5 secondes, on le supprime
        if len(self.kick_timestamps) > 0 and (time.time() - self.kick_timestamps[0]) > self.keep_last_kick_time:
            self.kick_timestamps.pop(0)
            
    def put_kick_timestamp_if_no_kick(self):
        
        #si le plus récent timestamp a plus de self.update_interval, on ajoute un faux kick
        if len(self.kick_timestamps) > 0 and (time.time()-0.001 - self.kick_timestamps[-1]) > self.update_interval:
            print("No kick detected recently, adding fake kick for BPM calculation.")
            self.kick_timestamps.append(time.time())

    def get_beat_per_minute_from_kicks(self, kick_timestamps):
        if len(kick_timestamps) < 3:
            return 0
        # Convertir en array numpy pour éviter les erreurs de type
        timestamps = np.array(kick_timestamps)

        # Calculer les intervalles entre les kicks
        intervals = np.diff(timestamps)
        
        valid_intervals = intervals[
            (intervals > 0.2) &    # Min 0.2s = 300 BPM max
            (intervals < 2.0) &    # Max 2.0s = 30 BPM min  
            np.isfinite(intervals)
        ]

        if len(valid_intervals) < 2:
            return 0
            
        median_interval = np.median(valid_intervals)
        
        if median_interval <= 0:
            return 0

        bpm = 60 / median_interval
        
        self.beat_history.append(int(np.clip(bpm, 30, 250)))
        if len(self.beat_history) == 0:
            return 0
        if len(self.beat_history) < 3:
            return int(np.mean(self.beat_history))
        
        print(f"combien d'historique: {len(self.beat_history)}, bpm calculé: {int(bpm)} recalculé(moy): {int(np.mean(self.beat_history))} recalculé(med): {int(np.median(self.beat_history))}")
        # Sinon, utiliser la médiane pour plus de robustesse
        self.current_bpm = int(np.median(self.beat_history))
        return self.current_bpm

    def start_audio_recording(self):
        """Démarre l'enregistrement audio en arrière-plan"""
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio recording status: {status}")
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
            print(f"Audio recording started on device {self.input_device_index}")
        except Exception as e:
            print(f"Failed to start audio recording: {e}")
            self.audio_stream = None

    def get_beat_per_minute_from_librosa(self):
        """Analyse le BPM avec librosa sur le buffer audio"""
        try:
            if len(self.audio_buffer) < self.sample_rate * 2:
                print("Not enough audio data for librosa analysis")
                return
            
            # Convertir le buffer en array numpy
            audio_array = np.array(list(self.audio_buffer), dtype=np.float32)
            
            concatenated_audio = np.concatenate([audio_array, audio_array, audio_array])
            
            # Détecter le tempo avec librosa
            tempo, beats = librosa.beat.beat_track(
                y=concatenated_audio,
                sr=self.sample_rate,
                hop_length=512,
                start_bpm=self.current_bpm if self.current_bpm > 0 else 120,
                tightness=100     # Contrainte sur la régularité du tempo
            )
            
            # Convertir les beats de frames en secondes
            beats_in_seconds = librosa.frames_to_time(beats, sr=self.sample_rate, hop_length=512)
            
            original_duration = len(audio_array) / self.sample_rate
            # Filtrer les beats pour ne garder que ceux de la première section (originale)
            # beats est en secondes, donc on garde ceux < original_duration
            valid_beats = beats_in_seconds[beats_in_seconds < original_duration]
            print(f"Valid beat times: {valid_beats}")
            
            # Recalculer le BPM basé uniquement sur les beats de la section originale
            if len(valid_beats) > 1:
                # Calculer les intervalles entre les beats valides
                beat_intervals = np.diff(valid_beats)
                if len(beat_intervals) > 0:
                    # Utiliser la médiane des intervalles pour plus de robustesse
                    median_beat_interval = np.median(beat_intervals)
                    recalculated_bpm = 60 / median_beat_interval
                    
                    print(f"Librosa BPM: {int(tempo)} (global)")
                    print(f"Recalculated BPM from valid beats: {int(recalculated_bpm)}")
                    
                    # Utiliser le BPM recalculé plutôt que le global
                    librosa_bpm = int(recalculated_bpm)
                else:
                    librosa_bpm = int(tempo)
            else:
                print("Not enough valid beats for recalculation, using global tempo")
                librosa_bpm = int(tempo)
            
            # Ajouter à l'historique si valide
            if 30 <= librosa_bpm <= 300:
                self.beat_history.append(librosa_bpm)
                
                # Recalculer le BPM final avec l'historique
                old_bpm = self.current_bpm
                if len(self.beat_history) < 3:
                    self.current_bpm = int(np.mean(self.beat_history))
                else:
                    self.current_bpm = int(np.median(self.beat_history))
                
                print(f"🎵 Librosa BPM added to history: {librosa_bpm}")
                print(f"History: {list(self.beat_history)} → Final BPM: {self.current_bpm}")
                
                if abs(self.current_bpm - old_bpm) > 3:
                    print(f"🎵 BPM Updated by librosa: {old_bpm} → {self.current_bpm}")
                    #self.mainboard.update_sequence_duration_and_fade_from_bpm(self.current_bpm)
            else:
                print(f"Librosa BPM {librosa_bpm} out of range (30-300), ignoring")

        except Exception as e:
            print(f"Error in librosa analysis: {e}")
    
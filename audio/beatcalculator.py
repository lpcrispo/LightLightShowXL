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
        self.record_duration = 5  # secondes d'enregistrement
        self.audio_buffer = deque(maxlen=int(self.sample_rate * self.record_duration))
        self.librosa_update_interval = 2  # Analyse librosa toutes les 4 secondes
        self.last_librosa_update = time.time()
        
        self.kick_timestamps = []
        self.beat_per_minute_finale = 0
        self.beat_from_librosa = 0
        self.beat_from_kick = 0
        
        self.kick_beat_history = deque(maxlen=4)
        self.librosa_beat_history = deque(maxlen=3)
        self._running = False
        self.last_update_time = time.time()
        self.update_interval = 3  # secondes
        self.keep_last_kick_time = 10  # secondes
        
        # Ajouter un historique des BPM finaux pour éviter les changements brusques
        self.final_bpm_history = deque(maxlen=3)
        self.stability_threshold = 0.3  # Seuil de stabilité minimum
        
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
                self.get_beat_per_minute_from_kicks(self.kick_timestamps)
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
        """Choisit le BPM le plus stable entre kick et librosa"""
        
        # Calculer la stabilité de chaque méthode
        kick_stability = self._calculate_stability(self.kick_beat_history)
        librosa_stability = self._calculate_stability(self.librosa_beat_history)
        
        # Calculer la confiance basée sur la quantité de données
        kick_confidence = min(len(self.kick_beat_history) / 5.0, 1.0)  # Max confiance à 5 échantillons
        librosa_confidence = min(len(self.librosa_beat_history) / 3.0, 1.0)  # Max confiance à 3 échantillons
        
        # Score combiné (stabilité * confiance)
        kick_score = kick_stability * kick_confidence if self.beat_from_kick > 0 else 0
        librosa_score = librosa_stability * librosa_confidence if self.beat_from_librosa > 0 else 0
        
        #print(f"Kick: BPM={self.beat_from_kick}, stability={kick_stability:.2f}, confidence={kick_confidence:.2f}, score={kick_score:.2f}")
        #print(f"Librosa: BPM={self.beat_from_librosa}, stability={librosa_stability:.2f}, confidence={librosa_confidence:.2f}, score={librosa_score:.2f}")
        
        # Choisir la meilleure méthode
        if kick_score > librosa_score and kick_score > 0.3:  # Seuil minimum de confiance
            self.beat_per_minute_finale = self.beat_from_kick
            source = "kick"
        elif librosa_score > 0.3:
            self.beat_per_minute_finale = self.beat_from_librosa
            source = "librosa"
        elif self.beat_from_kick > 0:
            self.beat_per_minute_finale = self.beat_from_kick
            source = "kick (fallback)"
        elif self.beat_from_librosa > 0:
            self.beat_per_minute_finale = self.beat_from_librosa
            source = "librosa (fallback)"
        else:
            # Garder la dernière valeur connue ou 0
            source = "previous"
        
        print(f"Selected BPM: {self.beat_per_minute_finale} from {source}")
        
        # Dans send_beat_to_mainboard(), à la fin :
        # Lisser avec l'historique des BPM finaux
        if len(self.final_bpm_history) > 0:
            previous_bpm = self.final_bpm_history[-1]
            if previous_bpm > 0 and self.beat_per_minute_finale > 0:
                # Si le changement est trop brusque (>5%), utiliser une transition progressive
                change_ratio = abs(self.beat_per_minute_finale - previous_bpm) / previous_bpm
                if change_ratio > 0.05:
                    self.beat_per_minute_finale = int(0.2 * previous_bpm + 0.8 * self.beat_per_minute_finale)
                    print(f"Smoothed BPM transition: {previous_bpm} -> {self.beat_per_minute_finale}")

        self.final_bpm_history.append(self.beat_per_minute_finale)
        self.mainboard.update_sequence_duration_and_fade_from_bpm(self.beat_per_minute_finale, self.last_librosa_beat_timestamp)
        
    def _calculate_stability(self, history):
        """Calcule un score de stabilité (0-1) basé sur la variance des valeurs"""
        if len(history) < 2:
            return 0.0
        
        # Convertir en numpy array
        values = np.array(history)
        
        # Calculer la variance relative (coefficient de variation inversé)
        mean_val = np.mean(values)
        if mean_val == 0:
            return 0.0
        
        std_val = np.std(values)
        cv = std_val / mean_val  # Coefficient de variation
        
        # Convertir en score de stabilité (plus la variance est faible, plus c'est stable)
        # Utiliser une fonction exponentielle décroissante pour le score
        stability_score = np.exp(-cv * 5)  # Le facteur 5 peut être ajusté
        
        return min(stability_score, 1.0)

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
        
        self.kick_beat_history.append(int(np.clip(bpm, 30, 300)))
        if len(self.kick_beat_history) == 0:
            return_bpm = 0
        if len(self.kick_beat_history) < 3:
            return_bpm = int(np.mean(self.kick_beat_history))

        #print(f"combien d'historique: {len(self.kick_beat_history)}, bpm calculé: {int(bpm)} recalculé(moy): {int(np.mean(self.kick_beat_history))} recalculé(med): {int(np.median(self.kick_beat_history))}")
        # Sinon, utiliser la médiane pour plus de robustesse
        return_bpm = int(np.median(self.kick_beat_history))
        self.beat_from_kick = return_bpm


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
            
            librosaTime = time.time()
            # Détecter le tempo avec librosa
            tempo, beats = librosa.beat.beat_track(
                y=concatenated_audio,
                sr=self.sample_rate,
                hop_length=512,
                start_bpm=self.beat_per_minute_finale if self.beat_per_minute_finale > 0 else 120,
                tightness=100     # Contrainte sur la régularité du tempo
            )
            
            # MAINTENANT on prend le temps de fin d'analyse
            analysis_end_time = time.time()
            analysis_duration = analysis_end_time - librosaTime
            #print(f"Librosa analysis took {analysis_duration:.2f}s, detected tempo: {tempo}, beats count: {len(beats)}")

            # Convertir les beats de frames en secondes
            beats_in_seconds = librosa.frames_to_time(beats, sr=self.sample_rate, hop_length=512)
            
            original_duration = len(audio_array) / self.sample_rate
            
            # Filtrer pour garder tous les beats valides des 3 copies
            all_valid_beats = []
            
            for beat_time in beats_in_seconds:
                if beat_time < original_duration:
                    all_valid_beats.append(beat_time)
                elif beat_time < 2 * original_duration:
                    equivalent_time = beat_time - original_duration
                    all_valid_beats.append(equivalent_time)
                elif beat_time < 3 * original_duration:
                    equivalent_time = beat_time - 2 * original_duration
                    all_valid_beats.append(equivalent_time)
            
            # Convertir en numpy array et trier
            valid_beats = np.array(sorted(all_valid_beats))
            
            # Supprimer les beats qui sont trop proches (moins de 0.1s d'écart)
            # pour éviter les triplons dus à la concaténation
            if len(all_valid_beats) > 1:
                unique_beats = [all_valid_beats[0]]
                for beat in all_valid_beats[1:]:
                    if beat - unique_beats[-1] > 0.1:  # Minimum 0.1s entre beats
                        unique_beats.append(beat)
                valid_beats = np.array(unique_beats)
            else:
                valid_beats = all_valid_beats
            
            #print(f"Valid beats after deduplication: {len(valid_beats)} from {len(all_valid_beats)} total")
            
            
            # Calculer les timestamps réels des beats
            if len(valid_beats) > 0:
                # Le dernier beat détecté dans l'audio buffer
                last_beat_offset = valid_beats[-1]  # En secondes depuis le début du buffer
                
                # Calculer le timestamp réel du dernier beat
                # Le buffer a été enregistré avant l'analyse, donc on recule de analysis_duration
                buffer_start_time = analysis_end_time - analysis_duration - original_duration
                last_beat_timestamp = buffer_start_time + last_beat_offset
                
                #print(f"Last beat occurred at timestamp: {last_beat_timestamp}, offset: {last_beat_offset:.2f}s in buffer")
                
                #stocker ce timestamp pour utilisation ultérieure
                self.last_librosa_beat_timestamp = last_beat_timestamp
            
            # Recalculer le BPM basé uniquement sur les beats de la section originale
            if len(valid_beats) > 1:
                # Calculer les intervalles entre les beats valides
                beat_intervals = np.diff(valid_beats)
                if len(beat_intervals) > 0:
                    # Utiliser la médiane des intervalles pour plus de robustesse
                    median_beat_interval = np.median(beat_intervals)
                    recalculated_bpm = 60 / median_beat_interval
                    
                    # Utiliser le BPM recalculé plutôt que le global
                    librosa_bpm = int(recalculated_bpm)
                else:
                    librosa_bpm = int(tempo)
            else:
                print("Not enough valid beats for recalculation, using global tempo")
                librosa_bpm = int(tempo)
            
            # Ajouter à l'historique si valide
            if 30 <= librosa_bpm <= 300:
                self.librosa_beat_history.append(librosa_bpm)
                
                # Recalculer le BPM final avec l'historique
                old_bpm = self.beat_from_librosa
                if len(self.librosa_beat_history) < 3:
                    self.beat_from_librosa = int(np.mean(self.librosa_beat_history))
                else:
                    self.beat_from_librosa = int(np.median(self.librosa_beat_history))
                
            else:
                print(f"Librosa BPM {librosa_bpm} out of range (30-300), ignoring")

        except Exception as e:
            print(f"Error in librosa analysis: {e}")
    
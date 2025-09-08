import numpy as np
import threading
import time

class BeatCalculator(threading.Thread):
    def __init__(self, mainboard):
        super().__init__(daemon=True)  # Initialiser le thread parent
        self.mainboard = mainboard
        self.kick_timestamps = []
        self.beat_per_minute = 0
        self._running = False
        self.last_update_time = time.time()
        self.update_interval = 3  # secondes
        self.keep_last_kick_time = 5  # secondes
        
    def run(self):
        """Méthode principale du thread"""
        self._running = True
        print("BeatCalculator thread started...")
        while self._running:
            self.send_beat_to_mainboard()
            # Le thread reste en vie pour traiter les timestamps
            time.sleep(0.1)
        print("BeatCalculator thread stopped.")
    
    def stop(self):
        """Arrête le thread proprement"""
        self._running = False
        
    def send_beat_to_mainboard(self):
        #à tout les 3 secondes on met à jour le bpm
        if time.time() - self.last_update_time > self.update_interval:
            self.last_update_time = time.time()
            self.beat_per_minute = self.get_beat_per_minute(self.kick_timestamps)
            print(f"Detected BPM: {self.beat_per_minute}")
            #self.mainboard.update_sequence_duration_and_fade_from_bpm(self.beat_per_minute)

    def put_kick_timestamp(self):
        #ajoute le timestamp actuel à la liste des kicks
        self.kick_timestamps.append([time.time()])
        #si le plus vieux timestamp a plus de 5 secondes, on le supprime
        if len(self.kick_timestamps) > 0 and (time.time() - self.kick_timestamps[0][0]) > self.keep_last_kick_time:
            self.kick_timestamps.pop(0)

    def get_beat_per_minute(self, kick_timestamps):
        if len(kick_timestamps) < 2:
            return 0
        # Convertir en array numpy pour éviter les erreurs de type
        timestamps = np.array(kick_timestamps)
        intervals = np.diff(timestamps)
        if len(intervals) == 0:
            return 0
        
        # Filtrer les intervalles invalides (trop petits ou NaN)
        valid_intervals = intervals[(intervals > 0.1) & np.isfinite(intervals)]
    
        if len(valid_intervals) == 0:
            return 0
            
        median_interval = np.median(valid_intervals)
        # Vérifications supplémentaires
        if not np.isfinite(median_interval) or median_interval <= 0:
            return 0
        bpm = 60 / median_interval
        
        # Vérifier que le BPM est valide et dans une plage raisonnable
        if not np.isfinite(bpm) or bpm <= 0 or bpm > 300:
            return 0
            
        return int(bpm)
import sounddevice as sd
import numpy as np
import threading
import time
from collections import deque
import scipy.signal

class BPMDetector:
    """
    Détecteur de BPM en temps réel ULTRA-RÉACTIF
    """
    def __init__(
        self,
        mainboard,
        input_device_index,
        sample_rate=44100,
        block_size=2048,         # AUGMENTÉ pour plus de stabilité
        low_freq=60,
        high_freq=150,           # RÉDUIT - focus sur les kicks
        bpm_range=(60, 180),     
        onset_threshold=0.3,     # AUGMENTÉ - moins sensible aux parasites
        update_interval=2.0,     # AUGMENTÉ - plus stable
        history_length=20,       # AUGMENTÉ
        smoothing_factor=0.8,    
        debug=False
    ):
        self.mainboard = mainboard
        self.input_device_index = input_device_index
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.bpm_range = bpm_range
        self.onset_threshold = onset_threshold
        self.update_interval = update_interval
        self.history_length = history_length
        self.smoothing_factor = smoothing_factor
        self.debug = debug

        # Historiques réduits pour plus de réactivité
        self._onset_times = deque()
        self._spectrum_history = deque(maxlen=3)  # Réduit
        self._bpm_history = deque(maxlen=5)       # Réduit
        self._last_update_time = time.time()
        
        # Variables pour filtrage intelligent des onsets
        self._last_strong_onset = 0
        self._min_beat_interval = 0.25  # 250ms minimum entre beats (240 BPM max)
            
        self._current_bpm = 120.0
        self._smoothed_bpm = 120.0
        self._first_detection = True  # Flag pour première détection

        # Filtre passe-bas pour le signal
        self._create_filter()

        self._stream = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def _create_filter(self):
        """Crée un filtre passe-bas pour isoler les basses fréquences"""
        nyquist = self.sample_rate / 2
        cutoff = self.high_freq
        self.b, self.a = scipy.signal.butter(4, cutoff / nyquist, btype='low')
        self.zi = scipy.signal.lfilter_zi(self.b, self.a)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_stream, daemon=True)
        self._thread.start()
        print(f"BPMDetector started (device {self.input_device_index})")

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.close()
            except Exception:
                pass

    def get_current_bpm(self):
        with self._lock:
            return self._smoothed_bpm

    def _spectral_flux(self, current_spectrum, previous_spectrum):
        """Calcule le flux spectral pour détecter les onsets"""
        if previous_spectrum is None:
            return 0
        diff = current_spectrum - previous_spectrum
        flux = np.sum(np.maximum(diff, 0))
        return flux

    def _detect_bpm_from_onsets(self, onset_times):
        """Version améliorée avec filtrage intelligent"""
        if self.debug:
            print(f"🔍 Analyzing {len(onset_times)} onsets")
        
        if len(onset_times) < 6:  # Augmenté à 6 pour plus de fiabilité
            if self.debug:
                print(f"❌ Pas assez d'onsets: {len(onset_times)}/6")
            return None

        # Convertir en intervalles de temps
        intervals = np.diff(sorted(onset_times))
        if self.debug:
            print(f"📊 Intervals (premières 5): {intervals[:5]}")
            print(f"📊 Stats intervals: min={np.min(intervals):.3f}, max={np.max(intervals):.3f}, mean={np.mean(intervals):.3f}")
        
        # Plage d'intervals pour BPM raisonnables
        min_interval = 60.0 / self.bpm_range[1]  # 0.33s pour 180 BPM
        max_interval = 60.0 / self.bpm_range[0]  # 1.0s pour 60 BPM
        
        valid_intervals = intervals[(intervals >= min_interval) & (intervals <= max_interval)]
        
        if self.debug:
            print(f"✅ Valid intervals: {len(valid_intervals)}/{len(intervals)}")
            if len(valid_intervals) > 0:
                print(f"📊 Valid range: {np.min(valid_intervals):.3f}-{np.max(valid_intervals):.3f}s")
        
        if len(valid_intervals) < 3:  # Minimum 3 intervals valides
            if self.debug:
                print(f"❌ Pas assez d'intervals valides: {len(valid_intervals)}/3")
            return None

        # Approche par clustering des intervals similaires
        # Trouver le mode (interval le plus fréquent)
        hist, bin_edges = np.histogram(valid_intervals, bins=20)
        peak_bin = np.argmax(hist)
        dominant_interval = (bin_edges[peak_bin] + bin_edges[peak_bin + 1]) / 2
        
        # Prendre les intervals proches du dominant (±20%)
        tolerance = dominant_interval * 0.2
        consistent_intervals = valid_intervals[
            np.abs(valid_intervals - dominant_interval) <= tolerance
        ]
        
        if len(consistent_intervals) < 2:
            if self.debug:
                print(f"❌ Pas assez d'intervals cohérents autour de {dominant_interval:.3f}s")
            return None
        
        # BPM basé sur l'interval médian des intervals cohérents
        final_interval = np.median(consistent_intervals)
        estimated_bpm = 60.0 / final_interval
        
        if self.debug:
            print(f"🎵 BPM calculé: {estimated_bpm:.1f} (de {len(consistent_intervals)} intervals cohérents, médiane {final_interval:.3f}s)")
        
        # Validation des multiples
        if estimated_bpm < 90:
            estimated_bpm *= 2
            if self.debug:
                print(f"⬆️ Doublé car trop bas: -> {estimated_bpm:.1f}")
        elif estimated_bpm > 150:
            estimated_bpm /= 2
            if self.debug:
                print(f"⬇️ Divisé car trop haut: -> {estimated_bpm:.1f}")
        
        return estimated_bpm

    def _update_bpm(self):
        """Version ultra-réactive"""
        current_time = time.time()
        
        if self.debug:
            print(f"\n🔄 Mise à jour BPM (onsets actuels: {len(self._onset_times)})")
        
        # Nettoyer les anciens onsets (historique plus court)
        cutoff_time = current_time - self.history_length
        initial_count = len(self._onset_times)
        while self._onset_times and self._onset_times[0] < cutoff_time:
            self._onset_times.popleft()
        
        if self.debug and len(self._onset_times) != initial_count:
            print(f"🧹 Nettoyé: {initial_count} -> {len(self._onset_times)} onsets")

        # Estimer le BPM
        onset_list = list(self._onset_times)
        estimated_bpm = self._detect_bpm_from_onsets(onset_list)
        
        if self.debug:
            print(f"📈 BPM estimé: {estimated_bpm}")
        
        if estimated_bpm and self.bpm_range[0] <= estimated_bpm <= self.bpm_range[1]:
            with self._lock:
                self._current_bpm = estimated_bpm
                self._bpm_history.append(estimated_bpm)
                
                if self.debug:
                    print(f"📝 Historique BPM: {list(self._bpm_history)}")
                
                # LOGIQUE ULTRA-RÉACTIVE
                if len(self._bpm_history) >= 2:  # Réduit de 3 à 2
                    recent_bpms = list(self._bpm_history)[-3:]  # 3 dernières valeurs max
                    median_bpm = np.median(recent_bpms)
                    
                    if self.debug:
                        print(f"🎯 Médiane récente: {median_bpm:.1f} (de {recent_bpms})")
                    
                    # Première détection ou changement significatif : accepter immédiatement
                    if self._first_detection:
                        self._smoothed_bpm = median_bpm
                        self._first_detection = False
                        if self.debug:
                            print(f"🎵 PREMIER BPM: {median_bpm:.1f}")
                    else:
                        # Calcul de différence
                        bpm_diff = abs(median_bpm - self._smoothed_bpm)
                        
                        if self.debug:
                            print(f"📊 Différence: {bpm_diff:.1f} (seuil 40%: {self._smoothed_bpm * 0.4:.1f})")
                        
                        # SEUILS TRÈS PERMISSIFS
                        if bpm_diff > self._smoothed_bpm * 0.4:  # 40% = changement majeur
                            # Changement important : vérifier cohérence sur 2 mesures seulement
                            if len(recent_bpms) >= 2:
                                recent_std = np.std(recent_bpms)
                                if self.debug:
                                    print(f"📏 Stabilité: std={recent_std:.1f}, seuil={median_bpm * 0.2:.1f}")
                                
                                if recent_std < median_bpm * 0.2:  # 20% de tolérance
                                    old_bpm = self._smoothed_bpm
                                    self._smoothed_bpm = median_bpm
                                    if self.debug:
                                        print(f"🔄 CHANGEMENT MAJEUR: {old_bpm:.1f} -> {median_bpm:.1f}")
                                else:
                                    if self.debug:
                                        print(f"❌ Instable: {median_bpm:.1f} (std: {recent_std:.1f})")
                        else:
                            # Changement normal : lissage minimal pour réactivité maximale
                            old_bpm = self._smoothed_bpm
                            alpha = 0.9  # TRÈS réactif
                            self._smoothed_bpm = alpha * median_bpm + (1 - alpha) * self._smoothed_bpm
                            if self.debug:
                                print(f"🎯 MAJ NORMALE: {old_bpm:.1f} -> {self._smoothed_bpm:.1f}")
                
                # Envoyer au mainboard
                try:
                    if self.debug:
                        print(f"📤 Envoi au mainboard: {self._smoothed_bpm:.1f}")
                    self.mainboard.update_sequence_duration_and_fade_from_bpm(self._smoothed_bpm)
                    if self.debug:
                        print(f"✅ BPM envoyé avec succès!")
                except Exception as e:
                    print(f"❌ BPMDetector update error: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            if self.debug:
                if estimated_bpm:
                    print(f"❌ BPM hors plage: {estimated_bpm:.1f} (plage: {self.bpm_range[0]}-{self.bpm_range[1]})")
                else:
                    print(f"❌ Aucun BPM détecté")

    def _run_stream(self):
        hann = np.hanning(self.block_size)
        filter_state = self.zi.copy()

        def callback(indata, frames, tinfo, status):
            nonlocal filter_state
            
            if not self._running:
                return
            if status and self.debug:
                print("BPMDetector status:", status)

            mono = indata[:, 0].astype(np.float32)
            if len(mono) != self.block_size:
                return

            # Filtrage passe-bas PLUS STRICT
            filtered, filter_state = scipy.signal.lfilter(
                self.b, self.a, mono, zi=filter_state
            )

            # FFT avec fenêtrage
            fft = np.fft.rfft(filtered * hann)
            mags = np.abs(fft)
            freqs = np.fft.rfftfreq(len(filtered), 1 / self.sample_rate)

            # NOUVEAU: Focus sur les très basses fréquences (kicks/bass)
            kick_mask = (freqs >= 60) & (freqs <= 100)  # Zone kick/bass drum
            kick_energy = np.sum(mags[kick_mask])
            
            # Énergie dans la bande rythmique complète
            band_mask = (freqs >= self.low_freq) & (freqs <= self.high_freq)
            current_spectrum = mags[band_mask]

            # Détection d'onset avec DOUBLE CRITÈRE
            if len(self._spectrum_history) > 0:
                flux = self._spectral_flux(current_spectrum, self._spectrum_history[-1])
                
                # Calculer aussi l'énergie instantanée des kicks
                prev_kick_energy = np.sum(self._spectrum_history[-1][:40]) if len(self._spectrum_history) > 0 else 0
                kick_increase = kick_energy - prev_kick_energy
                
                # Seuil adaptatif basé sur l'historique
                if len(self._spectrum_history) >= 3:
                    recent_flux = [
                        self._spectral_flux(self._spectrum_history[i], self._spectrum_history[i-1])
                        for i in range(1, len(self._spectrum_history))
                    ]
                    if recent_flux:
                        flux_mean = np.mean(recent_flux)
                        flux_std = np.std(recent_flux) + 1e-9
                        
                        # Seuil PLUS STRICT
                        flux_threshold = flux_mean + (self.onset_threshold * 3) * flux_std
                        kick_threshold = kick_energy > prev_kick_energy * 1.5  # 50% d'augmentation kick
                        
                        current_time = time.time()
                        
                        # TRIPLE CRITÈRE pour onset valide
                        is_flux_peak = flux > flux_threshold
                        is_kick_peak = kick_increase > 0 and kick_threshold
                        is_temporal_valid = (not self._onset_times or 
                                        current_time - self._onset_times[-1] > self._min_beat_interval)
                        
                        if is_flux_peak and is_kick_peak and is_temporal_valid:
                            self._onset_times.append(current_time)
                            self._last_strong_onset = current_time
                            if self.debug:
                                print(f"🥁 BEAT: flux={flux:.1f}>{flux_threshold:.1f}, kick={kick_energy:.1f}, interval={current_time - (self._onset_times[-2] if len(self._onset_times)>1 else current_time):.3f}s")

            # Stocker le spectre
            self._spectrum_history.append(current_spectrum.copy())
            
            # Mise à jour du BPM
            current_time = time.time()
            if current_time - self._last_update_time >= self.update_interval:
                self._update_bpm()
                self._last_update_time = current_time

        try:
            self._stream = sd.InputStream(
                device=self.input_device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=callback
            )
            self._stream.start()
            while self._running:
                time.sleep(0.1)
        except Exception as e:
            print(f"BPMDetector stream error: {e}")
            self._running = False
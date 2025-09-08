import sounddevice as sd
import numpy as np
import threading
import time
from collections import deque
import scipy.signal

class KickDetector:
    """
    Détection de kick live optimisée avec plusieurs approches :
    - Analyse spectrale dans la bande 60-120 Hz (kick fondamental)
    - Détection d'onset basée sur le flux spectral
    - Seuil adaptatif basé sur l'écart-type
    - Filtrage passe-bas pour éliminer les hautes fréquences parasites
    """
    def __init__(
        self,
        mainboard,
        input_device_index,
        sample_rate=44100,
        block_size=1024,         # Augmenté pour meilleure résolution fréquentielle
        low_freq=60,             # Fréquence fondamentale du kick
        high_freq=120,           # Harmonique principale
        baseline_window=50,      # Réduit pour adaptation plus rapide
        trigger_factor=1.2,      # BEAUCOUP plus sensible
        refractory_time=0.12,
        min_band_energy=100,     # Beaucoup plus bas
        use_onset_detection=True, # Nouvelle méthode
        onset_threshold=0.15,    # RÉDUIT pour plus de sensibilité
        smoothing_alpha=0.4,     # Plus réactif
        warmup_ratio=0.3,        # Warmup plus rapide
        debug=True,
    ):
        self.mainboard = mainboard
        self.input_device_index = input_device_index
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.baseline_window = baseline_window
        self.trigger_factor = trigger_factor
        self.refractory_time = refractory_time
        self.min_band_energy = min_band_energy
        self.use_onset_detection = use_onset_detection
        self.onset_threshold = onset_threshold
        self.smoothing_alpha = smoothing_alpha
        self.warmup_ratio = warmup_ratio
        self.debug = debug

        # Historiques pour baseline et onset detection
        self._energy_history = deque(maxlen=baseline_window)
        self._spectrum_history = deque(maxlen=3)  # Pour flux spectral
        self._flux_history = deque(maxlen=10)     # Historique du flux
        self._last_trigger_ts = 0.0
        self._smoothed_energy = None
        
        # Filtre passe-bas pour le signal d'entrée
        self._create_filters()

        self._stream = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def _create_filters(self):
        """Crée un filtre passe-bas pour éliminer les hautes fréquences"""
        nyquist = self.sample_rate / 2
        cutoff = 200  # Hz - éliminer tout au-dessus de 200Hz
        self.b, self.a = scipy.signal.butter(4, cutoff / nyquist, btype='low')
        self.zi = scipy.signal.lfilter_zi(self.b, self.a)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_stream, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.close()
            except Exception:
                pass

    def update_params(self, trigger_factor=None, refractory_time=None, 
                     min_band_energy=None, smoothing_alpha=None, onset_threshold=None):
        with self._lock:
            if trigger_factor is not None:
                self.trigger_factor = trigger_factor
            if refractory_time is not None:
                self.refractory_time = refractory_time
            if min_band_energy is not None:
                self.min_band_energy = min_band_energy
            if smoothing_alpha is not None:
                self.smoothing_alpha = smoothing_alpha
            if onset_threshold is not None:
                self.onset_threshold = onset_threshold

    def _spectral_flux(self, current_spectrum, previous_spectrum):
        """Calcule le flux spectral pour détecter les onsets"""
        if previous_spectrum is None:
            return 0
        diff = current_spectrum - previous_spectrum
        # Somme seulement les augmentations (half-wave rectification)
        flux = np.sum(np.maximum(diff, 0))
        return flux

    def _run_stream(self):
        hann = np.hanning(self.block_size)
        filter_state = self.zi.copy()

        def callback(indata, frames, tinfo, status):
            nonlocal filter_state
            
            if not self._running:
                return
            if status and self.debug:
                print("KickDetector status:", status)

            mono = indata[:, 0].astype(np.float32)
            if len(mono) != self.block_size:
                return

            # Filtrage passe-bas
            filtered, filter_state = scipy.signal.lfilter(
                self.b, self.a, mono, zi=filter_state
            )

            # FFT avec fenêtrage
            fft = np.fft.rfft(filtered * hann)
            mags = np.abs(fft)
            freqs = np.fft.rfftfreq(len(filtered), 1 / self.sample_rate)

            # Énergie dans la bande kick
            band_mask = (freqs >= self.low_freq) & (freqs <= self.high_freq)
            band_energy = float(np.sum(mags[band_mask] ** 2))
            
            # Énergie totale du signal pour normalisation
            total_energy = float(np.sum(mags ** 2)) + 1e-9
            normalized_energy = band_energy / total_energy

            # Seuil minimal absolu
            if band_energy < self.min_band_energy:
                return

            # Lissage exponentiel
            if self._smoothed_energy is None:
                self._smoothed_energy = normalized_energy
            else:
                a = self.smoothing_alpha
                self._smoothed_energy = a * normalized_energy + (1 - a) * self._smoothed_energy

            # Stockage pour baseline
            self._energy_history.append(self._smoothed_energy)

            # Détection onset basée sur le flux spectral
            onset_detected = False
            flux = 0
            if len(self._spectrum_history) > 0:
                flux = self._spectral_flux(
                    mags[band_mask], 
                    self._spectrum_history[-1] if self._spectrum_history else None
                )
                self._flux_history.append(flux)
                
                # Seuil adaptatif pour le flux basé sur son historique
                if len(self._flux_history) >= 5:
                    flux_array = np.array(list(self._flux_history))
                    flux_mean = np.mean(flux_array)
                    flux_std = np.std(flux_array) + 1e-9
                    flux_threshold = flux_mean + self.onset_threshold * flux_std
                    
                    if flux > flux_threshold:
                        onset_detected = True

            # Stockage du spectre pour onset detection
            self._spectrum_history.append(mags[band_mask].copy())

            # Warmup
            if len(self._energy_history) < int(self.baseline_window * self.warmup_ratio):
                return

            # Calcul du seuil avec écart-type (plus robuste que MAD)
            history_arr = np.array(list(self._energy_history), dtype=np.float32)
            mean_energy = float(np.mean(history_arr))
            std_energy = float(np.std(history_arr)) + 1e-9
            threshold = mean_energy + self.trigger_factor * std_energy

            if self.debug:
                print(f"band={band_energy:8.1f} norm={normalized_energy:6.3f} "
                      f"smooth={self._smoothed_energy:6.3f} mean={mean_energy:6.3f} "
                      f"std={std_energy:6.3f} thr={threshold:6.3f} "
                      f"flux={flux:6.1f} onset={onset_detected}")

            # LOGIQUE DE DÉTECTION MODIFIÉE : OU au lieu de ET
            energy_trigger = self._smoothed_energy > threshold
            
            # Option 1: Déclenchement par énergie OU onset (plus permissif)
            if self.use_onset_detection:
                trigger_condition = energy_trigger or onset_detected
            else:
                trigger_condition = energy_trigger
            
            # Option 2: Si vous voulez garder ET mais avec des seuils plus bas
            # trigger_condition = energy_trigger and onset_detected

            if trigger_condition:
                now = time.time()
                if now - self._last_trigger_ts >= self.refractory_time:
                    self._last_trigger_ts = now
                    try:
                        self.mainboard.activate_kick()
                        if self.debug:
                            trigger_type = "ENERGY" if energy_trigger else ""
                            trigger_type += "+ONSET" if onset_detected else ""
                            print(f"🥁 KICK DETECTED! ({trigger_type})")
                    except Exception as e:
                        print(f"KickDetector activate_kick error: {e}")

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
            print(f"KickDetector stream error: {e}")
            self._running = False
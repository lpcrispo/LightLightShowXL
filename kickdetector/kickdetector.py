import sounddevice as sd
import numpy as np
import threading
import time
from collections import deque

class KickDetector:
    """
    Détection de kick live :
    - Calcule l'énergie dans la bande 40–120 Hz via FFT rapide
    - Maintient un baseline dynamique (médiane d'une fenêtre glissante)
    - Déclenche mainboard.activate_kick() quand énergie > baseline * factor
    """
    def __init__(
        self,
        mainboard,
        input_device_index,
        sample_rate=44100,
        block_size=1024,
        low_freq=40,
        high_freq=120,
        baseline_window=120,        # nombre de blocs pour baseline
        trigger_factor=3.0,         # multiplicateur sur la médiane
        refractory_time=0.12        # évite double trigger (s)
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

        self._energy_history = deque(maxlen=baseline_window)
        self._last_trigger_ts = 0
        self._stream = None
        self._running = False
        self._lock = threading.Lock()

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

    def _run_stream(self):
        def callback(indata, frames, tinfo, status):
            if not self._running:
                return
            if status:
                # Optionnel : print(status)
                pass
            mono = indata[:, 0].astype(np.float32)

            # FFT
            fft = np.fft.rfft(mono * np.hanning(len(mono)))
            mags = np.abs(fft)
            freqs = np.fft.rfftfreq(len(mono), 1 / self.sample_rate)

            # Énergie bande kick
            band_mask = (freqs >= self.low_freq) & (freqs <= self.high_freq)
            band_energy = float(np.sum(mags[band_mask] ** 2))

            # Mettre à jour baseline
            self._energy_history.append(band_energy)
            if len(self._energy_history) < int(self.baseline_window * 0.3):
                return  # Attendre un peu avant de détecter

            median_energy = np.median(self._energy_history)
            if median_energy <= 0:
                return

            # Détection
            if band_energy > median_energy * self.trigger_factor:
                now = time.time()
                if now - self._last_trigger_ts >= self.refractory_time:
                    self._last_trigger_ts = now
                    # Appel thread-safe
                    try:
                        self.mainboard.activate_kick()
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
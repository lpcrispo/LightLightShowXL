import sounddevice as sd
import threading

class AudioPassthrough:
    def __init__(self, input_device_index, output_device_index, samplerate=44100, blocksize=512, channels=1, gain=1.0):
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.channels = channels
        self.gain = gain
        self._stream = None
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.close()
            except Exception:
                pass

    def _run(self):
        def callback(indata, outdata, frames, time_info, status):
            if status:
                # print(status)  # Debug si besoin
                pass
            if not self._running:
                outdata.fill(0)
                return
            outdata[:] = indata * self.gain

        try:
            # device tuple = (input, output)
            self._stream = sd.Stream(
                device=(self.input_device_index, self.output_device_index),
                samplerate=self.samplerate,
                channels=self.channels,
                blocksize=self.blocksize,
                dtype='float32',
                callback=callback,
            )
            self._stream.start()
            while self._running:
                sd.sleep(150)
        except Exception as e:
            print(f"AudioPassthrough error: {e}")
            self._running = False
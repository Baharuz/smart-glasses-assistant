"""En fazla 20 saniyelik, yalnızca bellekte tutulan mikrofon kaydı."""
import array
import io
import threading
import wave


class MicrophoneError(RuntimeError):
    pass


class Recorder:
    def __init__(self, stream_factory=None, samplerate=None):
        self._factory = stream_factory
        self.samplerate = samplerate
        self._stream = None
        self._chunks = []
        self._samples = 0
        self._lock = threading.Lock()
        self.full = threading.Event()
        self._overflow = False

    @property
    def recording(self):
        return self._stream is not None

    def start(self):
        self.cancel()
        try:
            if self._factory is None:
                import sounddevice as sd
                factory = sd.RawInputStream
                rate = int(sd.query_devices(kind="input")["default_samplerate"])
            else:
                factory = self._factory
                rate = self.samplerate or 16000
            self.samplerate = rate
            self._chunks = []
            self._samples = 0
            self._overflow = False
            self.full.clear()
            self._stream = factory(samplerate=rate, channels=1, dtype="int16",
                                   callback=self._receive)
            self._stream.start()
        except Exception:
            self.cancel()
            raise MicrophoneError("Mikrofon açılamadı. Windows mikrofon iznini ve giriş aygıtını kontrol et.") from None

    def _receive(self, data, frames, time, status):
        with self._lock:
            if status:
                self._overflow = True
            remaining = self.samplerate * 20 - self._samples
            if remaining > 0:
                chunk = bytes(data)[:remaining * 2]
                self._chunks.append(chunk)
                self._samples += len(chunk) // 2
            if self._samples >= self.samplerate * 20:
                self.full.set()

    def cancel(self):
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()
        self._chunks = []
        self._samples = 0
        self.full.clear()

    def finish(self):
        stream, self._stream = self._stream, None
        if stream is None:
            raise MicrophoneError("Önce M tuşuyla konuşmayı başlat.")
        try:
            stream.stop()
        finally:
            stream.close()
        pcm = b"".join(self._chunks)
        self._chunks = []
        self.full.clear()
        if self._overflow:
            raise MicrophoneError("Ses kaydı kesildi. Diğer uygulamaları kapatıp yeniden dene.")
        samples = array.array("h", pcm)
        if len(samples) < self.samplerate // 4 or not samples or max(abs(x) for x in samples) < 150:
            raise MicrophoneError("Ses duyulamadı. M ile yeniden konuşmayı dene.")
        output = io.BytesIO()
        with wave.open(output, "wb") as recording:
            recording.setnchannels(1)
            recording.setsampwidth(2)
            recording.setframerate(self.samplerate)
            recording.writeframes(pcm)
        return output.getvalue()

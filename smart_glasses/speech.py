"""Ses motorunu ayrı süreçte çalıştırarak kesilebilir seslendirme sağlar."""
import multiprocessing


def _speak(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        for voice in engine.getProperty("voices"):
            details = f"{voice.id} {voice.name} {voice.languages}".lower()
            if any(value in details for value in ("turkish", "tr-tr", "tr_tr")):
                engine.setProperty("voice", voice.id)
                break
        engine.say(text)
        engine.runAndWait()
    except Exception:
        print("Sesli okuma kullanılamıyor. Sonraki okumada yeniden denenecek.", flush=True)


class Speaker:
    def __init__(self, process_factory=None):
        self._factory = process_factory or multiprocessing.get_context("spawn").Process
        self._process = None

    @property
    def speaking(self):
        if self._process is None:
            return False
        if self._process.is_alive():
            return True
        self._process.join()
        self._process.close()
        self._process = None
        return False

    def say(self, text):
        self.stop()
        print(text, flush=True)
        process = self._factory(target=_speak, args=(text,), daemon=True)
        try:
            process.start()
        except Exception:
            process.close()
            print("Sesli okuma başlatılamadı. Yanıt terminalde gösterildi.", flush=True)
            return
        self._process = process

    def wait(self, timeout=8):
        if self._process is not None:
            self._process.join(timeout=timeout)

    def stop(self):
        process = self._process
        if process is None:
            return
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join(timeout=1)
        if not process.is_alive():
            process.close()
            self._process = None

"""Çalıştırma: python -m smart_glasses"""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .vision import GeminiVision, VisionError


class Speaker:
    """Yalnızca arka plan iş parçacığında kullanılır."""

    def __init__(self):
        self.engine = None
        self.failed = False

    def say(self, text):
        print(text, flush=True)
        if self.failed:
            return
        try:
            if self.engine is None:
                import pyttsx3
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 165)
                for voice in self.engine.getProperty("voices"):
                    details = f"{voice.id} {voice.name} {voice.languages}".lower()
                    if "turkish" in details or "tr-tr" in details or "tr_tr" in details:
                        self.engine.setProperty("voice", voice.id)
                        break
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            self.failed = True
            print("Sesli okuma kullanılamıyor. Yanıtlar terminalde gösterilecek.", flush=True)


def main():
    import cv2
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    try:
        vision = GeminiVision(os.getenv("GEMINI_API_KEY", ""),
                              os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
        camera_index = int(os.getenv("CAMERA_INDEX", "0"))
        if camera_index < 0:
            raise ValueError("CAMERA_INDEX sıfır veya pozitif olmalı.")
    except ValueError as exc:
        print(f"Ayar hatası: {exc}")
        return 1

    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        camera.release()
        print("Kamera açılamadı. Kamera iznini ve CAMERA_INDEX ayarını kontrol et.")
        return 1

    speaker = Speaker()
    executor = ThreadPoolExecutor(max_workers=1)
    task = None
    last_description = ""

    def scan(jpeg):
        try:
            text = vision.describe(jpeg)
        except VisionError as exc:
            speaker.say(str(exc))
            return None
        speaker.say(text)
        return text

    print("Kamera penceresi seçiliyken: BOŞLUK = tara, R = tekrar oku, Q/ESC = çıkış.")
    task = executor.submit(speaker.say, "Hazır. Boşluk tuşuyla çevreni tarayabilirsin.")
    window = "Smart Glasses Assistant"
    cv2.namedWindow(window)
    try:
        while True:
            if task is not None and task.done():
                try:
                    result = task.result()
                    if result:
                        last_description = result
                except Exception:
                    print("Tarama tamamlanamadı. Tekrar dene.")
                task = None
            ok, frame = camera.read()
            if not ok:
                print("Kameradan görüntü alınamadı.")
                return 1
            display = frame.copy()
            label = "Processing..." if task else "SPACE: scan | R: repeat | Q: quit"
            cv2.putText(display, label, (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 255), 2)
            cv2.imshow(window, display)
            key = cv2.waitKey(20) & 0xFF
            if key in (27, ord("q"), ord("Q")) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == 32 and task is None:
                # Analiz kareleri üstündeki arayüz yazıları modele gönderilmez.
                height, width = frame.shape[:2]
                if width > 1280:
                    frame = cv2.resize(frame, (1280, round(height * 1280 / width)))
                encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if encoded:
                    print("Görüntü analiz ediliyor...", flush=True)
                    task = executor.submit(scan, buffer.tobytes())
                else:
                    print("Görüntü kodlanamadı.")
            elif key in (ord("r"), ord("R")) and task is None:
                task = executor.submit(speaker.say, last_description or "Henüz bir tarama yapılmadı.")
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Kamera kapatıldı. Devam eden analiz veya sesli okuma varsa tamamlanması bekleniyor.")
        executor.shutdown(wait=True, cancel_futures=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

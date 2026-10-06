"""Çalıştırma: python -m smart_glasses"""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .vision import GeminiVision, VisionError
from .speech import Speaker


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

    speaker = Speaker()
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        camera.release()
        speaker.say("Kamera açılamadı. Kamera iznini ve CAMERA_INDEX ayarını kontrol et.")
        speaker.wait()
        speaker.stop()
        return 1

    executor = ThreadPoolExecutor(max_workers=1)
    task = None
    last_description = ""

    read_result = True
    print("Kamera penceresi seçiliyken: BOŞLUK = tara, S = sesi durdur, R = tekrar oku, Q/ESC = çıkış.")
    speaker.say("Hazır. Boşluk tuşuyla çevreni tarayabilirsin. S tuşuyla sesi durdurabilirsin.")
    window = "Smart Glasses Assistant"
    try:
        cv2.namedWindow(window)
        while True:
            if task is not None and task.done():
                try:
                    result = task.result()
                    if result:
                        last_description = result
                        if read_result:
                            speaker.say(result)
                        else:
                            print(result, flush=True)
                except VisionError as exc:
                    if read_result:
                        speaker.say(str(exc))
                    else:
                        print(str(exc), flush=True)
                except Exception:
                    if read_result:
                        speaker.say("Tarama tamamlanamadı. Tekrar dene.")
                    else:
                        print("Tarama tamamlanamadı. Tekrar dene.", flush=True)
                task = None
            ok, frame = camera.read()
            if not ok:
                speaker.say("Kameradan görüntü alınamadı.")
                speaker.wait()
                return 1
            display = frame.copy()
            label = "Analyzing... | S: mute" if task else ("Speaking... | S: stop | SPACE: scan" if speaker.speaking else "SPACE: scan | R: repeat | S: stop | Q: quit")
            cv2.putText(display, label, (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 255), 2)
            cv2.imshow(window, display)
            key = cv2.waitKey(20) & 0xFF
            if key in (27, ord("q"), ord("Q")) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key in (ord("s"), ord("S")):
                speaker.stop()
                read_result = False
                print("Ses durduruldu.", flush=True)
            elif key == 32 and task is None:
                # Analiz kareleri üstündeki arayüz yazıları modele gönderilmez.
                height, width = frame.shape[:2]
                if width > 1280:
                    frame = cv2.resize(frame, (1280, round(height * 1280 / width)))
                encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if encoded:
                    read_result = True
                    speaker.say("Görüntü analiz ediliyor.")
                    task = executor.submit(vision.describe, buffer.tobytes())
                else:
                    speaker.say("Görüntü kodlanamadı. Tekrar dene.")
            elif key in (ord("r"), ord("R")) and task is None:
                speaker.say(last_description or "Henüz bir tarama yapılmadı.")
    finally:
        speaker.stop()
        camera.release()
        cv2.destroyAllWindows()
        print("Kamera kapatıldı. Ses durduruldu. Devam eden analiz varsa tamamlanması bekleniyor.")
        executor.shutdown(wait=True, cancel_futures=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

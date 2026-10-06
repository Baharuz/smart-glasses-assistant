"""Çalıştırma: python -m smart_glasses"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .vision import GeminiVision, VisionError
from .speech import Speaker
from .microphone import Recorder, MicrophoneError


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

    recorder = Recorder()
    last_m_press = 0.0
    executor = ThreadPoolExecutor(max_workers=1)
    task = None
    last_description = ""

    read_result = True
    print("Kamera penceresi seçiliyken: BOŞLUK = tara, M = konuş/gönder, S = durdur/iptal, R = tekrar oku, Q/ESC = çıkış.")
    speaker.say("Hazır. Boşluk tuşuyla çevreni tarayabilirsin. M tuşuna bas, konuş ve tekrar M ile gönder. S tuşuyla sesi durdurabilirsin.")
    def encode_frame(frame):
        height, width = frame.shape[:2]
        if width > 1280:
            frame = cv2.resize(frame, (1280, round(height * 1280 / width)))
        encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not encoded:
            raise MicrophoneError("Görüntü kodlanamadı. Tekrar dene.")
        return buffer.tobytes()

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
            if recorder.recording:
                label = "Listening... | M: send | S: cancel (max 20s)"
            elif task:
                label = "Thinking... | S: mute"
            elif speaker.speaking:
                label = "Speaking... | M: talk | S: stop"
            else:
                label = "M: talk | SPACE: scan | R: repeat | S: stop | Q: quit"
            cv2.putText(display, label, (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 255), 2)
            cv2.imshow(window, display)
            key = cv2.waitKey(20) & 0xFF
            if key in (27, ord("q"), ord("Q")) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break
            auto_send = (recorder.recording and recorder.full.is_set()
                         and key not in (ord("s"), ord("S")))
            if auto_send or (key in (ord("m"), ord("M")) and time.monotonic() - last_m_press > 0.6):
                last_m_press = time.monotonic()
                if task is not None:
                    continue
                try:
                    if recorder.recording:
                        wav = recorder.finish()
                        jpeg = encode_frame(frame)
                        read_result = True
                        speaker.say("Sorunu yanıtlıyorum.")
                        task = executor.submit(vision.answer_audio, wav, jpeg)
                    else:
                        speaker.stop()
                        recorder.start()
                        # Kayıt sırasında sesli bildirim çalınmaz; modele karışmasın.
                        print("Dinliyorum. Konuş; M ile gönder, S ile iptal et.", flush=True)
                except MicrophoneError as exc:
                    speaker.say(str(exc))
            elif key in (ord("s"), ord("S")):
                speaker.stop()
                recorder.cancel()
                read_result = False
                print("Ses durduruldu.", flush=True)
            elif key == 32 and task is None and not recorder.recording:
                try:
                    jpeg = encode_frame(frame)
                    read_result = True
                    speaker.say("Görüntü analiz ediliyor.")
                    task = executor.submit(vision.describe, jpeg)
                except MicrophoneError as exc:
                    speaker.say(str(exc))
            elif key in (ord("r"), ord("R")) and task is None and not recorder.recording:
                speaker.say(last_description or "Henüz bir yanıt alınmadı.")
            elif key in (ord("c"), ord("C")) and task is None and not recorder.recording:
                vision.history.clear()
                speaker.say("Sohbet geçmişi temizlendi.")
    finally:
        recorder.cancel()
        speaker.stop()
        camera.release()
        cv2.destroyAllWindows()
        print("Kamera kapatıldı. Ses durduruldu. Devam eden analiz varsa tamamlanması bekleniyor.")
        executor.shutdown(wait=True, cancel_futures=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

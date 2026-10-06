import os
import sys
import unittest
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from smart_glasses.__main__ import main


class ImmediateExecutor:
    def __init__(self, **kwargs):
        pass
    def submit(self, fn, *args):
        future = Future()
        try:
            future.set_result(fn(*args))
        except Exception as exc:
            future.set_exception(exc)
        return future
    def shutdown(self, **kwargs):
        pass


class AppTests(unittest.TestCase):
    def run_app(self, keys):
        frame = MagicMock()
        frame.shape = (480, 640, 3)
        camera = MagicMock()
        camera.isOpened.return_value = True
        camera.read.return_value = (True, frame)
        buffer = MagicMock()
        buffer.tobytes.return_value = b'jpeg'
        cv = MagicMock()
        cv.VideoCapture.return_value = camera
        cv.imencode.return_value = (True, buffer)
        cv.waitKey.side_effect = keys
        cv.getWindowProperty.return_value = 1
        speaker = MagicMock()
        speaker.speaking = False
        recorder = MagicMock()
        recorder.recording = False
        recorder.full.is_set.return_value = False
        recorder.start.side_effect = lambda: setattr(recorder, 'recording', True)
        recorder.cancel.side_effect = lambda: setattr(recorder, 'recording', False)
        def finish():
            recorder.recording = False
            return b'wav'
        recorder.finish.side_effect = finish
        vision = MagicMock()
        vision.answer_audio.return_value = 'Masada bir kitap var.'
        clock = iter(range(1, 100))
        with patch.dict(sys.modules, {'cv2': cv, 'dotenv': SimpleNamespace(load_dotenv=lambda *a: None)}), \
                patch.dict(os.environ, {'GEMINI_API_KEY': 'test', 'CAMERA_INDEX': '0'}), \
                patch('smart_glasses.__main__.GeminiVision', return_value=vision), \
                patch('smart_glasses.__main__.Speaker', return_value=speaker), \
                patch('smart_glasses.__main__.Recorder', return_value=recorder), \
                patch('smart_glasses.__main__.ThreadPoolExecutor', ImmediateExecutor), \
                patch('smart_glasses.__main__.time.monotonic', side_effect=lambda: next(clock)):
            self.assertEqual(main(), 0)
        camera.release.assert_called_once()
        return recorder, vision, speaker

    def test_microphone_question_is_sent_and_answer_spoken(self):
        recorder, vision, speaker = self.run_app([ord('m'), ord('m'), ord('q')])
        recorder.start.assert_called_once()
        recorder.finish.assert_called_once()
        vision.answer_audio.assert_called_once_with(b'wav', b'jpeg')
        self.assertIn(unittest.mock.call('Masada bir kitap var.'), speaker.say.call_args_list)

    def test_cancelled_recording_never_reaches_api(self):
        recorder, vision, speaker = self.run_app([ord('m'), ord('s'), ord('q')])
        recorder.finish.assert_not_called()
        vision.answer_audio.assert_not_called()
        self.assertFalse(recorder.recording)

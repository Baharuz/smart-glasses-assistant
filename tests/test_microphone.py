import io
import unittest
import wave
from smart_glasses.microphone import Recorder, MicrophoneError


class FakeStream:
    def __init__(self, **kwargs):
        self.callback = kwargs['callback']
        self.closed = False
    def start(self):
        pass
    def stop(self):
        pass
    def close(self):
        self.closed = True


class MicrophoneTests(unittest.TestCase):
    def setUp(self):
        self.recorder = Recorder(FakeStream, samplerate=16000)
        self.recorder.start()
        self.stream = self.recorder._stream

    def test_valid_wav_and_closed_stream(self):
        self.stream.callback(b'\xe8\x03' * 8000, 8000, None, False)
        audio = self.recorder.finish()
        with wave.open(io.BytesIO(audio), 'rb') as wav:
            self.assertEqual(wav.getframerate(), 16000)
            self.assertEqual(wav.getnchannels(), 1)
            self.assertEqual(wav.getnframes(), 8000)
        self.assertTrue(self.stream.closed)
        self.assertFalse(self.recorder.recording)

    def test_silence_is_rejected(self):
        self.stream.callback(b'\0\0' * 8000, 8000, None, False)
        with self.assertRaises(MicrophoneError):
            self.recorder.finish()

    def test_limit_is_bounded_and_signal_is_set(self):
        self.stream.callback(b'\xe8\x03' * 400000, 400000, None, False)
        self.assertTrue(self.recorder.full.is_set())
        self.assertEqual(self.recorder._samples, 16000 * 20)
        self.recorder.cancel()
        self.assertTrue(self.stream.closed)
        self.assertEqual(self.recorder._chunks, [])

    def test_overflow_is_not_sent_as_valid_audio(self):
        self.stream.callback(b'\xe8\x03' * 8000, 8000, None, True)
        with self.assertRaises(MicrophoneError):
            self.recorder.finish()

    def test_start_failure_releases_device(self):
        self.recorder.cancel()
        stream = FakeStream(callback=None)
        def fail():
            raise RuntimeError()
        stream.start = fail
        self.recorder._factory = lambda **kwargs: stream
        with self.assertRaises(MicrophoneError):
            self.recorder.start()
        self.assertTrue(stream.closed)
        self.assertFalse(self.recorder.recording)

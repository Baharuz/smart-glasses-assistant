import unittest
from smart_glasses.speech import Speaker


class FakeProcess:
    def __init__(self, **kwargs):
        self.alive = False
        self.closed = False
        self.terminated = False
    def start(self):
        self.alive = True
    def is_alive(self):
        return self.alive
    def terminate(self):
        self.terminated = True
        self.alive = False
    def join(self, timeout=None):
        pass
    def close(self):
        self.closed = True


class SpeakerTests(unittest.TestCase):
    def setUp(self):
        self.processes = []
        def factory(**kwargs):
            process = FakeProcess(**kwargs)
            self.processes.append(process)
            return process
        self.speaker = Speaker(factory)

    def test_stop_terminates_active_speech_and_allows_replay(self):
        self.speaker.say('İlk yanıt')
        first = self.processes[0]
        self.assertTrue(self.speaker.speaking)
        self.speaker.stop()
        self.assertTrue(first.terminated)
        self.assertTrue(first.closed)
        self.assertFalse(self.speaker.speaking)
        self.speaker.say('Tekrar')
        self.assertTrue(self.speaker.speaking)
        self.speaker.stop()

    def test_new_speech_replaces_old_speech(self):
        self.speaker.say('Hazır')
        self.speaker.say('Analiz ediliyor')
        self.assertTrue(self.processes[0].terminated)
        self.assertTrue(self.speaker.speaking)
        self.speaker.stop()

    def test_finished_process_is_reaped(self):
        self.speaker.say('Yanıt')
        self.processes[0].alive = False
        self.assertFalse(self.speaker.speaking)
        self.assertTrue(self.processes[0].closed)
        self.speaker.stop()

    def test_start_failure_can_be_retried(self):
        broken = FakeProcess()
        def fail():
            raise RuntimeError('unavailable')
        broken.start = fail
        self.speaker._factory = lambda **kwargs: broken
        self.speaker.say('Bir')
        self.assertFalse(self.speaker.speaking)
        self.assertTrue(broken.closed)
        self.speaker._factory = FakeProcess
        self.speaker.say('İki')
        self.assertTrue(self.speaker.speaking)
        self.speaker.stop()

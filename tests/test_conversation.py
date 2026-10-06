import base64
import json
import unittest
from unittest.mock import patch
from smart_glasses.vision import GeminiVision, VisionError


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.vision = GeminiVision('test-secret', 'gemini-3.8-flash')

    @patch.object(GeminiVision, '_request')
    def test_audio_image_and_follow_up_history(self, request):
        request.return_value = '{"question":"Masada ne var?","answer":"Bir kitap var."}'
        self.assertEqual(self.vision.answer_audio(b'wav', b'jpeg'), 'Bir kitap var.')
        inputs = request.call_args.args[0]
        self.assertEqual(base64.b64decode(inputs[1]['data']), b'wav')
        self.assertEqual(inputs[1]['mime_type'], 'audio/wav')
        self.assertEqual(base64.b64decode(inputs[2]['data']), b'jpeg')
        request.return_value = '```json\n{"question":"Rengi ne?","answer":"Kırmızı."}\n```'
        self.vision.answer_audio(b'wav2', b'jpeg2')
        self.assertIn('Masada ne var?', request.call_args.args[0][0]['text'])
        self.assertIn('Bir kitap var.', request.call_args.args[0][0]['text'])
        self.assertEqual(len(self.vision.history), 2)

    @patch.object(GeminiVision, '_request')
    def test_failed_or_unintelligible_turn_does_not_enter_history(self, request):
        for raw in ['invalid', '[]', '{"question":"","answer":"Tekrar söyle."}',
                    '{"question":42,"answer":"x"}', '{"question":"x","answer":""}']:
            request.return_value = raw
            with self.assertRaises(VisionError):
                self.vision.answer_audio(b'wav', b'jpeg')
        self.assertEqual(self.vision.history, [])

    @patch.object(GeminiVision, '_request')
    def test_history_keeps_six_turns_without_audio(self, request):
        for i in range(8):
            request.return_value = json.dumps({'question': str(i), 'answer': 'Yanıt'})
            self.vision.answer_audio(b'wav', b'jpeg')
        self.assertEqual(len(self.vision.history), 6)
        self.assertEqual(self.vision.history[0]['question'], '2')
        self.assertNotIn('wav', json.dumps(self.vision.history))

    @patch.object(GeminiVision, '_request')
    def test_invalid_media_is_not_sent(self, request):
        for audio, image in [(b'', b'jpeg'), (b'wav', b''),
                             (b'x' * (4 * 1024 * 1024 + 1), b'jpeg')]:
            with self.assertRaises(VisionError):
                self.vision.answer_audio(audio, image)
        request.assert_not_called()

import base64
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from smart_glasses.vision import GeminiVision, VisionError


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.vision = GeminiVision("test-secret", "gemini-3.8-flash")

    def response(self, result):
        return io.BytesIO(json.dumps(result).encode())

    @patch("smart_glasses.vision.urlopen")
    def test_image_request_and_text_only_output(self, send):
        send.return_value = self.response({"status": "completed", "steps": [
            {"type": "model_output", "content": [
                {"type": "thought", "text": "internal"},
                {"type": "text", "text": " Solda sandalye var. "}]}]})
        self.assertEqual(self.vision.describe(b"jpeg"), "Solda sandalye var.")
        request = send.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(base64.b64decode(payload["input"][1]["data"]), b"jpeg")
        self.assertFalse(payload["store"])
        self.assertNotIn("test-secret", request.full_url)
        self.assertEqual(send.call_args.kwargs["timeout"], 30)

    @patch("smart_glasses.vision.urlopen")
    def test_missing_malformed_or_partial_response(self, send):
        for result in [[], {}, {"status": "completed", "steps": []},
                       {"status": "completed", "steps": [None]},
                       {"status": "completed", "steps": [{"type": "model_output", "content": None}]},
                       {"status": "incomplete", "steps": []}]:
            with self.subTest(result=result):
                send.return_value = self.response(result)
                with self.assertRaises(VisionError):
                    self.vision.describe(b"jpeg")

    @patch("smart_glasses.vision.urlopen")
    def test_network_and_quota_errors_hide_credentials(self, send):
        for error in [URLError("test-secret"), TimeoutError("test-secret"),
                      HTTPError("https://example.com", 429, "test-secret", {}, None)]:
            send.side_effect = error
            with self.assertRaises(VisionError) as caught:
                self.vision.describe(b"jpeg")
            self.assertNotIn("test-secret", str(caught.exception))

    @patch("smart_glasses.vision.urlopen")
    def test_invalid_json(self, send):
        send.return_value = io.BytesIO(b"invalid")
        with self.assertRaises(VisionError):
            self.vision.describe(b"jpeg")

    @patch("smart_glasses.vision.urlopen")
    def test_empty_or_large_image_never_sent(self, send):
        for image in [b"", b"x" * (10 * 1024 * 1024 + 1)]:
            with self.assertRaises(VisionError):
                self.vision.describe(image)
        send.assert_not_called()

    def test_configuration_validation(self):
        for key, model in [(" ", "gemini-3.8-flash"), ("key", "../model")]:
            with self.assertRaises(ValueError):
                GeminiVision(key, model)


if __name__ == "__main__":
    unittest.main()

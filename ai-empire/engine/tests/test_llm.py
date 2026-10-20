import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from empire import llm


class LocalModelTests(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(
            ollama_base_url="http://127.0.0.1:11434",
            ollama_model="qwen2.5-coder:3b",
            llm_timeout_seconds=17,
            llm_retries=2,
        )

    def test_chat_returns_model_content_and_uses_configured_timeout(self):
        response = Mock()
        response.json.return_value = {"message": {"content": "  ready  "}}
        with patch("empire.llm.settings", self.settings), patch(
            "empire.llm.requests.post", return_value=response
        ) as post:
            self.assertEqual(llm.chat("system", "user"), "ready")
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], 17)
        self.assertEqual(post.call_args.kwargs["json"]["model"], "qwen2.5-coder:3b")

    def test_chat_retries_transient_connection_failure_then_succeeds(self):
        response = Mock()
        response.json.return_value = {"message": {"content": "recovered"}}
        with patch("empire.llm.settings", self.settings), patch(
            "empire.llm.requests.post",
            side_effect=[requests.ConnectionError("busy"), response],
        ) as post, patch("empire.llm.time.sleep") as sleep:
            self.assertEqual(llm.chat("system", "user"), "recovered")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_chat_does_not_retry_non_transient_http_error(self):
        response = requests.Response()
        response.status_code = 400
        error = requests.HTTPError("bad request", response=response)
        with patch("empire.llm.settings", self.settings), patch(
            "empire.llm.requests.post", side_effect=error
        ) as post, patch("empire.llm.time.sleep") as sleep:
            with self.assertRaises(llm.ModelError) as caught:
                llm.chat("system", "user")
        self.assertIn("after 1 attempt(s)", str(caught.exception))
        post.assert_called_once()
        sleep.assert_not_called()

    def test_chat_rejects_empty_model_response_without_retry(self):
        response = Mock()
        response.json.return_value = {"message": {"content": "  "}}
        with patch("empire.llm.settings", self.settings), patch(
            "empire.llm.requests.post", return_value=response
        ) as post:
            with self.assertRaisesRegex(llm.ModelError, "empty response"):
                llm.chat("system", "user")
        post.assert_called_once()


if __name__ == "__main__":
    unittest.main()

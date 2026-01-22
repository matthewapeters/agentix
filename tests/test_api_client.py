"""Tests for api_client module."""

import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from agentix import api_client
from agentix.context.sessions import assemble_prompts


class TestAssemblePayload(unittest.TestCase):
    """Test assemble_payload function."""

    @patch("agentix.sessions.get_user_prompt", return_value="Test prompt")
    @patch("agentix.api_client.query_api", return_value="Test response")
    def test_assemble_payload_basic(self, mock_query, mock_get_user):
        args = MagicMock()
        args.model = "phi4-mini:3.8b"
        args.temperature = 0.7
        args.session = "test_session"
        args.tools = []

        payload = assemble_prompts(args, [], 4096)

        self.assertEqual(payload["model"], "phi4-mini:3.8b")
        self.assertEqual(payload["temperature"], 0.7)
        # Expect 2 messages: system and user
        self.assertEqual(len(payload["messages"]), 2)

    @patch("agentix.sessions.get_user_prompt", return_value="Test prompt")
    @patch(
        "agentix.sessions.get_attachments", return_value=["attachment1", "attachment2"]
    )
    @patch("agentix.api_client.query_api", return_value="Test response")
    def test_assemble_payload_with_attachments(
        self, mock_query, mock_get_attachments, mock_get_user
    ):
        args = MagicMock()
        args.model = "phi4-mini:3.8b"
        args.temperature = 0.7
        args.session = "test_session"
        args.tools = []

        payload = assemble_prompts(args, [], 4096)

        self.assertEqual(payload["model"], "phi4-mini:3.8b")
        self.assertEqual(payload["temperature"], 0.7)
        # Expect 2 messages: system and user
        self.assertEqual(len(payload["messages"]), 2)
        # Check attachments in the user message
        self.assertEqual(len(payload["messages"][1]["attachments"]), 2)


class TestQueryApi(unittest.TestCase):
    """Test query_api function."""

    @patch("requests.post")
    def test_query_api_success(self, mock_post):
        """Test successful API query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is the answer",
                        "reasoning": "Some reasoning",
                    },
                    "finish_reason": "stop",
                }
            ]
        }
        mock_post.return_value = mock_response

        args = MagicMock()
        args.debug = False
        payload = {"model": "llama2", "messages": []}

        result = api_client.query_api(args, payload)

        self.assertEqual(result, "This is the answer")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_query_api_error(self, mock_post):
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        args = MagicMock()
        args.debug = False
        payload = {"model": "llama2", "messages": []}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = api_client.query_api(args, payload)

        self.assertEqual(result, "")
        self.assertIn("Error", mock_stdout.getvalue())

    @patch("requests.post")
    def test_query_api_debug_output(self, mock_post):
        """Test debug output is printed."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Answer", "reasoning": "Reasoning"},
                    "finish_reason": "stop",
                }
            ]
        }
        mock_post.return_value = mock_response

        args = MagicMock()
        args.debug = True
        payload = {"model": "llama2", "messages": []}

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            api_client.query_api(args, payload)

        debug_output = mock_stderr.getvalue()
        self.assertIn("Payload:", debug_output)
        self.assertIn("Raw response:", debug_output)

    @patch("requests.post")
    def test_query_api_missing_choices(self, mock_post):
        """Test API response with missing choices."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        args = MagicMock()
        args.debug = False
        payload = {"model": "llama2", "messages": []}

        with self.assertRaises((KeyError, IndexError)):
            api_client.query_api(args, payload)


class TestSummarizeUserPrompt(unittest.TestCase):
    """Test summarize_user_prompt function."""

    @patch("agentix.api_client.query_api", return_value="Test_Session")
    @patch("agentix.api_client.get_user_prompt", return_value="Test prompt")
    def test_summarize_user_prompt_payload_structure(self, mock_get_user, mock_query):
        args = MagicMock()
        args.model = "phi4-mini:3.8b"

        api_client.summarize_user_prompt(args)

        mock_query.assert_called_once()
        call_args = mock_query.call_args[0]
        payload = call_args[1]

        self.assertEqual(payload["model"], "phi4-mini:3.8b")


if __name__ == "__main__":
    unittest.main()

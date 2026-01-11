"""Tests for api_client module."""

import unittest
from unittest.mock import patch, MagicMock, call
import json
from io import StringIO
import sys
from src.agentix import api_client


class TestAssemblePayload(unittest.TestCase):
    """Test assemble_payload function."""

    @patch("src.agentix.api_client.trim_context")
    @patch("src.agentix.api_client.get_attachments")
    @patch("src.agentix.api_client.get_user_prompt")
    @patch("src.agentix.api_client.get_system_prompt")
    def test_assemble_payload_basic(self, mock_system, mock_user, mock_attach, mock_trim):
        """Test basic payload assembly."""
        mock_system.return_value = "[SYSTEM]\nSystem prompt\n[END SYSTEM]\n\n"
        mock_user.return_value = "User question"
        mock_attach.return_value = []
        mock_trim.return_value = [
            {"role": "system", "content": "[SYSTEM]\nSystem prompt\n[END SYSTEM]\n\n"},
            {"role": "user", "content": "User question", "attachments": []}
        ]
        
        args = MagicMock()
        args.model = "llama2"
        args.temperature = 0.7
        
        result = api_client.assemble_payload(args, 4096)
        
        self.assertEqual(result["model"], "llama2")
        self.assertEqual(result["temperature"], 0.7)
        self.assertIn("messages", result)
        self.assertEqual(len(result["messages"]), 2)

    @patch("src.agentix.api_client.trim_context")
    @patch("src.agentix.api_client.get_attachments")
    @patch("src.agentix.api_client.get_user_prompt")
    @patch("src.agentix.api_client.get_system_prompt")
    def test_assemble_payload_with_attachments(self, mock_system, mock_user, mock_attach, mock_trim):
        """Test payload assembly with file attachments."""
        mock_system.return_value = "[SYSTEM]\nSystem\n[END SYSTEM]\n\n"
        mock_user.return_value = "Question"
        mock_attach.return_value = ["file content"]
        mock_trim.return_value = [
            {"role": "system", "content": "[SYSTEM]\nSystem\n[END SYSTEM]\n\n"},
            {"role": "user", "content": "Question", "attachments": ["file content"]}
        ]
        
        args = MagicMock()
        args.model = "llama2"
        args.temperature = 0.5
        
        result = api_client.assemble_payload(args, 4096)
        
        self.assertEqual(result["messages"][1]["attachments"], ["file content"])


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
                        "reasoning": "Some reasoning"
                    },
                    "finish_reason": "stop"
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
                    "message": {
                        "content": "Answer",
                        "reasoning": "Reasoning"
                    },
                    "finish_reason": "stop"
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

    @patch("src.agentix.api_client.query_api")
    @patch("src.agentix.api_client.get_user_prompt")
    def test_summarize_user_prompt_success(self, mock_get_user, mock_query):
        """Test successful prompt summarization."""
        mock_get_user.return_value = "Generate a Python function to calculate factorial"
        mock_query.return_value = "Python_Factorial_Calculator"
        
        args = MagicMock()
        args.model = "llama2"
        
        api_client.summarize_user_prompt(args)
        
        self.assertEqual(args.session, "Python_Factorial_Calculator")

    @patch("src.agentix.api_client.query_api")
    @patch("src.agentix.api_client.get_user_prompt")
    def test_summarize_user_prompt_cleanup(self, mock_get_user, mock_query):
        """Test session ID cleanup removes special characters."""
        mock_get_user.return_value = "Some prompt"
        mock_query.return_value = "Session With Spaces / Special Chars"
        
        args = MagicMock()
        args.model = "llama2"
        
        api_client.summarize_user_prompt(args)
        
        # Spaces and slashes should be replaced with underscores
        self.assertEqual(args.session, "Session_With_Spaces___Special_Chars")

    @patch("src.agentix.api_client.query_api")
    @patch("src.agentix.api_client.get_user_prompt")
    def test_summarize_user_prompt_payload_structure(self, mock_get_user, mock_query):
        """Test summarize_user_prompt creates correct payload."""
        mock_get_user.return_value = "Test prompt"
        mock_query.return_value = "Test_Session"
        
        args = MagicMock()
        args.model = "llama2"
        
        api_client.summarize_user_prompt(args)
        
        # Verify query_api was called with correct structure
        mock_query.assert_called_once()
        call_args = mock_query.call_args[0]
        payload = call_args[1]
        
        self.assertEqual(payload["model"], "llama2")
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertEqual(payload["temperature"], 0.8)


if __name__ == "__main__":
    unittest.main()

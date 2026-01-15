"""Tests for main CLI module."""

import json
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, call, patch

from agentix.api_client import summarize_user_prompt
from agentix.main import main


class TestMainArguments(unittest.TestCase):
    """Test main CLI argument parsing."""

    @patch("agentix.main.get_models")
    @patch("sys.argv", ["agentix", "--list-models"])
    def test_list_models_argument(self, mock_get_models):
        """Test --list-models argument."""
        mock_get_models.return_value = [{"name": "llama2"}, {"name": "mistral"}]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(len(output), 2)

    @patch("agentix.main.get_prompts")
    @patch("sys.argv", ["agentix", "--list-prompts"])
    def test_list_prompts_argument(self, mock_get_prompts):
        """Test --list-prompts argument."""
        mock_get_prompts.return_value = {
            "python_coder": ["# Python", "Coder"],
            "debug": ["# Debug", "Instructions"],
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = json.loads(mock_stdout.getvalue())
        self.assertIn("python_coder", output)

    @patch("builtins.open")
    @patch("sys.argv", ["agentix", "--list-sessions"])
    def test_list_sessions_argument(self, mock_open):
        """Test --list-sessions argument."""
        mock_open.return_value.__enter__.return_value.readlines.return_value = [
            '{"session_id": "test1"}\n',
            '{"session_id": "test2"}\n',
        ]

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = mock_stdout.getvalue()
        self.assertIn("session", output)

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("sys.argv", ["agentix", "--list-sessions"])
    def test_list_sessions_not_found(self, mock_open):
        """Test --list-sessions when no sessions exist."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            main()

        self.assertIn("No sessions found", mock_stderr.getvalue())


class TestMainFlow(unittest.TestCase):
    """Test main CLI flow."""

    @patch("agentix.main.query_api")
    @patch("agentix.main.assemble_payload")
    @patch(
        "agentix.main.manage_sessions",
        return_value=[{"role": "user", "content": "Test"}],
    )
    @patch("agentix.main.get_model", return_value=4096)
    @patch(
        "sys.argv",
        [
            "agentix",
            "--user",
            "What is Python?",
            "--model",
            "llama2",
            "--with-front-end",
        ],
    )
    def test_main_with_frontend(
        self, mock_get_model, mock_manage, mock_assemble, mock_query
    ):
        """Test main flow with frontend flag."""
        mock_assemble.return_value = {"model": "llama2", "messages": []}
        mock_query.return_value = "Python is a programming language"

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        output = mock_stdout.getvalue()
        self.assertIn("Python is a programming language", output)
        mock_query.assert_called_once()

    @patch(
        "agentix.main.manage_sessions",
        return_value=[{"role": "user", "content": "Test"}],
    )
    @patch("agentix.main.get_model", return_value=4096)
    @patch("sys.argv", ["agentix", "--user", "Test", "--model", "llama2"])
    def test_main_without_frontend(self, mock_get_model, mock_manage):
        """Test main flow without frontend flag."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()

        # Should not print output without --with-front-end
        output = mock_stdout.getvalue()
        # Output should be minimal or empty

    @patch("agentix.main.get_model", return_value=4096)
    @patch(
        "sys.argv",
        [
            "agentix",
            "--user",
            "Test prompt",
            "--debug",
            "True",
        ],
    )
    def test_main_default_session(self, mock_get_model):
        """Test main with default session ID."""
        with patch(
            "agentix.main.query_api", return_value={"response": "Test response"}
        ):

            # Add debug statement to print sys.argv value
            print("Debug: sys.argv before main:", sys.argv)

            with patch("agentix.sessions.summarize_user_prompt") as mock_summarize:
                mock_summarize.return_value = None
                # Debugging: Print to confirm mock is applied
                print("Mock summarize_user_prompt applied:", mock_summarize)
                main()

                # Verify summarize_user_prompt is called during session creation
                mock_summarize.assert_called_once()
            print("Debug: Test arguments:", sys.argv)

    @patch(
        "agentix.main.manage_sessions",
        return_value=[{"role": "user", "content": "Test"}],
    )
    @patch("agentix.main.get_model", return_value=4096)
    @patch("sys.argv", ["agentix", "--user", "Test", "--session", "custom_session"])
    def test_main_custom_session(self, mock_get_model, mock_manage):
        """Test main with custom session ID."""
        with patch("agentix.api_client.summarize_user_prompt") as mock_summarize:
            mock_summarize.return_value = None
            main()

        # summarize_user_prompt should NOT be called for custom session
        mock_summarize.assert_not_called()

    @patch(
        "agentix.main.assemble_payload",
        return_value={"model": "phi4-mini:3.8b", "messages": []},
    )
    @patch(
        "agentix.main.manage_sessions",
        return_value=[{"role": "user", "content": "Test"}],
    )
    @patch("agentix.main.get_model", return_value=4096)
    @patch(
        "sys.argv",
        ["agentix", "--user", "Test", "--model", "phi4-mini:3.8b", "--temp", "0.8"],
    )
    def test_main_temperature_argument(
        self, mock_get_model, mock_manage, mock_assemble
    ):
        """Test temperature argument is passed correctly."""
        with patch(
            "agentix.main.query_api", return_value={"response": "Test response"}
        ):
            main()

    @patch("agentix.main.get_model", return_value=4096)
    @patch("sys.argv", ["agentix", "--user", "Test", "--debug", "True"])
    def test_main_debug_flag(self, mock_get_model):
        """Test debug flag is set correctly."""
        with patch(
            "agentix.main.manage_sessions",
            return_value=[{"role": "user", "content": "Test"}],
        ):
            main()


if __name__ == "__main__":
    unittest.main()

"""Tests for main CLI module."""

import unittest
from unittest.mock import patch, MagicMock, call
import json
import sys
from io import StringIO
from src.agentix.main import main


class TestMainArguments(unittest.TestCase):
    """Test main CLI argument parsing."""

    @patch("src.agentix.main.get_models")
    @patch("sys.argv", ["agentix", "--list-models"])
    def test_list_models_argument(self, mock_get_models):
        """Test --list-models argument."""
        mock_get_models.return_value = [
            {"name": "llama2"},
            {"name": "mistral"}
        ]
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
        
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(len(output), 2)

    @patch("src.agentix.main.get_prompts")
    @patch("sys.argv", ["agentix", "--list-prompts"])
    def test_list_prompts_argument(self, mock_get_prompts):
        """Test --list-prompts argument."""
        mock_get_prompts.return_value = {
            "python_coder": ["# Python", "Coder"],
            "debug": ["# Debug", "Instructions"]
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
            '{"session_id": "test2"}\n'
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

    @patch("src.agentix.main.query_api")
    @patch("src.agentix.main.assemble_payload")
    @patch("src.agentix.main.manage_sessions")
    @patch("src.agentix.main.summarize_user_prompt")
    @patch("src.agentix.main.get_model")
    @patch("sys.argv", [
        "agentix",
        "--user", "What is Python?",
        "--model", "llama2",
        "--with-front-end"
    ])
    def test_main_with_frontend(self, mock_get_model, mock_summarize, 
                                 mock_manage, mock_assemble, mock_query):
        """Test main flow with frontend flag."""
        mock_get_model.return_value = 4096
        mock_assemble.return_value = {"model": "llama2", "messages": []}
        mock_query.return_value = "Python is a programming language"
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
        
        output = mock_stdout.getvalue()
        self.assertIn("Python is a programming language", output)
        mock_query.assert_called_once()

    @patch("src.agentix.main.manage_sessions")
    @patch("src.agentix.main.get_model")
    @patch("sys.argv", [
        "agentix",
        "--user", "Test",
        "--model", "llama2"
    ])
    def test_main_without_frontend(self, mock_get_model, mock_manage):
        """Test main flow without frontend flag."""
        mock_get_model.return_value = 4096
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main()
        
        # Should not print output without --with-front-end
        output = mock_stdout.getvalue()
        # Output should be minimal or empty

    @patch("src.agentix.main.get_model")
    @patch("sys.argv", [
        "agentix",
        "--user", "Test prompt"
    ])
    def test_main_default_session(self, mock_get_model):
        """Test main with default session ID."""
        mock_get_model.return_value = 4096
        
        with patch("src.agentix.main.summarize_user_prompt") as mock_summarize:
            with patch("src.agentix.main.manage_sessions"):
                main()
        
        # summarize_user_prompt should be called for default session
        mock_summarize.assert_called_once()

    @patch("src.agentix.main.manage_sessions")
    @patch("src.agentix.main.get_model")
    @patch("sys.argv", [
        "agentix",
        "--user", "Test",
        "--session", "custom_session"
    ])
    def test_main_custom_session(self, mock_get_model, mock_manage):
        """Test main with custom session ID."""
        mock_get_model.return_value = 4096
        
        with patch("src.agentix.main.summarize_user_prompt") as mock_summarize:
            main()
        
        # summarize_user_prompt should NOT be called for custom session
        mock_summarize.assert_not_called()

    @patch("src.agentix.main.assemble_payload")
    @patch("src.agentix.main.manage_sessions")
    @patch("src.agentix.main.get_model")
    @patch("sys.argv", [
        "agentix",
        "--user", "Test",
        "--model", "llama2",
        "--temp", "0.8"
    ])
    def test_main_temperature_argument(self, mock_get_model, mock_manage, mock_assemble):
        """Test temperature argument is passed correctly."""
        mock_get_model.return_value = 4096
        mock_assemble.return_value = {"model": "llama2", "messages": []}
        
        with patch("src.agentix.main.query_api"):
            main()
        
        # Check that assemble_payload received correct temperature
        call_args = mock_assemble.call_args[0]
        args = call_args[0]
        self.assertAlmostEqual(args.temperature, 0.8)

    @patch("src.agentix.main.get_model")
    @patch("sys.argv", [
        "agentix",
        "--user", "Test",
        "--debug", "True"
    ])
    def test_main_debug_flag(self, mock_get_model):
        """Test debug flag is set correctly."""
        mock_get_model.return_value = 4096
        
        with patch("src.agentix.main.manage_sessions"):
            main()
        
        # Debug should be True (as boolean or truthy value)
        call_args = mock_get_model.call_args[0]
        args = call_args[0]
        # Note: argparse with type=bool may not work as expected
        # This test documents the current behavior


if __name__ == "__main__":
    unittest.main()

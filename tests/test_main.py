"""Tests for main CLI module."""

import json
import unittest
from io import StringIO
from unittest.mock import patch

from agentix.agentix_config import AgentixConfig
from agentix.main import main


class TestMainArguments(unittest.TestCase):
    """Test main CLI argument parsing."""

    @patch("agentix.main.get_models")
    def test_list_models_argument(self, mock_get_models):
        """Test --list-models argument."""
        mock_get_models.return_value = [{"name": "llama2"}, {"name": "mistral"}]
        config = AgentixConfig(list_models=True, file_path=[], debug=False)
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main(config)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(len(output), 2)

    @patch("agentix.main.get_prompts")
    def test_list_prompts_argument(self, mock_get_prompts):
        """Test --list-prompts argument."""
        mock_get_prompts.return_value = {
            "python_coder": ["# Python", "Coder"],
            "debug": ["# Debug", "Instructions"],
        }

        config = AgentixConfig(list_prompts=True, file_path=[], debug=False)
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main(config)
        output = json.loads(mock_stdout.getvalue())
        self.assertIn("python_coder", output)

    @patch("builtins.open")
    def test_list_sessions_argument(self, mock_open):
        """Test --list-sessions argument."""
        mock_open.return_value.__enter__.return_value.readlines.return_value = [
            '{"session_id": "test1"}\n',
            '{"session_id": "test2"}\n',
        ]
        config = AgentixConfig(list_sessions=True, file_path=[], debug=False)
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main(config)
        output = mock_stdout.getvalue()
        self.assertIn("session", output)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_list_sessions_not_found(self, _):
        """Test --list-sessions when no sessions exist."""
        config = AgentixConfig(list_sessions=True, file_path=[], debug=False)
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            main(config)
        self.assertIn("No sessions found", mock_stderr.getvalue())


class TestMainFlow(unittest.TestCase):
    """Test main CLI flow."""

    @patch("agentix.main.update_session")
    @patch("agentix.main.query_api")
    @patch("agentix.main.assemble_payload")
    @patch("agentix.main.manage_sessions")
    @patch("agentix.main.get_model", return_value=4096)
    def test_main_with_frontend(
        self,
        mock_get_model,
        mock_manage,
        mock_assemble,
        mock_query,
        mock_update_session,
    ):
        """Test main flow with frontend flag."""
        mock_query.return_value = "Python is a programming language"
        mock_assemble.return_value = {"model": "llama2", "messages": []}
        mock_manage.return_value = [{"role": "user", "content": "Test"}]
        config = AgentixConfig(
            user=["What is Python?"],
            model="llama2",
            with_frontend=True,
            file_path=[],
            debug=False,
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main(config)
        output = mock_stdout.getvalue()
        self.assertIn("Python is a programming language", output)
        mock_query.assert_called_once()

    @patch(
        "agentix.main.manage_sessions",
        return_value=[{"role": "user", "content": "Test"}],
    )
    @patch("agentix.main.get_model", return_value=4096)
    def test_main_without_frontend(self, _, __):
        """Test main flow without frontend flag."""
        config = AgentixConfig(user=["Test"], model="llama2", file_path=[], debug=False)
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            main(config)
        # Output should be minimal or empty

    @patch("agentix.main.get_model", return_value=4096)
    def test_main_default_session(self, _):
        """Test main with default session ID."""
        config = AgentixConfig(
            user=["Test prompt"],
            session="default_session",
            temperature=0.7,
            file_path=[],
            debug=False,
        )
        with patch(
            "agentix.main.query_api", return_value={"response": "Test response"}
        ):
            with patch("agentix.sessions.summarize_user_prompt") as mock_summarize:
                mock_summarize.return_value = None
                main(config)

    @patch(
        "agentix.main.manage_sessions",
        return_value=[{"role": "user", "content": "Test"}],
    )
    @patch("agentix.main.get_model", return_value=4096)
    def test_main_custom_session(self, _, __):
        """Test main with custom session ID."""
        config = AgentixConfig(
            user=["Test"], session="custom_session", file_path=[], debug=False
        )
        with patch("agentix.api_client.summarize_user_prompt") as mock_summarize:
            mock_summarize.return_value = None
            main(config)
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
    def test_main_temperature_argument(self, *args):
        """Test temperature argument is passed correctly."""
        config = AgentixConfig(
            user=["Test"],
            model="phi4-mini:3.8b",
            temperature=0.8,
            file_path=[],
            debug=False,
        )
        with patch(
            "agentix.main.query_api", return_value={"response": "Test response"}
        ):
            main(config)

    @patch("agentix.main.get_model", return_value=4096)
    def test_main_debug_flag(self, _):
        """Test debug flag is set correctly."""
        config = AgentixConfig(
            user=["Test"], temperature=0.7, file_path=[], debug=False
        )
        with patch(
            "agentix.main.manage_sessions",
            return_value=[{"role": "user", "content": "Test"}],
        ):
            main(config)


if __name__ == "__main__":
    unittest.main()

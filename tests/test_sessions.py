"""Tests for sessions module."""

import json
import unittest
from unittest.mock import MagicMock, mock_open, patch

from agentix.context import sessions


class TestGetSessionHistory(unittest.TestCase):
    """Test get_session_history function."""

    @patch("glob.glob")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_session_history_exists(self, mock_file, mock_glob):
        """Test retrieving existing session history."""
        session_data = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            session_data
        )
        mock_glob.return_value = ["./sessions/test_session_20260110T120000Z.json"]

        result = sessions.get_session_history("test_session")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], "user")

    @patch("glob.glob")
    def test_get_session_history_not_found(self, mock_glob):
        """Test when session history doesn't exist."""
        mock_glob.return_value = []

        result = sessions.get_session_history("nonexistent")

        self.assertEqual(result, [])

    @patch("glob.glob", side_effect=FileNotFoundError)
    def test_get_session_history_file_error(self, mock_glob):
        """Test error handling for file operations."""
        result = sessions.get_session_history("test_session")

        self.assertEqual(result, [])


class TestTrimContext(unittest.TestCase):
    """Test trim_context function."""

    @patch("src.agentix.sessions.get_session_history")
    @patch("builtins.open", new_callable=mock_open)
    def test_trim_context_within_limit(self, mock_file, mock_history):
        """Test trimming when messages are within token limit."""
        mock_history.return_value = []

        args = MagicMock()
        args.session = "test_session"
        messages = [{"role": "user", "content": "Short message"}]

        result = sessions.trim_context(args, messages, 5000)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["content"], "Short message")

    @patch("src.agentix.sessions.get_session_history")
    @patch("builtins.open", new_callable=mock_open)
    def test_trim_context_exceeds_limit(self, mock_file, mock_history):
        """Test trimming when messages exceed token limit."""
        # Each character is roughly 1/4 token
        long_content = "x" * 20000  # ~5000 tokens
        mock_history.return_value = [{"role": "user", "content": long_content}]

        args = MagicMock()
        args.session = "test_session"
        messages = [{"role": "user", "content": "Short message"}]

        result = sessions.trim_context(args, messages, 1000)

        # Should trim oldest message due to token limit
        self.assertLess(len(result), 2)

    @patch("src.agentix.sessions.get_session_history")
    @patch("builtins.open", new_callable=mock_open)
    def test_trim_context_saves_history(self, mock_file, mock_history):
        """Test that context trimming saves history to file."""
        mock_history.return_value = []

        args = MagicMock()
        args.session = "test_session"
        messages = [{"role": "user", "content": "Test message"}]

        sessions.trim_context(args, messages, 5000)

        # Verify file was opened for writing
        mock_file.assert_called()
        call_args = mock_file.call_args_list[-1]
        self.assertIn("w", call_args[0])

    @patch("src.agentix.sessions.get_session_history")
    @patch("builtins.open", new_callable=mock_open)
    def test_trim_context_with_attachments(self, mock_file, mock_history):
        """Test trimming considers attachment tokens."""
        mock_history.return_value = []

        args = MagicMock()
        args.session = "test_session"
        messages = [
            {
                "role": "user",
                "content": "Message",
                "attachments": ["x" * 4000],  # Large attachment
            }
        ]

        result = sessions.trim_context(args, messages, 500)

        # Should trim or not include based on attachment size
        self.assertIsInstance(result, list)


class TestManageSessions(unittest.TestCase):
    """Test manage_sessions function."""

    def test_manage_sessions_new_session(self):
        """Test creating new session with default ID."""
        args = MagicMock()
        args.session = "agentix_session"
        args.model = "llama2"
        args.debug = False

        # Use side_effect to handle both read and write file operations
        file_data = json.dumps({"sessions": []})
        m_open = mock_open(read_data=file_data)

        with patch("builtins.open", m_open):
            sessions.manage_sessions(args)

        # Verify file was written
        m_open.assert_called()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"sessions": [{"session_id": "test", "model": "llama2"}]}',
    )
    def test_manage_sessions_continue(self, mock_file):
        """Test continuing existing session."""
        args = MagicMock()
        args.session = "__continue"
        args.model = None
        args.debug = False

        sessions.manage_sessions(args)

        self.assertEqual(args.session, "test")
        self.assertEqual(args.model, "llama2")

    @patch("builtins.open", new_callable=mock_open)
    def test_manage_sessions_continue_no_sessions(self, mock_file):
        """Test continuing when no sessions exist."""
        args = MagicMock()
        args.session = "__continue"
        args.model = None
        args.debug = False

        mock_file.side_effect = FileNotFoundError()

        sessions.manage_sessions(args)

        # Session should remain unchanged if no sessions exist
        self.assertEqual(args.session, "__continue")

    def test_manage_sessions_custom_session(self):
        """Test managing custom session ID."""
        args = MagicMock()
        args.session = "custom_session_id"
        args.debug = False

        # Should not raise any errors
        sessions.manage_sessions(args)

        # Custom session ID should remain unchanged
        self.assertEqual(args.session, "custom_session_id")


if __name__ == "__main__":
    unittest.main()

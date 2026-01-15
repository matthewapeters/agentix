"""Tests for prompts module."""

import unittest
from unittest.mock import MagicMock, mock_open, patch

from agentix import prompts
from agentix.constants import AGENTIX_HOME


class TestGetSystemPrompt(unittest.TestCase):
    """Test get_system_prompt function."""

    @patch("glob.glob")
    @patch("agentix.prompts.get_file")
    def test_get_system_prompt_single(self, mock_get_file, mock_glob):
        """Test loading a single system prompt."""
        mock_glob.return_value = [f"{AGENTIX_HOME}/system_prompts/python_coder.md"]
        mock_get_file.return_value = "Python coding guidelines"

        args = MagicMock()
        args.debug = False
        args.system = ["python_coder"]

        result = prompts.get_system_prompt(args)

        self.assertIn("[SYSTEM]", result)
        self.assertIn("[END SYSTEM]", result)
        self.assertIn("Python coding guidelines", result)

    @patch("glob.glob")
    @patch("agentix.prompts.get_file")
    def test_get_system_prompt_multiple(self, mock_get_file, mock_glob):
        """Test loading multiple system prompts."""
        mock_glob.return_value = [
            f"{AGENTIX_HOME}/system_prompts/python_coder.md",
            f"{AGENTIX_HOME}/system_prompts/structured_response.md",
        ]
        mock_get_file.side_effect = [
            "adhere to the following guidelines",
            "Keys in Dict/Object must be one of:",
        ]

        args = MagicMock()
        args.debug = False
        args.system = ["python_coder", "structured_response"]

        result = prompts.get_system_prompt(args)

        self.assertIn("adhere to the following guidelines", result)
        self.assertIn("Keys in Dict/Object must be one of:", result)

    @patch("glob.glob")
    def test_get_system_prompt_none(self, mock_glob):
        """Test when no system prompts are provided."""
        mock_glob.return_value = []

        args = MagicMock()
        args.debug = False
        args.system = None

        result = prompts.get_system_prompt(args)

        self.assertIn("[SYSTEM]", result)
        self.assertIn("[END SYSTEM]", result)


class TestGetUserPrompt(unittest.TestCase):
    """Test get_user_prompt function."""

    def test_get_user_prompt_single(self):
        """Test single user prompt."""
        args = MagicMock()
        args.user = ["What is Python?"]

        result = prompts.get_user_prompt(args)

        self.assertEqual(result, "What is Python?")

    def test_get_user_prompt_multiple(self):
        """Test multiple user prompts joined together."""
        args = MagicMock()
        args.user = ["First question", "Second question", "Third question"]

        result = prompts.get_user_prompt(args)

        self.assertEqual(result, "First question\nSecond question\nThird question")

    def test_get_user_prompt_none(self):
        """Test when no user prompt is provided."""
        args = MagicMock()
        args.user = None

        result = prompts.get_user_prompt(args)

        self.assertEqual(result, "")

    def test_get_user_prompt_empty_list(self):
        """Test when user prompt list is empty."""
        args = MagicMock()
        args.user = []

        result = prompts.get_user_prompt(args)

        self.assertEqual(result, "")


class TestGetPrompts(unittest.TestCase):
    """Test get_prompts function."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="# Python Coder\nGenerate Python code\n\nGuidelines:",
    )
    @patch("glob.glob")
    def test_get_prompts_single(self, mock_glob, mock_file):
        """Test getting single prompt metadata."""
        mock_glob.return_value = [f"{AGENTIX_HOME}/system_prompts/python_coder.md"]

        args = MagicMock()
        args.debug = False
        args.system = "python_coder"

        result = prompts.get_prompts(args)

        self.assertIn("python_coder", result)
        self.assertEqual(len(result["python_coder"]), 2)

    @patch("builtins.open", new_callable=mock_open)
    @patch("glob.glob")
    def test_get_prompts_multiple(self, mock_glob, mock_file):
        """Test getting multiple prompt metadata."""
        mock_glob.return_value = [
            f"{AGENTIX_HOME}/system_prompts/python_coder.md",
            f"{AGENTIX_HOME}/system_prompts/debug.md",
        ]

        # Setup different content for each file
        mock_file.return_value.__enter__.return_value.readlines.side_effect = [
            ["# Python Coder\n", "Generate code\n", "\n", "More content\n"],
            ["# Debug\n", "Debug guidelines\n", "\n", "More content\n"],
        ]

        args = MagicMock()
        args.debug = False

        result = prompts.get_prompts(args)

        self.assertEqual(len(result), 2)
        self.assertIn("python_coder", result)
        self.assertIn("debug", result)

    @patch("glob.glob")
    def test_get_prompts_empty(self, mock_glob):
        """Test when no prompts are available."""
        mock_glob.return_value = []

        args = MagicMock()
        args.debug = False

        result = prompts.get_prompts(args)

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()

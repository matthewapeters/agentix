"""Tests for constants module."""

import unittest

from agentix import constants


class TestConstants(unittest.TestCase):
    """Test constants are properly defined."""

    def test_max_tokens_is_integer(self):
        """Test MAX_TOKENS is an integer."""
        self.assertIsInstance(constants.MAX_TOKENS, int)
        self.assertGreater(constants.MAX_TOKENS, 0)

    def test_directory_paths_are_strings(self):
        """Test directory path constants are strings."""
        self.assertIsInstance(constants.SYSTEM_PROMPTS_DIR, str)
        self.assertIsInstance(constants.SESSIONS_DIR, str)

    def test_api_endpoints_are_strings(self):
        """Test API endpoint constants are strings."""
        self.assertIsInstance(constants.OLLAMA_API_BASE, str)
        self.assertIsInstance(constants.OLLAMA_MODELS_ENDPOINT, str)
        self.assertIsInstance(constants.OLLAMA_CHAT_ENDPOINT, str)

    def test_default_values_are_correct_types(self):
        """Test default values have correct types."""
        self.assertIsInstance(constants.DEFAULT_TEMPERATURE, float)
        self.assertIsInstance(constants.DEFAULT_SESSION_ID, str)
        self.assertIsInstance(constants.SESSIONS_METADATA_FILE, str)


if __name__ == "__main__":
    unittest.main()

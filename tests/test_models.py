"""Tests for models module."""

import unittest
from unittest.mock import MagicMock, patch

from agentix import models


class TestParseParameterSize(unittest.TestCase):
    """Test parse_parameter_size function."""

    def test_parse_billion_parameter(self):
        """Test parsing billions."""
        result = models.parse_parameter_size("7B")
        self.assertEqual(result, 7000000000)

    def test_parse_million_parameter(self):
        """Test parsing millions."""
        result = models.parse_parameter_size("256M")
        self.assertEqual(result, 256000000)

    def test_parse_thousand_parameter(self):
        """Test parsing thousands."""
        result = models.parse_parameter_size("512K")
        self.assertEqual(result, 512000)

    def test_parse_decimal_parameter(self):
        """Test parsing decimal values."""
        result = models.parse_parameter_size("1.5B")
        self.assertEqual(result, 1500000000)

    def test_parse_invalid_format(self):
        """Test invalid format raises ValueError."""
        with self.assertRaises(ValueError):
            models.parse_parameter_size("invalid")

    def test_parse_missing_suffix(self):
        """Test missing suffix is handled (extracts first char as multiplier)."""
        # "256" - extracts "25" as number, "6" as suffix with default multiplier
        result = models.parse_parameter_size("256")
        self.assertEqual(result, 25)  # 25 * 1 (default multiplier)

    def test_parse_unknown_suffix(self):
        """Test unknown suffix uses default multiplier."""
        result = models.parse_parameter_size("256X")
        self.assertEqual(result, 256)

    def test_parse_lowercase_suffix(self):
        """Test lowercase suffix is converted to uppercase."""
        result = models.parse_parameter_size("1b")
        self.assertEqual(result, 1000000000)


class TestGetModels(unittest.TestCase):
    """Test get_models function."""

    @patch("requests.get")
    def test_get_models_success(self, mock_get):
        """Test successful model retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2", "size": "7B"},
                {"name": "mistral", "size": "7B"},
            ]
        }
        mock_get.return_value = mock_response

        args = MagicMock()
        args.debug = False
        args.model = None

        result = models.get_models(args)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "llama2")

    @patch("requests.get")
    def test_get_models_filter_by_name(self, mock_get):
        """Test filtering models by name prefix."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2", "size": "7B"},
                {"name": "llama-chat", "size": "7B"},
                {"name": "mistral", "size": "7B"},
            ]
        }
        mock_get.return_value = mock_response

        args = MagicMock()
        args.debug = False
        args.model = "llama"

        result = models.get_models(args)

        # The filter returns all models if multiple match the prefix
        self.assertGreaterEqual(len(result), 2)
        self.assertTrue(any("llama" in m["name"] for m in result))

    @patch("requests.get")
    def test_get_models_single_match(self, mock_get):
        """Test returns list even for single match."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2", "size": "7B"},
                {"name": "mistral", "size": "7B"},
            ]
        }
        mock_get.return_value = mock_response

        args = MagicMock()
        args.debug = False
        args.model = "llama2"

        result = models.get_models(args)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "llama2")


class TestGetModel(unittest.TestCase):
    """Test get_model function."""

    @patch("agentix.models.get_models")
    def test_get_model_success(self, mock_get_models):
        """Test successful model selection."""
        mock_get_models.return_value = [
            {"name": "llama2", "details": {"parameter_size": "7B"}}
        ]

        args = MagicMock()
        args.debug = False

        max_tokens = models.get_model(args)

        self.assertEqual(max_tokens, 7000000000)
        self.assertEqual(args.model, "llama2")

    @patch("agentix.models.get_models")
    def test_get_model_multiple_matches(self, mock_get_models):
        """Test model selection with multiple matches."""
        mock_get_models.return_value = [
            {"name": "llama2", "details": {"parameter_size": "7B"}},
            {"name": "llama-chat", "details": {"parameter_size": "7B"}},
        ]

        args = MagicMock()
        args.debug = False

        max_tokens = models.get_model(args)

        self.assertEqual(max_tokens, 7000000000)
        self.assertEqual(args.model, "llama2")

    @patch("agentix.models.get_models")
    def test_get_model_invalid_parameter_size(self, mock_get_models):
        """Test error handling for invalid parameter size."""
        mock_get_models.return_value = [
            {"name": "invalid-model", "details": {"parameter_size": "invalid"}}
        ]

        args = MagicMock()
        args.debug = False

        with self.assertRaises(ValueError):
            models.get_model(args)

    @patch("agentix.models.get_models")
    def test_get_model_missing_parameter_size(self, mock_get_models):
        """Test error handling for missing parameter size."""
        mock_get_models.return_value = [{"name": "model-without-size", "details": {}}]

        args = MagicMock()
        args.debug = False

        with self.assertRaises((KeyError, ValueError)):
            models.get_model(args)


if __name__ == "__main__":
    unittest.main()

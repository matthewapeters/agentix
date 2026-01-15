"""Tests for file utilities module."""

import unittest
from io import StringIO
from unittest.mock import MagicMock, mock_open, patch

from src.agentix import file_utils

# pylint: disable=unused-argument


class TestLoadFile(unittest.TestCase):
    """Test load_file function."""

    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    def test_load_file_success(self, mock_file):
        """Test successful file loading."""
        result = file_utils.load_file("test.txt")
        self.assertEqual(result, "test content")
        mock_file.assert_called_once_with("test.txt", "r", encoding="utf-8")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_file_not_found(self, mock_file):
        """Test file not found raises exception."""
        with self.assertRaises(FileNotFoundError):
            file_utils.load_file("nonexistent.txt")


class TestGetFile(unittest.TestCase):
    """Test get_file function."""

    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    def test_get_file_success(self, mock_file):
        """Test get_file returns formatted output."""
        result = file_utils.get_file("test.txt")
        self.assertIn("[FILE: test.txt]", result)
        self.assertIn("test content", result)
        self.assertIn("[END OF FILE]", result)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_get_file_error_handling(self, mock_file):
        """Test get_file handles errors gracefully."""
        with patch("sys.stderr", new_callable=StringIO):
            result = file_utils.get_file("nonexistent.txt")
            self.assertEqual(result, "")

    @patch("builtins.open", side_effect=PermissionError)
    def test_get_file_permission_error(self, mock_file):
        """Test get_file handles permission errors."""
        with patch("sys.stderr", new_callable=StringIO):
            result = file_utils.get_file("protected.txt")
            self.assertEqual(result, "")


class TestGetAttachments(unittest.TestCase):
    """Test get_attachments function."""

    @patch("src.agentix.file_utils.get_file")
    def test_get_attachments_single_file(self, mock_get_file):
        """Test getting single attachment."""
        mock_get_file.return_value = "file content"
        args = MagicMock()
        args.file_path = ["file1.txt"]

        result = file_utils.get_attachments(args)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "file content")
        mock_get_file.assert_called_once_with("file1.txt")

    @patch("src.agentix.file_utils.get_file")
    def test_get_attachments_multiple_files(self, mock_get_file):
        """Test getting multiple attachments."""
        mock_get_file.side_effect = ["content1", "content2", "content3"]
        args = MagicMock()
        args.file_path = ["file1.txt", "file2.txt", "file3.txt"]

        result = file_utils.get_attachments(args)

        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["content1", "content2", "content3"])
        self.assertEqual(mock_get_file.call_count, 3)

    def test_get_attachments_no_files(self):
        """Test get_attachments with no files."""
        args = MagicMock()
        args.file_path = None

        result = file_utils.get_attachments(args)

        self.assertEqual(result, [])

    @patch("src.agentix.file_utils.get_file")
    def test_get_attachments_error_handling(self, mock_get_file):
        """Test get_attachments handles errors gracefully."""
        mock_get_file.side_effect = [
            "content1",
            FileNotFoundError("File not found"),
            "content3",
        ]
        args = MagicMock()
        args.file_path = ["file1.txt", "file2.txt", "file3.txt"]

        with patch("sys.stderr", new_callable=StringIO):
            result = file_utils.get_attachments(args)

        # Should still return attachments from successful calls
        self.assertEqual(len(result), 2)
        self.assertEqual(result, ["content1", "content3"])


if __name__ == "__main__":
    unittest.main()

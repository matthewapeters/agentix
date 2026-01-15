import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentix.tools.describe_tools import ToolExtractor

import unittest


class TestDescribeTools(unittest.TestCase):
    def setUp(self):
        self.extractor = ToolExtractor(debug=True)

    def test_extract_tools_from_code(self):
        source_code = """
def sample_function(param1: int, param2: str = \"default\") -> bool:
    \"\"\"This is a sample function.\"\"\"
    return True
"""
        tools = self.extractor.extract_tools_from_code(source_code)
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertEqual(tool["name"], "sample_function")
        self.assertEqual(tool["description"], "This is a sample function.")
        # Add assertions for parameters and return type once implemented

    def test_extract_tools_from_file(self):
        # Assuming a temporary file is created for testing
        with open("temp_test_file.py", "w") as temp_file:
            temp_file.write(
                """
def another_function(x: float) -> str:
    \"\"\"Another test function.\"\"\"
    return str(x)
"""
            )
        tools = self.extractor.extract_tools_from_file("temp_test_file.py")
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertEqual(tool["name"], "another_function")
        self.assertEqual(tool["description"], "Another test function.")
        # Add assertions for parameters and return type once implemented


if __name__ == "__main__":
    unittest.main()

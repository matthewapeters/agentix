import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentix.tools.describe_tools.tool_extractor import ToolExtractor

import unittest


class TestDescribeTools(unittest.TestCase):
    def setUp(self):
        self.extractor = ToolExtractor(debug=True)

    def test_extract_tools_from_code(self):
        source_code = """
def sample_function(param1: int, param2: str = \"default\") -> bool:
    \"\"\"This is a sample function.
    It has a multi-line docstring.
    \"\"\"
    return True
"""
        tools = self.extractor.extract_tools_from_code(source_code)
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertEqual(tool["name"], "sample_function")
        self.assertEqual(
            tool["description"],
            "This is a sample function.\nIt has a multi-line docstring.",
        )
        self.assertEqual(
            tool["parameters_schema"]["properties"]["param1"]["type"], "int"
        )
        self.assertEqual(
            tool["parameters_schema"]["properties"]["param2"]["type"], "str"
        )
        self.assertEqual(
            tool["parameters_schema"]["properties"]["param2"]["default"], "default"
        )
        self.assertEqual(tool["returns"]["type"], "bool")

    def test_extract_tools_from_file(self):
        # Assuming a temporary file is created for testing
        with open("temp_test_file.py", "w") as temp_file:
            temp_file.write(
                """
def another_function(x: float) -> str:
    \"\"\"Another example function.
    This docstring spans multiple lines.
    \"\"\"
    return str(x)
"""
            )
        tools = self.extractor.extract_tools_from_file("temp_test_file.py")
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertEqual(tool["name"], "another_function")
        self.assertEqual(
            tool["description"],
            "Another example function.\nThis docstring spans multiple lines.",
        )
        self.assertEqual(tool["parameters_schema"]["properties"]["x"]["type"], "float")
        self.assertEqual(tool["returns"]["type"], "str")


if __name__ == "__main__":
    unittest.main()

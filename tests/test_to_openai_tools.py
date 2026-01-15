"""
Unit test for agentix.tools.describe_tools.to_openai_tools
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentix.tools.describe_tools import ToolSpec, to_openai_tools


def make_tool_spec(**kwargs):
    # Helper to create ToolSpec with defaults
    defaults = dict(
        name="test_func",
        description="A test function.",
        docstring="A test function docstring.",
        parameters_schema={
            "type": "object",
            "properties": {"a": {"type": "int"}},
            "required": ["a"],
        },
        returns={"type": "str"},
        qualified_name="test_func",
        is_method=False,
        class_name=None,
    )
    defaults.update(kwargs)
    return ToolSpec(**defaults)


class TestToOpenAITools(unittest.TestCase):
    def test_single_tool(self):
        tool = make_tool_spec()
        result = to_openai_tools([tool])
        self.assertEqual(len(result), 1)
        openai_tool = result[0]
        self.assertEqual(openai_tool["type"], "function")
        self.assertIn("function", openai_tool)
        fn = openai_tool["function"]
        self.assertEqual(fn["name"], "test_func")
        self.assertEqual(fn["description"], "A test function.")
        self.assertEqual(fn["parameters"], tool.parameters_schema)

    def test_qualified_name_flattening(self):
        tool = make_tool_spec(qualified_name="my.module.func")
        result = to_openai_tools([tool])
        fn = result[0]["function"]
        self.assertEqual(fn["name"], "my__module__func")

    def test_description_fallback(self):
        tool = make_tool_spec(description=None, docstring="Docstring only.")
        result = to_openai_tools([tool])
        fn = result[0]["function"]
        self.assertEqual(fn["description"], "Docstring only.")

    def test_multiple_tools(self):
        tool1 = make_tool_spec(name="f1", qualified_name="f1")
        tool2 = make_tool_spec(name="f2", qualified_name="f2")
        result = to_openai_tools([tool1, tool2])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["function"]["name"], "f1")
        self.assertEqual(result[1]["function"]["name"], "f2")


if __name__ == "__main__":
    unittest.main()

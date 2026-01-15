""""""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

import libcst as cst

from .tool_extractor import ToolExtractor


def extract_tools_from_code(source: str) -> List[Dict]:
    """
    Parse Python source with LibCST and extract a list of tool specs (dicts) for
    top-level functions and class methods (non-nested).
    """
    module = cst.parse_module(source)
    collector = ToolExtractor()
    module.visit(collector)
    return [asdict(t) for t in collector.tools]


def extract_tools_from_file(path: str) -> List[Dict]:
    """
    Docstring for extract_tools_from_file

    :param path: Description
    :type path: str
    :return: Description
    :rtype: List[Dict]
    """
    with open(path, "r", encoding="utf8") as f:
        source = f.read()
    return extract_tools_from_code(source)


# Optional: format for OpenAI "tools" (function calling) style
def to_openai_tools(tools: List[Dict]) -> List[Dict]:
    """
    Docstring for to_openai_tools

    :param tools: Description
    :type tools: List[Dict]
    :return: Description
    :rtype: List[Dict]
    """
    out = []
    for t in tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t["qualified_name"].replace(
                        ".", "__"
                    ),  # flatten for API constraints
                    "description": t.get("description")
                    or (t.get("docstring") or "")[:300],
                    "parameters": t["parameters_schema"],
                },
            }
        )
    return out

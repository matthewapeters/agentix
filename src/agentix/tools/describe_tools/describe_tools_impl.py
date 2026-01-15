from __future__ import annotations

import ast as pyast
import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

import libcst as cst

# -------------------------------
# Utilities: docstrings & strings
# -------------------------------


def _extract_docstring_from_function(fn: cst.FunctionDef) -> Optional[str]:
    """
    Return the function docstring if present (entire content, including multi-line).
    """
    if not isinstance(fn.body, cst.IndentedBlock) or not fn.body.body:
        return None
    first = fn.body.body[0]
    if (
        isinstance(first, cst.SimpleStatementLine)
        and len(first.body) == 1
        and isinstance(first.body[0], cst.Expr)
        and isinstance(first.body[0].value, cst.SimpleString)
    ):
        raw = first.body[0].value.value  # includes quotes
        print(f"Raw docstring: {raw}")  # Debug log
        try:
            # Use ast.literal_eval to safely unescape multi-line string literals
            # Ensure all lines are preserved and unescaped
            unescaped_docstring = pyast.literal_eval(raw)
            return unescaped_docstring.strip()
        except Exception as e:
            print(f"Error parsing docstring: {e}")  # Debug log
            # Fallback: return raw string with stripped quotes
            return raw.strip("'\"")
    return None


def _docstring_summary(doc: Optional[str]) -> Optional[str]:
    if not doc:
        return None
    # summary = first non-empty line
    for line in doc.strip().splitlines():
        s = line.strip()
        if s:
            return s
    return None


# -----------------------------------
# Core: build tool specs for functions
# -----------------------------------


@dataclass
class ToolSpec:
    name: str
    description: Optional[str]
    docstring: Optional[str]
    parameters_schema: Dict
    returns: Optional[Dict]
    qualified_name: str
    is_method: bool = False
    class_name: Optional[str] = None


def extract_tools_from_code(source: str) -> List[Dict]:
    """
    Parse Python source with LibCST and extract a list of tool specs (dicts) for
    top-level functions and class methods (non-nested).
    """
    module = cst.parse_module(source)
    collector = _ToolCollector(module)
    module.visit(collector)
    return [asdict(t) for t in collector.tools]


def extract_tools_from_file(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf8") as f:
        source = f.read()
    return extract_tools_from_code(source)


# Optional: format for OpenAI "tools" (function calling) style
def to_openai_tools(tools: List[Dict]) -> List[Dict]:
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


if __name__ == "__main__":
    import sys

    file = sys.argv[1] if len(sys.argv) > 1 else "cst_tools.py"
    tools = extract_tools_from_file(file)
    print(json.dumps(tools, indent=2, ensure_ascii=False))
    # To OpenAI-style:
    # print(json.dumps(to_openai_tools(tools), indent=2, ensure_ascii=False))

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
    Return the function docstring if present (first statement literal string).
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
        try:
            return pyast.literal_eval(raw)  # safe unescape of Python string literal
        except Exception:
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


class ToolExtractor:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def extract_tools_from_code(self, source: str) -> List[Dict]:
        """
        Parse Python source with LibCST and extract a list of tool specs (dicts) for
        top-level functions and class methods (non-nested).
        """
        module = cst.parse_module(source)
        collector = _ToolCollector(module, debug=self.debug)
        module.visit(collector)
        return [asdict(t) for t in collector.tools]

    def extract_tools_from_file(self, path: str) -> List[Dict]:
        with open(path, "r", encoding="utf8") as f:
            source = f.read()
        return self.extract_tools_from_code(source)


class _ToolCollector(cst.CSTVisitor):
    def __init__(self, module: cst.Module, debug: bool = False):
        self.module = module
        self.tools: List[ToolSpec] = []
        self._class_stack: List[str] = []
        self._func_depth: int = 0
        self.debug = debug

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        if self.debug:
            print(f"Visiting function: {node.name.value}")
        # Only collect top-level functions
        if self._func_depth == 0:
            is_method = len(self._class_stack) > 0
            class_name = self._class_stack[-1] if is_method else None
            qname = (
                ".".join(self._class_stack + [node.name.value])
                if is_method
                else node.name.value
            )

            doc = _extract_docstring_from_function(node)
            desc = _docstring_summary(doc)

            params_schema = self._extract_params_schema(node)
            ret_schema = self._extract_return_schema(node)

            spec = ToolSpec(
                name=node.name.value,
                description=desc,
                docstring=doc,
                parameters_schema=params_schema,
                returns=ret_schema,
                qualified_name=qname,
                is_method=is_method,
                class_name=class_name,
            )
            self.tools.append(spec)

        return True

    def _extract_params_schema(self, node: cst.FunctionDef) -> Dict:
        """Extract parameter schema from function definition."""
        params = {}
        for param in node.params.params:
            param_name = param.name.value
            annotation = param.annotation.annotation if param.annotation else None
            param_type = (
                self.module.code_for_node(annotation) if annotation else "string"
            )
            params[param_name] = {"type": param_type}
        return {"properties": params}

    def _extract_return_schema(self, node: cst.FunctionDef) -> Optional[Dict]:
        """Extract return type schema from function definition."""
        if node.returns and node.returns.annotation:
            return_type = self.module.code_for_node(node.returns.annotation)
            return {"type": return_type}
        return None

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        # decrement depth
        self._func_depth -= 1
        if self._func_depth == 0:
            self._in_func = False


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

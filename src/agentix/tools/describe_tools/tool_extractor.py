from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional

import libcst as cst
from .utils import _extract_docstring_from_function, _docstring_summary
from .describe_tools_impl import ToolSpec


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

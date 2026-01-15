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


# --------------------------------------
# Utilities: type annotation -> JSONSchema
# --------------------------------------


def _strip_prefixes(t: str) -> str:
    # Normalize typing prefixes for simple matching
    prefixes = ("typing.", "collections.abc.", "builtins.")
    for p in prefixes:
        if t.startswith(p):
            t = t[len(p) :]
    return t


def _simple_type_map(name: str) -> Dict:
    """
    Map a simple type name to JSON Schema.
    """
    name = _strip_prefixes(name)
    base = name.split("[", 1)[0]  # e.g., List[int] -> List
    base = base.lower()

    if base in ("str",):
        return {"type": "string"}
    if base in ("int",):
        return {"type": "integer"}
    if base in ("float",):
        return {"type": "number"}
    if base in ("bool",):
        return {"type": "boolean"}
    if base in ("dict", "mapping"):
        return {"type": "object"}
    if base in ("list", "tuple", "sequence", "iterable"):
        return {"type": "array"}
    if base in ("none", "nonetype", "null"):
        return {"type": "null"}
    # Fallback
    return {"type": "string"}  # conservative default for unknowns


def _parse_union_parts(code: str) -> List[str]:
    """
    Very lightweight split for Union[A, B] or A | B (PEP 604).
    This is not a full parser; it assumes simple comma-separated types
    at the top level.
    """
    code = code.strip()
    if code.startswith("Union[") and code.endswith("]"):
        inner = code[len("Union[") : -1]
        parts = []
        depth = 0
        buf = []
        for ch in inner:
            if ch == "," and depth == 0:
                parts.append("".join(buf).strip())
                buf = []
            else:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                buf.append(ch)
        if buf:
            parts.append("".join(buf).strip())
        return parts

    # PEP 604: A | B | None
    parts = []
    depth = 0
    buf = []
    for ch in code:
        if ch == "|" and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return parts


def _type_expr_to_schema(type_code: Optional[str]) -> Dict:
    """
    Convert a (stringified) annotation expression into a JSON Schema fragment.
    Handles common typing forms: Optional[T], Union[A,B], List[T], Dict[K,V], etc.
    Falls back to string when unknown.
    """
    if not type_code:
        return {"type": "string"}  # unknown = string (conservative)
    t = _strip_prefixes(type_code.replace(" ", ""))

    # Optional[T] == Union[T, None]
    if t.startswith("Optional[") and t.endswith("]"):
        inner = t[len("Optional[") : -1]
        return {"anyOf": [_type_expr_to_schema(inner), {"type": "null"}]}

    # Union[A,B,...] or A|B
    if t.startswith("Union[") or "|" in t:
        parts = _parse_union_parts(t)
        return {"anyOf": [_type_expr_to_schema(p) for p in parts]}

    # List[T] / Sequence[T] / Iterable[T] / Tuple[T, ...]
    if any(
        t.startswith(prefix) for prefix in ("List[", "Sequence[", "Iterable[", "Tuple[")
    ) and t.endswith("]"):
        inner = t.split("[", 1)[1][:-1]
        # Tuple[A, B] → array of any (simple)
        if t.lower().startswith("tuple["):
            return {
                "type": "array",
                "items": {
                    "anyOf": [_type_expr_to_schema(p.strip()) for p in inner.split(",")]
                },
            }
        return {"type": "array", "items": _type_expr_to_schema(inner)}

    # Dict[K, V] / Mapping[K, V]
    if any(t.startswith(prefix) for prefix in ("Dict[", "Mapping[")) and t.endswith(
        "]"
    ):
        inner = t.split("[", 1)[1][:-1]
        parts = [
            p.strip() for p in _parse_union_parts(inner.replace(",", "|", 1))
        ]  # split once by first comma
        value_schema = (
            _type_expr_to_schema(parts[1]) if len(parts) > 1 else {"type": "string"}
        )
        return {"type": "object", "additionalProperties": value_schema}

    # Plain builtins or names
    return _simple_type_map(t)


def _expr_code(module: cst.Module, expr: Optional[cst.CSTNode]) -> Optional[str]:
    if expr is None:
        return None
    try:
        return module.code_for_node(expr)
    except Exception:
        return None


def _default_value(
    module: cst.Module, default_expr: Optional[cst.BaseExpression]
) -> Optional[object]:
    """
    Turn a default value expression into a JSON-serializable Python object when possible.
    Falls back to source string if literal evaluation fails.
    """
    if default_expr is None:
        return None
    code = _expr_code(module, default_expr)
    if code is None:
        return None
    try:
        return pyast.literal_eval(code)
    except Exception:
        return code  # non-literal default


# -----------------------------------
# Core: build tool specs for functions
# -----------------------------------


@dataclass
class ToolParam:
    name: str
    schema: Dict
    default: Optional[object] = None
    kind: str = "positional_or_keyword"  # posonly, vararg, kwonly, kwarg
    required: bool = True
    description: Optional[str] = None  # could be extended via docstring parsing


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


def _params_to_schema(module: cst.Module, fn: cst.FunctionDef, is_method: bool) -> Dict:
    """
    Convert LibCST Parameters to JSON Schema.
    We mark a param as required iff it has no default and is not Optional[...] in annotation.
    """
    params: List[ToolParam] = []

    def handle_param(p: cst.Param, kind: str):
        name = p.name.value
        # Skip implicit receiver
        if is_method and name in ("self", "cls"):
            return

        annotation_code = (
            _expr_code(module, p.annotation.annotation) if p.annotation else None
        )
        schema = _type_expr_to_schema(annotation_code)
        default = _default_value(module, p.default)
        # Optional types make required False
        is_optional = (
            isinstance(schema, dict)
            and "anyOf" in schema
            and any(s.get("type") == "null" for s in schema["anyOf"])
        )
        required = (default is None) and (not is_optional)
        params.append(
            ToolParam(
                name=name, schema=schema, default=default, kind=kind, required=required
            )
        )

    P = fn.params
    # pos-only
    for p in P.posonly_params:
        handle_param(p, "posonly")
    # normal params
    for p in P.params:
        handle_param(p, "positional_or_keyword")
    # *args
    if P.star_arg:
        p = P.star_arg
        # star_arg is a Param
        annotation_code = (
            _expr_code(module, p.annotation.annotation) if p.annotation else None
        )
        items_schema = (
            _type_expr_to_schema(annotation_code)
            if annotation_code
            else {
                "anyOf": [
                    {"type": t}
                    for t in ("string", "number", "boolean", "object", "array", "null")
                ]
            }
        )
        params.append(
            ToolParam(
                name="*" + p.name.value,
                schema={"type": "array", "items": items_schema},
                default=None,
                kind="vararg",
                required=False,
            )
        )
    # kw-only
    for p in P.kwonly_params:
        handle_param(p, "kwonly")
    # **kwargs
    if P.kwarg:
        p = P.kwarg
        annotation_code = (
            _expr_code(module, p.annotation.annotation) if p.annotation else None
        )
        value_schema = (
            _type_expr_to_schema(annotation_code)
            if annotation_code
            else {
                "anyOf": [
                    {"type": t}
                    for t in ("string", "number", "boolean", "object", "array", "null")
                ]
            }
        )
        params.append(
            ToolParam(
                name="**" + p.name.value,
                schema={"type": "object", "additionalProperties": value_schema},
                default=None,
                kind="kwarg",
                required=False,
            )
        )

    # Build JSON Schema object
    properties: Dict[str, Dict] = {}
    required: List[str] = []
    for p in params:
        # Don't expose *args/**kwargs names as ordinary properties; keep but mark special
        if p.kind in ("vararg", "kwarg"):
            # Represent as reserved “extras” fields for cleanliness
            properties[p.name] = p.schema
        else:
            properties[p.name] = p.schema
            if p.default is not None:
                properties[p.name]["default"] = p.default
            if p.required:
                required.append(p.name)

    schema: Dict = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def _returns_schema(module: cst.Module, fn: cst.FunctionDef) -> Optional[Dict]:
    if fn.returns and isinstance(fn.returns, cst.Annotation):
        code = _expr_code(module, fn.returns.annotation)
        return _type_expr_to_schema(code)
    return None


class _ToolCollector(cst.CSTVisitor):
    def __init__(self, module: cst.Module):
        self.module = module
        self.tools: List[ToolSpec] = []
        self._class_stack: List[str] = []
        self._func_depth: int = 0

    # Track nesting to avoid nested functions
    # def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
    #    self._func_depth += 1

    # def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
    #    self._func_depth -= 1

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self._class_stack.append(node.name.value)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self._class_stack.pop()

    def on_visit(self, node: cst.CSTNode) -> bool:
        # Continue traversal
        return True

    def on_leave(self, original_node: cst.CSTNode) -> None:
        # When leaving a FunctionDef, collect if top-level or inside a class (but not nested in functions)
        if isinstance(original_node, cst.FunctionDef) and self._func_depth == 0:
            pass  # shouldn't happen due to leave timing
        # Nothing here

    def leave_IndentedBlock(self, node: cst.IndentedBlock) -> None:
        # Not used
        pass

    def visit_SimpleStatementLine(
        self, node: cst.SimpleStatementLine
    ) -> Optional[bool]:
        return True

    def visit_FunctionDef_body(self, node: cst.FunctionDef) -> None:
        # Not used
        pass

    def leave_Module(self, original_node: cst.Module) -> None:
        # Not used
        pass

    # The core collection hook: capture on every FunctionDef at the moment we *see* it.
    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        # increment depth
        if getattr(self, "_in_func", False):
            self._func_depth += 1
        else:
            self._in_func = True
            self._func_depth = 1

        # Only collect functions that are not nested inside other functions
        if self._func_depth == 1:
            is_method = len(self._class_stack) > 0
            class_name = self._class_stack[-1] if is_method else None
            qname = (
                ".".join(self._class_stack + [node.name.value])
                if is_method
                else node.name.value
            )

            doc = _extract_docstring_from_function(node)
            desc = _docstring_summary(doc)
            params_schema = _params_to_schema(self.module, node, is_method=is_method)
            ret_schema = _returns_schema(self.module, node)

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

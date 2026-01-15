from typing import Optional
import ast as pyast
import libcst as cst

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
        except Exception:
            # Fallback: return raw string with stripped quotes
            return raw.strip("'")
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
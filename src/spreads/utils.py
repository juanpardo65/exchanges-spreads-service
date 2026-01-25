"""Helpers for formatting and conversion."""


def to_decimal_str(s: str) -> str:
    """
    Convert string (possibly in scientific notation, e.g. "2.645e-05") to normal decimal string ("0.00002645").
    """
    if not s or not isinstance(s, str):
        return "0"
    s = s.strip()
    if not s:
        return "0"
    try:
        x = float(s)
        if x == 0:
            return "0"
        out = f"{x:.12f}".rstrip("0").rstrip(".")
        return out if out else "0"
    except (ValueError, TypeError):
        return s

def to_decimal_str(s: str) -> str:
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
        return "0"

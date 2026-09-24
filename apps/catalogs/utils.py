import re


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize_code(value: str) -> str:
    return normalize_whitespace(value).upper()


def normalize_name(value: str) -> str:
    return normalize_whitespace(value)

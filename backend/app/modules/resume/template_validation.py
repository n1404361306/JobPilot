import re

UNSAFE_TAG_PATTERNS = (
    re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE),
    re.compile(r"<iframe[\s\S]*?</iframe>", re.IGNORECASE),
    re.compile(r"<object[\s\S]*?</object>", re.IGNORECASE),
    re.compile(r"<embed[\s\S]*?>", re.IGNORECASE),
)

UNSAFE_ATTR_PATTERNS = (
    re.compile(r"\son\w+\s*=\s*('[^']*'|\"[^\"]*\"|[^\s>]+)", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
)

MAX_TEMPLATE_BYTES = 256 * 1024


def sanitize_template_content(content: str) -> str:
    """Remove unsafe tags/attributes while keeping layout HTML."""
    cleaned = content
    for pattern in UNSAFE_TAG_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    for pattern in UNSAFE_ATTR_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return cleaned.strip()


def validate_template_content(content: str) -> str:
    cleaned = sanitize_template_content(content)
    if len(cleaned.encode("utf-8")) > MAX_TEMPLATE_BYTES:
        raise ValueError("template file too large")
    if not cleaned:
        raise ValueError("template content is empty")
    return cleaned

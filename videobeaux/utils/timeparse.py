"""Forgiving time parsing for text arguments: seconds (12, 12.5, .12, 12.) or [HH:]MM:SS[.ms]."""
from __future__ import annotations

import re

_NUM = r"(?:\d+\.?\d*|\.\d+)"
_CLOCK = re.compile(rf"^(?:(\d+):)?(\d{{1,2}}):({_NUM})$")
_PLAIN = re.compile(rf"^({_NUM})$")


def parse_time(text, name: str = "time") -> float:
    """Seconds as float. Accepts '.12', '0.12', '12.', '90', '1:02.5', '0:01:02.5'. Raises ValueError on junk."""
    if isinstance(text, (int, float)):
        return float(text)
    s = str(text).strip().replace(",", ".")
    m = _PLAIN.match(s)
    if m:
        return float(m.group(1))
    m = _CLOCK.match(s)
    if m:
        h = int(m.group(1)) if m.group(1) else 0
        return h * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    raise ValueError(f"Could not read {name} {text!r}. Use seconds (12.5, .5) or HH:MM:SS(.ms) (01:02:03.5).")

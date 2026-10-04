"""Where user-written photobooth filters live (shared by booth_filters and booth_labels)."""
import os
from pathlib import Path


def user_filter_dir() -> Path:
    return Path(os.environ.get("VIDEOBEAUX_USER_FILTERS") or (Path.home() / ".videobeaux" / "filters"))

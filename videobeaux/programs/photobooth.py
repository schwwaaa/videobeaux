"""
photobooth (Filter Library) — every photo-booth filter in one list, plus your own.

Each filter also exists as its own program with its own controls (Negative, Pixelate, VHS Camcorder, ...);
this one is the catch-all, and the home of filters you drop into ~/.videobeaux/filters/ (see
videobeaux/utils/booth_filters.py for the format) — restart the app after adding one.
"""
from videobeaux.utils.booth_labels import DEFAULT_LABEL, all_labels
from videobeaux.utils.booth_runner import run_effect

LABELS = all_labels()

GUI_METADATA = {
    'args': {
        'filter': {'type': 'select', 'label': 'Filter', 'default': DEFAULT_LABEL, 'choices': LABELS,
                   'help': 'Grouped by pack (Classic, Retro TV, Print & pixel, Art, Colour, Warp, Face, Time…).'},
        'amount': {'label': 'Amount', 'min': 0, 'max': 1,
                   'help': '1 = full filter, lower values blend the original back in.'},
        'detail': {'label': 'Detail (px)', 'min': 0, 'max': 2160,
                   'help': 'The filter is applied at this size on the short side, then scaled back up — keeps the look '
                           'consistent on any resolution and is faster. 0 = full resolution.'},
        'seed': {'hidden': True}, 'crf': {'hidden': True},
    }
}


def register_arguments(parser):
    parser.description = (
        "Photo-booth filters for video: Negative, Game Boy, CGA / C64 / PICO-8, VHS, CRT, thermal, "
        "halftone, LED wall, comic, oil paint, watercolour, neon, kaleidoscope, fisheye, swirl, tunnel, "
        "face warps (big head / big eyes / face swap), slit-scan, ghost trails and more. Pick one with "
        "--filter. Drop your own into ~/.videobeaux/filters/ to extend the list."
    )
    parser.add_argument("--filter", type=str, default=DEFAULT_LABEL,
                        help='Which filter, e.g. "Print & pixel · Game Boy" (the part after · also works: "game boy").')
    parser.add_argument("--amount", type=float, default=1.0, help="Filter strength 0-1. Default: 1.")
    parser.add_argument("--detail", type=int, default=720,
                        help="Short-side pixels the filter works at (0 = full size). Default: 720.")
    parser.add_argument("--seed", type=int, default=0, help="Seed for the random parts (0 = different every run).")
    parser.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def resolve_filter(name: str, filters: dict):
    """Exact label, else a case-insensitive match on the full label or just its name part."""
    if name in filters:
        return name
    key = (name or "").strip().lower()
    for label in filters:
        if label.lower() == key or label.split(" · ", 1)[-1].lower() == key:
            return label
    raise SystemExit(f"❌ Unknown filter {name!r}. Try one of:\n  " + "\n  ".join(filters))


def run(args):
    from videobeaux.utils.booth_filters import build_filters
    filters = build_filters()
    label = resolve_filter(args.filter, filters)
    effect = filters[label]
    run_effect(args, lambda a: effect, faces=effect.needs_faces, eyes=effect.needs_eyes, label=label)

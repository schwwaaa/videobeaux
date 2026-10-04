"""
luma_key — key out the darkest or brightest parts of the picture (black backgrounds, white skies, ...).

Pure ffmpeg (lumakey), fully offline. For fire / smoke / light-leak footage on black, Composite =
screen or add usually looks better than a hard key because it keeps the soft glow.
"""
from videobeaux.utils import keying

KEYS = ["dark", "bright", "custom"]
COMPOSITES = ["key (cut out)", "screen", "add", "lighten"]
_BLEND = {"screen": "screen", "add": "addition", "lighten": "lighten"}

GUI_METADATA = {
    'args': {
        **keying.GUI_COMMON,
        'key': {'type': 'select', 'label': 'Remove', 'default': 'dark', 'choices': KEYS,
                'help': 'dark = knock out blacks · bright = knock out whites/sky · custom = knock out around Threshold.'},
        'threshold': {'label': 'Threshold (custom)', 'min': 0, 'max': 1, 'help': 'Brightness to remove for Remove = custom (0 black … 1 white).'},
        'tolerance': {'label': 'Tolerance', 'min': 0, 'max': 1, 'help': 'How wide a brightness range gets removed.'},
        'softness': {'label': 'Edge softness', 'min': 0, 'max': 1, 'help': 'Gradual fade at the edge of the range.'},
        'invert': {'label': 'Invert matte', 'help': 'Keep what would be removed, remove what would be kept.'},
        'composite': {'type': 'select', 'label': 'Composite', 'default': COMPOSITES[0], 'choices': COMPOSITES,
                      'help': 'key = cut out with transparency. screen / add / lighten = blend onto the background '
                              '(best for fire, smoke, light on black).'},
    }
}


def register_arguments(p):
    p.description = (
        "Luma key: make the darkest (or brightest) parts transparent and put something behind the rest. "
        "Choose Composite = screen / add for fire, smoke and light-leak overlays on black."
    )
    p.add_argument("--key", choices=KEYS, default="dark", help="Which brightness to remove. Default: dark.")
    p.add_argument("--threshold", type=float, default=0.5, help="Brightness to remove with --key custom (0-1). Default: 0.5.")
    p.add_argument("--tolerance", type=float, default=0.12, help="Brightness range removed (0-1). Default: 0.12.")
    p.add_argument("--softness", type=float, default=0.08, help="Edge softness (0-1). Default: 0.08.")
    p.add_argument("--invert", action="store_true", help="Invert the matte.")
    p.add_argument("--composite", choices=COMPOSITES, default=COMPOSITES[0],
                   help="key = cut out; screen / add / lighten = blend onto the background.")
    keying.add_common_arguments(p)


def run(args):
    if args.composite != COMPOSITES[0]:
        if args.view != "composite":
            raise SystemExit("❌ View matte/checkerboard only applies when Composite = key.")
        keying.run_key(args, "", blend_mode=_BLEND[args.composite])
        return
    thr = {"dark": 0.0, "bright": 1.0}.get(args.key, min(1.0, max(0.0, args.threshold)))
    key = (f"format=yuv420p,lumakey=threshold={thr:.3f}:tolerance={min(1.0, max(0.0, args.tolerance)):.3f}"
           f":softness={min(1.0, max(0.0, args.softness)):.3f}")
    keying.run_key(args, key, invert=args.invert)

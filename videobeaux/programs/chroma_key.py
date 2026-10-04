"""
chroma_key — remove a green/blue screen (or any solid color) and put something behind the subject.

Pure ffmpeg (chromakey / colorkey + despill), so it's fast and fully offline. Tune with View = matte
(white = kept, black = removed). Save as .webm or .mov for a transparent background.
"""
from videobeaux.utils import keying
from videobeaux.utils.keying import auto_key_color, ff_color, spill_type_for

METHODS = ["chromakey (YUV, best for most)", "colorkey (RGB)"]

GUI_METADATA = {
    'args': {
        **keying.GUI_COMMON,
        'key_color': {'type': 'color', 'label': 'Key color', 'default': '#00B140',
                      'help': 'The screen color to remove. Typical green screen ≈ #00B140, blue ≈ #0047BB.'},
        'auto_key': {'label': 'Auto-detect key color',
                     'help': 'Sample the edges of the first frame to find the screen color (ignores the color picker).'},
        'method': {'type': 'select', 'label': 'Method', 'default': METHODS[0], 'choices': METHODS},
        'similarity': {'label': 'Similarity', 'min': 0.01, 'max': 1,
                       'help': 'How far from the key color still counts as screen. Raise until the background is gone.'},
        'blend': {'label': 'Edge softness', 'min': 0, 'max': 1, 'help': 'Gradual transparency at the edge of the key.'},
        'spill': {'label': 'Spill removal', 'min': 0, 'max': 1,
                  'help': 'Removes the green/blue tint reflected onto the subject. 0 = off.'},
    }
}


def register_arguments(p):
    p.description = (
        "Chroma key: remove a green/blue (or any solid color) screen and replace it with a color, image or "
        "another video — or export with transparency (.webm / .mov). Use --view matte to tune, --auto_key to "
        "detect the screen color, --spill to clean color spill off the subject."
    )
    p.add_argument("--key_color", type=str, default="#00B140", help="Screen color to remove. Default: #00B140.")
    p.add_argument("--auto_key", action="store_true", help="Detect the key color from the frame edges.")
    p.add_argument("--method", choices=METHODS, default=METHODS[0], help="Keying method.")
    p.add_argument("--similarity", type=float, default=0.15, help="Key tolerance 0.01-1. Default: 0.15.")
    p.add_argument("--blend", type=float, default=0.05, help="Edge softness 0-1. Default: 0.05.")
    p.add_argument("--spill", type=float, default=0.3, help="Spill removal 0-1. Default: 0.3.")
    keying.add_common_arguments(p)


def run(args):
    key_hex = args.key_color
    if args.auto_key:
        key_hex = auto_key_color(args.input)
        print(f"ℹ️  Detected key color {key_hex}", flush=True)
    color = ff_color(key_hex, (0, 177, 64))
    sim = min(1.0, max(0.01, args.similarity))
    blend = min(1.0, max(0.0, args.blend))
    if args.method.startswith("colorkey"):
        key = f"format=rgba,colorkey=color={color}:similarity={sim:.3f}:blend={blend:.3f}"
    else:
        key = f"format=yuv420p,chromakey=color={color}:similarity={sim:.3f}:blend={blend:.3f}"
    keying.run_key(args, key, spill=spill_type_for(key_hex), spill_mix=args.spill)

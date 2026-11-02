"""
key_composite: the second half of Remove Background, as its own program. It puts the subject of the source over a new
background, using a matte video you connect: a Remove Background node set to View = matte, or any grayscale video
(white = keep, black = remove). Change the background or the edge clean-up without running the matte again.
"""
from pathlib import Path

from videobeaux.utils import keying

GUI_METADATA = {
    'args': {
        **keying.GUI_COMMON,
        'matte': {'type': 'file', 'subtype': 'video', 'label': 'Matte video',
                  'help': 'Connect a Remove Background node set to View = matte (or any grayscale video): white = keep, black = remove.'},
    }
}


def register_arguments(p):
    p.description = (
        "Key Composite: put the subject over a new background, using a matte video (white = keep, black = remove). "
        "Connect a Remove Background node set to View = matte to its Matte input."
    )
    p.add_argument("--matte", required=True, type=str,
                   help="Grayscale matte video: white = keep, black = remove. Connect a Remove Background node set to View = matte.")
    keying.add_common_arguments(p)
    p.set_defaults(shrink=0, feather=0)          # the matte has already been cleaned up upstream


def run(args):
    if not Path(args.matte).exists():
        raise SystemExit(f"❌ Matte video not found: {args.matte}")
    keying.run_key(args, "", matte_path=str(args.matte))

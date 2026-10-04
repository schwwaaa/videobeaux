"""
key_feedback — video feedback with two keys, like patching a keyer into a feedback loop on a video synth:

  • the INSERT key decides which parts of the live picture enter the loop (a luma band, a color, or both);
  • the FEEDBACK key decides which parts of the recirculating picture survive each pass.

Each pass the loop is also zoomed / rotated / shifted / hue-shifted, so what gets keyed in leaves spiraling,
color-cycling trails. Use View = insert key / feedback key to see (and tune) each matte. OpenCV, fully offline.
"""
import numpy as np

from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.feedback_core import KEY_MODES, build_key, combine, transform_feedback
from videobeaux.utils.frame_pipe import process_video

MIXES = ["over", "screen", "lighten", "add"]
VIEWS = ["output", "insert key", "feedback key"]

GUI_METADATA = {
    'args': {
        'insert_key': {'type': 'select', 'label': 'Insert key', 'default': 'luma', 'choices': KEY_MODES,
                       'help': 'Which part of the live picture is let into the loop.'},
        'insert_low': {'label': 'Insert: luma from', 'min': 0, 'max': 1, 'good_min': 0.3, 'good_max': 0.6,
                       'help': 'Brightness band that enters the loop (0 = black, 1 = white).'},
        'insert_high': {'label': 'Insert: luma to', 'min': 0, 'max': 1, 'good_min': 0.8, 'good_max': 1},
        'insert_soft': {'label': 'Insert: edge softness', 'min': 0, 'max': 0.5, 'good_min': 0.02, 'good_max': 0.2},
        'insert_color': {'type': 'color', 'label': 'Insert: color', 'default': '#00FF00'},
        'insert_similarity': {'label': 'Insert: color range', 'min': 0.02, 'max': 1, 'good_min': 0.15, 'good_max': 0.5,
                              'help': 'How far from the picked color still counts (hue/chroma only, brightness ignored).'},
        'insert_invert': {'label': 'Insert: invert', 'help': 'Let in everything except the key.'},
        'fb_key': {'type': 'select', 'label': 'Feedback key', 'default': 'none', 'choices': KEY_MODES,
                   'help': 'Which part of the recirculating picture survives each pass.'},
        'fb_low': {'label': 'Feedback: luma from', 'min': 0, 'max': 1, 'good_min': 0.1, 'good_max': 0.4},
        'fb_high': {'label': 'Feedback: luma to', 'min': 0, 'max': 1, 'good_min': 0.7, 'good_max': 1},
        'fb_soft': {'label': 'Feedback: edge softness', 'min': 0, 'max': 0.5, 'good_min': 0.02, 'good_max': 0.2},
        'fb_color': {'type': 'color', 'label': 'Feedback: color', 'default': '#FF00FF'},
        'fb_similarity': {'label': 'Feedback: color range', 'min': 0.02, 'max': 1, 'good_min': 0.15, 'good_max': 0.5},
        'fb_invert': {'label': 'Feedback: invert', 'help': 'Keep everything except the key.'},
        'decay': {'label': 'Feedback amount', 'min': 0, 'max': 0.99, 'good_min': 0.6, 'good_max': 0.95,
                  'help': 'How much of the previous output returns each pass. Near 1 = long trails.'},
        'zoom': {'label': 'Zoom (% per frame)', 'min': -20, 'max': 20, 'good_min': -3, 'good_max': 4},
        'rotate': {'label': 'Rotate (° per frame)', 'min': -30, 'max': 30, 'good_min': -3, 'good_max': 3},
        'shift_x': {'label': 'Shift X (px)', 'min': -100, 'max': 100},
        'shift_y': {'label': 'Shift Y (px)', 'min': -100, 'max': 100},
        'hue_shift': {'label': 'Hue shift (° per frame)', 'min': -45, 'max': 45, 'good_min': -8, 'good_max': 8},
        'mix_mode': {'type': 'select', 'label': 'Combine', 'default': 'over', 'choices': MIXES,
                     'help': 'over = keyed pixels replace the feedback; the others blend them in.'},
        'view': {'type': 'select', 'label': 'View', 'default': 'output', 'choices': VIEWS,
                 'help': 'Show a matte instead of the result to tune the keys (white = in).'},
        'crf': {'hidden': True},
    },
    'presets': {
        'Bright trails': {'insert_key': 'luma', 'insert_low': 0.55, 'insert_high': 1.0, 'fb_key': 'none', 'decay': 0.9,
                          'zoom': 1.5, 'rotate': 1.0, 'hue_shift': 4, 'mix_mode': 'over'},
        'Color echo': {'insert_key': 'color', 'insert_similarity': 0.3, 'fb_key': 'luma', 'fb_low': 0.15, 'fb_high': 1.0,
                       'decay': 0.93, 'zoom': 2.5, 'rotate': 0, 'hue_shift': 10, 'mix_mode': 'screen'},
        'Dark tunnel': {'insert_key': 'luma', 'insert_low': 0.0, 'insert_high': 0.3, 'insert_invert': False, 'fb_key': 'none',
                        'decay': 0.88, 'zoom': -2.5, 'rotate': -2, 'hue_shift': 0, 'mix_mode': 'over'},
    },
}


def register_arguments(p):
    p.description = (
        "Video feedback with two keys: the Insert key picks which parts of the live picture enter the loop "
        "(luma band and/or a color), the Feedback key picks which parts of the recirculating picture survive each "
        "pass. Each pass is also zoomed, rotated, shifted and hue-shifted. Use --view to see either matte."
    )
    p.add_argument("--insert_key", choices=KEY_MODES, default="luma", help="Insert key type. Default: luma.")
    p.add_argument("--insert_low", type=float, default=0.5, help="Insert luma band start, 0 to 1. Default: 0.5.")
    p.add_argument("--insert_high", type=float, default=1.0, help="Insert luma band end, 0 to 1. Default: 1.")
    p.add_argument("--insert_soft", type=float, default=0.1, help="Insert edge softness. Default: 0.1.")
    p.add_argument("--insert_color", type=str, default="#00FF00", help="Insert key color. Default: #00FF00.")
    p.add_argument("--insert_similarity", type=float, default=0.3, help="Insert color range. Default: 0.3.")
    p.add_argument("--insert_invert", action="store_true", help="Invert the insert key.")
    p.add_argument("--fb_key", choices=KEY_MODES, default="none", help="Feedback key type. Default: none.")
    p.add_argument("--fb_low", type=float, default=0.15, help="Feedback luma band start. Default: 0.15.")
    p.add_argument("--fb_high", type=float, default=1.0, help="Feedback luma band end. Default: 1.")
    p.add_argument("--fb_soft", type=float, default=0.1, help="Feedback edge softness. Default: 0.1.")
    p.add_argument("--fb_color", type=str, default="#FF00FF", help="Feedback key color. Default: #FF00FF.")
    p.add_argument("--fb_similarity", type=float, default=0.3, help="Feedback color range. Default: 0.3.")
    p.add_argument("--fb_invert", action="store_true", help="Invert the feedback key.")
    p.add_argument("--decay", type=float, default=0.9, help="Feedback amount, 0 to 0.99. Default: 0.9.")
    p.add_argument("--zoom", type=float, default=1.5, help="Zoom per frame in percent. Default: 1.5.")
    p.add_argument("--rotate", type=float, default=1.0, help="Rotation per frame in degrees. Default: 1.")
    p.add_argument("--shift_x", type=float, default=0.0, help="Horizontal shift per frame, pixels. Default: 0.")
    p.add_argument("--shift_y", type=float, default=0.0, help="Vertical shift per frame, pixels. Default: 0.")
    p.add_argument("--hue_shift", type=float, default=4.0, help="Hue shift per frame in degrees. Default: 4.")
    p.add_argument("--mix_mode", choices=MIXES, default="over", help="How keyed pixels join the feedback.")
    p.add_argument("--view", choices=VIEWS, default="output", help="What to show: the result or a key matte.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def key_for(cv2, frame, mode, low, high, soft, color_hex, similarity, invert):
    return build_key(cv2, frame, mode, low=min(low, high), high=max(low, high), soft=soft,
                     color_rgb=hex_to_rgb(color_hex, (0, 255, 0)), similarity=similarity, color_soft=max(0.05, soft), invert=invert)


def run(args):
    cv2 = require_cv2()
    decay = max(0.0, min(0.99, args.decay))
    st = {"fb": None}

    def frame_fn(frame, i, t):
        if st["fb"] is None:
            st["fb"] = np.zeros_like(frame)
        fb = transform_feedback(cv2, st["fb"], args.zoom, args.rotate, args.shift_x, args.shift_y, args.hue_shift)
        fb_key = key_for(cv2, fb, args.fb_key, args.fb_low, args.fb_high, args.fb_soft, args.fb_color, args.fb_similarity, args.fb_invert)
        ins_key = key_for(cv2, frame, args.insert_key, args.insert_low, args.insert_high, args.insert_soft,
                          args.insert_color, args.insert_similarity, args.insert_invert)
        kept = (fb.astype(np.float32) * (fb_key[..., None] * decay)).astype(np.uint8)       # what survives the pass
        out = np.clip(combine(frame, kept, ins_key, args.mix_mode), 0, 255).astype(np.uint8)
        st["fb"] = out
        if args.view == "insert key":
            g = (ins_key * 255).astype(np.uint8)
            return np.dstack([g, g, g])
        if args.view == "feedback key":
            g = (fb_key * 255).astype(np.uint8)
            return np.dstack([g, g, g])
        return out

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(getattr(args, "force", False)))
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")

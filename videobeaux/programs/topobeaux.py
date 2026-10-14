"""
topobeaux — slice the picture into tonal bands, like a topographic map of brightness (an homage to the LZX
Topogram sequential soft-key generator).

A signal (luma, a color channel, saturation, hue or motion) is cut at up to five thresholds into up to six
non-overlapping bands; the band weights always sum to 1, and a shared edge softness blends hard edges into
gradients. Show the bands as flat false color, as a tint over the picture, as contour lines, as different input
videos per band, or cut a band (or a group of bands) out as a matte with a real alpha channel.

Press ✎ next to "Cut points" to drag the dividers on a gradient strip.
"""
import numpy as np

from videobeaux.utils import keying
from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.feedback_core import luma01
from videobeaux.utils.frame_pipe import process_video
from videobeaux.utils.matte_pipeline import run_matte_program

SIGNALS = ["luma", "red", "green", "blue", "saturation", "hue", "motion"]
STYLES = ["false color", "tint original", "contour lines", "bands from inputs", "band matte (cutout)"]
S_FALSE, S_TINT, S_LINES, S_INPUTS, S_MATTE = STYLES


def _only(style, **meta):
    """Show an option only for the output style(s) that use it (the node hides the rest)."""
    return {**meta, 'show_if': {'style': style}}
DEFAULT_COLORS = ["#0b1d51", "#1f6fa8", "#3fb68b", "#d6d84a", "#f08a3c", "#c8372d"]

GUI_METADATA = {
    'args': {
        'input2': _only(S_INPUTS, type='file', subtype='video', label='Band picture B',
                        help="Only used by 'bands from inputs'. Shows through the bands you assign to B in 'Pictures per band'."),
        'input3': _only(S_INPUTS, type='file', subtype='video', label='Band picture C',
                        help="Only used by 'bands from inputs'. Shows through the bands you assign to C."),
        'style': {'type': 'select', 'label': 'Output style', 'default': STYLES[0], 'choices': STYLES,
                  'help': "What the bands are drawn as. false color / tint original / contour lines use only the main picture (A) · "
                          "bands from inputs puts a different video in each band (needs B and/or C) · "
                          "band matte (cutout) keeps chosen bands and makes the rest transparent."},
        'signal': {'type': 'select', 'label': 'Slice by', 'default': 'luma', 'choices': SIGNALS,
                   'help': 'What is cut into bands. luma = brightness · motion = how much each pixel changed since the previous frame.'},
        'bands': {'label': 'Bands', 'min': 2, 'max': 6, 'good_min': 3, 'good_max': 6},
        'cuts': {'type': 'text', 'label': 'Cut points', 'default': '0.2,0.4,0.6,0.8',
                 'help': 'Comma-separated thresholds between bands, 0 to 1, low to high (bands − 1 of them). '
                         'Press ✎ to drag them on a gradient strip.'},
        'sources': _only(S_INPUTS, type='text', label='Pictures per band', default='A,B,C,A,B,C',
                         help="Which picture shows in each band, darkest signal first: A = the main input, B / C = Band picture B / C. "
                              "e.g. A,B,A for three bands. Letters for pictures that aren't connected fall back to A."),
        'colors': _only([S_FALSE, S_TINT], type='text', label='Band colors', default=','.join(DEFAULT_COLORS),
                        help='Comma-separated hex colors, one per band, darkest signal first.'),
        'softness': {'label': 'Edge softness', 'min': 0, 'max': 0.5, 'step': 0.01, 'good_min': 0, 'good_max': 0.1,
                     'help': '0 = hard steps between bands; higher = gradients.'},
        'smooth': {'label': 'Smooth signal (px)', 'min': 0, 'max': 30, 'good_min': 0, 'good_max': 8,
                   'help': 'Blur the signal first so contours are clean instead of noisy.'},
        'invert': {'label': 'Invert signal'},
        'amount': _only(S_TINT, label='Tint amount', min=0, max=1, step=0.05, help='How much band color replaces the picture.'),
        'line_width': _only(S_LINES, label='Line width (px)', min=1, max=12, good_min=1, good_max=4),
        'line_color': _only(S_LINES, type='color', label='Line color', default='#FFFFFF'),
        'dim': _only(S_LINES, label='Dim picture under lines', min=0, max=1, step=0.05),
        'matte_bands': _only(S_MATTE, type='text', label='Cutout bands', default='1',
                             help="Which bands to keep: numbers from 1 (darkest), e.g. 2,3."),
        'scan_speed': {'label': 'Scan speed (Hz)', 'min': 0, 'max': 4, 'step': 0.05,
                       'help': 'Sweeps all cut points up and down together (0 = still).'},
        'scan_depth': {'label': 'Scan depth', 'min': 0, 'max': 0.5, 'step': 0.01, 'good_min': 0.05, 'good_max': 0.25},
        # background / view / edge options only mean something for the cutout style
        **{k: {**v, 'show_if': {'style': S_MATTE}} for k, v in keying.GUI_COMMON.items()},
        'crf': {'hidden': True},
    },
    'presets': {
        'Topographic': {'signal': 'luma', 'bands': 6, 'cuts': '0.17,0.34,0.5,0.67,0.84', 'softness': 0.0, 'smooth': 3,
                        'style': 'false color', 'colors': ','.join(DEFAULT_COLORS)},
        'Heat map': {'signal': 'luma', 'bands': 5, 'cuts': '0.2,0.4,0.6,0.8', 'softness': 0.15, 'smooth': 2,
                     'style': 'false color', 'colors': '#050010,#6b0f7a,#d6292a,#ffb000,#fffbd0'},
        'Edges only': {'signal': 'luma', 'bands': 5, 'cuts': '0.2,0.4,0.6,0.8', 'smooth': 4, 'style': 'contour lines',
                       'line_width': 2, 'dim': 0.5},
        'Posterized tint': {'signal': 'luma', 'bands': 4, 'cuts': '0.25,0.5,0.75', 'softness': 0.04, 'style': 'tint original',
                            'amount': 0.7, 'colors': '#1b1f4b,#a23b72,#f18f01,#fcefb4'},
        'Motion bands': {'signal': 'motion', 'bands': 4, 'cuts': '0.05,0.15,0.4', 'softness': 0.05, 'smooth': 2,
                         'style': 'false color', 'colors': '#000000,#2b2d8c,#ff3d7f,#fff1a8'},
        'Three clips by brightness': {'signal': 'luma', 'bands': 3, 'cuts': '0.33,0.66', 'softness': 0.08, 'smooth': 3,
                                      'style': 'bands from inputs', 'sources': 'A,B,C'},
    },
}


def register_arguments(p):
    p.description = (
        "Topobeaux — slice the picture into up to 6 tonal bands (by luma, color channel, saturation, hue or "
        "motion) and show them as false color, a tint, contour lines, different videos per band, or a matte "
        "cutout. Homage to the LZX Topogram."
    )
    p.add_argument("--input2", type=str, default=None, help="Input B (optional).")
    p.add_argument("--input3", type=str, default=None, help="Input C (optional).")
    p.add_argument("--style", choices=STYLES, default=STYLES[0], help="What to render. Default: false color.")
    p.add_argument("--sources", type=str, default="A,B,C,A,B,C",
                   help="Picture per band for 'bands from inputs', darkest first, e.g. A,B,A (A = main input, B/C = --input2/--input3).")
    p.add_argument("--signal", choices=SIGNALS, default="luma", help="Signal to slice. Default: luma.")
    p.add_argument("--bands", type=int, default=5, help="Number of bands, 2 to 6. Default: 5.")
    p.add_argument("--cuts", type=str, default="0.2,0.4,0.6,0.8", help="Comma-separated cut points, 0 to 1.")
    p.add_argument("--colors", type=str, default=",".join(DEFAULT_COLORS), help="Comma-separated band colors.")
    p.add_argument("--softness", type=float, default=0.0, help="Edge softness, 0 to 0.5. Default: 0.")
    p.add_argument("--smooth", type=float, default=2.0, help="Blur the signal by this many pixels first. Default: 2.")
    p.add_argument("--invert", action="store_true", help="Invert the signal.")
    p.add_argument("--amount", type=float, default=0.8, help="Tint strength for 'tint original'. Default: 0.8.")
    p.add_argument("--line_width", type=int, default=2, help="Contour line width in pixels. Default: 2.")
    p.add_argument("--line_color", type=str, default="#FFFFFF", help="Contour line color. Default: #FFFFFF.")
    p.add_argument("--dim", type=float, default=0.4, help="Darken the picture under contour lines. Default: 0.4.")
    p.add_argument("--matte_bands", type=str, default="1", help="Bands kept by 'band matte', e.g. 2,3. Default: 1.")
    p.add_argument("--scan_speed", type=float, default=0.0, help="Cut-point sweep speed in Hz. Default: 0.")
    p.add_argument("--scan_depth", type=float, default=0.15, help="Cut-point sweep depth, 0 to 0.5. Default: 0.15.")
    keying.add_common_arguments(p)


# ── pure helpers (unit-tested) ──────────────────────────────────────────────────

def parse_cuts(text: str, bands: int):
    """Sorted cut points for `bands` bands; missing/invalid values fall back to an even split."""
    vals = []
    for part in (text or "").replace(";", ",").split(","):
        try:
            vals.append(float(part.strip()))
        except ValueError:
            pass
    n = max(1, bands - 1)
    if len(vals) != n:
        vals = [(k + 1) / bands for k in range(n)]
    return sorted(min(1.0, max(0.0, v)) for v in vals)


def parse_colors(text: str, bands: int):
    cols = [c.strip() for c in (text or "").split(",") if c.strip()]
    cols = (cols + DEFAULT_COLORS)[:bands] if len(cols) < bands else cols[:bands]
    return np.array([hex_to_rgb(c, (128, 128, 128)) for c in cols], np.float32)


def band_weights(signal: np.ndarray, cuts, softness: float) -> np.ndarray:
    """(n_bands, H, W) float32 weights that sum to exactly 1 at every pixel."""
    edge = max(float(softness), 1e-4)
    steps = [np.clip((signal - c) / edge + 0.5, 0.0, 1.0) for c in cuts]      # 1 above the cut, 0 below
    out = [1.0 - steps[0]]
    for k in range(1, len(steps)):
        out.append(steps[k - 1] - steps[k])
    out.append(steps[-1])
    return np.stack(out).astype(np.float32)


def band_labels(signal: np.ndarray, cuts) -> np.ndarray:
    lab = np.zeros(signal.shape, np.uint8)
    for c in cuts:
        lab += (signal > c).astype(np.uint8)
    return lab


def parse_sources(text: str, bands: int, available: int):
    """Index (0 = A, 1 = B, 2 = C) of the picture for each band; letters that aren't connected fall back to A."""
    letters = [t.strip().upper() for t in (text or "").replace(";", ",").split(",") if t.strip()]
    if not letters:
        letters = ["A", "B", "C"]
    out = []
    for k in range(bands):
        letter = letters[k % len(letters)]
        idx = {"A": 0, "B": 1, "C": 2}.get(letter, 0)
        out.append(idx if idx < available else 0)
    return out


def parse_band_list(text: str, bands: int):
    out = set()
    for part in (text or "").replace(";", ",").split(","):
        try:
            k = int(part.strip())
        except ValueError:
            continue
        if 1 <= k <= bands:
            out.add(k - 1)
    return sorted(out) or [0]


def extract_signal(cv2, frame, kind: str, prev_luma=None):
    """Signal 0..1 for a frame, plus this frame's luma (for the motion signal)."""
    luma = luma01(frame)
    if kind == "luma":
        s = luma
    elif kind in ("red", "green", "blue"):
        s = frame[..., "rgb".index(kind[0])].astype(np.float32) / 255.0
    elif kind in ("saturation", "hue"):
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        s = hsv[..., 1 if kind == "saturation" else 0].astype(np.float32) / (255.0 if kind == "saturation" else 179.0)
    else:   # motion
        s = np.zeros_like(luma) if prev_luma is None else np.clip(np.abs(luma - prev_luma) * 4.0, 0.0, 1.0)
    return s.astype(np.float32), luma


def run(args):
    cv2 = require_cv2()
    bands = int(min(6, max(2, args.bands)))
    cuts0 = np.array(parse_cuts(args.cuts, bands), np.float32)
    colors = parse_colors(args.colors, bands)
    line_rgb = np.array(hex_to_rgb(args.line_color, (255, 255, 255)), np.float32)
    keep = parse_band_list(args.matte_bands, bands)
    extras_given = [p for p in (args.input2, args.input3) if p]
    st = {"prev": None}
    source_of = parse_sources(getattr(args, "sources", ""), bands, 1 + len(extras_given))
    if args.style == S_INPUTS:
        names = "ABC"
        print("Bands (darkest first) → " + ", ".join(f"{k + 1}: {names[source_of[k]]}" for k in range(bands)))
        if not extras_given:
            print("⚠️  Only the main picture is connected, so every band shows picture A and the result looks like the original. "
                  "Connect Band picture B (and C) to see different videos in different bands.")
    elif extras_given:
        print(f"ℹ️  Band pictures B/C are connected but the style '{args.style}' only uses the main picture (A). "
              f"Choose 'bands from inputs' to use them.")

    def signal_for(frame, t):
        s, luma = extract_signal(cv2, frame, args.signal, st["prev"])
        st["prev"] = luma
        if args.smooth > 0.2:
            s = cv2.GaussianBlur(s, (0, 0), float(args.smooth))
        if args.invert:
            s = 1.0 - s
        cuts = cuts0
        if args.scan_speed > 0 and args.scan_depth > 0:
            cuts = np.clip(cuts0 + args.scan_depth * np.sin(2 * np.pi * args.scan_speed * t), 0.0, 1.0)
            cuts = np.sort(cuts)
        return s, cuts

    def matte_fn(frame, i, t):
        s, cuts = signal_for(frame, t)
        w = band_weights(s, cuts, args.softness)
        return np.clip(sum(w[k] for k in keep), 0.0, 1.0)

    if args.style == STYLES[4]:
        run_matte_program(args, matte_fn)
        return

    def render(frame, i, t, extras=()):
        s, cuts = signal_for(frame, t)
        f = frame.astype(np.float32)
        if args.style == "contour lines":
            lab = band_labels(s, cuts)
            edge = cv2.morphologyEx(lab, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
            k = max(1, int(args.line_width))
            if k > 1:
                edge = cv2.dilate(edge.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
            out = f * (1.0 - float(args.dim))
            out[edge] = line_rgb
            return np.clip(out, 0, 255).astype(np.uint8)
        w = band_weights(s, cuts, args.softness)
        if args.style == "bands from inputs":
            srcs = [f] + [e.astype(np.float32) for e in extras]
            out = np.zeros_like(f)
            for k in range(bands):
                out += w[k][..., None] * srcs[source_of[k]]
            return np.clip(out, 0, 255).astype(np.uint8)
        flat = np.tensordot(w, colors, axes=([0], [0]))                  # (H, W, 3) band color mix
        if args.style == "tint original":
            a = float(np.clip(args.amount, 0.0, 1.0))
            return np.clip(f * (1.0 - a) + flat * a, 0, 255).astype(np.uint8)
        return np.clip(flat, 0, 255).astype(np.uint8)

    stats = process_video(args.input, args.output, render, crf=args.crf, force=bool(getattr(args, "force", False)),
                          extra_inputs=extras_given or None)
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")

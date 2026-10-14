"""
stackadelic — three stacked quadrilateral layers with layer priority (an homage to the LZX Stacker, a triple
quadrilateral key generator and layer-priority encoder).

Each layer is a rectangle or rhombus defined by four edge thresholds (left / right / top / bottom), with size,
ratio, rotation, optional tiling into a mosaic and a soft edge. Layers are stacked: layer 1 sits on top and each
layer is subtracted from the layers beneath it, so the shapes cut letterforms and icons out of each other. Each
layer can reveal a solid color, input A / B / C, or A keyed by its own brightness. "Complex source" displaces the
shapes by the picture's tones so they follow the image.

Press ✎ next to "Layer 1 left" to drag the three boxes on a stand-in frame.
"""
import numpy as np

from videobeaux.utils import fields, keying
from videobeaux.utils.cv import hex_to_rgb, require_cv2
from videobeaux.utils.feedback_core import luma01
from videobeaux.utils.frame_pipe import process_video
from videobeaux.utils.matte_pipeline import run_matte_program

SHAPES = ["rectangle", "rhombus"]
SOURCES = ["color", "input A", "input B", "input C", "input A × its brightness"]
BASES = ["input A", "black", "color"]
STYLES = ["stack over base", "matte (white shapes)", "cutout (A inside the stack)"]
LAYERS = (1, 2, 3)
DEFAULT_COLORS = {1: "#FF3D7F", 2: "#FFB000", 3: "#2EC4B6"}
DEFAULT_BOX = {1: (35, 65, 35, 65), 2: (22, 78, 22, 78), 3: (8, 92, 8, 92)}   # left, right, top, bottom (%)

_args = {
    'input2': {'type': 'file', 'subtype': 'video', 'label': 'Input B', 'help': "Optional. Used by layers whose source is 'input B'."},
    'input3': {'type': 'file', 'subtype': 'video', 'label': 'Input C', 'help': "Optional. Used by layers whose source is 'input C'."},
    'style': {'type': 'select', 'label': 'Output style', 'default': STYLES[0], 'choices': STYLES,
              'help': "The Background / View / Edge options at the bottom only apply to 'cutout'."},
    'base': {'type': 'select', 'label': 'Under the stack', 'default': BASES[0], 'choices': BASES},
    'base_color': {'type': 'color', 'label': 'Base color', 'default': '#000000'},
    'complex': {'label': 'Complex source', 'help': 'Displace the shapes by the picture’s brightness so they follow the image.'},
    'complex_amount': {'label': 'Complex amount', 'min': 0, 'max': 1, 'step': 0.01, 'good_min': 0.05, 'good_max': 0.4},
}
for _n in LAYERS:
    L = f'Layer {_n}'
    _args.update({
        f'l{_n}_shape': {'type': 'select', 'label': f'{L} shape', 'default': 'rectangle', 'choices': SHAPES},
        f'l{_n}_left': {'label': f'{L} left (%)', 'min': 0, 'max': 100},
        f'l{_n}_right': {'label': f'{L} right (%)', 'min': 0, 'max': 100},
        f'l{_n}_top': {'label': f'{L} top (%)', 'min': 0, 'max': 100},
        f'l{_n}_bottom': {'label': f'{L} bottom (%)', 'min': 0, 'max': 100},
        f'l{_n}_size': {'label': f'{L} size', 'min': 0.1, 'max': 3, 'step': 0.01, 'good_min': 0.5, 'good_max': 1.5,
                        'help': 'Scales the box about its centre (the Stacker’s Size control).'},
        f'l{_n}_ratio': {'label': f'{L} ratio', 'min': 0.25, 'max': 4, 'step': 0.05, 'good_min': 0.5, 'good_max': 2,
                         'help': 'Wider (above 1) or taller (below 1), keeping the area (the Stacker’s Ratio control).'},
        f'l{_n}_rotate': {'label': f'{L} rotate (°)', 'min': -180, 'max': 180},
        f'l{_n}_tiles': {'label': f'{L} tiles', 'min': 1, 'max': 12, 'good_min': 1, 'good_max': 8,
                         'help': '1 = a single box; more repeats it into a grid (a mosaic).'},
        f'l{_n}_softness': {'label': f'{L} edge softness', 'min': 0, 'max': 0.5, 'step': 0.01, 'good_min': 0, 'good_max': 0.15},
        f'l{_n}_opacity': {'label': f'{L} opacity', 'min': 0, 'max': 1, 'step': 0.05, 'good_min': 0.6, 'good_max': 1,
                           'help': '0 switches the layer off (it still cuts nothing out of the layers below).'},
        f'l{_n}_source': {'type': 'select', 'label': f'{L} shows', 'default': 'color', 'choices': SOURCES},
        f'l{_n}_color': {'type': 'color', 'label': f'{L} color', 'default': DEFAULT_COLORS[_n]},
    })


def _preset(boxes, **extra):
    vals = {}
    for n, b in boxes.items():
        for k, v in zip(("left", "right", "top", "bottom"), b):
            vals[f'l{n}_{k}'] = v
    vals.update(extra)
    return vals


GUI_METADATA = {
    'args': {**_args, **keying.GUI_COMMON, 'crf': {'hidden': True}},
    'presets': {
        'Nested squares': _preset({1: (38, 62, 38, 62), 2: (24, 76, 24, 76), 3: (10, 90, 10, 90)},
                                  l1_opacity=1, l2_opacity=1, l3_opacity=1),
        'Letterbox': _preset({1: (0, 100, 0, 12), 2: (0, 100, 88, 100), 3: (0, 100, 0, 100)},
                             l1_color='#000000', l2_color='#000000', l1_opacity=1, l2_opacity=1, l3_opacity=0),
        'Diamond stack': _preset({1: (40, 60, 20, 80), 2: (30, 70, 10, 90), 3: (15, 85, 0, 100)},
                                 l1_shape='rhombus', l2_shape='rhombus', l3_shape='rhombus',
                                 l1_opacity=1, l2_opacity=1, l3_opacity=0.9),
        'Mosaic': _preset({1: (0, 100, 0, 100), 2: (0, 100, 0, 100), 3: (0, 100, 0, 100)},
                          l1_tiles=6, l1_size=0.8, l1_source='input A', l1_opacity=1,
                          l2_tiles=6, l2_size=1.0, l2_opacity=0.9, l3_opacity=0),
        'Tone windows': _preset({1: (30, 70, 30, 70), 2: (15, 85, 15, 85), 3: (0, 100, 0, 100)},
                                complex=True, complex_amount=0.25, l1_opacity=1, l2_opacity=0.9, l3_opacity=0.7,
                                l1_softness=0.05, l2_softness=0.05, l3_softness=0.05),
    },
}


def register_arguments(p):
    p.description = (
        "Stackadelic — three stacked quadrilateral layers (rectangle or rhombus) with layer priority: each layer "
        "is cut out of the ones beneath it, and each can show a color, input A/B/C or A keyed by its brightness. "
        "Complex source makes the shapes follow the picture. Homage to the LZX Stacker."
    )
    p.add_argument("--input2", type=str, default=None, help="Input B (optional).")
    p.add_argument("--input3", type=str, default=None, help="Input C (optional).")
    p.add_argument("--style", choices=STYLES, default=STYLES[0], help="What to render.")
    p.add_argument("--base", choices=BASES, default=BASES[0], help="What is under the stack.")
    p.add_argument("--base_color", type=str, default="#000000", help="Base color when --base color.")
    p.add_argument("--complex", action="store_true", help="Displace the shapes by the picture's brightness.")
    p.add_argument("--complex_amount", type=float, default=0.2, help="Displacement amount. Default: 0.2.")
    for n in LAYERS:
        l, r, t, b = DEFAULT_BOX[n]
        p.add_argument(f"--l{n}_shape", choices=SHAPES, default="rectangle", help=f"Layer {n} shape.")
        p.add_argument(f"--l{n}_left", type=float, default=l, help="Left edge, percent of frame width.")
        p.add_argument(f"--l{n}_right", type=float, default=r, help="Right edge, percent of frame width.")
        p.add_argument(f"--l{n}_top", type=float, default=t, help="Top edge, percent of frame height.")
        p.add_argument(f"--l{n}_bottom", type=float, default=b, help="Bottom edge, percent of frame height.")
        p.add_argument(f"--l{n}_size", type=float, default=1.0, help="Size multiplier about the box centre.")
        p.add_argument(f"--l{n}_ratio", type=float, default=1.0, help="Width/height ratio multiplier (area kept).")
        p.add_argument(f"--l{n}_rotate", type=float, default=0.0, help="Rotation in degrees.")
        p.add_argument(f"--l{n}_tiles", type=int, default=1, help="Tiles per side (1 = single box).")
        p.add_argument(f"--l{n}_softness", type=float, default=0.03, help="Edge softness.")
        p.add_argument(f"--l{n}_opacity", type=float, default=1.0 if n == 1 else 0.0, help="Layer opacity (0 = off).")
        p.add_argument(f"--l{n}_source", choices=SOURCES, default="color", help="What the layer shows.")
        p.add_argument(f"--l{n}_color", type=str, default=DEFAULT_COLORS[n], help="Layer color.")
    keying.add_common_arguments(p)


# ── pure helpers (unit-tested) ──────────────────────────────────────────────────

def layer_shape(args, n: int, h: int, w: int, disp=None) -> np.ndarray:
    """0..1 matte of layer n (its own shape, before the priority subtraction)."""
    g = lambda k: getattr(args, f"l{n}_{k}")
    aspect = w / h
    x, y = fields.ramps(h, w)
    if disp is not None:
        x, y = x + disp[0], y + disp[1]
    left, right = min(g("left"), g("right")) / 100.0, max(g("left"), g("right")) / 100.0
    top, bottom = min(g("top"), g("bottom")) / 100.0, max(g("top"), g("bottom")) / 100.0
    cx = ((left + right) / 2.0 * 2.0 - 1.0) * aspect
    cy = (top + bottom) / 2.0 * 2.0 - 1.0
    hw = max((right - left) * aspect, 1e-3)               # half-width in coordinate units (frame width = 2·aspect)
    hh = max(bottom - top, 1e-3)                          # half-height (frame height = 2)
    ratio = max(g("ratio"), 1e-3)
    hw, hh = hw * g("size") * np.sqrt(ratio), hh * g("size") / np.sqrt(ratio)
    if g("rotate"):
        a = np.deg2rad(g("rotate"))
        c, s = np.cos(a), np.sin(a)
        xr, yr = x - cx, y - cy
        x, y = c * xr + s * yr + cx, -s * xr + c * yr + cy
    tiles = max(1, int(g("tiles")))
    if tiles > 1:
        cell_w, cell_h = 2.0 * aspect / tiles, 2.0 / tiles
        u = np.mod(x + aspect, cell_w) - cell_w / 2.0
        v = np.mod(y + 1.0, cell_h) - cell_h / 2.0
        u = u / max(cell_w / 2.0 * (right - left) * g("size") * np.sqrt(ratio), 1e-3)
        v = v / max(cell_h / 2.0 * (bottom - top) * g("size") / np.sqrt(ratio), 1e-3)
    else:
        u, v = (x - cx) / hw, (y - cy) / hh
    f = (np.abs(u) + np.abs(v)) if g("shape") == "rhombus" else np.maximum(np.abs(u), np.abs(v))
    return fields.inside(f.astype(np.float32), max(g("softness"), 0.005))


def priority_keys(shapes):
    """Layer 1 on top; layer i keeps only what the layers above it leave: key_i = shape_i · Π_{j<i}(1 − shape_j)."""
    keys, free = [], None
    for s in shapes:
        k = s if free is None else s * free
        keys.append(k)
        free = (1.0 - s) if free is None else free * (1.0 - s)
    return keys


def run(args):
    cv2 = require_cv2()
    extras_given = [p for p in (args.input2, args.input3) if p]
    slot = {}
    for name, path in (("input B", args.input2), ("input C", args.input3)):
        if path:
            slot[name] = len(slot)
    colors = {n: np.array(hex_to_rgb(getattr(args, f"l{n}_color"), (255, 255, 255)), np.float32) for n in LAYERS}
    base_rgb = np.array(hex_to_rgb(args.base_color, (0, 0, 0)), np.float32)

    def shapes_for(frame):
        h, w = frame.shape[:2]
        disp = None
        if args.complex and args.complex_amount > 0:
            lum = luma01(frame) - 0.5
            disp = (lum * 2.0 * args.complex_amount * (w / h), lum * 2.0 * args.complex_amount)
        return [layer_shape(args, n, h, w, disp) for n in LAYERS]

    if args.style == STYLES[2]:
        def cut_fn(frame, i, t):
            keys = priority_keys(shapes_for(frame))
            return np.clip(sum(keys), 0.0, 1.0)
        run_matte_program(args, cut_fn)
        return

    def render(frame, i, t, extras=()):
        keys = priority_keys(shapes_for(frame))
        if args.style == STYLES[1]:
            g = (np.clip(sum(keys), 0, 1) * 255).astype(np.uint8)
            return np.dstack([g, g, g])
        f = frame.astype(np.float32)
        if args.base == "black":
            out = np.zeros_like(f)
        elif args.base == "color":
            out = np.broadcast_to(base_rgb, f.shape).copy()
        else:
            out = f.copy()
        luma = luma01(frame)[..., None]
        cover = np.zeros(frame.shape[:2], np.float32)
        paint = np.zeros_like(f)
        for n, k in zip(LAYERS, keys):
            op = float(np.clip(getattr(args, f"l{n}_opacity"), 0.0, 1.0))
            if op <= 0:
                continue
            src = getattr(args, f"l{n}_source")
            if src == "color":
                col = np.broadcast_to(colors[n], f.shape)
                a = k * op
            elif src == "input A":
                col, a = f, k * op
            elif src == "input A × its brightness":
                col, a = f, k * op * luma[..., 0]
            else:
                idx = slot.get(src)
                col = extras[idx].astype(np.float32) if idx is not None and idx < len(extras) else f
                a = k * op
            paint += a[..., None] * col
            cover += a
        cover = np.clip(cover, 0.0, 1.0)
        out = out * (1.0 - cover[..., None]) + paint
        return np.clip(out, 0, 255).astype(np.uint8)

    stats = process_video(args.input, args.output, render, crf=args.crf, force=bool(getattr(args, "force", False)),
                          extra_inputs=extras_given or None)
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")

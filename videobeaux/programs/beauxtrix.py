"""
beauxtrix — a video blending matrix, an homage to the LZX Industries Video Blending Matrix.

Three mixers (red, green, blue) each sum up to four videos (A–D) with their own level knobs. Levels run from
−2 to +2 (negative = inverted / subtracted, 0 = off), each mixer has a bias, and each can output its plain
SUM or its ABSOLUTE value (full-wave rectification — which is solarization). The three mixer outputs become the
red, green and blue of the picture; a soft limiter keeps hot sums from clipping harshly.

Two source modes:
  • Luma matrix    — like the hardware: every input is reduced to a gray signal, so all color comes from the mixing.
  • Channel matrix — each mixer mixes the same color channel of the inputs, so source colors survive.
Empty inputs B, C, D simply repeat A, so it works with a single clip too (try Solarize or Negative).
"""
import numpy as np

from videobeaux.utils.feedback_core import luma01
from videobeaux.utils.frame_pipe import process_video

SOURCES = ["Channel matrix (keep colors)", "Luma matrix (like the hardware)"]
OUTS = ["sum", "absolute"]
LIMITERS = ["soft", "hard"]
MIXERS = ["r", "g", "b"]
NAMES = {"r": "Red", "g": "Green", "b": "Blue"}

_LEVEL = {'min': -2, 'max': 2, 'step': 0.05, 'good_min': -1, 'good_max': 1}
_args = {
    'input2': {'type': 'file', 'subtype': 'video', 'label': 'Input B', 'help': 'Optional. Empty = repeats A.'},
    'input3': {'type': 'file', 'subtype': 'video', 'label': 'Input C', 'help': 'Optional. Empty = repeats A.'},
    'input4': {'type': 'file', 'subtype': 'video', 'label': 'Input D', 'help': 'Optional. Empty = repeats A.'},
    'source': {'type': 'select', 'label': 'Source', 'default': SOURCES[0], 'choices': SOURCES},
    'limiter': {'type': 'select', 'label': 'Limiter', 'default': LIMITERS[0], 'choices': LIMITERS,
                'help': 'soft = hot sums roll off gently; hard = clipped.'},
    'detail': {'label': 'Processing width (px)', 'min': 240, 'max': 3840, 'help': 'Mixed at this width (result scaled back up).'},
    'crf': {'hidden': True},
}
for _m in MIXERS:
    for _ch in "abcd":
        _args[f'{_m}_{_ch}'] = {**_LEVEL, 'label': f'{NAMES[_m]} ← {_ch.upper()}',
                                'help': f'How much of input {_ch.upper()} goes into the {NAMES[_m].lower()} mixer. Negative inverts it.'}
    _args[f'{_m}_bias'] = {'label': f'{NAMES[_m]} bias', 'min': -1, 'max': 1, 'step': 0.05, 'good_min': -0.5, 'good_max': 0.5,
                           'help': 'A constant added to the mixer (the hardware makes this from an unused input).'}
    _args[f'{_m}_out'] = {'type': 'select', 'label': f'{NAMES[_m]} output', 'default': OUTS[0], 'choices': OUTS,
                          'help': 'sum = the mix. absolute = full-wave rectified (solarize).'}


def _preset(a=None, bias=0.0, out="sum", **per):
    """Preset values for all three mixers; `per` overrides per mixer: r=dict(...)."""
    vals = {}
    for m in MIXERS:
        gains = {"a": 1.0, "b": 0.0, "c": 0.0, "d": 0.0}
        gains.update(a or {})
        gains.update(per.get(m, {}))
        for ch in "abcd":
            vals[f"{m}_{ch}"] = gains[ch]
        vals[f"{m}_bias"] = bias
        vals[f"{m}_out"] = out
    return vals


GUI_METADATA = {
    'args': _args,
    'presets': {
        'Identity': _preset(),
        'Negative': _preset(a={"a": -1.0}, bias=1.0),
        'Solarize': _preset(a={"a": 2.0}, bias=-1.0, out="absolute"),
        'Difference A−B': _preset(a={"a": 1.0, "b": -1.0}, out="absolute"),
        'Mono mix A+B': _preset(a={"a": 0.5, "b": 0.5}),
        'Psychedelic': _preset(a={"a": 1.4, "b": -0.7}, bias=0.15, out="absolute", g={"a": 0.9, "b": -1.1}, b={"a": 1.7, "b": 0.4}),
    },
}


def register_arguments(p):
    p.description = (
        "Beauxtrix — a video blending matrix (homage to the LZX Video Blending Matrix): three mixers (R, G, B), "
        "each summing videos A–D with levels from -2 to +2 plus a bias, output as the sum or its absolute value "
        "(solarize), through a soft limiter. Try the presets: Solarize, Negative, Difference A−B, Psychedelic."
    )
    p.add_argument("--input2", type=str, default=None, help="Input B (optional; repeats A when empty).")
    p.add_argument("--input3", type=str, default=None, help="Input C (optional; repeats A when empty).")
    p.add_argument("--input4", type=str, default=None, help="Input D (optional; repeats A when empty).")
    p.add_argument("--source", choices=SOURCES, default=SOURCES[0], help="Channel matrix keeps colors; luma matrix mixes gray signals.")
    for m in MIXERS:
        for ch in "abcd":
            p.add_argument(f"--{m}_{ch}", type=float, default=1.0 if ch == "a" else 0.0,
                           help=f"Level of input {ch.upper()} in the {NAMES[m].lower()} mixer, -2 to 2.")
        p.add_argument(f"--{m}_bias", type=float, default=0.0, help=f"{NAMES[m]} mixer bias, -1 to 1.")
        p.add_argument(f"--{m}_out", choices=OUTS, default=OUTS[0], help=f"{NAMES[m]} mixer output: sum or absolute.")
    p.add_argument("--limiter", choices=LIMITERS, default=LIMITERS[0], help="Soft or hard limiting of hot sums.")
    p.add_argument("--detail", type=int, default=1280, help="Width the mix is computed at. Default: 1280.")
    p.add_argument("--crf", type=int, default=18, help="x264 quality. Default: 18.")


def soft_limit(y: np.ndarray, knee: float = 0.8) -> np.ndarray:
    """Roll peaks off smoothly beyond ±knee, approaching ±1 (the hardware's soft limiters)."""
    mag = np.abs(y)
    return np.where(mag <= knee, y, np.sign(y) * (knee + (1.0 - knee) * np.tanh((mag - knee) / (1.0 - knee))))


def matrix_mix(sources, gains, biases, outs, *, luma_mode, limiter="soft"):
    """
    sources: 4 uint8 RGB frames (A–D). gains[m][i] for mixer m in (r, g, b), input i in A–D.
    Returns a uint8 RGB frame. y_m = limit(Σ g·s + bias); 'absolute' → |y_m|; the result is clipped to 0..1.
    """
    if luma_mode:
        planes = [luma01(s) for s in sources]                       # each input is one gray signal
        pick = lambda i, c: planes[i]
    else:
        planes = [s.astype(np.float32) / 255.0 for s in sources]
        pick = lambda i, c: planes[i][..., c]
    chans = []
    for c, m in enumerate(MIXERS):
        y = np.full(sources[0].shape[:2], biases[m], np.float32)
        for i in range(4):
            g = gains[m][i]
            if g:
                y = y + g * pick(i, c)
        if limiter == "soft":
            y = soft_limit(y)
        if outs[m] == "absolute":
            y = np.abs(y)
        chans.append(np.clip(y, 0.0, 1.0))
    return (np.dstack(chans) * 255.0 + 0.5).astype(np.uint8)


def run(args):
    gains = {m: [getattr(args, f"{m}_{ch}") for ch in "abcd"] for m in MIXERS}
    biases = {m: getattr(args, f"{m}_bias") for m in MIXERS}
    outs = {m: getattr(args, f"{m}_out") for m in MIXERS}
    luma_mode = args.source == SOURCES[1]
    given = [p for p in (args.input2, args.input3, args.input4)]
    paths = [p for p in given if p]
    slot = {}                                   # input index (B=1, C=2, D=3) → position among the decoded extras
    for i, p in enumerate(given, start=1):
        if p:
            slot[i] = len(slot)

    def frame_fn(frame, i, t, extras=()):
        srcs = [frame] + [extras[slot[k]] if k in slot else frame for k in (1, 2, 3)]
        return matrix_mix(srcs, gains, biases, outs, luma_mode=luma_mode, limiter=args.limiter)

    stats = process_video(args.input, args.output, frame_fn, crf=args.crf, force=bool(getattr(args, "force", False)),
                          max_width=args.detail or None, extra_inputs=paths)
    print(f"✅ {stats['frames']} frames in {stats['seconds']:.1f}s")

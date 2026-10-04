"""
Oil Paint — Painterly oil-paint look: smoothed brush regions, posterized tones and a little canvas relief.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Painterly oil-paint look: smoothed brush regions, posterized tones and a little canvas relief.'

PARAMS = [
    Param('brush', 'float', 40.0, 'Brush size', 'Larger = broader strokes.', min=5, max=100),
    Param('levels', 'int', 24, 'Tone step', 'Larger = flatter color regions.', min=2, max=64),
    Param('relief', 'float', 0.35, 'Relief', '', min=0, max=1),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_oil(a.brush, a.levels, a.relief)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

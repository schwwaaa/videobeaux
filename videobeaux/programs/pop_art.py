"""
Pop Art — Warhol-style flat-color panels — four colorways in a 2×2 grid, or one palette over the whole frame.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Warhol-style flat-color panels — four colorways in a 2×2 grid, or one palette over the whole frame.'

PARAMS = [
    Param('layout', 'select', '2x2 panels', 'Layout', '', choices=['2x2 panels', 'single']),
    Param('palette', 'int', 0, 'Palette (single)', 'Which colorway when Layout = single (0-3).', min=0, max=3),
    Param('low', 'int', 90, 'Shadow cut', 'Brightness where dark turns to mid tone.', min=0, max=254),
    Param('high', 'int', 170, 'Highlight cut', 'Brightness where mid turns to light.', min=1, max=255),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_popart(a.layout, a.palette, a.low, a.high)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

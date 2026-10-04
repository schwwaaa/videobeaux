"""
CRT Monitor — Old TV tube: curved glass, scanlines, RGB shadow mask, glow and a dark vignette.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Old TV tube: curved glass, scanlines, RGB shadow mask, glow and a dark vignette.'

PARAMS = [
    Param('curvature', 'float', 0.1, 'Curvature', '', min=0, max=0.4),
    Param('scanlines', 'float', 0.45, 'Scanlines', '', min=0, max=1),
    Param('mask', 'float', 0.28, 'Shadow mask', '', min=0, max=0.8),
    Param('glow', 'float', 0.3, 'Glow', '', min=0, max=1),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.CRT(a.curvature, a.scanlines, a.mask, a.glow)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

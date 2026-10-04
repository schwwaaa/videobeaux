"""
Lomo — Cross-processed toy-camera look: punchy curves, color cast and dark vignette corners.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Cross-processed toy-camera look: punchy curves, color cast and dark vignette corners.'

PARAMS = [
    Param('vignette', 'float', 0.65, 'Vignette', 'Corner darkening.', min=0, max=1.2),
    Param('saturation', 'float', 1.0, 'Saturation', '', min=0, max=2.5),
    Param('contrast', 'float', 1.0, 'Curve strength', '', min=0.4, max=2),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_lomo(a.vignette, a.saturation, a.contrast)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

"""
Little Planet — Polar-coordinate 'tiny planet' — the bottom of the picture becomes a small round world with sky all around.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = "Polar-coordinate 'tiny planet' — the bottom of the picture becomes a small round world with sky all around."

PARAMS = [
    Param('curve', 'float', 0.8, 'Curve', 'Lower = bigger planet.', min=0.3, max=2),
    Param('spin', 'float', 0.0, 'Spin (°/sec)', '', min=-180, max=180),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.LittlePlanet(a.curve, a.spin)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

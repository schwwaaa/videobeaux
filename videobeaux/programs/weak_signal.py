"""
Weak Signal — Edge-of-reception transmission: skew, colour misregistration, noise, streaks and bursts of static.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Edge-of-reception transmission: skew, colour misregistration, noise, streaks and bursts of static.'

PARAMS = [
    Param('noise', 'float', 14.0, 'Noise', '', min=0, max=60),
    Param('streaks', 'int', 5, 'Streaks', '', min=0, max=30),
    Param('bursts', 'float', 0.35, 'Static bursts', 'Chance per frame.', min=0, max=1),
    Param('skew', 'float', 0.035, 'Skew', '', min=0, max=0.2),
    Param('speckle', 'float', 0.02, 'Speckle', '', min=0, max=0.2),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_weak_signal(a.noise, a.streaks, a.bursts, a.skew, a.speckle)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

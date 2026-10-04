"""
Hue Cycle — Rotate every color around the color wheel continuously.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Rotate every color around the color wheel continuously.'

PARAMS = [
    Param('speed', 'float', 60.0, 'Speed (°/sec)', 'Negative runs the wheel backwards.', min=-360, max=360),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_hue_cycle(a.speed)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

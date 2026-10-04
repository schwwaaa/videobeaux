"""
Face Swap — Swap the two biggest faces in the shot, colour-matched with a soft edge.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Swap the two biggest faces in the shot, colour-matched with a soft edge.'

PARAMS = [
    Param('softness', 'float', 0.06, 'Edge softness', '', min=0, max=0.3),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_face_swap(a.softness)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build, faces=True, eyes=True)

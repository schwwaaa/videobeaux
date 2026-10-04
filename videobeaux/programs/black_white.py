"""
Black & White — High-contrast black and white with local contrast boost (faces and texture pop), optional film grain.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'High-contrast black and white with local contrast boost (faces and texture pop), optional film grain.'

PARAMS = [
    Param('contrast', 'float', 2.5, 'Contrast', 'Local contrast boost.', min=0.5, max=8),
    Param('grain', 'float', 0.0, 'Grain', 'Film grain amount.', min=0, max=1),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_bw(a.contrast, a.grain)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

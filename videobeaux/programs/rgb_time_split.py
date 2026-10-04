"""
RGB Time Split — Red channel is now, green and blue lag behind — motion leaves rainbow fringes.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Red channel is now, green and blue lag behind — motion leaves rainbow fringes.'

PARAMS = [
    Param('delay_green', 'int', 9, 'Green delay (frames)', '', min=0, max=60),
    Param('delay_blue', 'int', 18, 'Blue delay (frames)', '', min=0, max=60),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.RGBSplit(a.delay_green, a.delay_blue)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

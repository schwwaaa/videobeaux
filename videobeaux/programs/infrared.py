"""
Infrared Film — False-color infrared film look — foliage turns pink and red, skies go dark.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'False-color infrared film look — foliage turns pink and red, skies go dark.'

PARAMS = [
    Param('saturation', 'float', 1.5, 'Saturation', '', min=0, max=3),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_infrared(a.saturation)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

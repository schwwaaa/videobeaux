"""
LED Wall — The picture rebuilt from a grid of round glowing LEDs, like a stadium video wall.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'The picture rebuilt from a grid of round glowing LEDs, like a stadium video wall.'

PARAMS = [
    Param('cell', 'int', 10, 'LED size (px)', '', min=3, max=60),
    Param('brightness', 'float', 1.15, 'Brightness', '', min=0.5, max=2),
    Param('dot', 'float', 1.0, 'Dot size', '', min=0.3, max=1.3),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.LEDWall(a.cell, a.brightness, a.dot)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

"""
Tunnel — The picture wrapped around the inside of a tunnel you fly down.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'The picture wrapped around the inside of a tunnel you fly down.'

PARAMS = [
    Param('speed', 'float', 90.0, 'Speed', 'Negative flies backwards.', min=-400, max=400),
    Param('around', 'int', 3, 'Tiles around', '', min=1, max=8),
    Param('deep', 'int', 4, 'Tiles deep', '', min=1, max=10),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.Tunnel(a.speed, a.around, a.deep)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

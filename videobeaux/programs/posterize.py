"""
Posterize — Reduce each color channel to a few flat levels.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Reduce each color channel to a few flat levels.'

PARAMS = [
    Param('levels', 'int', 4, 'Levels', 'Shades per channel.', min=2, max=16),
    Param('sharp', 'bool', False, 'Keep edges sharp', 'Skip the slight pre-blur.'),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_posterize(a.levels, not a.sharp)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

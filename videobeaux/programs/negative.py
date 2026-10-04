"""
Negative — Invert the picture like a photo negative — or flip only the brightness and keep the colors.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Invert the picture like a photo negative — or flip only the brightness and keep the colors.'

PARAMS = [
    Param('mode', 'select', 'full', 'Invert', 'full = every color inverted. brightness only = light/dark flipped, hues kept.', choices=['full', 'brightness only']),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_negative(a.mode)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

"""
Long Exposure — A slowly fading average of past frames — moving things smear into ghostly trails.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'A slowly fading average of past frames — moving things smear into ghostly trails.'

PARAMS = [
    Param('persistence', 'float', 0.85, 'Persistence', 'Higher = longer trails.', min=0, max=0.99),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.Ghost(a.persistence)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

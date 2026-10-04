"""
Emboss — Raised-relief emboss lit from any angle, in gray or keeping the colors.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Raised-relief emboss lit from any angle, in gray or keeping the colors.'

PARAMS = [
    Param('strength', 'float', 1.0, 'Strength', '', min=0, max=4),
    Param('angle', 'float', 135.0, 'Light angle (°)', '', min=0, max=360),
    Param('keep_color', 'bool', False, 'Keep color'),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_emboss(a.strength, a.angle, a.keep_color)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

"""
Glitch Tear — RGB channel split plus horizontal tears and scanline dimming, re-rolled every frame.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'RGB channel split plus horizontal tears and scanline dimming, re-rolled every frame.'

PARAMS = [
    Param('intensity', 'float', 0.5, 'Intensity', '', min=0, max=1),
    Param('tears', 'int', 4, 'Tears per frame', '', min=0, max=16),
    Param('rgb_shift', 'int', 9, 'RGB shift (px)', '', min=0, max=40),
    Param('no_scanlines', 'bool', False, 'No scanlines'),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_glitch(a.intensity, a.tears, a.rgb_shift, not a.no_scanlines)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

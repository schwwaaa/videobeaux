"""
Face Warp — Big head, tiny head or big eyes — warps tracked faces (works on several faces at once).

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Big head, tiny head or big eyes — warps tracked faces (works on several faces at once).'

PARAMS = [
    Param('effect', 'select', 'big head', 'Effect', '', choices=['big head', 'tiny head', 'big eyes']),
    Param('strength', 'float', 1.0, 'Strength', '', min=0, max=2),
    Param('size', 'float', 1.0, 'Size', 'Area of the warp.', min=0.5, max=2),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_face_warp(a.effect, a.strength, a.size)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build, faces=True, eyes=True)

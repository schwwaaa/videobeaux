"""
Pixelate — Chunky square pixels — a mosaic of any block size.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Chunky square pixels — a mosaic of any block size.'

PARAMS = [
    Param('block', 'int', 16, 'Block size (px)', '', min=2, max=200),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_pixelate(a.block)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

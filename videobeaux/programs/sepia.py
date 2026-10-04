"""
Sepia & Tones — Antique single-tone looks: sepia, cyanotype blue, rose, forest or gold.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Antique single-tone looks: sepia, cyanotype blue, rose, forest or gold.'

PARAMS = [
    Param('tone', 'select', 'sepia', 'Tone', '', choices=['sepia', 'cyanotype', 'rose', 'forest', 'gold']),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_sepia(a.tone)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

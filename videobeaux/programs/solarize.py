"""
Solarize — Darkroom solarization — tones above the threshold flip, giving glowing metallic edges.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Darkroom solarization — tones above the threshold flip, giving glowing metallic edges.'

PARAMS = [
    Param('threshold', 'int', 128, 'Threshold', 'Brightness where the tones fold over.', min=1, max=254),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_solarize(a.threshold)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

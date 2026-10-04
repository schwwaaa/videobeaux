"""
Thermal — Thermal-camera false color — pick the heat palette (inferno, jet, turbo, hot, plasma…).

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Thermal-camera false color — pick the heat palette (inferno, jet, turbo, hot, plasma…).'

PARAMS = [
    Param('colormap', 'select', 'inferno', 'Palette', '', choices=['inferno', 'jet', 'turbo', 'hot', 'magma', 'plasma', 'viridis', 'rainbow', 'ocean', 'bone']),
    Param('no_equalize', 'bool', False, 'Skip auto-contrast', "Don't stretch the brightness range first."),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_thermal(a.colormap, not a.no_equalize)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

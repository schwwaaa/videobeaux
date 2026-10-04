"""
Blueprint — Technical-drawing look — white edge lines on blueprint blue, with an optional grid.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program, rgb

DESCRIPTION = 'Technical-drawing look — white edge lines on blueprint blue, with an optional grid.'

PARAMS = [
    Param('sensitivity', 'float', 0.5, 'Line detail', 'More lines at higher values.', min=0, max=1),
    Param('line_color', 'color', '#EBF5FF', 'Line color'),
    Param('paper_color', 'color', '#0A4696', 'Paper color'),
    Param('grid', 'bool', False, 'Draw grid'),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_blueprint(a.sensitivity, rgb(a.line_color, (235, 245, 255)), rgb(a.paper_color, (10, 70, 150)), a.grid)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

"""
VHS Camcorder — Home-video camcorder look: soft chroma, tape noise, a rolling tracking band and the on-screen PLAY / date stamp.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Home-video camcorder look: soft chroma, tape noise, a rolling tracking band and the on-screen PLAY / date stamp.'

PARAMS = [
    Param('label', 'text', 'PLAY', 'On-screen label'),
    Param('hide_osd', 'bool', False, 'Hide on-screen display'),
    Param('hide_date', 'bool', False, 'Hide date/time'),
    Param('noise', 'float', 7.0, 'Tape noise', '', min=0, max=30),
    Param('no_tracking', 'bool', False, 'No tracking band'),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_vhs(not a.hide_osd, a.label, not a.hide_date, a.noise, not a.no_tracking)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

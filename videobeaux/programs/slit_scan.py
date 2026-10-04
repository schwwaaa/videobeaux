"""
Slit-Scan — Different parts of the frame show different moments in time — rows, rings, columns or waves of delay.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = 'Different parts of the frame show different moments in time — rows, rings, columns or waves of delay.'

PARAMS = [
    Param('pattern', 'select', 'rows (time warp)', 'Pattern', '', choices=['rows (time warp)', 'radial', 'columns', 'wavy']),
    Param('bands', 'int', 48, 'Bands', 'How many strips/rings the frame is cut into.', min=8, max=200),
    Param('depth', 'int', 48, 'Depth (frames)', 'How far back in time the oldest band reaches.', min=4, max=120),
]


def _slit_scan(bf, a):
    n, depth = a.bands, a.depth
    if a.pattern == "wavy":
        return bf.DelayMap(depth, n, bf.bands_rows(n), bf.wavy_delays(n, depth))
    band_fn = {"rows (time warp)": bf.bands_rows, "radial": bf.bands_radial, "columns": bf.bands_columns}[a.pattern](n)

    def spread(b, t):                   # band number → frames back, spread over the whole depth
        return (b * (depth - 1) // max(1, n - 1)).astype(int)
    return bf.DelayMap(depth, n, band_fn, spread)



def build(a):
    from videobeaux.utils import booth_filters as bf
    return _slit_scan(bf, a)


register_arguments, run, GUI_METADATA = make_program(DESCRIPTION, PARAMS, build)

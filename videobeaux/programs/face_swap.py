"""
Face Swap — swap two faces, copy the biggest face onto the others, or put a photo's face onto every face in the shot.

Faces are found with the bundled detector; each swap is aligned on the eyes / nose / mouth, colour-matched to the
skin it lands on and blended through a soft oval, so it follows head tilt and size instead of pasting a rectangle.

One of the photo-booth filters (see videobeaux/utils/booth_filters.py for the filter itself and
videobeaux/utils/booth_runner.py for the shared frame loop). Also reachable, with every other
booth filter and your own, through the Filter Library program.
"""
from videobeaux.utils.booth_runner import Param, make_program

DESCRIPTION = ('Swap two faces in the shot, copy the biggest face onto the others, or put a photo\'s face on everyone — '
               'aligned on the eyes and mouth and colour-matched to the skin.')

MODES = ["Swap two faces", "Biggest face onto the others", "Photo onto every face"]

PARAMS = [
    Param('mode', 'select', MODES[0], 'Mode',
          "Swap two faces needs two people in the same frame · Biggest face onto the others copies the largest face to every "
          "other face · Photo onto every face works with just one person (choose a Face photo).", choices=MODES),
    Param('photo', 'file', '', 'Face photo', 'A picture of a face (JPEG/PNG). Used by "Photo onto every face".',
          show_if={'mode': MODES[2]}),
    Param('softness', 'float', 0.06, 'Edge softness', 'How gently the pasted face blends into its surroundings.', min=0, max=0.3),
    Param('match', 'float', 0.85, 'Skin-tone match',
          '0 = keep the pasted face\'s own colours · 1 = fully recoloured to the skin it lands on.', min=0, max=1),
]


def build(a):
    from videobeaux.utils import booth_filters as bf
    return bf.make_face_swap(a.softness, a.mode, a.photo or None, a.match)


# detect on every frame and smooth lightly: a swap that lags or hops is much more obvious than a tag following a face
register_arguments, run, GUI_METADATA = make_program(
    DESCRIPTION, PARAMS, build, faces=True, eyes=False, tracker={'detect_every': 1, 'smoothing': 0.3})

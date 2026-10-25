# bad_predator: Amount slider + keep its length (APPLIED 2026-10-25)

Applied directly in `videobeaux/programs/bad_predator.py` (the user's own values — `tpad` 8, `amplify radius=8` — were kept):
the dry/wet **Amount** slider (`add_amount_argument` / `apply_amount`, default 1.0 = the original look), and the end padding
`tpad … stop=17` (was `stop=8`).

Why 17: `amplify=radius=8` needs a 17-frame window and drops 17 frames at the end of the stream, `trim=start_frame=8` drops the 8 padded
start frames, so the end must be padded by 17 for the output to have exactly the input's number of frames (measured: stop=8 → 24
frames in / 15 out, stop=16 → 23 out, stop=17 → 24 out, also 96 → 96).

# bad_predator: add the "Amount" slider (apply by hand in the real repo)

`videobeaux/programs/bad_predator.py` has your own newer edit in the real repo, so it was deliberately **not** changed in
`videobeaux-gui` (a sync would otherwise have overwritten it). Four small edits give it the same dry/wet Amount as the other
preset programs (default 1.0 = exactly today's output):

1. Under the existing import:
   ```python
   from videobeaux.utils.preset_filter import add_amount_argument, apply_amount, AMOUNT_METADATA

   GUI_METADATA = AMOUNT_METADATA
   ```
2. In `register_arguments`, replace the line `print("✅ This program mode does not require additional arguments")` with:
   ```python
       add_amount_argument(parser)
   ```
3. In `run`, directly after the closing `]` of `command = [ ... ]`, add:
   ```python
       command = apply_amount(command, getattr(args, "amount", 1.0))
   ```
4. Nothing else — the filter graph already ends in `[out_v]`, which is what `apply_amount` expects.

`videobeaux/utils/preset_filter.py` arrives with the normal `tools/sync-to-repo.sh` run. Until this patch is applied,
`tests/unit/test_preset_filter.py` still passes in the real repo because Bad Predator is on its allow-list.

## Also: keep its length on short clips (same family of fix as T-1000)
In your real-repo version the chain is `tpad=start=8…stop=8` → `amplify=radius=8` → `trim=start_frame=8`. `amplify` loses 8 frames at each
end and `trim` drops 8 more, so the output is **8 frames shorter than the input** (and gives no picture at all on a clip of
8 frames or fewer). Pad the end by 16 instead of 8 — change `stop=8` to `stop=16` — and it keeps every frame:

    "tpad=start=8:start_mode=clone:stop=16:stop_mode=clone,"

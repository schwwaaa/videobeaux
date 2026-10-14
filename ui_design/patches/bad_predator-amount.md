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

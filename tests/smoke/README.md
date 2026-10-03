# Smoke test

Runs every videobeaux program once against a short section of
`gui/Wil_Willis-OnTheJob_edit_0001.mp4` (8s at 6s in, downscaled to 640px wide),
validates the output, and writes a report grouped by GUI category.

```bash
source venv/bin/activate
python tests/smoke/run_smoke.py                  # everything (~1 min with --jobs 4)
python tests/smoke/run_smoke.py --jobs 4
python tests/smoke/run_smoke.py --category glitch
python tests/smoke/run_smoke.py --only pixel_sort,thumbs --keep   # keep outputs to eyeball
```

Reports land in `tests/smoke/reports/` (`latest.md`, `latest.json`, plus a timestamped copy).
Exit code is 1 if anything FAILs or TIMEOUTs; SKIPs don't count.

- **PASS** — exit 0 and the output exists and decodes (video/audio/image via ffprobe, JSON parses, directory outputs have files).
  This proves the program runs and produces valid output, not that the effect looks right — use `--keep` to look.
- **SKIP** — can't run here: needs network (`download_yt`) or an ffmpeg filter this build lacks
  (`zscale`→`tonemap_hdr_sdr`, `ass`→`captburn`), or needs OpenCV / a Vosk model / kokoro-tts that isn't installed.
- **Adding a program** — if it has required args, add an entry to `SPECS` in `run_smoke.py`
  (the runner prints a warning listing any program with required args and no entry).

Speech-dependent programs (`ngrams`, `grep_supercut`, `qwikchop_deluxe`, `silence_xtraction`, …) use the
transcript produced by the `transcraibe` test, which always runs first; if the clip has no speech they SKIP.

Face programs (`face_track`, `face_redact`, `face_follow`) also assert their "Faces detected in N/M frames"
summary is non-zero, so a run that silently finds no faces fails instead of passing.

Fast numpy-only unit tests for the dithering core live in `tests/unit/`:

```bash
python -m unittest discover -s tests/unit -v
```

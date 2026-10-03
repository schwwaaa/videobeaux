from __future__ import annotations
r"""
videobeaux.programs.qwikchop_deluxe - content-aware highlight extraction

Where qwikchop.py blindly slices a video into N equal time-pieces, this
picks WHICH moments to cut based on the transcript: it scores candidate
excerpts (built from the transcript's own sentence/pause boundaries) and
exports the highest-scoring ones — the same idea as "find the good bits"
tools like Opus Clip, done with fully local, no-network heuristics:

  - TextRank-style centrality: a candidate that shares distinctive
    vocabulary with the rest of the transcript scores higher than filler/
    repeated small talk — classic unsupervised extractive summarization
    (word-frequency similarity graph + PageRank), no model download.
  - Audio energy: louder/more dynamic segments score higher (a quick
    ffmpeg volumedetect pass per candidate).
  - Keyword hooks: a configurable word list nudges the score up.

This is a genuine local approximation, not a clone of a paid ML virality
model — it reliably surfaces distinctive, energetic, well-formed moments
and skips dead air/filler, but won't always match a trained model's (or a
human editor's) judgment. An optional, opt-in local Ollama pass can
re-rank the shortlist for smarter selection when a model is available —
skipped entirely, zero network calls, when --llm_model isn't set (same
pattern as auto_narrate's --topic).

Entry points expected by cli.py:
  * register_arguments(parser)
  * run(args)
"""
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests

from videobeaux.programs.captburn import _coerce_segments, _extract_words, _is_capton
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

OLLAMA_URL = "http://localhost:11434/api/chat"

_STOPWORDS = frozenset("""
a an the and or but if then so because as of at by for with about against
between into through during before after above below to from up down in
out on off over under again further once here there when where why how
all any both each few more most other some such no nor not only own same
than too very s t can will just don should now is are was were be been
being have has had do does did i you he she it we they me him her us
them my your his its our their this that these those
""".split())


def _ffprobe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", "ignore").strip()
    try:
        return float(out)
    except Exception:
        return 0.0


# =====================
# Candidate building
# =====================

def _build_candidates(
    segments: List[Dict[str, Any]], min_time: float, max_time: float
) -> List[List[Dict[str, Any]]]:
    """
    Turns the transcript's own sentence/pause segments into excerpt
    candidates, each a list of word dicts (text/start/end). Consecutive
    segments are greedily merged as long as the combined span stays within
    max_time (so a burst of short sentences becomes one candidate); a
    single segment that alone exceeds max_time (rare — a long run-on with
    no natural pause) is split by raw word count instead. A trailing
    candidate under min_time is merged forward into its neighbor when that
    still fits, rather than exporting a too-short throwaway clip.
    """
    seg_word_lists: List[List[Dict[str, Any]]] = []
    for seg in segments:
        words = _extract_words(seg)
        if not words:
            continue
        seg_dur = words[-1]["end"] - words[0]["start"]
        if seg_dur <= max_time:
            seg_word_lists.append(words)
        else:
            chunk: List[Dict[str, Any]] = []
            for w in words:
                if chunk and (w["end"] - chunk[0]["start"]) > max_time:
                    seg_word_lists.append(chunk)
                    chunk = []
                chunk.append(w)
            if chunk:
                seg_word_lists.append(chunk)

    if not seg_word_lists:
        return []

    candidates: List[List[Dict[str, Any]]] = []
    buf = seg_word_lists[0]
    for words in seg_word_lists[1:]:
        combined_dur = words[-1]["end"] - buf[0]["start"]
        if combined_dur <= max_time:
            buf = buf + words
        else:
            candidates.append(buf)
            buf = words
    candidates.append(buf)

    merged: List[List[Dict[str, Any]]] = []
    i = 0
    while i < len(candidates):
        cur = candidates[i]
        dur = cur[-1]["end"] - cur[0]["start"]
        if dur < min_time and i + 1 < len(candidates):
            nxt = candidates[i + 1]
            combined_dur = nxt[-1]["end"] - cur[0]["start"]
            if combined_dur <= max_time:
                candidates[i + 1] = cur + nxt
                i += 1
                continue
        merged.append(cur)
        i += 1
    return merged


# =====================
# Scoring
# =====================

def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if t not in _STOPWORDS and len(t) > 1]


def _centrality_scores(texts: List[str]) -> np.ndarray:
    """
    TextRank-style centrality: build a word-frequency vector per candidate,
    score similarity between every pair (cosine), then run PageRank power
    iteration over that similarity graph. A candidate that shares
    distinctive vocabulary with much of the rest of the transcript ends up
    central (summary-worthy); one-off filler doesn't. Pure numpy — no
    model, no network.
    """
    n = len(texts)
    if n == 0:
        return np.array([])
    if n == 1:
        return np.array([1.0])

    token_lists = [_tokenize(t) for t in texts]
    vocab: Dict[str, int] = {}
    for toks in token_lists:
        for t in toks:
            if t not in vocab:
                vocab[t] = len(vocab)

    if not vocab:
        return np.full(n, 1.0 / n)

    mat = np.zeros((n, len(vocab)), dtype=np.float64)
    for i, toks in enumerate(token_lists):
        for t in toks:
            mat[i, vocab[t]] += 1.0

    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit = mat / norms
    sim = unit @ unit.T
    np.fill_diagonal(sim, 0.0)
    sim[sim < 0] = 0.0

    row_sums = sim.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    trans = sim / row_sums

    damping = 0.85
    scores = np.full(n, 1.0 / n)
    for _ in range(50):
        new_scores = (1 - damping) / n + damping * (trans.T @ scores)
        if np.allclose(new_scores, scores, atol=1e-6):
            scores = new_scores
            break
        scores = new_scores

    return scores


def _measure_loudness_db(src: Path, start: float, dur: float) -> float:
    """Mean volume in dB for the given window (higher = louder). -91.0 (silence floor) on failure."""
    cmd = [
        "ffmpeg", "-ss", f"{start:.3f}", "-t", f"{max(0.05, dur):.3f}",
        "-i", str(src), "-af", "volumedetect", "-vn", "-f", "null", "-",
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        m = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", proc.stderr or "")
        return float(m.group(1)) if m else -91.0
    except Exception:
        return -91.0


def _hook_scores(texts: List[str], hook_words: List[str]) -> np.ndarray:
    hooks = {h.strip().lower() for h in hook_words if h.strip()}
    if not hooks:
        return np.zeros(len(texts))
    out = []
    for t in texts:
        toks = set(re.findall(r"[a-z0-9']+", t.lower()))
        out.append(float(len(toks & hooks)))
    return np.array(out, dtype=np.float64)


def _minmax(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return arr
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-9:
        return np.full_like(arr, 0.5)
    return (arr - lo) / (hi - lo)


# =====================
# Optional Ollama re-ranking
# =====================

def _ollama_rerank(candidates_text: List[str], count: int, model: str) -> Optional[List[int]]:
    """
    Hands the shortlisted candidates to a local Ollama model and asks it to
    pick the best `count` for a short-form highlight reel. Returns a list
    of 0-based indices (best first), or None on any failure — the caller
    falls back to the local score ranking rather than treating this as
    fatal, since this whole path is optional by design.
    """
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(candidates_text))
    prompt = f"""
Below are {len(candidates_text)} numbered excerpts from a video transcript.

{numbered}

Pick the {count} best excerpts for a short-form highlight reel — the most
interesting, distinctive, or attention-grabbing moments, in order from
best to worst.

Return ONLY a comma-separated list of the excerpt numbers, e.g. "4, 1, 7".
No other text.
"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
    except Exception as e:
        print(f"⚠️  Ollama re-ranking failed ({e}) — falling back to the local score ranking.")
        return None

    nums = [int(n) - 1 for n in re.findall(r"\d+", content)]
    valid = [n for n in nums if 0 <= n < len(candidates_text)]
    seen = set()
    ordered = []
    for n in valid:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered or None


# =====================
# Selection + export
# =====================

def _select(
    order: List[int],
    candidates: List[List[Dict[str, Any]]],
    count: int,
    target_duration: float,
    min_gap: float,
) -> List[int]:
    selected: List[int] = []
    total = 0.0
    accepted_ranges: List[Tuple[float, float]] = []
    rejected_close = 0
    rejected_budget = 0
    stop_reason = "exhausted every candidate"

    for idx in order:
        if count > 0 and len(selected) >= count:
            stop_reason = f"reached --count {count}"
            break
        words = candidates[idx]
        start, end = words[0]["start"], words[-1]["end"]

        too_close = any(
            (start < a_end + min_gap) and (end + min_gap > a_start)
            for a_start, a_end in accepted_ranges
        )
        if too_close:
            rejected_close += 1
            continue

        dur = end - start
        # Every candidate is checked against the budget uniformly — no
        # special-casing the first pick — so several smaller candidates can
        # accumulate toward target_duration instead of one large candidate
        # (candidates tend to run close to --max_time) silently consuming
        # the whole budget and ending selection right there regardless of
        # --count. The one legitimate reason to let a single overlong
        # candidate through is handled below, only if NOTHING else fit.
        if target_duration > 0 and total + dur > target_duration:
            rejected_budget += 1
            continue

        selected.append(idx)
        accepted_ranges.append((start, end))
        total += dur

        if target_duration > 0 and total >= target_duration:
            stop_reason = f"reached --target_duration {target_duration:.1f}s"
            break

    if not selected and order:
        # Degenerate case: every candidate individually exceeds
        # target_duration (or every candidate was rejected for some other
        # reason) — take the single best-scoring one anyway rather than
        # exporting nothing.
        selected.append(order[0])
        stop_reason = "no candidate fit target_duration alone — took the top-scoring one anyway"

    print(
        f"ℹ️  Selection: {len(order)} candidates → {rejected_close} rejected (too close to "
        f"an accepted pick), {rejected_budget} rejected (would overflow --target_duration) → "
        f"{len(selected)} selected. Stopped because: {stop_reason}."
    )
    if target_duration > 0 and rejected_budget > 0 and (count <= 0 or len(selected) < count):
        # The single most common cause of "why did I only get 1-2 highlights
        # despite a high --count": individual candidates run close to
        # --max_time, so only a couple fit inside --target_duration at all —
        # not a bug, but easy to not realize without this hint.
        print(
            f"ℹ️  Tip: {rejected_budget} candidate(s) would have overflowed the "
            f"{target_duration:.0f}s budget — they're close to --max_time in length. "
            f"Lower --max_time (so more, shorter clips fit) or raise/clear --target_duration "
            f"if you want closer to --count highlights."
        )

    return selected


def _export_clip(inp: Path, start: float, end: float, padding: float, dst: Path,
                  vcodec: str, crf: int, preset: str):
    s = max(0.0, start - padding)
    d = max(0.05, (end - start) + 2 * padding)
    cmd = [
        "ffmpeg",
        "-ss", f"{s:.6f}",
        "-t", f"{d:.6f}",
        "-i", str(inp),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", vcodec, "-preset", preset, "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(dst),
    ]
    run_ffmpeg_with_progress(cmd, str(inp), str(dst))


# =====================
# Program API
# =====================

GUI_METADATA = {
    'args': {
        'stt_model': {
            'type': 'file',
            'subtype': 'model',
            'label': 'Vosk Model',
            'help': 'Used to transcribe the video first, if no transcript for it exists yet.',
        },
        'llm_model': {
            'type': 'file',
            'subtype': 'ollama_model',
            'label': 'Ollama Model (optional)',
            'help': 'Optional local re-ranking of the shortlisted excerpts. Leave blank to use the local scoring only.',
        },
    }
}


def register_arguments(parser):
    parser.description = (
        "Content-aware highlight extraction: scores candidate excerpts built from the transcript's "
        "own sentence/pause boundaries (local TextRank-style centrality + audio energy + keyword "
        "hooks — no network, no ML model) and exports the best ones, each as its own file. Unlike "
        "qwikchop's blind equal-time slicing, this picks WHICH moments to cut based on content.\n"
        "Looks for a transcript JSON next to --input; if none exists, transcribes first using "
        "--stt_model."
    )
    parser.add_argument(
        "-t", "--trans_json", type=str, default=None,
        help="Transcript JSON to use (default: <input>.json)."
    )
    parser.add_argument(
        "--stt_model", required=True, type=str,
        help="Path to the Vosk model directory, used to transcribe --input if no transcript exists yet."
    )
    parser.add_argument(
        "--count", type=int, default=5,
        help="Number of excerpts to export. Default: 5."
    )
    parser.add_argument(
        "--target_duration", type=float, default=0.0,
        help="If set (>0), keep adding top-scoring excerpts (skipping any that would overflow) until "
             "this total duration is reached, instead of a fixed --count. --count still caps the count "
             "if both are set."
    )
    parser.add_argument(
        "--min_time", type=float, default=3.0,
        help="Shortest allowed excerpt, in seconds. Default: 3."
    )
    parser.add_argument(
        "--max_time", type=float, default=20.0,
        help="Longest allowed excerpt, in seconds. Default: 20."
    )
    parser.add_argument(
        "--min_gap", type=float, default=2.0,
        help="Minimum seconds of separation between selected excerpts, so picks don't cluster on the "
             "same moment. Default: 2."
    )
    parser.add_argument(
        "--padding", type=float, default=0.0,
        help="Seconds of padding added before and after each exported excerpt. Default: 0."
    )
    parser.add_argument(
        "--hook_words", type=str,
        default="secret,never,actually,literally,wow,insane,worst,best,amazing,shocking,unbelievable,crazy,honestly,wild",
        help="Comma-separated words that nudge an excerpt's score up when present. Default: a generic "
             "hook-word list — tune it for your content."
    )
    parser.add_argument(
        "--weight_centrality", type=float, default=0.5,
        help="Weight of the local TextRank-style centrality score, 0-1ish. Default: 0.5."
    )
    parser.add_argument(
        "--weight_energy", type=float, default=0.3,
        help="Weight of the audio-energy score, 0-1ish. Default: 0.3."
    )
    parser.add_argument(
        "--weight_hooks", type=float, default=0.2,
        help="Weight of the keyword-hook score, 0-1ish. Default: 0.2."
    )
    parser.add_argument(
        "--llm_model", type=str, default=None,
        help="Optional: a locally-pulled Ollama model name to re-rank the shortlisted excerpts for "
             "smarter selection. Leave unset to use the local scoring only — no network call is made "
             "unless this is set."
    )
    parser.add_argument(
        "--llm_candidates", type=int, default=15,
        help="How many top locally-scored candidates to hand to --llm_model for re-ranking. Default: 15."
    )
    parser.add_argument("--vcodec", default="libx264")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="veryfast")


def run(args):
    in_video = Path(args.input)
    if not in_video.exists():
        print(f"❌ Input not found: {in_video}")
        return

    trans_json = Path(args.trans_json) if getattr(args, "trans_json", None) else in_video.with_suffix(".json")
    if not trans_json.exists():
        print(f"ℹ️  No transcript found at {trans_json} — transcribing with Vosk first…")
        from videobeaux.programs.transcraibe import transcribe_single
        try:
            transcribe_single(
                input_video=in_video,
                model_path=Path(args.stt_model),
                json_path=trans_json,
                emit_txt=False,
                overwrite=False,
            )
        except Exception as e:
            print(f"❌ Could not produce a transcript for {in_video}: {e}")
            return
        if not trans_json.exists():
            print(f"❌ Transcription did not produce {trans_json}. Nothing to extract.")
            return

    import json
    with open(trans_json, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if _is_capton(raw):
        print(f"❌ {trans_json} is a captburn capton file, not a transcript. Point --trans_json at the original transcript instead.")
        return
    segments = _coerce_segments(raw)

    candidates = _build_candidates(segments, min_time=max(0.1, args.min_time), max_time=max(0.2, args.max_time))
    if not candidates:
        print("⚠️ No candidate excerpts could be built from the transcript. Nothing to extract.")
        return

    texts = [" ".join(w["text"] for w in words) for words in candidates]
    print(f"ℹ️  {len(candidates)} candidate excerpt(s) built from the transcript. Scoring…")

    centrality = _minmax(_centrality_scores(texts))

    print("ℹ️  Measuring audio energy per candidate…")
    loudness = np.array([
        _measure_loudness_db(in_video, words[0]["start"], words[-1]["end"] - words[0]["start"])
        for words in candidates
    ])
    energy = _minmax(loudness)

    hooks = _minmax(_hook_scores(texts, args.hook_words.split(",")))

    total_score = (
        args.weight_centrality * centrality
        + args.weight_energy * energy
        + args.weight_hooks * hooks
    )
    order = list(np.argsort(-total_score))

    if args.llm_model:
        top_k = order[:max(args.count, args.llm_candidates)]
        top_texts = [texts[i] for i in top_k]
        print(f"ℹ️  Re-ranking top {len(top_k)} candidates via Ollama ({args.llm_model})…")
        llm_order = _ollama_rerank(top_texts, args.count, args.llm_model)
        if llm_order:
            order = [top_k[i] for i in llm_order] + [i for i in order if i not in {top_k[j] for j in llm_order}]

    selected = _select(
        order, candidates,
        count=max(0, args.count),
        target_duration=max(0.0, args.target_duration),
        min_gap=max(0.0, args.min_gap),
    )
    if not selected:
        print("⚠️ No excerpts survived selection (try loosening --min_gap/--max_time). Nothing exported.")
        return

    selected.sort(key=lambda i: candidates[i][0]["start"])

    if args.output:
        export_dir = Path(args.output).with_suffix("")
    else:
        export_dir = in_video.parent / f"{in_video.stem}_qwikchop_deluxe"
    export_dir.mkdir(parents=True, exist_ok=True)
    if getattr(args, "force", False):
        for stale in export_dir.glob(f"{in_video.stem}_highlight_*"):
            stale.unlink(missing_ok=True)

    pad = max(2, len(str(len(selected))))
    for i, idx in enumerate(selected, start=1):
        words = candidates[idx]
        start, end = words[0]["start"], words[-1]["end"]
        dst = export_dir / f"{in_video.stem}_highlight_{i:0{pad}d}.mp4"
        print(f"🎬 [{i}/{len(selected)}] {start:.2f}s–{end:.2f}s (score {total_score[idx]:.3f}): {texts[idx][:80]!r}")
        _export_clip(in_video, start, end, args.padding, dst, args.vcodec, args.crf, args.preset)

    print(f"📦 Exported {len(selected)} highlight(s) → {export_dir}")

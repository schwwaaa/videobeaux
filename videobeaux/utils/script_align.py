"""
Time a known script with the words a recogniser heard.

Auto Narrate speaks a script the user wrote, then transcribes that audio with Vosk. Vosk mishears unusual words (names,
jargon), so its words are not the script's words. The script is known, so its own words can take the timing Vosk found
for the words that match them. This is a text alignment over the transcript that already exists: nothing is
transcribed again, so it adds almost no time next to the speech synthesis and transcription.
"""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

MATCH_FLOOR = 0.4      # a script word and a heard word must be at least this alike to share a timing
SUBSTITUTE_BIAS = 0.5  # a pair scores (similarity - bias), so dissimilar pairs cost more than they gain
SKIP_COST = 0.3        # leaving a word unpaired, on either side
WORDS_PER_SEGMENT = 12 # how many words go in each segment of the transcript written for the caption renderer


def _norm(word: str) -> str:
    return re.sub(r"\W", "", word.lower())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def pair_words(script_words: Sequence[str], heard_words: Sequence[str]) -> List[Tuple[int, int, float]]:
    """
    Pair script words with heard words, in order, so the total similarity is as high as it can be.
    Returns (script_index, heard_index, similarity) for each pair whose similarity reaches MATCH_FLOOR.
    """
    n, m = len(script_words), len(heard_words)
    sims = [[_similarity(a, b) for b in heard_words] for a in script_words]
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[0] * (m + 1) for _ in range(n + 1)]  # 0 = pair, 1 = skip script word, 2 = skip heard word
    for i in range(1, n + 1):
        score[i][0], back[i][0] = -SKIP_COST * i, 1
    for j in range(1, m + 1):
        score[0][j], back[0][j] = -SKIP_COST * j, 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            options = (
                (score[i - 1][j - 1] + sims[i - 1][j - 1] - SUBSTITUTE_BIAS, 0),
                (score[i - 1][j] - SKIP_COST, 1),
                (score[i][j - 1] - SKIP_COST, 2),
            )
            score[i][j], back[i][j] = max(options, key=lambda option: option[0])  # ties keep the earlier option: pairing

    pairs: List[Tuple[int, int, float]] = []
    i, j = n, m
    while i > 0 and j > 0:
        step = back[i][j]
        if step == 0:
            sim = sims[i - 1][j - 1]
            if sim >= MATCH_FLOOR:
                pairs.append((i - 1, j - 1, sim))
            i, j = i - 1, j - 1
        elif step == 1:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return pairs


def align_script(script: str, heard: Sequence[Dict[str, Any]], duration: Optional[float] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Return the script's words, in the script's order and spelling, each with a start and end in seconds, and how many of
    them took their timing from the heard words.

    heard: Vosk words, [{"word", "start", "end"}, ...].
    duration: length of the narration in seconds. Words after the last matched word are timed up to it.
    Words that were not heard are placed evenly between their matched neighbours, by length.
    """
    tokens = script.split()
    if not tokens:
        return [], 0

    heard_norm = [_norm(str(w.get("word", ""))) for w in heard]
    pairs = pair_words([_norm(t) for t in tokens], heard_norm)

    timed: List[Optional[Tuple[float, float]]] = [None] * len(tokens)
    for si, hi, _sim in pairs:
        timed[si] = (float(heard[hi]["start"]), float(heard[hi]["end"]))

    if duration is not None:
        end_of_audio = float(duration)
    elif heard:
        end_of_audio = float(heard[-1]["end"])
    else:
        end_of_audio = len(tokens) * 0.4

    i, prev_end = 0, 0.0
    while i < len(tokens):
        if timed[i] is not None:
            prev_end = timed[i][1]
            i += 1
            continue
        j = i
        while j < len(tokens) and timed[j] is None:
            j += 1
        next_start = timed[j][0] if j < len(tokens) else end_of_audio
        span_start, span_end = prev_end, max(prev_end, next_start)
        weights = [max(1, len(_norm(tokens[k]))) for k in range(i, j)]
        total, cursor = float(sum(weights)), span_start
        for k, w in zip(range(i, j), weights):
            length = (span_end - span_start) * w / total
            timed[k] = (cursor, cursor + length)
            cursor += length
        prev_end = span_end
        i = j

    words = [
        {"text": tok, "start": round(s, 3), "end": round(max(s, e), 3)}
        for tok, (s, e) in zip(tokens, timed)
    ]
    return words, len(pairs)


def to_transcript(words: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The same shape Vosk transcripts have (a list of segments with words), so the caption renderer reads it unchanged."""
    segments = []
    for k in range(0, len(words), WORDS_PER_SEGMENT):
        chunk = words[k:k + WORDS_PER_SEGMENT]
        segments.append({
            "content": " ".join(w["text"] for w in chunk),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
            "words": [{"word": w["text"], "start": w["start"], "end": w["end"]} for w in chunk],
        })
    return segments


def vosk_words(transcript_path: Path) -> List[Dict[str, Any]]:
    """All the words in a Vosk transcript JSON (a list of segments, each with its words)."""
    chunks = json.loads(Path(transcript_path).read_text(encoding="utf-8"))
    return [w for chunk in chunks for w in chunk.get("words", [])]

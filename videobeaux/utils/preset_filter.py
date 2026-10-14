"""
Dry/wet "Amount" for the single-filtergraph preset programs (Digital Boss, Fever, Double Cup, Steel Wash, ...).

Those programs build one fixed `-filter_complex` graph that ends in `[out_v]`. `apply_amount` keeps that graph exactly as it
is and mixes its result back with the untouched picture:

    <original graph, output renamed [fx]> ; [0:v]...[o] ; [fx]...[e] ; [e][o]blend=all_opacity=<amount>[out_v]

so Amount 1.0 (the default) returns the command *unchanged* — the program behaves exactly as it always did — and 0.0 is
the source picture. Nothing else in the command (audio mapping, codecs, output) is touched.
"""
from __future__ import annotations

from typing import List

# Merged into a program's GUI_METADATA so the node shows a labelled 0–1 slider.
AMOUNT_METADATA = {
    "args": {
        "amount": {
            "label": "Amount",
            "min": 0, "max": 1, "step": 0.05,
            "help": "How much of the effect is mixed in. 1 = the full effect (default); 0 = the original picture.",
        }
    }
}


def add_amount_argument(parser) -> None:
    parser.add_argument("--amount", type=float, default=1.0,
                        help="How much of the effect to mix in, 0–1 (default 1 = full effect).")


def _clamp(v) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 1.0


def apply_amount(command: List[str], amount) -> List[str]:
    """Return `command` with the video effect blended back with the original by `amount` (1.0 → unchanged)."""
    a = _clamp(amount)
    if a >= 0.999:
        return command
    cmd = list(command)
    mix = (";[0:v]format=yuv420p[vb_o];[fx]format=yuv420p[vb_e];"
           f"[vb_e][vb_o]blend=all_mode=normal:all_opacity={a:.3f}[out_v]")   # blend: 1st input = top layer

    if "-filter_complex" in cmd:
        i = cmd.index("-filter_complex")
        graph = str(cmd[i + 1]).rstrip()
        if not graph.endswith("[out_v]"):
            return command                      # unknown shape: leave the program alone rather than guess
        cmd[i + 1] = graph[: -len("[out_v]")] + "[fx]" + mix
        return cmd

    if "-vf" in cmd:                            # a plain filter chain → make it a graph so the original is reachable
        i = cmd.index("-vf")
        chain = str(cmd[i + 1]).strip()
        graph = f"[0:v]{chain}[fx]" + mix
        extra = [] if "-map" in cmd else ["-map", "[out_v]", "-map", "0:a?"]
        return cmd[:i] + ["-filter_complex", graph, *extra] + cmd[i + 2:]
    return command

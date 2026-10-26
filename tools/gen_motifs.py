#!/usr/bin/env python3
"""
Header motifs with a reason.

Every module's header pattern depicts the *mechanic* of that module (what it does to the picture), and a motif is only
ever used inside ONE category — so a pattern tells you the verb, the header colour tells you the category.

    python tools/gen_motifs.py

writes
  gui/src/renderer/src/looks/shared/motifs.css   the drawings as CSS custom properties + the selectors that apply them
  gui/src/renderer/src/looks/motif-data.js       module → motif map (read by the app and its tests)
  ui_design/pattern-map.md                       the reviewable table: module → motif → why
  ui_design/pattern-gallery.html                 the same, drawn (open it in a browser)

All drawings are original (squiggles, zig-zags, dots, plus signs, triangles, bricks — the Memphis vocabulary).
Tile = 64 x 32; two translucent marks (dark + light) so they sit on any header colour in light or dark mode.
"""
from __future__ import annotations

import json
import math
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W, H = 64, 32
D = "rgba(8,8,8,0.36)"        # dark marks
M = "rgba(8,8,8,0.18)"        # soft dark
L = "rgba(255,253,246,0.70)"  # light marks


# ── tiny drawing kit ──────────────────────────────────────────────────────────
def R(x, y, w, h, c, r=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c}"/>'


def RO(x, y, w, h, c, sw=2, r=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="{c}" stroke-width="{sw}"/>'


def C(x, y, r, c):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'


def CO(x, y, r, c, sw=2):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{c}" stroke-width="{sw}"/>'


def P(d, c, sw=2.2, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round"{da}/>')


def T(pts, c):
    return f'<polygon points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="{c}"/>'


def TX(x, y, s, size, c):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x}" y="{y}" font-family="Menlo,Consolas,monospace" font-weight="700" font-size="{size}" '
            f'fill="{c}">{s}</text>')


def wave(y, amp=3, step=8, c=D, sw=2.2, x0=0, x1=64):
    d = f"M{x0} {y}"
    x, up = x0, True
    while x < x1:
        d += f" q{step / 2} {-amp if up else amp} {step} 0"
        x += step
        up = not up
    return P(d, c, sw)


def lcg(seed):
    s = seed
    while True:
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


# ── motifs: id → (category, label, reason, [modules], drawing) ──────────────────
MOTIFS = []


def motif(mid, cat, label, reason, modules, body):
    MOTIFS.append(dict(id=mid, category=cat, label=label, reason=reason, modules=modules, body=body))


# GLITCH & CORRUPTION ─────────────────────────────────────────────────────────
motif("g_blocks", "glitch", "Broken pixel blocks", "These smash the picture into hard-edged blocks of corrupted colour.",
      ["digital_boss", "bad_contrast"],
      R(4, 4, 10, 5, D) + R(18, 11, 6, 3, L) + R(30, 3, 12, 6, D) + R(46, 10, 8, 3, L) + R(8, 21, 14, 3, L) +
      R(27, 24, 6, 5, D) + R(39, 18, 10, 5, D) + R(54, 23, 7, 6, L) + R(1, 14, 4, 4, D))
motif("g_rgb", "glitch", "Split red/green/blue", "They pull the colour channels apart so the picture fringes into offset R, G and B copies.",
      ["xrgb", "slight_smear", "chromatic_pulse"],
      CO(14, 15, 8, D, 2.4) + CO(21, 12, 8, L, 2.4) + CO(20, 20, 8, M, 2.4) + CO(48, 14, 5, D, 2) + CO(53, 12, 5, L, 2) + CO(51, 19, 5, M, 2))
motif("g_scan", "glitch", "Rolling scan-bands + static", "Tape / tube / weak-signal looks: horizontal scan-lines, tracking bands and static.",
      ["vhs_tracking", "vhs_camcorder", "crt_monitor", "weak_signal"],
      R(0, 4, 64, 3, M) + R(0, 12, 64, 3, D) + R(0, 20, 64, 3, M) + R(0, 27, 64, 2, D) +
      R(10, 11, 18, 5, L) + C(44, 9, 1, L) + C(52, 22, 1, L) + C(36, 25, 1, L) + C(58, 5, 1, D))
motif("g_tear", "glitch", "Torn offset slices", "The picture is cut into horizontal slices and the slices slide sideways.",
      ["glitch_tear", "splitting", "splitting_pro"],
      R(0, 4, 38, 5, D) + R(12, 11, 52, 5, L) + R(0, 18, 26, 5, D) + R(20, 25, 44, 4, L) + P("M40 2l4 6-4 6 4 6", D, 1.6))
motif("g_mosh", "glitch", "Smeared blocks", "Datamosh: one clip's blocks smear into the next one's motion.",
      ["crossmosh"],
      R(4, 8, 12, 16, D) + R(16, 10, 10, 5, M) + R(16, 17, 16, 5, M) + R(26, 12, 24, 4, L) + R(34, 19, 26, 4, M) + R(50, 8, 8, 8, D))
motif("g_sort", "glitch", "Sorted bars", "Pixels are sorted by brightness into rising streaks.",
      ["pixel_sort"],
      "".join(R(2 + 6 * i, 30 - (5 + 4 * i), 4, 5 + 4 * i, D if i % 2 else L) for i in range(10)))
motif("g_fry", "glitch", "Burnt speckle", "Everything is cooked until it crackles with burnt noise.",
      ["deep_fry"],
      "".join(C(round(3 + 61 * a), round(3 + 27 * b), 1.0 + 1.4 * c, D if i % 3 else L)
              for i, (a, b, c) in zip(range(26), zip(lcg(7), lcg(11), lcg(13)))))
motif("g_frames", "glitch", "Uneven film frames", "Frame timing is broken, so the film strip stutters unevenly.",
      ["bad_animation"],
      RO(2, 5, 10, 22, L, 2) + RO(15, 5, 16, 22, D, 2) + RO(34, 5, 8, 22, L, 2) + RO(45, 5, 12, 22, D, 2) + R(60, 5, 3, 22, M))
motif("g_diff", "glitch", "Ghost outline", "Frame-difference amplification: only what moved survives as a doubled outline.",
      ["twociz", "twociz_pro"],
      RO(8, 6, 22, 20, D, 2.4, 3) + RO(14, 10, 22, 20, L, 2.4, 3) + CO(50, 14, 7, D, 2.2) + CO(54, 18, 7, L, 2.2))
motif("g_pixblur", "glitch", "Blurred pixel squares", "Pixelation layered with a blur — squares that smear into each other.",
      ["blur_pix"],
      R(4, 6, 10, 10, D) + R(16, 6, 10, 10, M) + R(28, 6, 10, 10, L) + R(10, 18, 10, 10, M) + R(22, 18, 10, 10, D) + R(46, 10, 12, 12, M))
motif("g_warp", "glitch", "Bent lines", "Pixels are pushed along bending lines — a warped, flowing picture.",
      ["warp", "flow_warp"],
      P("M0 8 Q16 -2 32 8 T64 8", D, 2.4) + P("M0 16 Q16 6 32 16 T64 16", L, 2.4) + P("M0 24 Q16 14 32 24 T64 24", D, 2.4))

# TRAILS & ECHOES ────────────────────────────────────────────────────────────
motif("t_nest", "trails", "Nested receding frames", "The picture is fed back into itself, so frames recede inside frames.",
      ["feedback_loop", "key_feedback"],
      RO(3, 3, 58, 26, D, 2.2, 2) + RO(11, 8, 42, 16, L, 2.2, 2) + RO(20, 12, 24, 8, D, 2.2, 1) + R(29, 15, 6, 2, L))
motif("t_ghost", "trails", "Offset repeated outlines", "A delayed copy trails behind the live picture like an afterimage.",
      ["ghostee", "mirror_delay", "frame_delay_pro1", "frame_delay_pro2"],
      CO(10, 16, 7, D, 2.2) + CO(19, 16, 7, M, 2.2) + CO(28, 16, 7, L, 2.2) + T([(44, 24), (52, 24), (48, 10)], D) +
      T([(50, 26), (58, 26), (54, 12)], M))
motif("t_swirl", "trails", "Spiral swirl", "Feedback that spins and zooms into a hypnotic spiral.",
      ["lsd_feedback", "lsd_feedback_pro"],
      P("M32 16 c3-3 8-1 7 4 c-2 6-11 5-12-2 c-1-9 12-12 17-3 c5 10-6 18-16 15", D, 2.6) + P("M4 6 q8 6 16 0", L, 2) +
      P("M46 28 q8-6 16 0", L, 2))
motif("t_streak", "trails", "Dragged streaks", "Paint / light is dragged across the picture, leaving long streaks.",
      ["smudge", "repainting", "long_exposure"],
      P("M2 8H44", D, 4) + C(48, 8, 3, D) + P("M10 16H58", L, 4) + C(60, 16, 2.5, L) + P("M2 24H30", D, 4) + C(34, 24, 3, D))
motif("t_split", "trails", "Colour-offset echoes", "Three time-shifted copies, one per colour channel.",
      ["rgb_time_split"],
      RO(6, 4, 20, 20, D, 2.2, 2) + RO(14, 8, 20, 20, M, 2.2, 2) + RO(22, 12, 20, 18, L, 2.2, 2) + P("M48 6v20M54 6v20M60 6v20", D, 2))
motif("t_drip", "trails", "Drips", "A thick liquid look: colour that pools and drips.",
      ["double_cup", "t1000"],
      P("M6 0v14", D, 4) + C(6, 18, 4, D) + P("M20 0v8", L, 4) + C(20, 12, 3.5, L) + P("M34 0v18", D, 4) + C(34, 23, 4.5, D) +
      P("M48 0v10", L, 4) + C(48, 14, 3.5, L) + P("M58 0v6", D, 3) + C(58, 9, 3, D))
motif("t_wave", "trails", "Heat wobble", "A feverish shimmer: the picture wobbles like rising heat.",
      ["fever"],
      P("M6 0q5 4 0 8t0 8t0 8t0 8", D, 2.4) + P("M18 0q5 4 0 8t0 8t0 8t0 8", L, 2.4) + P("M30 0q5 4 0 8t0 8t0 8t0 8", D, 2.4) +
      P("M42 0q5 4 0 8t0 8t0 8t0 8", L, 2.4) + P("M54 0q5 4 0 8t0 8t0 8t0 8", D, 2.4))

# TIME & MOTION ──────────────────────────────────────────────────────────────
motif("m_speed", "temporal", "Speed lines", "They change how fast time runs: lines streaking past.",
      ["speed", "time_ramp"],
      P("M2 6H30", D, 2.6) + P("M12 12H52", L, 2.6) + P("M2 18H40", D, 2.6) + P("M18 24H60", L, 2.6) + T([(56, 7), (63, 12), (56, 17)], D))
motif("m_reverse", "temporal", "◄◄ chevrons", "Time runs backwards.",
      ["reverse"],
      P("M22 4L10 16l12 12", D, 3) + P("M40 4L28 16l12 12", L, 3) + P("M58 4L46 16l12 12", D, 3))
motif("m_boom", "temporal", "There-and-back arc", "Forward, then backward, again and again: a loop that returns.",
      ["boomerang", "looper_pro"],
      P("M6 26Q32 -8 58 26", D, 2.6) + T([(2, 22), (10, 24), (6, 30)], D) + T([(54, 30), (62, 22), (60, 30)], L))
motif("m_strobe", "temporal", "Flash bursts", "Hard flashes and held frames — a strobing light.",
      ["strobe_cut", "strobe_hold"],
      "".join(P(f"M{16 + 5 * math.cos(a):.1f} {16 + 5 * math.sin(a):.1f}L{16 + 13 * math.cos(a):.1f} {16 + 13 * math.sin(a):.1f}",
                D if k % 2 else L, 2.4) for k, a in enumerate([i * math.pi / 4 for i in range(8)])) +
      "".join(P(f"M{48 + 3 * math.cos(a):.1f} {16 + 3 * math.sin(a):.1f}L{48 + 9 * math.cos(a):.1f} {16 + 9 * math.sin(a):.1f}", L, 2)
              for a in [i * math.pi / 3 for i in range(6)]))
motif("m_freeze", "temporal", "Snowflake", "The picture is frozen solid.",
      ["freeze_frame", "freeze_punch"],
      P("M16 4V28M5 10L27 22M27 10L5 22", D, 2.4) + P("M12 7l4 3 4-3M12 25l4-3 4 3", D, 1.8) +
      P("M48 8V24M41 12L55 20M55 12L41 20", L, 2.2) + CO(48, 16, 9, M, 1.4))
motif("m_stutter", "temporal", "Stepped repeats", "A frame is repeated in steps — a stuttering stair.",
      ["stutter_pro", "nostalgic_stutter", "overexposed_stutter"],
      R(2, 20, 10, 8, D) + R(14, 20, 10, 8, D) + R(14, 12, 10, 8, L) + R(26, 12, 10, 8, L) + R(26, 4, 10, 8, D) + R(38, 4, 10, 8, D) +
      R(50, 20, 10, 8, M))
motif("m_interp", "temporal", "In-between dots", "New frames are invented between the real ones.",
      ["frame_interpolate"],
      C(6, 16, 4.5, D) + CO(18, 16, 3.5, D, 1.8) + C(30, 16, 4.5, D) + CO(42, 16, 3.5, D, 1.8) + C(54, 16, 4.5, D) + P("M10 26h44", L, 1.6, "2 3"))
motif("m_scroll", "temporal", "Rolling bands", "The picture scrolls / rolls like a broken vertical hold.",
      ["scrolling_pro", "broken_scroll"],
      T([(0, 6), (26, 6), (22, 12), (-4, 12)], D) + T([(20, 16), (52, 16), (48, 22), (16, 22)], L) + T([(40, 4), (64, 4), (64, 9), (36, 9)], M) +
      T([(6, 26), (30, 26), (28, 30), (4, 30)], D))
motif("m_slit", "temporal", "Stretched stripes", "Slit-scan: one thin slice of every frame is stretched across time.",
      ["slit_scan"],
      "".join(R(2 + 4 * i, 0, 1 + (i % 3), 32, D if i % 2 else L) for i in range(16)) + R(0, 14, 64, 4, M))
motif("m_tunnel", "temporal", "Tunnel rings", "The picture is bent into rings, as if seen from inside a tunnel / on a small planet.",
      ["tunnel", "little_planet"],
      CO(32, 16, 3, D, 2) + CO(32, 16, 7, L, 2) + CO(32, 16, 12, D, 2) + CO(32, 16, 18, L, 2) + CO(32, 16, 25, D, 2))

# COLOR & LOOK ───────────────────────────────────────────────────────────────
motif("l_dots", "look", "Halftone dots", "The picture becomes a grid of dots whose size follows brightness.",
      ["halftone", "led_wall", "pixelate"],
      "".join(C(4 + 8 * i, 4 + 8 * j, 0.8 + 2.0 * (i / 7), D if (i + j) % 2 == 0 else L) for i in range(8) for j in range(4)))
motif("l_checker", "look", "Dither checker", "Few colours, mixed with checker patterns to fake the in-betweens.",
      ["dither", "retro_dither", "ordered_dither"],
      "".join(R(4 + 8 * i, 2 + 8 * j, 8, 8, D if (i + j) % 2 == 0 else "rgba(0,0,0,0)") for i in range(8) for j in range(4)) +
      "".join(R(4 + 8 * i, 2 + 8 * j, 4, 4, L) for i in range(8) for j in range(4) if (i + j) % 2 == 1))
motif("l_ascii", "look", "Text characters", "The picture is rebuilt out of typed characters.",
      ["ascii_art"],
      TX(2, 12, "@#%&@#", 10, D) + TX(8, 24, "&*+=:.", 10, L) + TX(38, 12, "%&@", 10, L) + TX(34, 28, "#@*", 10, D))
motif("l_steps", "look", "Tone steps", "Colours are flattened into a few distinct steps.",
      ["posterize", "duotone", "kmeans_palette"],
      R(0, 0, 13, 32, "rgba(8,8,8,0.10)") + R(13, 0, 13, 32, "rgba(8,8,8,0.22)") + R(26, 0, 13, 32, "rgba(8,8,8,0.34)") +
      R(39, 0, 13, 32, "rgba(8,8,8,0.46)") + R(52, 0, 12, 32, "rgba(8,8,8,0.58)") + P("M0 16H64", L, 2))
motif("l_edge", "look", "Outline glow", "Only the edges of things are drawn, glowing.",
      ["neon_edges", "emboss"],
      RO(6, 6, 24, 20, L, 5, 6) + RO(6, 6, 24, 20, D, 1.6, 6) + P("M40 24 L48 8 L56 24 Z", L, 5) + P("M40 24 L48 8 L56 24 Z", D, 1.6))
motif("l_blueprint", "look", "Blueprint grid", "White line-work on a drafting grid.",
      ["blueprint"],
      P("M0 8H64M0 16H64M0 24H64M10 0V32M22 0V32M34 0V32M46 0V32M58 0V32", M, 1) + RO(12, 6, 20, 14, L, 2.2) + P("M44 24L58 10", D, 2.2) +
      CO(44, 24, 2.5, D, 1.6))
motif("l_hatch", "look", "Pen hatching", "The picture is redrawn with pen strokes and hatching.",
      ["sketch", "ball_point_pen"],
      "".join(P(f"M{x} 26l8-20", D, 1.8) for x in (2, 7, 12, 17)) + "".join(P(f"M{x} 26l8-20", L, 1.8) for x in (30, 35, 40, 45)) +
      P("M52 24l10-6M52 18l10-6M52 12l10-6", D, 1.8))
motif("l_rays", "look", "Sun rays", "Light blooms and colour is pushed warm, like sunshine on film.",
      ["xpiritualism", "lomo", "wbflare", "wbflare_pro"],
      "".join(P(f"M32 34L{x} 0", L, 2) for x in (2, 12, 22, 32, 42, 52, 62)) + C(10, 8, 2, D) + C(54, 10, 2, D) + C(32, 22, 3, D))
motif("l_bloom", "look", "Bloom", "A dramatic bloom around everything bright.",
      ["recalled_sensor", "recalled_sensor_pro"],
      C(20, 16, 5, L) + CO(20, 16, 10, L, 3) + CO(20, 16, 15, D, 1.6) + C(46, 10, 3, L) + CO(46, 10, 7, D, 1.6) + C(54, 24, 2, D))
motif("l_bw", "look", "Split light / dark", "Brightness is inverted, drained or toned.",
      ["black_white", "negative", "solarize", "sepia"],
      T([(0, 32), (0, 0), (32, 0)], D) + T([(64, 0), (64, 32), (32, 32)], L) + CO(32, 16, 8, D, 2.2) + P("M32 8V24", L, 2.2))
motif("l_heat", "look", "Heat blobs", "A heat-map: colour mapped to temperature or light level.",
      ["thermal", "infrared", "night_vision"],
      '<ellipse cx="20" cy="16" rx="16" ry="12" fill="rgba(8,8,8,0.14)"/><ellipse cx="20" cy="16" rx="10" ry="7" fill="rgba(8,8,8,0.24)"/>'
      '<ellipse cx="20" cy="16" rx="4" ry="3" fill="rgba(255,253,246,0.7)"/><ellipse cx="50" cy="10" rx="9" ry="6" fill="rgba(8,8,8,0.2)"/>'
      '<ellipse cx="50" cy="10" rx="4" ry="2.5" fill="rgba(255,253,246,0.7)"/>')
motif("l_paint", "look", "Brush strokes", "The picture is repainted: cartoon outlines and oil strokes.",
      ["oil_paint", "cartoon"],
      P("M4 24L22 6", D, 5) + P("M16 28L38 8", L, 5) + P("M30 26L50 10", D, 5) + P("M44 26L62 12", L, 5))
motif("l_film", "look", "Film scratches", "Old film: dust, scratches and snow.",
      ["old_film_damage", "light_snow", "zapruder"],
      P("M8 0V32M25 0V32M43 0V32", L, 1.2) + P("M52 0q-4 14 2 32", D, 1.4) + C(14, 9, 1.6, D) + C(33, 20, 1.2, D) + C(58, 8, 1.6, L) +
      C(20, 26, 1.2, L) + P("M32 4l3 2", D, 1.6))
motif("l_wash", "look", "Colour wash", "A single colour treatment washed over the whole picture.",
      ["steel_wash", "pickle_juice", "septic", "bad_predator", "soapblind", "rb_blur", "rb_blur_pro"],
      P("M0 6Q16 0 32 6T64 6", "rgba(8,8,8,0.22)", 7) + P("M0 16Q16 10 32 16T64 16", L, 7) + P("M0 26Q16 20 32 26T64 26", "rgba(8,8,8,0.22)", 7))
motif("l_sliders", "look", "Sliders", "Plain tone / colour controls.",
      ["proc_amp", "gamma_fix", "lut_apply", "color_pass", "hue_cycle"],
      P("M4 7H60M4 16H60M4 25H60", D, 1.8) + C(18, 7, 3.4, L) + C(40, 16, 3.4, L) + C(28, 25, 3.4, L) + CO(18, 7, 3.4, D, 1.2) + CO(40, 16, 3.4, D, 1.2) + CO(28, 25, 3.4, D, 1.2))
motif("l_pop", "look", "Pop-art dots", "Bold comic printing: big dots and a thick bolt.",
      ["pop_art", "photobooth"],
      "".join(C(6 + 12 * i, 8 + 16 * (j % 2) + (6 if i % 2 else 0), 3.2, D) for i in range(5) for j in range(2) if (i + j) % 2 == 0) +
      P("M42 4l-6 12h8l-6 12", L, 3.4) + C(56, 24, 3.2, D))
motif("l_topo", "look", "Contour lines", "Slices the picture into tonal bands like a topographic map.",
      ["topobeaux"],
      P("M4 20q8-14 20-8t20-4 16 8", D, 1.8) + P("M4 26q8-12 20-6t20-4 16 6", L, 1.8) + P("M8 14q8-10 16-4t18-2", D, 1.8) +
      P("M14 8q6-5 12-2", L, 1.8))
motif("l_matrix", "look", "Cell grid", "A matrix of cells, each showing a different treatment.",
      ["beauxtrix"],
      "".join(RO(4 + 15 * i, 3 + 15 * j, 12, 12, D if (i + j) % 2 == 0 else L, 2, 2) for i in range(4) for j in range(2)) +
      R(21, 5, 8, 8, D, 1))

# VISION & TRACKING ──────────────────────────────────────────────────────────
motif("v_reticle", "vision", "Reticle", "They find a face and lock a target on it.",
      ["face_track", "face_follow"],
      CO(16, 16, 8, D, 2) + P("M16 3V10M16 22V29M3 16H10M22 16H29", D, 2) + CO(46, 16, 4, L, 2) + P("M34 16H42M50 16H62", L, 1.6, "2 3"))
motif("v_redact", "vision", "Blocked-out bars", "A face is covered with a bar or pixel block.",
      ["face_redact"],
      R(4, 10, 24, 8, D, 1) + R(34, 6, 10, 10, D) + R(46, 6, 10, 10, M) + R(34, 18, 10, 10, M) + R(46, 18, 10, 10, D))
motif("v_trail", "vision", "Dotted track path", "Moving points leave a trail behind them.",
      ["motion_ghost", "feature_trails"],
      C(6, 24, 1.8, D) + C(14, 20, 2.2, D) + C(24, 17, 2.8, D) + C(36, 12, 3.4, D) + C(50, 8, 4.2, D) + P("M4 28L58 10", L, 1.4, "2 3"))
motif("v_swap", "vision", "Overlapping faces", "Two faces trade places.",
      ["face_swap"],
      '<ellipse cx="22" cy="16" rx="10" ry="13" fill="none" stroke="' + D + '" stroke-width="2.4"/>'
      '<ellipse cx="38" cy="16" rx="10" ry="13" fill="none" stroke="' + L + '" stroke-width="2.4"/>' +
      P("M10 6l-6 0M54 26l6 0", D, 2) + T([(54, 6), (60, 10), (54, 14)], L))
motif("v_warp", "vision", "Pinched oval", "A face that is stretched, pinched and bulged.",
      ["face_warp"],
      P("M32 2C14 2 14 30 32 30C50 30 50 2 32 2", D, 2.4) + P("M18 12C26 8 38 8 46 12", L, 2) + P("M20 22C28 26 36 26 44 22", L, 2) +
      C(26, 16, 1.6, D) + C(38, 16, 1.6, D))

# LAYOUT & OVERLAY ───────────────────────────────────────────────────────────
motif("y_stamp", "layout", "Corner badge", "Stamps a logo / badge onto the corner of the picture.",
      ["watermark"],
      RO(3, 3, 58, 26, M, 1.6, 2) + R(40, 18, 18, 8, D, 2) + P("M44 22H54", L, 2) + C(10, 10, 2.5, L))
motif("y_cutout", "layout", "Cut-out silhouette", "Cuts a subject out of its background.",
      ["remove_background"],
      C(20, 11, 6, D) + P("M8 30q12-18 24 0", D, 2.6) + P("M2 4H62M2 30H62", L, 1.4, "3 3") + R(44, 8, 14, 14, L, 2))
motif("y_key", "layout", "Key squares", "Makes one colour (or brightness) transparent.",
      ["chroma_key", "luma_key"],
      R(4, 4, 14, 12, D) + R(18, 16, 14, 12, D) + RO(32, 4, 14, 12, L, 2) + RO(46, 16, 14, 12, L, 2) + R(4, 18, 6, 6, L) + R(52, 6, 6, 6, M))
motif("y_stack", "layout", "Stacked tiles", "Puts several videos side by side or on top of each other.",
      ["stack_2x", "triptych", "quad_split", "video_wall"],
      RO(3, 3, 27, 12, D, 2) + RO(34, 3, 27, 12, L, 2) + RO(3, 18, 27, 11, L, 2) + RO(34, 18, 27, 11, D, 2))
motif("y_layers", "layout", "Overlapping layers", "Layers of picture blended through each other.",
      ["lagkage", "layer_blend", "stackadelic"],
      R(4, 4, 28, 18, D, 2) + R(16, 10, 28, 18, L, 2) + RO(30, 6, 28, 18, D, 2.2, 2))
motif("y_pip", "layout", "Frame in frame", "A small picture inside the big one.",
      ["picture_in_picture"],
      RO(3, 3, 58, 26, D, 2.2, 2) + R(34, 14, 22, 12, L, 2) + RO(34, 14, 22, 12, D, 1.6, 2))
motif("y_rotate", "layout", "Tilted frame", "Turns the whole picture: a frame tilted on its corner with a turning arrow.",
      ["rotate"],
      '<g transform="rotate(32 20 16)">' + RO(10, 7, 20, 18, D, 2.4, 2) + '</g>' + P("M44 24a10 10 0 1 1 10-12", L, 2.6) +
      T([(50, 6), (60, 10), (52, 16)], L) + RO(2, 2, 60, 28, M, 1.2, 2))
motif("y_shapes", "layout", "Circle · triangle · square", "Generates basic shapes to build the picture from.",
      ["shape_synth"],
      CO(12, 16, 8, D, 2.4) + T([(26, 26), (40, 26), (33, 6)], L) + RO(46, 8, 14, 16, D, 2.4, 1))

# CUT & ASSEMBLE ─────────────────────────────────────────────────────────────
motif("e_trim", "edit", "Trim brackets", "Keeps a section of the clip between two handles.",
      ["trim"],
      R(2, 12, 60, 8, M) + R(14, 12, 36, 8, L) + P("M14 4V28M50 4V28", D, 3.4) + P("M14 4h5M50 4h-5M14 28h5M50 28h-5", D, 3))
motif("e_chop", "edit", "Chopped segments", "Chops a clip into pieces.",
      ["qwikchop", "mince"],
      R(2, 10, 8, 12, D) + R(14, 10, 12, 12, L) + R(30, 10, 6, 12, D) + R(40, 10, 14, 12, L) + R(58, 10, 4, 12, D) + P("M12 4V28M28 4V28M38 4V28M56 4V28", D, 1.4, "2 2"))
motif("e_join", "edit", "Joined blocks", "Sticks clips together end to end.",
      ["concat", "insert_clip"],
      R(2, 9, 18, 14, D, 2) + R(24, 9, 18, 14, L, 2) + R(46, 9, 16, 14, D, 2) + P("M20 16h4M42 16h4", D, 3.6))
motif("e_wipe", "edit", "Diagonal wipe", "One picture is wiped away by another.",
      ["wipe_transitions", "fade_flash"],
      T([(0, 0), (40, 0), (24, 32), (0, 32)], D) + T([(44, 0), (64, 0), (64, 32), (28, 32)], L) + P("M42 0L26 32", M, 3))
motif("e_note", "edit", "Music notes", "Lays a music track under the picture.",
      ["soundtrack"],
      C(14, 24, 4, D) + P("M18 24V6l14-3v17", D, 2.4) + C(28, 20, 4, D) + C(46, 22, 3.4, L) + P("M49 22V10l9-2v12", L, 2.2) + C(56, 18, 3.4, L))

# SPEECH & CAPTIONS ──────────────────────────────────────────────────────────
motif("s_words", "speech", "Lines of words", "Turns what is said into lines of text.",
      ["transcraibe"],
      R(4, 5, 40, 3, D, 1.5) + R(4, 12, 54, 3, L, 1.5) + R(4, 19, 30, 3, D, 1.5) + R(38, 19, 18, 3, L, 1.5) + R(4, 26, 46, 3, D, 1.5))
motif("s_kinetic", "speech", "Bouncing letters", "Letters that move and bounce with the speech.",
      ["captburn"],
      TX(3, 20, "A", 16, D) + TX(18, 14, "B", 16, L) + TX(33, 24, "C", 16, D) + TX(48, 16, "!", 16, L))
motif("s_voice", "speech", "Voice rings", "Creates a spoken voice.",
      ["auto_narrate"],
      R(6, 11, 4, 10, D, 2) + P("M14 8q4 8 0 16", L, 2.4) + P("M20 4q8 12 0 24", D, 2.4) + P("M26 0q12 16 0 32", L, 2.4) +
      P("M46 10v12M52 6v20M58 12v8", D, 2.6))
motif("s_search", "speech", "Magnifier ticks", "Finds words and phrases and pulls them out.",
      ["grep_supercut", "ngrams"],
      CO(18, 14, 8, D, 2.6) + P("M24 20L32 28", D, 3.4) + R(40, 6, 20, 3, L, 1.5) + R(40, 14, 14, 3, L, 1.5) + R(40, 22, 18, 3, L, 1.5))
motif("s_cut", "speech", "Waveform with gaps", "Cuts silences and picks out the spoken parts of the sound.",
      ["silence_xtraction", "word_xtraction_vad", "qwikchop_deluxe"],
      "".join(R(3 + 5 * i, 16 - h / 2, 3, h, D if i % 3 else L, 1.5) for i, h in enumerate([6, 14, 22, 10, 4, 2, 2, 18, 24, 12, 4, 2]) ) +
      P("M34 3V29", L, 1.6, "2 3"))

# MEDIA TOOLS ────────────────────────────────────────────────────────────────
motif("c_convert", "media", "Swap arrows", "Changes one format into another.",
      ["convert_mux", "subs_convert"],
      P("M4 10H48", D, 3) + T([(46, 4), (60, 10), (46, 16)], D) + P("M60 22H16", L, 3) + T([(18, 16), (4, 22), (18, 28)], L))
motif("c_resize", "media", "Size marks", "Changes the picture's dimensions.",
      ["convert_dims", "resize", "shortify"],
      RO(4, 4, 24, 24, M, 1.6) + P("M10 22V10H22", D, 2.6) + P("M36 24L58 6", D, 2.4) + T([(52, 4), (60, 4), (60, 12)], D) + T([(34, 18), (34, 26), (42, 26)], D))
motif("c_hdr", "media", "Sun to moon steps", "Squeezes bright HDR light down into ordinary screens.",
      ["tonemap_hdr_sdr"],
      C(14, 16, 7, L) + P("M14 3V6M14 26V29M1 16H4M24 16H27M5 7l2 2M23 25l2 2M23 7l-2 2M5 25l2-2", L, 2) +
      P("M34 16H46", D, 2.6) + T([(44, 10), (54, 16), (44, 22)], D) + P("M58 8a8 8 0 1 0 0 16a6 6 0 1 1 0-16", D, 2.2))
motif("c_frames", "media", "Film-strip squares", "Pulls individual frames out of a video.",
      ["extract_frames", "thumbs"],
      RO(2, 5, 14, 22, D, 2, 1) + RO(18, 5, 14, 22, L, 2, 1) + RO(34, 5, 14, 22, D, 2, 1) + RO(50, 5, 12, 22, L, 2, 1) + "".join(R(x, 1, 3, 3, D) for x in (4, 20, 36, 52)))
motif("c_sound", "media", "Waveform", "Pulls the sound out of the video.",
      ["extract_sound"],
      "".join(R(3 + 4.2 * i, 16 - h / 2, 2.6, h, D if i % 2 else L, 1.3) for i, h in enumerate([4, 8, 14, 22, 12, 6, 18, 26, 14, 8, 20, 10, 4, 12, 6])))
motif("c_info", "media", "Table rows", "Reads facts about a file and reports them.",
      ["media_info", "meta_extraction", "hash_fingerprint"],
      R(4, 4, 56, 24, "none", 2).replace('fill="none"', f'fill="none" stroke="{D}" stroke-width="1.8"') +
      P("M4 12H60M4 20H60M24 4V28", D, 1.6) + R(8, 6, 12, 4, L, 1) + R(28, 14, 24, 4, L, 1) + R(28, 22, 16, 4, L, 1))
motif("c_stab", "media", "Steadied line", "Smooths shaky motion into a steady path.",
      ["stabilize"],
      P("M2 20l4-10 4 12 4-12 4 10 4-8 4 6", D, 1.8) + P("M34 16H62", L, 3) + T([(58, 11), (63, 16), (58, 21)], L) + P("M4 28H30", M, 1.6, "2 3"))

CATEGORY_MOTIF = {   # the pattern on a category's chip in the sidebar
    "glitch": "g_blocks", "trails": "t_nest", "temporal": "m_speed", "look": "l_dots", "vision": "v_reticle",
    "layout": "y_stack", "edit": "e_trim", "speech": "s_words", "media": "c_convert",
}
CATEGORY_LABEL = {"glitch": "Glitch & Corruption", "trails": "Trails & Echoes", "temporal": "Time & Motion", "look": "Color & Look",
                  "vision": "Vision & Tracking", "layout": "Layout & Overlay", "edit": "Cut & Assemble", "speech": "Speech & Captions",
                  "media": "Media Tools"}
CATEGORY_COLOR = {"glitch": "#d52c91", "trails": "#ff9f1c", "temporal": "#ff6847", "look": "#8654aa", "vision": "#2ec4b6",
                  "layout": "#32b9df", "edit": "#c5d92d", "speech": "#ffe500", "media": "#a8ad23"}


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{body}</svg>'


def data_uri(body):
    return "data:image/svg+xml," + urllib.parse.quote(svg(body), safe="/:=,()' ")


def validate():
    seen = {}
    ids = set()
    for m in MOTIFS:
        assert m["id"] not in ids, f"duplicate motif {m['id']}"
        ids.add(m["id"])
        for prog in m["modules"]:
            assert prog not in seen, f"{prog} has two motifs ({seen[prog]}, {m['id']})"
            seen[prog] = m["id"]
        assert m["category"] in CATEGORY_MOTIF, m["category"]
    for cat, mid in CATEGORY_MOTIF.items():
        owner = next(m for m in MOTIFS if m["id"] == mid)
        assert owner["category"] == cat, f"category chip motif {mid} belongs to {owner['category']}"
    return seen


def build_css():
    out = ["/* GENERATED by tools/gen_motifs.py — do not edit by hand. Original drawings; scoped to the non-Classic looks. */",
           ":root[data-look] {"]
    for m in MOTIFS:
        out.append(f'  --mot-{m["id"]}: url("{data_uri(m["body"])}");')
    out.append("}")
    looks = ['patterns', 'motifs', 'signatures', 'output-art']
    sel = lambda tail: ",\n".join(f':root[data-look="{l}"] {tail}' for l in looks if l != 'patterns')   # v1 "patterns" keeps family tiles
    for m in MOTIFS:
        out.append(sel(f'[data-motif="{m["id"]}"]') + f" {{ --pat: var(--mot-{m['id']}); }}")
    out.append(sel(".node-header[data-motif]") + """ {
  background-image: var(--pat);
  background-size: 64px 32px;
  background-position: 0 0;
}""")
    out.append(sel(".cat-chip[data-motif]") + """ {
  background-image: linear-gradient(90deg, var(--node-color) 0 60%, transparent 92%), var(--pat);
  background-size: 100% 100%, 64px 32px;
}""")
    out.append(sel(".prog-dot[data-motif]") + """ {
  width: 20px !important; height: 13px !important; border-radius: 3px !important;
  background-image: var(--pat); background-size: 32px 16px;
}""")
    return "\n".join(out) + "\n"


def build_data(seen):
    data = {
        "motifs": {m["id"]: {"category": m["category"], "label": m["label"], "reason": m["reason"]} for m in MOTIFS},
        "programs": seen,
        "categories": CATEGORY_MOTIF,
    }
    return ("// GENERATED by tools/gen_motifs.py — module → motif map (edit the table in that script, then regenerate).\n"
            "export default " + json.dumps(data, indent=1, sort_keys=True) + "\n")


def build_markdown(seen):
    md = ["# Header motifs — module → pattern → why", "",
          "Generated by `tools/gen_motifs.py`. **Rule:** a pattern depicts the *mechanic* of the module, and a motif is only ever "
          "used inside one category (the header colour tells you the category, the pattern tells you the verb).", ""]
    for cat, label in CATEGORY_LABEL.items():
        ms = [m for m in MOTIFS if m["category"] == cat]
        md += [f"## {label} — {CATEGORY_COLOR[cat]}", "", "| Pattern | Modules | Why this pattern |", "|---|---|---|"]
        for m in ms:
            md.append(f"| `{m['id']}` {m['label']} | {', '.join(m['modules'])} | {m['reason']} |")
        md.append("")
    return "\n".join(md)


def build_gallery():
    rows = []
    for cat, label in CATEGORY_LABEL.items():
        rows.append(f'<h2>{label} <small>{CATEGORY_COLOR[cat]}</small></h2><div class="grid">')
        for m in [m for m in MOTIFS if m["category"] == cat]:
            for prog in m["modules"]:
                rows.append(
                    f'<div class="card"><div class="hd" style="background-color:{CATEGORY_COLOR[cat]};background-image:url(&quot;{data_uri(m["body"])}&quot;)">'
                    f'<span style="background:{CATEGORY_COLOR[cat]}">{prog.replace("_", " ").upper()}</span></div>'
                    f'<p><b>{m["label"]}</b><br>{m["reason"]}</p></div>')
        rows.append("</div>")
    return ("<!doctype html><meta charset=utf-8><title>Videobeaux header motifs</title><style>"
            "body{font:14px 'Atkinson Hyperlegible',Arial,sans-serif;background:#fffdf6;color:#080808;margin:24px}"
            "h1{font:900 22px Impact,sans-serif}h2{margin:26px 0 8px}h2 small{font:12px monospace;color:#6a6a62}"
            ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}"
            ".card{border:3px solid #080808;border-radius:12px;overflow:hidden;box-shadow:4px 4px 0 #080808;background:#fffdf6}"
            ".hd{height:36px;border-bottom:3px solid #080808;background-size:64px 32px;display:flex;align-items:center;padding:0 10px}"
            ".hd span{font:700 11px 'IBM Plex Mono',monospace;letter-spacing:.07em;padding:1px 7px;border-radius:6px}"
            ".card p{margin:0;padding:8px 10px;font-size:12px;color:#444}"
            "</style><h1>Header motifs — module → pattern → why</h1>"
            "<p>One pattern = one mechanic, never shared across categories.</p>" + "".join(rows))


def main():
    seen = validate()
    look = ROOT / "gui/src/renderer/src/looks"
    (look / "shared").mkdir(parents=True, exist_ok=True)
    (look / "shared/motifs.css").write_text(build_css(), encoding="utf-8")
    (look / "motif-data.js").write_text(build_data(seen), encoding="utf-8")
    (ROOT / "ui_design/pattern-map.md").write_text(build_markdown(seen), encoding="utf-8")
    (ROOT / "ui_design/pattern-gallery.html").write_text(build_gallery(), encoding="utf-8")
    print(f"{len(MOTIFS)} motifs for {len(seen)} modules in {len(CATEGORY_MOTIF)} categories → looks/shared/motifs.css, "
          f"looks/motif-data.js, ui_design/pattern-map.md, ui_design/pattern-gallery.html")


if __name__ == "__main__":
    main()

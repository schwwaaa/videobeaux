# videobeaux/programs/crossmosh.py
# True P-only datamosh (concat protocol keeps decoder state) + optional melt trail.
# Backward-compatible with the earlier crossmosh args:
#   --b-input, --outfile, --codec, --qscale, --gop, --keep-temp, (respects global --force)
#
# New options:
#   --mode {proto,smear}  (default proto)
#   --frames (smear)      --decay (smear)   --blend (smear)

import os, tempfile, shutil
from pathlib import Path
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(p):
    p.description = "Cross-mosh (real datamosh): keep decoder state A→B; optional smear trail."
    # Inputs
    p.add_argument("--b-input", required=True, help="Second clip (B)")
    # Output (note: NOT -o; use --outfile to avoid conflict with global -o)
    p.add_argument("--outfile", required=True, help="Final output (e.g. out/mosh.avi)")

    # Keep old knobs for compatibility
    p.add_argument("--codec", default="libxvid", choices=["libxvid", "mpeg4"],
                   help="P-only friendly MPEG-4 ASP codec. libxvid strongly recommended.")
    p.add_argument("--qscale", type=float, default=3.0,
                   help="Quality scale (lower = higher quality). Default: 3")
    p.add_argument("--gop", type=int, default=9999,
                   help="Large GOP to minimize I-frames. Default: 9999")
    p.add_argument("--keep-temp", action="store_true", help="Keep intermediates")

    # New “melt” options
    p.add_argument("--mode", choices=["proto", "smear"], default="proto",
                   help="proto = pure datamosh; smear = datamosh + melt trail")
    p.add_argument("--frames", type=int, default=9, help="[smear] tmix frames")
    p.add_argument("--decay", type=float, default=0.90, help="[smear] lagfun decay 0..1")
    p.add_argument("--blend", default="screen",
                   help='[smear] tblend all_mode (screen|lighten|add|average|... )')

def _force(cmd, force):
    return (cmd[:1] + ["-y"] + cmd[1:]) if force else cmd

def _vtag_for(codec):
    return "XVID" if codec == "libxvid" else "DIVX"

def run(args):
    A = Path(args.input)
    B = Path(args.b_input)
    if not A.exists(): raise FileNotFoundError(f"Input A not found: {A}")
    if not B.exists(): raise FileNotFoundError(f"Input B not found: {B}")

    out = Path(args.outfile)
    if out.suffix.lower() != ".avi":
        out = out.with_suffix(".avi")  # concat protocol + ASP works best in AVI

    tmp = Path(tempfile.mkdtemp(prefix="vb_crossmosh_"))
    try:
        A_p   = tmp / f"{A.stem}_P.avi"
        B_p   = tmp / f"{B.stem}_P.avi"
        B_noI = tmp / f"{B.stem}_P_noI.avi"
        moshed = tmp / "mosh.avi"

        vtag = _vtag_for(args.codec)
        common_encode = [
            "-c:v", args.codec,
            "-vtag", vtag,
            "-qscale:v", str(args.qscale),
            "-bf", "0",
            "-g", str(args.gop),
            "-sc_threshold", "0",
            "-an"
        ]

        # 1) A → P-only (allow the very first I-frame)
        cmd_A = ["ffmpeg", "-i", str(A), *common_encode, str(A_p)]
        run_ffmpeg_with_progress(_force(cmd_A, getattr(args, "force", False)), str(A), str(A_p))

        # 2) B → P-only with NO I-frames (force keyframes impossibly far away)
        cmd_B = ["ffmpeg", "-i", str(B), *common_encode,
                 "-force_key_frames", "expr:gte(t,1e9)",  # no I-frames in practice
                 str(B_p)]
        run_ffmpeg_with_progress(_force(cmd_B, getattr(args, "force", False)), str(B), str(B_p))

        # 3) Drop first frame of B (belt-and-suspenders to ensure no I hits the join)
        cmd_noI = ["ffmpeg", "-i", str(B_p),
                   "-vf", "trim=start_frame=1,setpts=PTS-STARTPTS",
                   *common_encode, str(B_noI)]
        run_ffmpeg_with_progress(_force(cmd_noI, getattr(args, "force", False)), str(B_p), str(B_noI))

        # 4) TRUE MOSH: concat protocol preserves decoder state (no demux/file reset)
        concat_uri = f"concat:{A_p.as_posix()}|{B_noI.as_posix()}"
        cmd_cat = ["ffmpeg", "-i", concat_uri,
                   "-bsf:v", "mpeg4_unpack_bframes",
                   "-c", "copy", "-fflags", "+genpts",
                   str(moshed)]
        run_ffmpeg_with_progress(_force(cmd_cat, getattr(args, "force", False)), str(A_p), str(moshed))

        if args.mode == "proto":
            final_src = moshed
        else:
            # 5) Optional smear pass (tmix + lagfun + tblend) for melt/overlap vibes
            n = max(2, args.frames)
            weights = " ".join([f"{(args.decay**i):.3f}" for i in range(n)])
            vf = (
                f"tmix=frames={n}:weights='{weights}',"
                f"lagfun=decay={args.decay:.3f},"
                f"tblend=all_mode={args.blend},"
                "format=yuv420p"
            )
            smeared = tmp / "mosh_smear.avi"
            cmd_smear = ["ffmpeg", "-i", str(moshed),
                         "-vf", vf,
                         "-c:v", args.codec, "-qscale:v", str(args.qscale),
                         "-an", str(smeared)]
            run_ffmpeg_with_progress(_force(cmd_smear, getattr(args, "force", False)), str(moshed), str(smeared))
            final_src = smeared

        # Deliver
        final_src = Path(final_src)
        if final_src.resolve() != out.resolve():
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(final_src), str(out))
        print(f"✅ crossmosh → {out}")

        # Cleanup
        if not args.keep_temp:
            try: shutil.rmtree(tmp)
            except Exception: pass
        else:
            print(f"ℹ️ Kept intermediates: {tmp}")

    except Exception:
        print(f"⚠️ Keeping intermediates for debugging: {tmp}")
        raise

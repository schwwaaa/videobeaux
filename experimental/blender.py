#!/usr/bin/env python3
import argparse
import subprocess
import json
import shutil
import os
import sys

BLEND_MODES = [
    "addition","and","average","burn","darken","difference","divide","dodge",
    "exclusion","extremity","freeze","glow","grainextract","grainmerge",
    "hardlight","hardmix","heat","lighten","linearlight","multiply","negation",
    "or","overlay","phoenix","pinlight","reflect","screen","softlight","subtract",
    "vividlight","xor"
]

def require_ffmpeg():
    if not shutil.which("ffmpeg"):
        sys.exit("❌ ffmpeg not found in PATH.")
    if not shutil.which("ffprobe"):
        sys.exit("❌ ffprobe not found in PATH (needed to inspect streams).")

def probe_streams(path):
    """Return dict with has_video, has_audio, width, height for the first video stream."""
    try:
        out = subprocess.check_output([
            "ffprobe","-v","error","-print_format","json",
            "-show_streams","-select_streams","v:0","-show_entries","stream=width,height",
            path
        ], text=True)
        info_v = json.loads(out)
        w = h = None
        if info_v.get("streams"):
            w = info_v["streams"][0].get("width")
            h = info_v["streams"][0].get("height")
        outa = subprocess.check_output([
            "ffprobe","-v","error","-print_format","json",
            "-show_streams","-select_streams","a","-show_entries","stream=index",
            path
        ], text=True)
        info_a = json.loads(outa)
        has_audio = bool(info_a.get("streams"))
        return {"width": w, "height": h, "has_audio": has_audio}
    except subprocess.CalledProcessError:
        return {"width": None, "height": None, "has_audio": False}

def build_filter_complex(args, base_w, base_h, base_has_a, over_has_a):
    """
    Build a filter_complex that:
      - aligns timestamps
      - (optionally) scales+pads overlay to base dimensions
      - applies pre-filters to each input if supplied
      - blends with mode or custom expression
      - applies post-filters if supplied
      - mixes audio if requested (and present)
    Returns: (filter_complex_str, have_audio_from_filters)
    """
    parts = []

    # Base video chain
    base_label = "basev"
    base_chain = "[0:v]setpts=PTS-STARTPTS,format=rgba"
    if args.pre1:
        base_chain += f",{args.pre1}"
    base_chain += f"[{base_label}]"
    parts.append(base_chain)

    # Overlay video chain
    over_label = "overv"
    over_chain = "[1:v]setpts=PTS-STARTPTS,format=rgba"
    if args.keep_ar:
        if not (base_w and base_h):
            sys.exit("❌ --keep-ar requires FFprobe to get base dimensions; couldn't detect width/height.")
        over_chain += f",scale={base_w}:{base_h}:force_original_aspect_ratio=decrease,pad={base_w}:{base_h}:(ow-iw)/2:(oh-ih)/2"
    else:
        # Exact match to base frame dims; if base dims unknown, scale2ref will still match whatever base is.
        over_chain += ",format=rgba"
        # Prefer scale2ref so we don't alter base at all
        over_chain += "[ovrtmp];[ovrtmp][0:v]scale2ref=w=iw:h=ih[" + over_label + "][" + base_label + "]"
        # We already produced both labels here; skip adding pre2 to ovrtmp path
        if args.pre2:
            # Apply pre2 after scale2ref on overlay
            parts[-1] += ""  # keep index alignment
            over_chain = f"[{over_label}]{args.pre2}[{over_label}]"
            parts.append(over_chain)
            # prevent re-adding base
            over_chain = None
    if over_chain:
        if args.pre2:
            over_chain += f",{args.pre2}"
        over_chain += f"[{over_label}]"
        parts.append(over_chain)

    # Blend stage
    if args.expr:
        # NOTE: if your expression contains ':' characters, escape them as '\:'
        blend = f"[{base_label}][{over_label}]blend=all_expr={args.expr}:all_opacity={args.opacity}[vtmp]"
    else:
        # Validate mode
        mode = args.mode.lower()
        if mode not in BLEND_MODES:
            sys.exit(f"❌ Unknown blend mode '{args.mode}'. Valid: {', '.join(BLEND_MODES)}")
        blend = f"[{base_label}][{over_label}]blend=all_mode={mode}:all_opacity={args.opacity}[vtmp]"
    parts.append(blend)

    # Post-filters + output format
    if args.post:
        parts.append(f"[vtmp]{args.post}[vout]")
    else:
        parts.append("[vtmp]format=yuv420p[vout]")

    have_audio_from_filters = False

    # Audio handling
    if args.audio == "mix":
        if base_has_a and over_has_a:
            # Use volume on each then amix; avoid 'weights=' quoting hassles
            v1 = args.mix_weights[0]
            v2 = args.mix_weights[1]
            parts.append(f"[0:a]asetpts=PTS-STARTPTS,volume={v1}[a0]")
            parts.append(f"[1:a]asetpts=PTS-STARTPTS,volume={v2}[a1]")
            parts.append(f"[a0][a1]amix=inputs=2:normalize={1 if args.mix_normalize else 0}[aout]")
            have_audio_from_filters = True
        elif base_has_a:
            # Only base has audio – behave like 'v1'
            pass
        elif over_has_a:
            # Only overlay has audio – behave like 'v2'
            pass
        else:
            # No audio at all
            pass

    return ";".join(parts), have_audio_from_filters

def main():
    require_ffmpeg()

    p = argparse.ArgumentParser(
        description="Blend two videos with FFmpeg filters, and choose audio (mix, vid1, vid2, none)."
    )
    p.add_argument("-i1","--input1", required=True, help="Path to first video (base).")
    p.add_argument("-i2","--input2", required=True, help="Path to second video (overlay).")
    p.add_argument("-o","--output", required=True, help="Output video path.")
    # Video blend controls
    p.add_argument("--mode", default="overlay", help=f"Blend mode (default: overlay). Options: {', '.join(BLEND_MODES)}")
    p.add_argument("--expr", help="Custom blend all_expr (overrides --mode). If it contains ':', escape as '\\:'.")
    p.add_argument("--opacity", type=float, default=1.0, help="Blend opacity 0.0–1.0 (default 1.0).")
    p.add_argument("--pre1", help="Filter chain for base video before blending (e.g. 'eq=brightness=0.05:saturation=0.9').")
    p.add_argument("--pre2", help="Filter chain for overlay video before blending.")
    p.add_argument("--post", help="Filter chain on blended output (e.g. 'gblur=sigma=8,unsharp=5:5:0.8').")
    p.add_argument("--keep-ar", action="store_true",
                   help="Preserve overlay aspect ratio: scale to fit inside base, then pad to match base size.")
    # Audio controls
    p.add_argument("--audio", choices=["mix","v1","v2","none"], default="mix",
                   help="Audio selection: mix both, use video1, use video2, or none. Default: mix.")
    p.add_argument("--mix-weights", default="1,1",
                   help="When --audio mix and both audios exist: linear weights as 'w1,w2' (applied via volume). Default '1,1'.")
    p.add_argument("--mix-normalize", action="store_true",
                   help="Normalize amix output (might affect dynamics). Off by default.")
    # Encoding controls
    p.add_argument("--vcodec", default="libx264", help="Video codec (default libx264).")
    p.add_argument("--crf", type=int, default=18, help="CRF (x264/x265 quality target). Default 18.")
    p.add_argument("--preset", default="veryfast", help="Encoding preset (x264/x265). Default veryfast.")
    p.add_argument("--acodec", default="aac", help="Audio codec (default aac).")
    p.add_argument("--ab", default="192k", help="Audio bitrate (default 192k).")
    p.add_argument("--extra", help="Extra args to append to ffmpeg (verbatim).")

    args = p.parse_args()

    # Validate files
    for path in (args.input1, args.input2):
        if not os.path.isfile(path):
            sys.exit(f"❌ File not found: {path}")

    # Parse mix weights
    try:
        w1, w2 = args.mix_weights.split(",")
        w1 = float(w1.strip()); w2 = float(w2.strip())
        args.mix_weights = (w1, w2)
    except Exception:
        sys.exit("❌ --mix-weights must be 'w1,w2' (numbers).")

    # Probe base for dimensions and both for audio presence
    base = probe_streams(args.input1)
    over = probe_streams(args.input2)

    # Build filter_complex
    filt, audio_from_filters = build_filter_complex(
        args, base.get("width"), base.get("height"), base.get("has_audio"), over.get("has_audio")
    )

    # Assemble ffmpeg command
    cmd = ["ffmpeg","-y",
           "-i", args.input1,
           "-i", args.input2,
           "-filter_complex", filt,
           "-map","[vout]"]
    # Audio mapping
    if args.audio == "none":
        cmd += ["-an"]
    elif args.audio == "v1":
        cmd += ["-map","0:a?"]
    elif args.audio == "v2":
        cmd += ["-map","1:a?"]
    elif args.audio == "mix":
        if audio_from_filters:
            cmd += ["-map","[aout]"]
        else:
            # Fallback if one/both inputs lack audio
            if base.get("has_audio"):
                cmd += ["-map","0:a?"]
            elif over.get("has_audio"):
                cmd += ["-map","1:a?"]
            else:
                cmd += ["-an"]

    # Codecs & muxing
    cmd += ["-c:v", args.vcodec]
    if args.vcodec in ("libx264","libx265"):
        cmd += ["-crf", str(args.crf), "-preset", args.preset]
    cmd += ["-pix_fmt","yuv420p"]
    if args.audio != "none":
        cmd += ["-c:a", args.acodec, "-b:a", args.ab]
    cmd += ["-shortest"]  # avoid hanging on streams of different lengths

    if args.extra:
        cmd += args.extra.split()

    cmd += [args.output]

    # Show command and run
    print(">> FFmpeg command:")
    print(" ".join(subprocess.list2cmdline([c]) for c in cmd))
    try:
        subprocess.check_call(cmd)
        print(f"✅ Done: {args.output}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ FFmpeg failed with code {e.returncode}")
    except KeyboardInterrupt:
        sys.exit("⛔ Interrupted.")

if __name__ == "__main__":
    main()

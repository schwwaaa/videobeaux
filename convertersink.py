#!/usr/bin/env python3
import argparse, os, shlex, subprocess, sys
from pathlib import Path

# ------------------------------
# Helpers
# ------------------------------
def run(cmd):
    print(">>", " ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        sys.exit(proc.returncode)

def ext_lower(path):
    return Path(path).suffix.lower().lstrip(".")

def guess_container(output_path, fmt_override=None):
    if fmt_override:
        return fmt_override.lower()
    ext = ext_lower(output_path)
    # Map common aliases/extensions to FFmpeg muxer names
    alias = {
        "mp4":"mp4", "m4v":"mp4", "mov":"mov", "qt":"mov", "mkv":"matroska",
        "webm":"webm", "avi":"avi", "wmv":"asf", "asf":"asf",
        "flv":"flv", "ts":"mpegts", "m2ts":"mpegts", "mpeg":"mpeg", "mpg":"mpeg",
        "mxf":"mxf", "wav":"wav", "mp3":"mp3", "m4a":"ipod", "aac":"adts", "ogg":"ogg",
        "oga":"ogg", "opus":"ogg", "flac":"flac", "alac":"ipod",
        "gif":"gif",
        # image sequences
        "jpg":"image2", "jpeg":"image2", "png":"image2", "tif":"image2", "tiff":"image2", "bmp":"image2", "exr":"image2"
    }
    return alias.get(ext, ext or "mp4")

def is_audio_only(fmt):
    return fmt in {"mp3","ipod","adts","ogg","flac","wav"}

def default_codecs_for_container(mux):
    """
    Conservative, broadly compatible defaults.
    Overridden by profiles or explicit --vcodec/--acodec.
    """
    if mux in ("mp4", "mov", "matroska"):
        return ("libx264", "aac")
    if mux == "webm":
        return ("libvpx-vp9", "libopus")
    if mux == "gif":
        return (None, None)  # handled via palette method
    if mux in ("mp3","adts","ogg","flac","wav","ipod"):
        return (None, None)  # audio-only handled separately
    if mux == "mxf":
        # Default to XDCAM HD 50 unless profile overrides
        return ("mpeg2video", "pcm_s16le")
    if mux == "mpegts":
        return ("libx264", "aac")
    if mux == "avi":
        # Legacy default: MPEG-4 ASP + MP3
        return ("mpeg4", "mp3")
    return ("libx264", "aac")

# ------------------------------
# Profiles (curated, battle-tested)
# ------------------------------
PROFILES = {
    # Web/General delivery
    "mp4_h264": lambda: [
        "-c:v","libx264","-preset","veryfast","-crf","18",
        "-pix_fmt","yuv420p",
        "-movflags","+faststart",
        "-c:a","aac","-b:a","192k","-ac","2"
    ],
    "mp4_hevc": lambda: [
        "-c:v","libx265","-preset","medium","-crf","22",
        "-tag:v","hvc1",
        "-pix_fmt","yuv420p",
        "-movflags","+faststart",
        "-c:a","aac","-b:a","192k","-ac","2"
    ],
    "mp4_av1": lambda: [
        "-c:v","libaom-av1","-crf","28","-b:v","0",
        "-pix_fmt","yuv420p",
        "-movflags","+faststart",
        "-c:a","aac","-b:a","192k","-ac","2"
    ],

    # WebM
    "webm_vp9": lambda: [
        "-c:v","libvpx-vp9","-b:v","0","-crf","30",
        "-row-mt","1",
        "-pix_fmt","yuv420p",
        "-c:a","libopus","-b:a","160k","-ac","2"
    ],
    "webm_av1": lambda: [
        "-c:v","libaom-av1","-crf","32","-b:v","0",
        "-pix_fmt","yuv420p",
        "-c:a","libopus","-b:a","160k","-ac","2"
    ],

    # Professional mezzanine
    "prores_422": lambda: [
        "-c:v","prores_ks","-profile:v","2",
        "-pix_fmt","yuv422p10le",
        "-c:a","pcm_s16le"
    ],
    "prores_4444": lambda: [
        "-c:v","prores_ks","-profile:v","4",
        "-pix_fmt","yuva444p10le",
        "-c:a","pcm_s24le"
    ],
    "dnxhr_hq": lambda: [
        "-c:v","dnxhd","-profile:v","dnxhr_hq",
        "-pix_fmt","yuv422p",
        "-c:a","pcm_s16le"
    ],

    # Broadcast MXF (OP1a)
    "mxf_xdcamhd50_1080i59": lambda: [
        "-c:v","mpeg2video","-b:v","50M","-minrate","50M","-maxrate","50M","-bufsize","17825792",
        "-r","30000/1001","-flags","+ildct+ilme","-top","1",
        "-pix_fmt","yuv422p",
        "-c:a","pcm_s24le","-ar","48000","-ac","2",
        "-f","mxf"
    ],

    # Archival lossless
    "lossless_ffv1": lambda: [
        "-c:v","ffv1","-level","3","-g","1","-slicecrc","1",
        "-c:a","pcm_s24le"
    ],

    # GIF
    "gif": lambda: ["-filter_complex","[0:v]fps=15,scale=iw:-2:flags=lanczos"],

    # Image sequences
    "png_seq": lambda: ["-c:v","png"],
    "jpg_seq": lambda: ["-qscale:v","2"],

    # Audio-only
    "mp3_320": lambda: ["-vn","-c:a","libmp3lame","-b:a","320k"],
    "aac_192": lambda: ["-vn","-c:a","aac","-b:a","192k"],
    "flac":    lambda: ["-vn","-c:a","flac"],

    # --- NEW: AVI speed-focused presets ---
    # Very fast encode, big files; great for quick turnarounds or NLE ingest
    "avi_mjpeg_fast": lambda: ["-c:v","mjpeg","-q:v","3","-c:a","pcm_s16le"],
    # Legacy-compatible, faster-than-default MPEG-4 ASP
    "avi_mpeg4_fast": lambda: ["-c:v","mpeg4","-qscale:v","3","-bf","0","-mbd","0","-c:a","mp3","-b:a","192k"]
}

# ------------------------------
# Command builder
# ------------------------------
def build_ffmpeg_command(args):
    in_path = args.input
    out_path = args.output

    if not out_path:
        base = str(Path(in_path).with_suffix(""))
        ext = f".{args.format}" if args.format else ".mp4"
        out_path = base + ext

    mux = guess_container(out_path, args.format)
    common = ["ffmpeg", "-hide_banner", "-y" if args.force else "-n", "-i", in_path]

    # Stream copy?
    if args.copy:
        return common + ["-c","copy", out_path]

    # Explicit codecs (can be overridden by profile if repeated later)
    vcodec = args.vcodec
    acodec = args.acodec

    # Apply profile if chosen
    profile_args = []
    if args.profile:
        prof = PROFILES.get(args.profile)
        if not prof:
            sys.exit(f"Unknown profile: {args.profile}")
        profile_args = prof()

    # If no explicit profile and no explicit codecs, choose container defaults
    if not args.profile:
        dv, da = default_codecs_for_container(mux)
        if not vcodec and dv: vcodec = dv
        if not acodec and da: acodec = da

    cmd = list(common)

    # Special path: GIF palette method
    if mux == "gif" or args.profile == "gif":
        vf = []
        if args.vf: vf.append(args.vf)
        else: vf.append("fps=15,scale=iw:-2:flags=lanczos")
        palette_chain = f"[0:v]{','.join(vf)},palettegen[p];[0:v]{','.join(vf)}[v];[v][p]paletteuse"
        gif_cmd = list(common) + ["-filter_complex", palette_chain, "-gifflags", "+transdiff", out_path]
        return gif_cmd

    # Video settings
    if vcodec:
        cmd += ["-c:v", vcodec]
    if args.crf is not None:
        cmd += ["-crf", str(args.crf)]
    if args.bitrate:
        cmd += ["-b:v", args.bitrate]
    if args.maxrate:
        cmd += ["-maxrate", args.maxrate]
    if args.bufsize:
        cmd += ["-bufsize", args.bufsize]
    if args.preset:
        cmd += ["-preset", args.preset]
    if args.profile_v:
        cmd += ["-profile:v", args.profile_v]
    if args.level:
        cmd += ["-level", args.level]
    if args.pix_fmt:
        cmd += ["-pix_fmt", args.pix_fmt]
    if args.gop:
        cmd += ["-g", str(args.gop)]
    if args.r:
        cmd += ["-r", args.r]
    if args.vf:
        cmd += ["-vf", args.vf]
    if args.tagv:
        cmd += ["-tag:v", args.tagv]

    # Audio settings
    if acodec:
        cmd += ["-c:a", acodec]
    if args.abitrate:
        cmd += ["-b:a", args.abitrate]
    if args.ac:
        cmd += ["-ac", str(args.ac)]
    if args.ar:
        cmd += ["-ar", args.ar]

    # Container niceties
    if mux == "mp4" and "+faststart" not in " ".join(profile_args):
        cmd += ["-movflags", "+faststart"]

    # Append profile args last so they can set container-specific flags
    if profile_args:
        cmd += profile_args

    # --- NEW: Sensible AVI defaults when user didn't specify quality flags or a profile ---
    if mux == "avi" and not args.profile:
        # If using MPEG-4 ASP and no quality flags were set, favor speed with decent visual quality
        have_quality_flag = any(x in (args.crf, args.bitrate, args.maxrate, args.bufsize) for x in [args.crf, args.bitrate, args.maxrate, args.bufsize])
        if (vcodec or "").lower() == "mpeg4" and not have_quality_flag:
            # Avoid B-frames for speed; use qscale for constant quality
            cmd += ["-qscale:v","3","-bf","0"]
        # If user picked MJPEG explicitly without profile and no quality, set q:v
        if (vcodec or "").lower() == "mjpeg" and not have_quality_flag:
            cmd += ["-q:v","3"]
        # Reasonable audio default if none provided
        if not acodec:
            cmd += ["-c:a","mp3","-b:a","192k"]

    # Raw passthrough flags after '--'
    if args.ffmpeg_args:
        cmd += args.ffmpeg_args

    cmd += [out_path]
    return cmd

# ------------------------------
# CLI
# ------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Black-box FFmpeg converter: any format in → any format out.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Globals / required
    p.add_argument("-i","--input", required=True, help="Input media file")
    p.add_argument("-o","--output", help="Output path (extension chooses container unless --format)")
    p.add_argument("-F","--force", action="store_true", help="Overwrite output file")

    # Container/format control
    p.add_argument("--format", help="Force container/muxer (e.g., mp4, mov, webm, matroska, mxf, gif, image2, avi)")
    p.add_argument("--profile", choices=sorted(PROFILES.keys()), help="Apply a curated preset")

    # Codecs & quality
    p.add_argument("--vcodec", help="Video codec (e.g., libx264, libx265, libaom-av1, prores_ks, dnxhd, mpeg2video, mpeg4, mjpeg)")
    p.add_argument("--acodec", help="Audio codec (e.g., aac, libopus, libmp3lame, mp3, pcm_s16le)")
    p.add_argument("--crf", type=int, help="Constant Rate Factor (quality target for many codecs)")
    p.add_argument("--bitrate", help="Video bitrate (e.g., 5M)")
    p.add_argument("--maxrate", help="Video maxrate")
    p.add_argument("--bufsize", help="Video VBV buffer size")
    p.add_argument("--preset", help="Codec speed/efficiency preset (varies by codec)")
    p.add_argument("--profile-v", dest="profile_v", help="Video codec profile (e.g., high, main, baseline; or prores profile index)")
    p.add_argument("--level", help="Video level (e.g., 4.1)")
    p.add_argument("--pix-fmt", dest="pix_fmt", help="Pixel format (e.g., yuv420p, yuv422p10le, yuva444p10le)")
    p.add_argument("--gop", type=int, help="GOP/keyframe interval (frames)")
    p.add_argument("-r", help="Output frame rate (e.g., 30000/1001, 25, 24)")
    p.add_argument("--vf", help="Video filtergraph")
    p.add_argument("--tagv", help="Force video fourcc/tag (e.g., hvc1)")

    # Audio
    p.add_argument("--abitrate", help="Audio bitrate (e.g., 192k)")
    p.add_argument("--ac", type=int, help="Audio channels")
    p.add_argument("--ar", help="Audio sample rate (e.g., 48000)")

    # Stream copy
    p.add_argument("--copy", action="store_true", help="Stream copy all streams when compatible (no re-encode)")

    # Pass-through extra ffmpeg args after --
    p.add_argument("ffmpeg_args", nargs=argparse.REMAINDER, help="Raw args after -- go straight to ffmpeg")
    return p.parse_args()

def main():
    args = parse_args()
    cmd = build_ffmpeg_command(args)
    run(cmd)

if __name__ == "__main__":
    main()

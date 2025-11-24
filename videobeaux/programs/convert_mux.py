# videobeaux/programs/convert_mux.py
# A videobeaux-ready “convert” module that mirrors your standalone converter.
# - Uses register_arguments(parser) + run(args) like other videobeaux programs.
# - Respects global -i/--input, -o/--output, -F/--force from cli.py
# - Shows progress via run_ffmpeg_with_progress, just like your other modules.

import argparse
import shlex
import sys
from pathlib import Path

from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress  # progress + error plumbing

# ------------------------------
# Helpers
# ------------------------------

def _ext_lower(path: str) -> str:
    return Path(path).suffix.lower().lstrip(".")

def _guess_container_from_path(output_path: str, fmt_override: str | None = None) -> str:
    """
    Map extension or fmt override to an FFmpeg muxer name.
    NOTE: cli.py currently forces .mp4 extension. We still keep this map for completeness.
    """
    if fmt_override:
        return fmt_override.lower()

    ext = _ext_lower(output_path)
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

def _default_codecs_for_container(mux: str) -> tuple[str | None, str | None]:
    """
    Conservative defaults if no profile and no explicit codec flags were provided.
    """
    if mux in ("mp4", "mov", "matroska"):
        return ("libx264", "aac")
    if mux == "webm":
        return ("libvpx-vp9", "libopus")
    if mux == "gif":
        return (None, None)  # handled via palette method, not simple v/a codecs
    if mux in ("mp3","adts","ogg","flac","wav","ipod"):
        return (None, None)  # audio-only handled separately
    if mux == "mxf":
        return ("mpeg2video", "pcm_s16le")
    if mux == "mpegts":
        return ("libx264", "aac")
    if mux == "avi":
        return ("mpeg4", "mp3")
    return ("libx264", "aac")

def _profile_container_hint(name: str) -> str | None:
    """
    Rough container hint to sanity-check against .mp4 limitation in cli.py.
    """
    if name.startswith("mp4_"):
        return "mp4"
    if name.startswith("webm_"):
        return "webm"
    if name in {"prores_422", "prores_4444"}:
        return "mov"
    if name.startswith("dnxhr"):
        return "mov"
    if name.startswith("mxf_"):
        return "mxf"
    if name in {"lossless_ffv1"}:
        return "matroska"
    if name in {"gif", "png_seq", "jpg_seq"}:
        return name  # special
    if name in {"mp3_320", "aac_192", "flac"}:
        return "audio"
    if name.startswith("avi_"):
        return "avi"
    return None

# ------------------------------
# Profiles (same names/values you provided)
# ------------------------------
def _PROFILES():
    return {
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

        # GIF (special palette path handled later)
        "gif": lambda: ["-filter_complex","[0:v]fps=15,scale=iw:-2:flags=lanczos"],

        # Image sequences
        "png_seq": lambda: ["-c:v","png"],
        "jpg_seq": lambda: ["-qscale:v","2"],

        # Audio-only
        "mp3_320": lambda: ["-vn","-c:a","libmp3lame","-b:a","320k"],
        "aac_192": lambda: ["-vn","-c:a","aac","-b:a","192k"],
        "flac":    lambda: ["-vn","-c:a","flac"],

        # AVI speed-focused presets
        "avi_mjpeg_fast": lambda: ["-c:v","mjpeg","-q:v","3","-c:a","pcm_s16le"],
        "avi_mpeg4_fast": lambda: ["-c:v","mpeg4","-qscale:v","3","-bf","0","-mbd","0","-c:a","mp3","-b:a","192k"]
    }

# ------------------------------
# Command builder
# ------------------------------

def _build_ffmpeg_command(args: argparse.Namespace) -> list[str]:
    in_path = args.input
    out_path = args.output

    # Even though cli.py appends .mp4 and enforces it, we preserve format logic for future flexibility.
    mux = _guess_container_from_path(out_path, args.format)

    # FAIL FAST if profile clearly mismatches .mp4 (helps avoid confusing FFmpeg errors)
    if out_path.lower().endswith(".mp4") and args.profile:
        hint = _profile_container_hint(args.profile)
        if hint and hint not in ("mp4", "audio"):  # audio-only is also incompatible with .mp4 filename
            raise SystemExit(
                f"❌ Profile '{args.profile}' expects container '{hint}', "
                f"but your output is '.mp4' (cli.py is MP4-only). "
                f"Pick one of: mp4_h264, mp4_hevc, mp4_av1 — or pass raw FFmpeg flags after ' -- '."
            )

    # Base invocation (respect global --force)
    cmd = ["ffmpeg", "-hide_banner"]
    cmd += ["-y"] if args.force else ["-n"]
    cmd += ["-i", in_path]

    # Stream copy?
    if args.copy:
        cmd += ["-c", "copy"]
        if args.ffmpeg_args:
            cmd += args.ffmpeg_args
        cmd += [out_path]
        return cmd

    # Start collecting settings
    vcodec = args.vcodec
    acodec = args.acodec

    # Apply profile, if any
    profile_args = []
    if args.profile:
        prof = _PROFILES().get(args.profile)
        if not prof:
            raise SystemExit(f"❌ Unknown profile: {args.profile}")
        profile_args = prof()

    # If no profile -> default codecs for the container
    if not args.profile:
        dv, da = _default_codecs_for_container(mux)
        if not vcodec and dv: vcodec = dv
        if not acodec and da: acodec = da

    # GIF special path (but remember: cli forces .mp4; we still guard for correctness)
    if mux == "gif" or args.profile == "gif":
        if out_path.lower().endswith(".mp4"):
            raise SystemExit("❌ GIF output requested, but output file ends with .mp4 (cli is MP4-only).")
        vf_chain = args.vf if args.vf else "fps=15,scale=iw:-2:flags=lanczos"
        palette_chain = f"[0:v]{vf_chain},palettegen[p];[0:v]{vf_chain}[v];[v][p]paletteuse"
        gif_cmd = ["ffmpeg", "-hide_banner"] + (["-y"] if args.force else ["-n"]) + [
            "-i", in_path,
            "-filter_complex", palette_chain,
            "-gifflags", "+transdiff",
            out_path
        ]
        return gif_cmd

    # Video opts
    if vcodec:               cmd += ["-c:v", vcodec]
    if args.crf is not None: cmd += ["-crf", str(args.crf)]
    if args.bitrate:         cmd += ["-b:v", args.bitrate]
    if args.maxrate:         cmd += ["-maxrate", args.maxrate]
    if args.bufsize:         cmd += ["-bufsize", args.bufsize]
    if args.preset:          cmd += ["-preset", args.preset]
    if args.profile_v:       cmd += ["-profile:v", args.profile_v]
    if args.level:           cmd += ["-level", args.level]
    if args.pix_fmt:         cmd += ["-pix_fmt", args.pix_fmt]
    if args.gop:             cmd += ["-g", str(args.gop)]
    if args.r:               cmd += ["-r", args.r]
    if args.vf:              cmd += ["-vf", args.vf]
    if args.tagv:            cmd += ["-tag:v", args.tagv]

    # Audio opts
    if acodec:               cmd += ["-c:a", acodec]
    if args.abitrate:        cmd += ["-b:a", args.abitrate]
    if args.ac is not None:  cmd += ["-ac", str(args.ac)]
    if args.ar:              cmd += ["-ar", args.ar]

    # MP4 nicety
    if mux == "mp4" and (not args.profile or "+faststart" not in " ".join(profile_args)):
        cmd += ["-movflags", "+faststart"]

    # Append profile-specific args last (so they can override)
    if profile_args:
        cmd += profile_args

    # AVI niceties if user forces .avi in the future; harmless if .mp4
    if mux == "avi" and not args.profile:
        have_quality_flag = any(x is not None for x in (args.crf, args.bitrate, args.maxrate, args.bufsize))
        if (vcodec or "").lower() == "mpeg4" and not have_quality_flag:
            cmd += ["-qscale:v","3","-bf","0"]
        if (vcodec or "").lower() == "mjpeg" and not have_quality_flag:
            cmd += ["-q:v","3"]
        if not acodec:
            cmd += ["-c:a","mp3","-b:a","192k"]

    # Raw passthrough after --
    if args.ffmpeg_args:
        cmd += args.ffmpeg_args

    cmd += [out_path]
    return cmd

# ------------------------------
# videobeaux hooks
# ------------------------------

def register_arguments(parser):
    """
    Register per-program flags only. Global -i/-o/-F/--help come from cli.py.
    """
    parser.description = "Black-box FFmpeg converter: any format in → any format out (mp4 outputs enforced by cli)."

    # Container/format control
    parser.add_argument("--format", help="Force container/muxer hint (mp4, mov, webm, matroska, mxf, gif, image2, avi)")
    parser.add_argument("--profile", choices=sorted(_PROFILES().keys()), help="Apply a curated preset")

    # Codecs & quality
    parser.add_argument("--vcodec", help="Video codec (e.g., libx264, libx265, libaom-av1, prores_ks, dnxhd, mpeg2video, mpeg4, mjpeg)")
    parser.add_argument("--acodec", help="Audio codec (e.g., aac, libopus, libmp3lame, mp3, pcm_s16le)")
    parser.add_argument("--crf", type=int, help="Constant Rate Factor (quality target)")
    parser.add_argument("--bitrate", help="Video bitrate, e.g. 5M")
    parser.add_argument("--maxrate", help="Video maxrate")
    parser.add_argument("--bufsize", help="VBV buffer size")
    parser.add_argument("--preset", help="Codec speed/efficiency preset")
    parser.add_argument("--profile-v", dest="profile_v", help="Video codec profile (e.g., high/main/baseline; or ProRes profile index)")
    parser.add_argument("--level", help="Video level (e.g., 4.1)")
    parser.add_argument("--pix-fmt", dest="pix_fmt", help="Pixel format (e.g., yuv420p, yuv422p10le, yuva444p10le)")
    parser.add_argument("--gop", type=int, help="GOP/keyframe interval (frames)")
    parser.add_argument("-r", help="Output frame rate (e.g., 30000/1001, 25, 24)")
    parser.add_argument("--vf", help="Video filtergraph")
    parser.add_argument("--tagv", help="Force video fourcc/tag (e.g., hvc1)")

    # Audio
    parser.add_argument("--abitrate", help="Audio bitrate (e.g., 192k)")
    parser.add_argument("--ac", type=int, help="Audio channels")
    parser.add_argument("--ar", help="Audio sample rate (e.g., 48000)")

    # Stream copy
    parser.add_argument("--copy", action="store_true", help="Stream copy all streams when compatible (no re-encode)")

    # Passthrough: raw ffmpeg args after `--`
    parser.add_argument("ffmpeg_args", nargs=argparse.REMAINDER, help="Raw args after -- go straight to ffmpeg")


def run(args):
    """
    Build command and execute through videobeaux's progress runner.
    """
    cmd = _build_ffmpeg_command(args)

    # Friendly echo so users can see exactly what will run (quoted like your original)
    print("↪︎", " ".join(shlex.quote(c) for c in cmd))

    # Use the shared runner so progress + errors are consistent across programs
    run_ffmpeg_with_progress(
        (cmd[:1] + ["-y"] + cmd[1:]) if args.force else cmd,
        args.input,
        args.output
    )

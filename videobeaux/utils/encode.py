"""
Output-compatibility helpers: make sure the files we write open everywhere (Finder / QuickLook, QuickTime, phones,
browsers), not just in VLC.

The usual culprits: H.264 written as High 4:2:2 / 10-bit because a phone clip was 10-bit (yuv422p10le,
yuv420p10le), MPEG-4 Part 2 or MP3 audio inside .mp4, or `moov` at the end of the file.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

MP4_LIKE = {".mp4", ".m4v", ".mov"}
# Video codecs whose output is *meant* to be exotic (leave pix_fmt alone for these).
_SPECIAL_VIDEO = ("prores", "dnx", "ffv1", "mjpeg", "libvpx", "libaom", "libsvtav1", "gif", "png", "rawvideo", "mpeg2",
                  "v210", "huffyuv", "utvideo", "qtrle", "cfhd")
_BAD_MP4_AUDIO = ("libmp3lame", "mp3", "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "libvorbis", "flac", "ac3")


def h264_mp4_args(crf: int = 18, preset: str = "medium", audio_bitrate: str = "192k") -> List[str]:
    """Encoder arguments for a universally playable H.264 + AAC MP4."""
    return [
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-movflags", "+faststart", "-tag:v", "avc1",
        "-c:a", "aac", "-b:a", audio_bitrate, "-ar", "48000", "-ac", "2",
    ]


def even(n: int) -> int:
    n = int(n)
    return max(2, n - n % 2)


def _value_after(cmd: List[str], flag: str):
    for i, tok in enumerate(cmd[:-1]):
        if tok == flag:
            return cmd[i + 1]
    return None


def harden_command(cmd: List[str]) -> List[str]:
    """
    Safety net applied to every ffmpeg command run through run_ffmpeg_with_progress: when the output is an MP4/MOV and
    the video is being (re)encoded as H.264/H.265, force a QuickLook-friendly pixel format, `+faststart`, an AAC audio
    codec (if the caller picked MP3/PCM/…), and an `hvc1` tag for HEVC. Anything else is returned unchanged.
    """
    if len(cmd) < 3 or Path(cmd[0]).name not in ("ffmpeg", "ffmpeg.exe"):
        return cmd
    out = cmd[-1]
    if not isinstance(out, str) or "%" in out or Path(out).suffix.lower() not in MP4_LIKE:
        return cmd
    body = list(cmd[:-1])
    extra: List[str] = []

    vcodec = _value_after(body, "-c:v") or _value_after(body, "-vcodec")
    acodec = _value_after(body, "-c:a") or _value_after(body, "-acodec")
    copy_all = _value_after(body, "-c") == "copy"
    no_video = "-vn" in body
    video_reencoded = not no_video and not copy_all and vcodec != "copy" and not (
        vcodec and vcodec.lower().startswith(_SPECIAL_VIDEO))

    if video_reencoded and vcodec in (None, "libx264", "libx265", "libx264rgb", "h264", "hevc", "h264_videotoolbox", "hevc_videotoolbox"):
        if "-pix_fmt" not in body and "-pixel_format" not in body:
            extra += ["-pix_fmt", "yuv420p"]
        if vcodec in ("libx265", "hevc", "hevc_videotoolbox") and "-tag:v" not in body and "-vtag" not in body:
            extra += ["-tag:v", "hvc1"]
    if video_reencoded and "-movflags" not in body:
        extra += ["-movflags", "+faststart"]
    elif not video_reencoded and "-movflags" not in body and vcodec == "copy":
        extra += ["-movflags", "+faststart"]

    if acodec and acodec.lower() in _BAD_MP4_AUDIO and Path(out).suffix.lower() != ".mov":
        body = [("aac" if (body[i - 1] in ("-c:a", "-acodec") and t == acodec) else t) for i, t in enumerate(body)]
        if "-b:a" not in body and "-ab" not in body:
            extra += ["-b:a", "192k"]

    return body + extra + [out]

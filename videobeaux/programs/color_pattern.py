"""
color_pattern — makes a video of a solid colour or a test pattern.

With no input video it makes the picture alone, for a set number of seconds (connect it straight to Output). Pick a
colour and a pattern, or a preset from the library (colours and the colour bars). The size works like Convert Dims:
pick a named size and the width and height fill in, or type your own.

With an input video connected, the picture is laid over it ("Over the input": the picture on top, the input underneath)
or under it ("Behind the input": the input on top, the picture showing wherever the input is transparent). The picture
takes the input's size and length, the input's sound is kept, and Opacity sets how strong the picture is.
"""
from videobeaux.programs.convert_dims import SIZE_FILLS, VIDEO_PRESETS, target_size
from videobeaux.utils.encode import even, h264_mp4_args
from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress
from videobeaux.utils.frame_pipe import probe_video

PATTERNS = [
    "Solid colour",
    "Gradient (colour to black)",
    "Checkerboard",
    "SMPTE colour bars",
    "SMPTE HD colour bars",
    "Test pattern",
    "RGB ramp",
    "Noise",
]

MAKE = "Make a picture"
BEHIND = "Behind the input"
OVER = "Over the input"
MODES = [MAKE, BEHIND, OVER]

# A library of starting points: each sets the pattern and colour in one click.
PRESETS = {
    "Colour bars": {"pattern": "SMPTE colour bars"},
    "HD colour bars": {"pattern": "SMPTE HD colour bars"},
    "Test pattern": {"pattern": "Test pattern"},
    "Black": {"pattern": "Solid colour", "color": "#000000"},
    "White": {"pattern": "Solid colour", "color": "#FFFFFF"},
    "Red": {"pattern": "Solid colour", "color": "#FF0000"},
    "Green": {"pattern": "Solid colour", "color": "#00FF00"},
    "Blue": {"pattern": "Solid colour", "color": "#0040FF"},
    "Yellow": {"pattern": "Solid colour", "color": "#FFE128"},
    "Red / black checks": {"pattern": "Checkerboard", "color": "#FF0000"},
}

GUI_METADATA = {
    "source": True,   # makes its own picture: the node does not need an input video
    "args": {
        "pattern": {"label": "Pattern", "default": PATTERNS[0], "choices": PATTERNS,
                    "help": "Solid colour uses the colour below. Gradient and Checkerboard use it too. The bars, test pattern, "
                            "RGB ramp and noise have their own colours."},
        "color": {"type": "color", "label": "Colour", "default": "#FF0000",
                  "help": "The colour for Solid colour, Gradient and Checkerboard."},
        "mode": {"label": "Input", "default": MAKE, "choices": MODES,
                 "help": "Make a picture: the picture alone, for the length below. Over the input: the picture on top of the "
                         "video connected to this node. Behind the input: the picture underneath it, showing through wherever "
                         "the video is transparent. With an input, the size and length come from the video."},
        "opacity": {"label": "Opacity", "min": 0, "max": 1, "default": 1.0,
                    "help": "How strong the picture is over or behind the input video, 0 to 1. Only used with an input."},
        "seconds": {"label": "Length (seconds)", "min": 0.1, "max": 600, "default": 5.0,
                    "help": "How long the picture runs when no input is connected."},
        "fps": {"label": "Frame rate", "min": 1, "max": 120, "default": 30,
                "help": "Frame rate when no input is connected. With an input, its frame rate is used."},
        "preset": {"label": "Size preset", "fills": SIZE_FILLS,
                   "help": "Pick a common size and the width and height fill in. Pick Custom to type your own. "
                           "Not used when an input is connected."},
        "width": {"label": "Width (px)", "default": 1920, "min": 16, "max": 8192,
                  "help": "Output width. Used with Height; overrides the preset. Not used when an input is connected."},
        "height": {"label": "Height (px)", "default": 1080, "min": 16, "max": 8192,
                   "help": "Output height. Used with Width; overrides the preset. Not used when an input is connected."},
    },
    "presets": PRESETS,
}


def register_arguments(parser):
    parser.description = (
        "Makes a video of a solid colour, a gradient, a checkerboard, SMPTE colour bars, a test pattern, an RGB ramp or noise. "
        "With no input it lasts --seconds; with an input video, the picture goes over it (--mode Over the input) or behind it "
        "(--mode Behind the input), at --opacity, and the input's size and length are used."
    )
    parser.add_argument("--pattern", choices=PATTERNS, default=PATTERNS[0],
                        help="What to draw. Default: Solid colour.")
    parser.add_argument("--color", type=str, default="#FF0000",
                        help="Colour as hex (#RRGGBB) for Solid colour, Gradient and Checkerboard. Default: #FF0000.")
    parser.add_argument("--mode", choices=MODES, default=MAKE,
                        help="Make a picture (default), Over the input, or Behind the input. The last two need an input video.")
    parser.add_argument("--opacity", type=float, default=1.0,
                        help="How strong the picture is over or behind the input, 0 to 1. Default: 1.")
    parser.add_argument("--seconds", type=float, default=5.0, help="Length in seconds, with no input. Default: 5.")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate, with no input. Default: 30.")
    parser.add_argument("--preset", type=str, default="1080p", choices=[*VIDEO_PRESETS.keys(), "custom"],
                        help="Named size (e.g. 1080p, instagram_reels), or 'custom' with --width and --height. Default: 1080p.")
    parser.add_argument("--width", type=int, default=None, help="Custom width in px. Use with --height; overrides --preset.")
    parser.add_argument("--height", type=int, default=None, help="Custom height in px. Use with --width; overrides --preset.")


def _hex(color: str) -> str:
    c = color.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in c):
        raise SystemExit(f"❌ --color must be a hex colour like #FF0000 (got {color!r}).")
    return c.upper()


def source_graph(pattern: str, w: int, h: int, fps: int, color: str) -> str:
    """The lavfi source for one pattern. Output size, rate and colour are already in it; the length comes from -t."""
    c = _hex(color)
    size = f"{w}x{h}"
    rate = f"{fps}"
    if pattern == "Solid colour":
        return f"color=c=0x{c}:s={size}:r={rate}"
    if pattern == "Gradient (colour to black)":
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        fade = "(1-X/W)"
        return (f"nullsrc=s={size}:r={rate},format=rgb24,"
                f"geq=r='{r}*{fade}':g='{g}*{fade}':b='{b}*{fade}'")
    if pattern == "Checkerboard":
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        cell = max(4, w // 16)
        on = f"mod(floor(X/{cell})+floor(Y/{cell}),2)"
        return (f"nullsrc=s={size}:r={rate},format=rgb24,"
                f"geq=r='{r}*{on}':g='{g}*{on}':b='{b}*{on}'")
    if pattern == "SMPTE colour bars":
        return f"smptebars=s={size}:r={rate}"
    if pattern == "SMPTE HD colour bars":
        return f"smptehdbars=s={size}:r={rate}"
    if pattern == "Test pattern":
        return f"testsrc2=s={size}:r={rate}"
    if pattern == "RGB ramp":
        return f"rgbtestsrc=s={size}:r={rate}"
    if pattern == "Noise":
        return f"nullsrc=s={size}:r={rate},noise=alls=100:allf=t+u"
    raise SystemExit(f"❌ Unknown pattern: {pattern}")


# The pictures are made in RGB and H.264 stores YUV. Convert with the BT.709 matrix the file is tagged with, so a player
# that reads the tags shows the colour asked for: white comes out #FFFFFF, not a grey-tinted #F9FBFA.
TO_YUV = "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p"
# The same conversion, keeping an alpha channel, for a picture that is laid over or under a video.
TO_YUVA = "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuva420p"


def run(args):
    if args.seconds <= 0:
        raise SystemExit("❌ --seconds must be above 0.")
    if args.fps <= 0:
        raise SystemExit("❌ --fps must be above 0.")
    source = getattr(args, "input", None)
    if args.mode != MAKE and source:
        return _over_input(args, source)
    if args.mode != MAKE:
        print("ℹ️  No input video is connected, so the picture is made alone.", flush=True)

    w, h = target_size(args)
    graph = f"{source_graph(args.pattern, w, h, args.fps, args.color)},{TO_YUV}"
    print(f"Making {args.seconds:g} s of {args.pattern.lower()} at {w}x{h}, {args.fps} fps.", flush=True)

    enc = h264_mp4_args(crf=18)
    enc = enc[:enc.index("-c:a")]          # video only: there is no sound in a generated picture
    command = ["ffmpeg", "-f", "lavfi", "-i", graph, "-t", f"{args.seconds:.3f}", *enc, args.output]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command,
                             args.output, args.output, duration_override=args.seconds)


def _over_input(args, source):
    """The picture laid over (or under) the input video: the input's size, length, frame rate and sound."""
    info = probe_video(source)
    w, h = even(info.width), even(info.height)
    fps = round(info.fps, 3) if info.fps else args.fps
    opacity = min(1.0, max(0.0, float(args.opacity)))
    picture = (f"{source_graph(args.pattern, w, h, fps, args.color)},"
               f"{TO_YUVA},colorchannelmixer=aa={opacity:.3f}")
    if args.mode == OVER:
        # The input is the base; the picture is laid on top of it.
        graph = f"[0:v]format=yuv420p[base];{picture}[pic];[base][pic]overlay=format=auto:shortest=1[v]"
    else:
        # A black base, the picture over it, and the input over that: the picture only shows where the input is transparent.
        graph = (f"color=c=black:s={w}x{h}:r={fps},format=yuv420p[black];{picture}[pic];"
                 f"[black][pic]overlay=format=auto[bg];[0:v]format=yuva420p[fg];"
                 f"[bg][fg]overlay=format=auto:shortest=1[v]")
    print(f"Laying {args.pattern.lower()} {args.mode.lower()} at {w}x{h}, opacity {opacity:g}.", flush=True)

    command = ["ffmpeg", "-i", source, "-filter_complex", graph, "-map", "[v]", "-map", "0:a?",
               *h264_mp4_args(crf=18), args.output]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command,
                             source, args.output, duration_override=info.duration)

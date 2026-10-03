from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress


def register_arguments(parser):
    parser.description = (
        "Forward-then-reverse ping-pong loop — the clip plays normally, then plays "
        "itself backwards, back to the start."
    )


def run(args):
    filter_complex = (
        "[0:v]split[va][vb];[vb]reverse[vr];[va][vr]concat=n=2:v=1:a=0[out_v];"
        "[0:a]asplit[aa][ab];[ab]areverse[ar];[aa][ar]concat=n=2:v=0:a=1[out_a]"
    )
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "[out_a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        args.output,
    ]
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

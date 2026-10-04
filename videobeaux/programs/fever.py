from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
   parser.description = (
        "Makes the video seem like a dream when you are sick with a bug."
    )
   print("✅ This program mode does not require additional arguments")

def run(args):

    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]shuffleplanes=map1=0:map3=2,smartblur=luma_radius=.6:lr=2.88:luma_strength=0.11:lt=-17:cr=0.93,amplify=radius=1.4:factor=4[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

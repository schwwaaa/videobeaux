from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
   parser.description = (
            "introduces uneven timing to simulate poorly animated sequences."
    )
   print("✅ This program mode does not require additional arguments")

def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]detelecine=first_field=bottom:pattern=5:start_frame=4[out_v]",
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

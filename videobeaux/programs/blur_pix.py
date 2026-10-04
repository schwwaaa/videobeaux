from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

def register_arguments(parser):
    parser.description = (
            "Applies a double-layered blur and pixelation combined effect."
    )
    print("✅ This program mode does not require additional arguments")


def run(args):
    command = [
        "ffmpeg",
        "-i", args.input,
        "-filter_complex", "[0:v]pixelize=width=1:w=9:height=1:h=1,lagfun=decay=0.97:planes=1,tmix=frames=19,chromashift=cbh=-152:cbv=95:crh=-79:crv=142:edge=wrap[out_v]", 
        "-map", "[out_v]",
        "-map", "0:a?",
        args.output
    ]
    
    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

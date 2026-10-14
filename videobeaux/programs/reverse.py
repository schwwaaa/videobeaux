from videobeaux.utils.ffmpeg_operations import run_ffmpeg_with_progress

AUDIO_CHOICES = ["Reversed", "Forward", "Mute"]

GUI_METADATA = {
    'args': {
        'audio': {
            'type': 'select', 'label': 'Audio', 'default': AUDIO_CHOICES[0], 'choices': AUDIO_CHOICES,
            'help': 'Reversed = the sound plays backwards with the picture (default) · Forward = keep the sound as it was · Mute = no sound.',
        },
    },
}

def register_arguments(parser):
    parser.description = (
        "Reverses the video.oediv eht sesreveR"
    )
    parser.add_argument("--audio", choices=AUDIO_CHOICES, default=AUDIO_CHOICES[0],
                        help="What to do with the sound: Reversed (default), Forward, or Mute.")

def run(args):
    audio = getattr(args, "audio", AUDIO_CHOICES[0])
    command = [
        "ffmpeg",
        "-y",
        "-i", args.input,
        "-vf", "reverse",
    ]
    if audio == "Reversed":
        command += ["-af", "areverse"]
    elif audio == "Mute":
        command += ["-an"]
    command += [args.output]

    run_ffmpeg_with_progress((command[:1] + ["-y"] + command[1:]) if args.force else command, args.input, args.output)

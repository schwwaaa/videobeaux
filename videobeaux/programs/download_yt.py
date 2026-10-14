import yt_dlp
# yt_dlp is dope, but the docs for the python module suck. 
# they say "oh, just read the official yt-dlp docs and it should just work"
# but, while the logic is the same, the param format is not exact
# for example - to include a subtitle file in the download via the yt-dlp cli tool, yt-dlp docs say to use --write-auto-subs
# but, the same option here is writeautomaticsub for no discernable reason
# dm us if you know why
# in the meantime, you need to check the source code AND the docs to use certain options

# https://pypi.org/project/yt-dlp/
# https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L181

GUI_METADATA = {
    'args': {
        'max_height': {'label': 'Max height (px)', 'min': 0, 'max': 2160, 'step': 120,
                       'help': 'Cap the picture height to keep files small (e.g. 720). 0 = best quality available (default).'},
    },
}

def register_arguments(parser):
    parser.description = (
            "downloads the yt video url provided in the --input arg as mp4. \n"
            "--output just takes a filename"
    )
    parser.add_argument("--max_height", type=int, default=0,
                        help="Maximum picture height in pixels (0 = best available, default).")

def run(args):
    max_h = int(getattr(args, "max_height", 0) or 0)
    fmt = "mp4" if max_h <= 0 else (f"bv*[height<={max_h}][ext=mp4]+ba[ext=m4a]/b[height<={max_h}][ext=mp4]/b[height<={max_h}]")
    ydl_opts = {
        'format': fmt,
        'outtmpl': f"{args.output}", #https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#output-template
        "writeautomaticsub":True # will include a vtt file. note: this won't work for some videobeaux functions that require an srt from vosk
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(args.input)
    

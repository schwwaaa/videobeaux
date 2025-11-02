# import os
# import json
# import time
# import subprocess
# import imageio_ffmpeg
# from vosk import Model, KaldiRecognizer, SetLogLevel
# from pathlib import Path
# import sys

# def register_arguments(parser):
#     parser.add_argument(
#         "-m", "--stt_model",
#         required=True,
#         type=str,
#         help="The file path to the vosk model being used. \n"
#         "Transcriptions will be saved with the same filename as the input video file, in the same directory.  as the input file. \n"
#         "This is to ensure compatibilty with other program modes that rely on the transcription. \n"
#         "--output is required for every program mode, but will be ignored here."
#         )

# # this piece is pulled almost verbatim from videogrep
# # maybe we could have just used subprocess and run videogrep --transcribe since it is already a dependancy
# # but it is here for archival purposes
# # big up to Sam Levigne aka antiboredom 
# # https://github.com/antiboredom/videogrep

# def run(args):
#     if args.output:
#         print("📢 NOTE: --output is required, but will be ignored. see transcraibe --help for more info. \n ")
#     MAX_CHARS = 36

#     start_time = time.time()

#     transcript_file = os.path.splitext(args.input)[0] + ".json"

#     if os.path.exists(transcript_file):
#         print(f"Transcription file '{transcript_file}' already exists")
#         sys.exit(1)


#     if not os.path.exists(args.input):
#         print("Could not find file", args.input)
#         return []

#     _model_path: str = 'defaultmodel'

#     if args.stt_model is not None:
#         _model_path = args.stt_model

#     if not os.path.exists(_model_path):
#         print("Could not find model folder")
#         exit(1)

#     print("Transcribing", args.input)
#     SetLogLevel(-1)

#     sample_rate = 16000
#     model = Model(_model_path)
#     rec = KaldiRecognizer(model, sample_rate)
#     rec.SetWords(True)

#     process = subprocess.Popen(
#         [
#             imageio_ffmpeg.get_ffmpeg_exe(),
#             "-nostdin",
#             "-loglevel",
#             "quiet",
#             "-i",
#             args.input,
#             "-ar",
#             str(sample_rate),
#             "-ac",
#             "1",
#             "-f",
#             "s16le",
#             "-",
#         ],
#         stdout=subprocess.PIPE,
#     )

#     tot_samples = 0
#     result = []
#     while True:
#         data = process.stdout.read(4000)
#         if len(data) == 0:
#             break
#         if rec.AcceptWaveform(data):
#             tot_samples += len(data)
#             result.append(json.loads(rec.Result()))
#     result.append(json.loads(rec.FinalResult()))

#     out = []
#     for r in result:
#         if "result" not in r:
#             continue
#         words = [w for w in r["result"]]
#         item = {"content": "", "start": None, "end": None, "words": []}
#         for w in words:
#             item["content"] += w["word"] + " "
#             item["words"].append(w)
#             if len(item["content"]) > MAX_CHARS or w == words[-1]:
#                 item["content"] = item["content"].strip()
#                 item["start"] = item["words"][0]["start"]
#                 item["end"] = item["words"][-1]["end"]
#                 out.append(item)
#                 item = {"content": "", "start": None, "end": None, "words": []}

#     if len(out) == 0:
#         print("No words found.")
#         return []

#     with open(transcript_file, "w", encoding="utf-8") as outfile:
#         json.dump(out, outfile)
    
#     end_time = time.time()
#     execution_time = end_time - start_time
#     print(f"Transcription took: {execution_time} seconds")

#     #return out
#     return [] 

import os
import json
import time
import subprocess
import imageio_ffmpeg
from vosk import Model, KaldiRecognizer, SetLogLevel
from pathlib import Path
import sys

# --------------------------
# CLI Args
# --------------------------
def register_arguments(parser):
    parser.add_argument(
        "-m", "--stt_model",
        required=True,
        type=str,
        help=("Path to the Vosk model directory. "
              "Use --json_out in batch mode to gather outputs in one folder.")
    )
    # DO NOT add --input or --output here; they come from the global parser.

    parser.add_argument(
        "--batch_dir",
        type=str,
        help="Directory containing videos to transcribe. Processes recursively."
    )
    parser.add_argument(
        "--json_out",
        type=str,
        default=None,
        help="If set, write all JSON transcripts to this folder. Created if missing."
    )
    parser.add_argument(
        "--emit_txt",
        action="store_true",
        help="Also write a .txt version of the transcript (one chunk per line)."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing transcript files if present."
    )


# --------------------------
# Core helpers
# --------------------------
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"}

def build_paths_for_output(input_video: Path, json_out_dir: Path | None) -> tuple[Path, Path]:
    """
    Returns (json_path, txt_path) for a given input video and optional json_out_dir.
    """
    base = input_video.stem
    if json_out_dir:
        json_out_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_out_dir / f"{base}.json"
    else:
        json_path = input_video.with_suffix(".json")

    txt_path = json_path.with_suffix(".txt")
    return json_path, txt_path


def transcribe_single(input_video: Path, model_path: Path, json_path: Path, emit_txt: bool, overwrite: bool) -> None:
    """
    Transcribes one file to JSON (and optionally TXT).
    """
    if not input_video.exists():
        print(f"⚠️  Missing input: {input_video}")
        return

    if json_path.exists() and not overwrite:
        print(f"⏭️  Exists, skipping JSON: {json_path}")
        if emit_txt:
            txt_path = json_path.with_suffix(".txt")
            if not txt_path.exists() or overwrite:
                # Try to (re)emit TXT from existing JSON
                try:
                    json_to_txt(json_path, txt_path)
                    print(f"📝 Wrote TXT: {txt_path}")
                except Exception as e:
                    print(f"⚠️  Failed TXT from existing JSON for {json_path}: {e}")
        return

    print(f"🎬 Transcribing: {input_video}")
    SetLogLevel(-1)

    sample_rate = 16000
    model = Model(str(model_path))
    rec = KaldiRecognizer(model, sample_rate)
    rec.SetWords(True)

    # ffmpeg pipes PCM to stdout
    process = subprocess.Popen(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-loglevel", "quiet",
            "-i", str(input_video),
            "-ar", str(sample_rate),
            "-ac", "1",
            "-f", "s16le",
            "-",
        ],
        stdout=subprocess.PIPE,
    )

    MAX_CHARS = 36
    result = []
    while True:
        data = process.stdout.read(4000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            result.append(json.loads(rec.Result()))
    result.append(json.loads(rec.FinalResult()))

    # Build chunked transcript like your original structure
    out = []
    for r in result:
        if "result" not in r:
            continue
        words = [w for w in r["result"]]
        item = {"content": "", "start": None, "end": None, "words": []}
        for w in words:
            item["content"] += w["word"] + " "
            item["words"].append(w)
            if len(item["content"]) > MAX_CHARS or w == words[-1]:
                item["content"] = item["content"].strip()
                item["start"] = item["words"][0]["start"]
                item["end"] = item["words"][-1]["end"]
                out.append(item)
                item = {"content": "", "start": None, "end": None, "words": []}

    if not out:
        print(f"⚠️  No words found for {input_video}")
        return

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"✅ Wrote JSON: {json_path}")

    if emit_txt:
        txt_path = json_path.with_suffix(".txt")
        json_to_txt(json_path, txt_path)
        print(f"📝 Wrote TXT: {txt_path}")


def json_to_txt(json_path: Path, txt_path: Path) -> None:
    """
    Convert our transcript JSON (list of chunks with 'content') into a human-friendly .txt.
    - One chunk per line
    - Preserves order
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Each item is a line; trim spaces; skip empties
    lines = []
    for item in data:
        content = (item.get("content") or "").strip()
        if content:
            lines.append(content)

    txt_path.parent.mkdir(parents=True, exist_ok=True)
    # Use '\n' newlines; if you want Windows CRLF, change to '\r\n'
    with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


# --------------------------
# Entry
# --------------------------
def run(args):
    if args.output:
        print("📢 NOTE: --output is accepted for compatibility, but ignored by this mode.\n")

    # Validate mutually exclusive input options
    single_input = args.input is not None
    batch_input = args.batch_dir is not None
    if (single_input and batch_input) or (not single_input and not batch_input):
        print("❌ Provide exactly one of: --input <file>  OR  --batch_dir <folder>")
        sys.exit(2)

    model_path = Path(args.stt_model)
    if not model_path.exists():
        print("❌ Could not find model folder:", model_path)
        sys.exit(1)

    json_out_dir = Path(args.json_out).resolve() if args.json_out else None
    if json_out_dir:
        json_out_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    if single_input:
        input_video = Path(args.input).resolve()
        json_path, _txt_path = build_paths_for_output(input_video, json_out_dir)
        if not input_video.exists():
            print("❌ Could not find file:", input_video)
            sys.exit(1)

        transcribe_single(
            input_video=input_video,
            model_path=model_path,
            json_path=json_path,
            emit_txt=args.emit_txt,
            overwrite=args.overwrite,
        )

    else:
        # Batch mode
        batch_root = Path(args.batch_dir).resolve()
        if not batch_root.exists() or not batch_root.is_dir():
            print("❌ --batch_dir is not a directory:", batch_root)
            sys.exit(1)

        files = [p for p in batch_root.rglob("*") if p.suffix.lower() in VIDEO_EXTS]
        if not files:
            print("⚠️  No media files found under:", batch_root)
        else:
            print(f"📁 Batch: found {len(files)} media files under {batch_root}")
        for p in files:
            json_path, _txt_path = build_paths_for_output(p, json_out_dir)
            transcribe_single(
                input_video=p,
                model_path=model_path,
                json_path=json_path,
                emit_txt=args.emit_txt,
                overwrite=args.overwrite,
            )

    elapsed = time.time() - start_time
    print(f"⏱️  Done in {elapsed:.2f}s")
    return []

import subprocess
import re
import sys
import tempfile
import time
from tqdm import tqdm
from pathlib import Path

def get_video_duration(input_file):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_file
        ],
        capture_output=True,
        text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        # Inputs without a container duration (e.g. a bare .srt, some raw
        # streams) report "N/A" — progress just can't show a percentage then.
        return 0.0

_FILTER_CACHE = None

def ffmpeg_has_filter(name):
    """True if the ffmpeg on PATH was built with the named filter.

    Some builds omit filters that depend on optional libraries (zscale ->
    libzimg, ass/subtitles -> libass, drawtext -> libfreetype), so programs
    use this to fail up front with a clear message instead of a cryptic
    "Filter not found" from deep in a filtergraph.
    """
    global _FILTER_CACHE
    if _FILTER_CACHE is None:
        try:
            out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                                 capture_output=True, text=True).stdout
        except OSError:
            out = ""
        _FILTER_CACHE = {parts[1] for parts in (ln.split() for ln in out.splitlines())
                         if len(parts) > 2 and len(parts[0]) <= 4}
    return name in _FILTER_CACHE

def time_to_seconds(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)

def run_ffmpeg_with_progress(command, input_file, output_file, show_ffmpeg_output=False, duration_override=None):
    # duration_override lets a caller that's only processing part of input_file
    # (e.g. trimming a sub-clip) report progress against the clip's own length
    # instead of the full source — otherwise out_time never reaches the
    # source's total duration and the bar appears to stall short of 100%.
    duration = duration_override if duration_override is not None else get_video_duration(input_file)
    print(f"Input duration: {duration:.2f} seconds")
    output_idx = len(command) - 1
    command = command[:output_idx] + ["-progress", "pipe:1"] + command[output_idx:]
    # ffmpeg's stderr goes to a temp file (not DEVNULL) so that when it
    # fails, the last few lines — which say *why* — can go into the error
    # instead of a bare exit code.
    err_file = None if show_ffmpeg_output else tempfile.TemporaryFile(
        mode="w+", encoding="utf-8", errors="replace")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if show_ffmpeg_output else err_file,
        bufsize=1,
        universal_newlines=True
    )
    # tqdm redraws its bar in place using carriage returns, which only works
    # on a real terminal. When stderr is piped (e.g. spawned by the GUI), each
    # \r-update gets read as its own line and re-printed as a new one, so the
    # bar appears to grow taller instead of updating in place. In that case,
    # emit plain "time=.../speed=..." lines instead — the same format ffmpeg's
    # own stats use, which the GUI already parses into a single progress bar.
    interactive = sys.stderr.isatty()
    pbar = None
    if interactive:
        pbar = tqdm(
            total=duration,
            unit="s",
            dynamic_ncols=True,
            bar_format="{l_bar}{bar} | {n:.2f}/{total:.2f}s [{elapsed}<{remaining}]"
        )
        pbar.set_description(f"🔨 Processing {Path(input_file).name}")

    start_wall = time.monotonic()
    # Previous report's (video-time, wall-time), used to compute speed as a
    # windowed rate between consecutive ticks rather than a cumulative
    # average since the process started. A cumulative average lets any
    # one-time startup cost (filter graph init, decoder startup) permanently
    # skew the number — a slow start drags it toward ~0x forever, while a
    # fast pass can read as an absurd multiple once amortized. Neither
    # reflects the current rate, which is what this is meant to show.
    prev_elapsed = 0.0
    prev_wall = start_wall

    def report(elapsed):
        nonlocal prev_elapsed, prev_wall
        if pbar is not None:
            increment = elapsed - pbar.n
            if increment > 0:
                pbar.update(min(increment, duration - pbar.n))
        else:
            now = time.monotonic()
            d_elapsed = elapsed - prev_elapsed
            d_wall = now - prev_wall
            speed = (d_elapsed / d_wall) if d_wall > 0 else 0.0
            prev_elapsed, prev_wall = elapsed, now
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            print(f"time={int(h):02d}:{int(m):02d}:{s:06.3f} speed={speed:.2f}x", file=sys.stderr, flush=True)

    try:
        out_time_re = re.compile(r"out_time=(\d+):(\d+):(\d+\.\d+)")
        current = 0.0

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            line = line.strip()
            match = out_time_re.match(line)
            if match:
                elapsed = min(time_to_seconds(*match.groups()), duration)
                if elapsed > current:
                    current = elapsed
                    report(current)

            elif line == "progress=end":
                break

        process.wait()
        if current < duration:
            current = duration
            report(current)
        if pbar is not None:
            pbar.close()

        if process.returncode != 0:
            reason = ""
            if err_file is not None:
                err_file.seek(0)
                lines = [ln.strip() for ln in err_file.read().splitlines() if ln.strip()]
                reason = "\n".join(lines[-10:])
            raise RuntimeError(
                f"❌ ffmpeg exited with code {process.returncode}"
                + (f"\n{reason}" if reason else "")
            )

        print(f"\n📺 Process Complete: {output_file} \n")

    except Exception as e:
        if pbar is not None:
            pbar.close()
        process.kill()
        raise e

def run_ffmpeg_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def run_ffmpeg_supercut(clips, input_file, output_file, force=False):
    """
    Concatenate a list of {'start', 'end'} clip ranges cut from a single
    input file into one output — a single ffmpeg trim+concat filter graph,
    driven through run_ffmpeg_with_progress so it reports progress the same
    way every other program does. Used in place of videogrep's own
    create_supercut(), which drives moviepy internally and has its own
    separate, unintegrated progress output.
    """
    if not clips:
        raise ValueError("No clips to concatenate")

    filter_parts = []
    concat_inputs = []
    for i, clip in enumerate(clips):
        start = float(clip['start'])
        end = float(clip['end'])
        filter_parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]")
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs.append(f"[v{i}][a{i}]")

    filter_complex = (
        ";".join(filter_parts) + ";" +
        "".join(concat_inputs) + f"concat=n={len(clips)}:v=1:a=1[v][a]"
    )

    command = [
        "ffmpeg",
        "-i", str(input_file),
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        str(output_file)
    ]
    if force:
        command = command[:1] + ["-y"] + command[1:]

    run_ffmpeg_with_progress(command, input_file, output_file)
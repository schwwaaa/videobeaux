# deinterlace

## Description
Turns interlaced footage into clean progressive frames. Interlaced video (old camcorders, broadcast recordings) stores each frame as two fields, so moving edges show a comb pattern. Deinterlacing weaves or interpolates the fields back into whole frames.

## Purpose
Old tape transfers and broadcast recordings that show combing on any movement.

## How It Works
1. **Method**
   `yadif` is quick and reliable. `bwdif` keeps a little more fine detail, but is slower.
2. **Frame rate**
   By default one output frame is made per input frame. `--double` makes one frame per field, which doubles the frame rate and gives the smoothest motion. The clip gets longer in frames, not in time.
3. **Encoding**
   The video is re-encoded as H.264. The audio is copied unchanged.

## Program Template
```bash
videobeaux -P deinterlace -i input.mp4 -o output.mp4 --method yadif
```

## Arguments
- **method**: `yadif` (default) or `bwdif`.
- **double**: one output frame per field (double frame rate).

## Real World Example
A VHS transfer that combs during camera pans:
```bash
videobeaux -P deinterlace -i tape_transfer.mp4 -o tape_clean.mp4 --method bwdif
```

## Technical Notes
- Progressive footage passes through with little change, so it is safe to run on any clip.
- Use `--double` only when you want the smoother motion: the file becomes twice as many frames.

# reverse
:contentReference[oaicite:1]{index=1}

## Description
Reverses the playback of the input video, producing a backward-motion effect.  
This simple but powerful manipulation can completely change the emotional or aesthetic tone of footage, turning ordinary actions into surreal rewinds, resets, or temporal loops.

## Purpose
`reverse` is designed for creators who want to:
- flip time direction for stylistic emphasis,  
- generate rewind moments or temporal reversals,  
- create looping effects by combining forward and reverse sequences,  
- enhance glitch, montage, or collage workflows,  
- build playful or cinematic transformations by reversing motion.

## How It Works
1. **Frame Order Inversion**  
   All frames in the source video stream are read, then written backwards.
2. **Audio Handling**  
   Depending on global Videobeaux settings and FFmpeg behavior, audio may be reversed or muted.  
   (Many workflows intentionally mute or replace audio for reverse sequences.)
3. **Encoding**  
   The final reversed output is encoded using global Videobeaux codec, CRF, and pixel-format settings.

## Program Template
```bash
videobeaux -P reverse -i input.mp4 -o output.mp4
```

## Arguments
- *(No additional program-specific arguments; uses global videobeaux options only.)*

## Real World Example
```bash
videobeaux -P reverse \
  -i myvideo.mp4 \
  -o reverse_styled.mp4
```

## Program Output
<video controls preload="metadata" style="max-width:100%; border-radius:8px; margin:1em 0;">
  <source src="https://github.com/schwwaaa/videobeaux/assets/7625379/74367227-6fee-455f-af36-804a1e6d6cb6" type="video/mp4">
  Your browser does not support the video tag.
</video>

## Technical Notes
- Perfect for reversible motion such as walking, pouring, splashing, spinning, or transitions.  
- Some codecs do not allow efficient reverse seeking; full decoding may be required.  
- Audio reversal is often undesirable unless explicitly intended, so many pipelines mute or replace the audio after reversing.  
- Large files may require significant memory or disk usage during reverse operations.

## Recommended Usage
- Rewind effects in music videos or narrative sequences.  
- Loop creation by combining forward + reversed versions of the same clip.  
- Glitch-art assemblies where time feels elastic or broken.  
- Transitions or visual punctuation in experimental edits.  
- Montage moments where reverse motion provides humor, shock, or surreal tone.

## Quality Tips
- For crisp reversed motion, use lower CRF values.  
- Pair with `looper_pro` to generate seamless mirrored loops.  
- Combine with `bad_contrast` or `double_cup` for stylized retro or dreamy rewinds.  
- Apply `reverse` before heavy effects if you want the *effects themselves* to accumulate in reverse order.  
- Apply `reverse` after stylistic effects if you want the look preserved but motion reversed.


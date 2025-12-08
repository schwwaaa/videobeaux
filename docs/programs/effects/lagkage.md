# lagkage

## Description
A JSON-driven multilayer video compositor that stacks, positions, resizes, mixes, sequences, and animates multiple media layers into a single rendered output.  
`lagkage` is the most powerful structural tool in Videobeaux, allowing complex collage-based edits without touching an editor timeline.

## Purpose
`lagkage` is designed for creators who want to:
- Build multi-layer compositions through JSON instead of a traditional NLE  
- Automate repetitive collage, mosaic, and layout generation  
- Mix videos of different sizes, formats, and aspect ratios  
- Control audio selection, muting, and sequencing  
- Create dense visual stacks for music videos, installations, and VJ systems  
- Generate hundreds of layouts for automated or procedural video art workflows  

## How It Works
1. **JSON Layout File (`--layout_json`)**  
   The layout file describes each layer:
   - filename  
   - position (x/y)  
   - size or scale  
   - opacity  
   - z-order  
   - type (video, image)  
   - audio mute flag  
   - mode (free, grid, fit, fill, etc.)
2. **Layer Sequencing (`--sequence_direction`)**  
   Defines how layers progress in time:
   - `forward`  
   - `reverse`  
   - other sequence logic depending on layout design
3. **Audio Mode (`--audio_mode`)**  
   Controls where final output audio comes from:
   - `base` → input `-i` base video's audio  
   - `all` → mix audio from all layers  
   - `first` → only the first layer  
   - `none` → mute output  
   - additional modes depending on project configuration
4. **Audio Source Override (`--audio_src`)**  
   Allows specifying a custom audio file or one of the layer files as the final mix source.
5. **Compositing & Rendering**  
   After building filtergraphs, `lagkage`:
   - aligns layers  
   - pads or scales  
   - composes them in order  
   - applies opacity  
   - writes unified audio  
   - encodes the final video with global Videobeaux settings

## Program Template
```bash
videobeaux -P lagkage \
  -i input.mp4 \
  -o output.mp4 \
  --layout_json VALUE \
  --sequence_direction VALUE \
  --audio_mode VALUE \
  --audio_src VALUE
```

## Arguments

- **layout_json** — Path to a JSON file describing all layers, sizes, positions, opacities, and behaviors.  
- **sequence_direction** — Controls temporal ordering of layer playback (e.g., `forward`, `reverse`).  
- **audio_mode** — Defines the audio strategy (`base`, `all`, `first`, `none`, etc.).  
- **audio_src** — Optional override for specifying which audio file to use as final output.

## Real World Example
```bash
videobeaux -P lagkage \
  -i myvideo.mp4 \
  -o lagkage_styled.mp4 \
  --layout_json EXAMPLE \
  --sequence_direction EXAMPLE \
  --audio_mode EXAMPLE \
  --audio_src EXAMPLE
```

## Program Output
_Program output video not yet linked._

## Technical Notes
- JSON structure is strict — malformed layouts will cause FFmpeg filtergraph errors.  
- Large numbers of layers may significantly increase render time.  
- Mixed-resolution layers are automatically managed, but explicit sizing in JSON gives better control.  
- Audio mixing behavior varies depending on `audio_mode` and per-layer mute flags.  
- Layers can be animated if JSON includes frame-range-based or time-based instructions (depending on version).  
- Works extremely well in automated pipelines due to pure declarative structure.

## Recommended Usage
- Multi-video mosaics, walls, and grids.  
- Dense collage compositions for live visual systems.  
- Automated layout generation tools (e.g., Procedural 30-layout batches).  
- Narrative video art where positioning and scaling shift across cuts.  
- Social-media variants (reels, stories, square layouts) using preset JSON templates.  
- Long-form music videos with high-density sampling or montage.

## Quality Tips
- Keep JSON clean and validated before rendering large batches.  
- Use absolute pixel sizes for precision; use percentages for flexibility.  
- For crisp compositing, pre-normalize all input files using `convert_dims` or `convert`.  
- For advanced lighting looks, apply `lut_apply` to individual layers before compositing in lagkage.  
- For glitch workflows, combine `lagkage` with moshers (`crossmosh`, `bad_predator`, etc.) at layer level.


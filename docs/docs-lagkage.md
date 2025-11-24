# `lagkage` – JSON‑driven layered compositor for videobeaux

`lagkage` is a videobeaux program that lets you build complex, multi‑layer video compositions from a **single JSON file**.

You define:

- A **base video** (passed via `-i` as usual)
- A set of **layers** (images, GIFs, or videos) in a JSON layout file
- Per‑layer properties: position, size, opacity, zoom, crop, audio gain
- Global behavior: sequence ordering, audio mix mode

`lagkage` then builds an ffmpeg filtergraph that:

- Scales, crops, and blends each layer into the base frame
- Treats GIFs as animated overlays (pre‑processed to loop for the base duration)
- Handles audio according to your chosen mode (base/json/all/external/none)
- Optionally applies **per‑layer audio gain**, so you can do a rough pre‑mix
  directly from the JSON without opening a DAW


---

## 1. CLI usage

From your videobeaux project root:

```bash
videobeaux -P lagkage \
  -i media/base.mp4 \
  -o out/composite.mp4 \
  --layout-json lagkage_layouts/layout_ex01_logo_corner.json \
  --force
```

### Arguments

- `-i, --input`  
  Base video to composite onto. **Required**.

- `-o, --output`  
  Final rendered video. **Required**.

- `--layout-json PATH`  
  Path to a JSON file that describes all overlay layers. **Required**.

- `--sequence-direction {forward,backward,random}`  
  Optional override for the order in which layers are applied. If omitted, the
  layout JSON’s own `sequence_direction` is used.

- `--audio-mode {base,all,json_only,external,none}`  
  How to construct the final audio track:

  - `base` (default) – only the base video’s audio. JSON layers are visual only.
  - `all` – mix **base audio + all JSON layer audio** together.
  - `json_only` – ignore the base audio, use only JSON layer audio.
  - `external` – ignore base + JSON audio, use the file supplied via `--audio-src`.
  - `none` – no audio at all (silent output).

- `--audio-src PATH`  
  Path to an external audio file. Only used when `--audio-mode=external`.

- `--force`  
  From the global videobeaux CLI: forces overwrite of existing outputs and adds
  `-y` to ffmpeg under the hood.


---

## 2. Layout JSON format

A layout JSON looks like this at the top level:

```json
{
  "sequence_direction": "forward",
  "layers": [
    {
      "layer_number": 1,
      "name": "logo",
      "filename": "../media/reem.png",
      "type": "img",
      "mode": "place",
      "place": "top_right",
      "size": 18,
      "opacity": 0.95
    }
  ]
}
```

### 2.1 Top level

- `sequence_direction` (string, optional)

  Controls how `lagkage` orders the layers before applying them:

  - `"forward"` – smallest `layer_number` first (default)
  - `"backward"` – largest `layer_number` first
  - `"random"` – random permutation of layers

  You can override this per‑run using `--sequence-direction` on the CLI.

- `layers` (array, **required**)

  Each element is a **layer object** describing one overlay media item.


### 2.2 Per‑layer fields

All layers share a common set of fields. Some are optional depending on mode.

#### Identity and source

- `layer_number` (int, **recommended**)

  Used for ordering and for sequence modes. Lowest layer_number is “first” in
  forward mode. If omitted, it defaults to 0 for sorting, but it’s best to set
  explicit numbers.

- `name` (string, optional)

  Short human‑readable label for the layer. Not used by the code, but useful
  for documentation.

- `filename` (string, **required**)

  Path to the media file for this layer. Resolution rules:

  - Absolute paths (`/Users/you/...`) are used as‑is.
  - URLs (`https://...`) are passed directly to ffmpeg.
  - Paths starting with `'../media/'` are normalized to `media/...` **relative
    to your project root**.
  - Paths starting with `'media/'` are also treated as project‑root relative.
  - Any other relative path is treated as **layout‑relative**:
    resolved against the folder that contains the JSON.

- `type` (string, **required**)

  The kind of media:
  - `"img"`  – PNG/JPEG/etc.; single frame, no audio
  - `"gif"`  – animated GIF; pre‑processed to a looping RGBA video
  - `"video"` – standard video file; may contain audio

  This mainly affects whether we run the GIF preprocessing pipeline.

#### Positioning: `mode`, `place`, `pos_x`, `pos_y`

A layer can be positioned in **place** mode (logical corners/center) or in
**free** mode (explicit pixel coordinates).

- `mode` (string, **required**)

  - `"place"` – snap the layer into a logical slot:
    - uses `place`
  - `"free"` – place the layer at exact coordinates:
    - uses `pos_x`, `pos_y`

- `place` (string, required if `mode="place"`)

  One of:

  - `"top_left"`
  - `"top_right"`
  - `"bottom_left"`
  - `"bottom_right"`
  - `"center"`

- `pos_x`, `pos_y` (int, required if `mode="free"`)

  Pixel coordinates in the **base video’s pixel space**. (0,0) is top‑left of
  the base frame. These are the top‑left of the scaled/cropped layer box.

  You *can* push a layer partially or fully off‑screen by using negative values
  or values greater than the base width/height.


#### Size and opacity

- `size` (float, optional; default `100`)

  Percentage of the **base video width** that this layer should occupy. The
  layer is scaled to:

  ```text
  box_w = base_width * (size / 100)
  box_h = box_w / aspect_ratio
  ```

  Both are forced to even integers (necessary for some codecs).

- `opacity` (float, optional; default `1.0`)

  Range `[0.0, 1.0]`. Implemented using `colorchannelmixer` on the layer’s
  alpha channel before overlay:

  - `1.0` – fully opaque
  - `0.5` – half transparent
  - `0.0` – fully transparent (invisible)


#### Zoom and crop

These operate in **layer space** before the final overlay.

- `zoom` (float, optional; default `1.0`)

  - `1.0` – no zoom (layer fits exactly inside the computed `box_w x box_h`)
  - `>1.0` – zoom in; layer is scaled up to `zoom * box` then center‑cropped
    back down to the box. This gives the effect of “zooming inside” a fixed
    PIP area.

- `crop_x`, `crop_y`, `crop_w`, `crop_h` (float, optional)

  **Percentages** of the original source width/height, all in `[0,100]`.

  If all four are present, lagkage applies:

  ```text
  crop=in_w*crop_w/100 : in_h*crop_h/100 : in_w*crop_x/100 : in_h*crop_y/100
  ```

  This happens *before* zoom/scale. Use this to punch out a region from a
  larger frame (for example, turning a full‑frame video into a “face cam” PIP).


#### Per‑layer audio gain

These fields only matter if:

- the layer’s media actually has audio (e.g. `type: "video"` with an audio stream),
- and `--audio-mode` is `all` or `json_only` so layer audio is in the mix.

- `audio_gain_db` (float, optional)

  Gain in decibels applied to the layer’s audio *before* mixing:

  - `0`   – keep original level
  - `-6`  – roughly “half as loud” perceptually
  - `+3`  – a bit louder
  - `+12` – very loud / likely to clip unless sources are quiet

- `audio_gain` (float, optional)

  Linear multiplier, converted internally to dB as:

  ```text
  audio_gain_db = 20 * log10(audio_gain)
  ```

  Only used if `audio_gain_db` is not set.  
  For example, `audio_gain: 0.5` ≈ `-6.02 dB`.


---

## 3. Audio behavior in detail

### 3.1 Modes

- `--audio-mode base` (default)

  - Map `0:a?` (base audio only).
  - JSON layers are *visual only*; per‑layer audio gains are ignored.

- `--audio-mode all`

  - Take audio from:
    - base input (index 0) if it has audio
    - all JSON layers whose preprocessed media has audio
  - Apply **per‑layer gains** (where specified) on JSON layers.
  - Use `amix` to combine all sources into a single output stream.

- `--audio-mode json_only`

  - Ignore base audio completely.
  - Mix only JSON layer audio (with per‑layer gains) via `amix`.

- `--audio-mode external`

  - Append `--audio-src PATH` as an extra ffmpeg input.
  - Map only that input’s audio (`N:a?`) to the output.
  - JSON layer audio and base audio are ignored.

- `--audio-mode none`

  - Add `-an` to ffmpeg.
  - Output video is silent.


### 3.2 When do per‑layer gains matter?

Per‑layer audio gains (`audio_gain_db` / `audio_gain`) are applied:

- only on JSON layers that actually have an audio stream, and
- only when `--audio-mode` is `all` or `json_only`.

They do **not** affect:

- the base input audio (there’s currently no `base_audio_gain_db`),
- the external audio when `--audio-mode=external`,
- GIF overlays (their preprocessed videos are silent),
- image layers (no audio).


---

## 4. GIF handling

GIFs are pre‑processed before the main pass so the compositor can treat them
like normal video streams with alpha.

For each `type: "gif"` layer:

1. lagkage runs a helper ffmpeg command that:
   - loops the GIF (`-stream_loop -1`, `-ignore_loop 0`)
   - clamps to the base duration using `-t base_duration`
   - forces even dimensions with `scale=trunc(iw/2)*2:trunc(ih/2)*2`
   - converts to RGBA pixels (`format=rgba`)
   - writes a `.mov` with `qtrle` codec and **alpha preserved**
2. The resulting `.mov` is used as the actual overlay source.

This is why animated GIFs loop smoothly across the entire base clip and retain
their transparency when overlaid.


---

## 5. Path resolution rules

Given a `layout_exNN.json` at:

```text
lagkage_layouts/layout_exNN_*.json
```

and a layer `filename` value, lagkage resolves paths as follows:

1. If `filename` contains `"://"` → treat as URL and pass directly to ffmpeg.
2. If `filename` is an absolute path (e.g. `/Users/you/file.mp4`) → use as‑is.
3. If `filename` starts with `"../media/"` → normalize to `media/...` relative
   to your project root.
4. If `filename` starts with `"media/"` → treat as project‑root relative.
5. Otherwise → resolve relative to the **layout JSON’s directory**.


---

## 6. Example layouts & commands

This repo includes a set of example layouts and matching commands that showcase:

- place vs free mode
- cropping and zoom
- animated GIF overlays
- multiple layers with different sizes & opacities
- different `sequence_direction` values
- all audio modes, including per‑layer gain

See:

- `lagkage_layouts/` – 20 example layout JSON files (layout_ex01_*.json … layout_ex20_*.json)
- `lagkage_examples_full.txt` – example commands, one per layout

You can copy one example, tweak the filenames to match your media, and then
iterate from there.

---

## 7. Minimal “hello lagkage” example

`lagkage_layouts/layout_ex01_logo_corner.json`:

```json
{
  "sequence_direction": "forward",
  "layers": [
    {
      "layer_number": 1,
      "name": "logo_corner",
      "filename": "../media/reem.png",
      "type": "img",
      "mode": "place",
      "place": "top_right",
      "size": 18,
      "opacity": 0.95
    }
  ]
}
```

Command:

```bash
videobeaux -P lagkage   -i media/base.mp4   -o out/ex01_logo_corner.mp4   --layout-json lagkage_layouts/layout_ex01_logo_corner.json   --audio-mode base   --force
```

This is the simplest setup:

- Base video at `media/base.mp4`
- One PNG logo (`reem.png`) in the top‑right corner
- Base audio only
- No zoom/crop or audio mixing yet

From here, add more layers, switch to `audio-mode=all`, and start using
`audio_gain_db` to explore full lagkage functionality.

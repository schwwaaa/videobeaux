# convert_dims

## Description
Converts the dimensions of a video to a chosen preset (e.g., 1080p, instagram_reels, tiktok_video) and applies a configurable aspect-ratio handling mode (pad, fit, fill, fill_crop, stretch).  
Supports portrait overrides, crop/pad anchoring, custom pad color, and scaling kernel selection.

## Purpose
`convert_dims` provides a predictable, explicit way to resize video assets into standardized resolutions for:
- social platforms (Reels, Shorts, TikTok, Stories),
- broadcast or web delivery,
- square or portrait exports,
- ultrawide and cinema formats,
- archival normalization.

It gives direct control over **how** the aspect ratio is treated: padded, stretched, cropped, or fit.

## How It Works
1. **Preset Selection**  
   `--preset` chooses a named dimension from a predefined list (e.g., `1080p`, `square1080`, `instagram_reels`, `portrait4k`, `ultrawide1440`, etc.).  
   Each preset maps to a fixed width/height pair.
2. **Portrait Override**  
   `--portrait-full` forces a 9:16 portrait output based on the preset’s larger side, using a full-frame cover + crop (fill_crop behavior).
3. **Mode Handling**  
   `--mode` controls aspect-ratio handling:
   - `pad` – keep AR, fit inside target, pad with color as needed.  
   - `fit` – keep AR, fit inside target, no padding (may not fill entire frame).  
   - `fill` / `fill_crop` – cover the frame and center-crop to the target size.  
   - `stretch` – ignore AR, stretch directly to target dimensions.

   If `--mode` is not set, `--translate` (deprecated) chooses between:
   - `yes` → `stretch`  
   - `no`  → `pad`
4. **Anchor & Padding**  
   `--anchor` biases **where** crop or pad happens (`center`, `top`, `bottom`, `left`, `right`, `top_left`, etc.).  
   `--pad-color` defines the color of any added borders.
5. **Scaling Quality**  
   `--scale-flags` selects the FFmpeg scale kernel (`lanczos`, `bicubic`, `bilinear`, `neighbor`), affecting sharpness and performance.
6. **Encoding & Output**  
   - Output filename is resolved to match `--output-format` extension.  
   - Video is encoded via libx264 (`yuv420p`, ~5000k, `medium` preset) with AAC audio and `+faststart` for streaming-friendly MP4/MOV.

## Program Template
    videobeaux -P convert_dims \
      -i input.mp4 \
      -o output.mp4 \
      --output-format VALUE \
      --preset VALUE \
      --mode VALUE \
      --translate VALUE \
      --anchor VALUE \
      --pad-color VALUE \
      --scale-flags VALUE \
      --portrait-full

## Arguments

- **output-format** — Required. Output file format/extension (e.g., `mp4`, `mov`). If the `-o` path has a different suffix, it is replaced with this.  
- **preset** — Required. Named dimension preset (e.g., `1080p`, `square1080`, `instagram_reels`, `tiktok_video`, `ultrawide1440`, etc.). Each maps to a specific width/height.  
- **mode** — Aspect-ratio handling mode:
  - `pad` – maintain AR, fit inside target, pad with color.  
  - `fit` – maintain AR, fit inside target, no padding.  
  - `fill`, `fill_crop` – cover target and center-crop based on `anchor`.  
  - `stretch` – ignore AR and stretch to the exact width/height.  
- **translate** — Deprecated compatibility flag. When `--mode` is not set:
  - `yes` → behaves like `stretch`.  
  - `no`  → behaves like `pad`.  
- **anchor** — Crop/pad bias position:
  - `center`, `top`, `bottom`, `left`, `right`,  
  - `top_left`, `top_right`, `bottom_left`, `bottom_right`.  
  Affects where the image sits when padding or cropping.  
- **pad-color** — Hex color for padding borders in `pad` mode (e.g., `#000000`, `#FFFFFF`).  
- **scale-flags** — Scaling kernel: `lanczos`, `bicubic`, `bilinear`, or `neighbor`. Controls quality vs speed.  
- **portrait-full** — When present, forces a 9:16 full-frame portrait output using the preset’s larger dimension as height and a derived width, then uses a cover + crop mode (effectively `fill_crop`).

### Available Presets

Each preset maps to a `(width, height)` pair:
- `sd` – 320×240  
- `720hd` – 640×360  
- `1080hd` – 960×540  
- `widescreen` – 320×180  
- `portrait1080` – 1080×1620  
- `480p` – 640×480  
- `576p` – 720×576  
- `720p` – 1280×720  
- `1080p` – 1920×1080  
- `1440p` – 2560×1440  
- `4k` – 3840×2160  
- `8k` – 7680×4320  
- `vga` – 640×480  
- `qvga` – 320×240  
- `wvga` – 800×480  
- `svga` – 800×600  
- `xga` – 1024×768  
- `wxga` – 1280×800  
- `sxga` – 1280×1024  
- `uxga` – 1600×1200  
- `wuxga` – 1920×1200  
- `qwxga` – 2048×1152  
- `qhd` – 2560×1440  
- `wqxga` – 2560×1600  
- `5k` – 5120×2880  
- `portrait720` – 720×1280  
- `portrait4k` – 2160×3840  
- `square1080` – 1080×1080  
- `square720` – 720×720  
- `cinema4k` – 4096×2160  
- `ultrawide1080` – 2560×1080  
- `ultrawide1440` – 3440×1440  
- `instagram_feed` – 1080×1080  
- `instagram_reels` – 1080×1920  
- `instagram_stories` – 1080×1920  
- `tiktok_video` – 1080×1920  
- `youtube_standard` – 1920×1080  
- `youtube_shorts` – 1080×1920  
- `facebook_feed` – 1080×1080  
- `facebook_stories` – 1080×1920  
- `twitter_video` – 1280×720  
- `twitter_square` – 1080×1080  
- `linkedin_video` – 1920×1080  
- `linkedin_square` – 1080×1080  
- `snapchat_video` – 1080×1920  
- `pinterest_video` – 1080×1920  
- `pinterest_square` – 1000×1000  

## Real World Example
    videobeaux -P convert_dims \
      -i myvideo.mp4 \
      -o convert_dims_instareel.mp4 \
      --output-format mp4 \
      --preset instagram_reels \
      --mode fill_crop \
      --anchor center \
      --pad-color "#000000" \
      --scale-flags lanczos \
      --portrait-full

## Technical Notes
- Dimensions are always adjusted to even values to remain codec-safe.  
- `portrait-full` effectively overrides `mode` to a full-frame, cover-style portrait crop while honoring the preset’s size.  
- `scale-flags=lanczos` offers high-quality resizing at the cost of some speed.  
- FFmpeg is called with:
  - `-c:v libx264`, `-b:v 5000k`, `-pix_fmt yuv420p`, `-preset medium`  
  - `-c:a aac`, `-b:a 160k`, `-ar 48000`, `-movflags +faststart`  
- `--force` (global Videobeaux argument) controls overwrite; if not set, existing files cause an error.

## Recommended Usage
- Generating social-media-optimized versions (Reels, Shorts, Stories, TikTok).  
- Converting to square or portrait outputs while controlling crop bias via `anchor`.  
- Quickly standardizing deliverables to 1080p, 4K, or other common presets.  
- Converting landscape footage into vertical 9:16 promo clips using `--portrait-full`.

## Quality Tips
- Use `mode=pad` with a neutral `pad-color` when you want to preserve entire frames without cropping.  
- Use `mode=fill_crop` for platform-native aspect ratios where filling the frame is more important than preserving the entire source frame.  
- Set `anchor=top` or `anchor=bottom` for content where the action is biased toward one edge (e.g., heads near the top).  
- Keep `scale-flags=lanczos` for master/delivery renders; drop to `bicubic` or `bilinear` for faster, iterative tests.  
- Always verify the final AR and framing visually after using `stretch` to avoid unwanted distortion.

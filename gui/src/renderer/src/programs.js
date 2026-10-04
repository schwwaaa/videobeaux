/**
 * Program registry for videobeaux GUI.
 * Each program matches a Python module in videobeaux/programs/.
 *
 * Arg types: 'text' | 'number' | 'select' | 'file' | 'checkbox'
 * File subtypes: 'dir' (folder picker) | 'video' (also renders a connectable
 * graph handle on EffectNode, in addition to the file-picker fallback)
 */

export const CATEGORIES = [
  {
    id: 'glitch',
    label: 'Glitch & Corruption',
    color: '#d52c91',
    programs: [
      { id: 'bad_animation',     label: 'Bad Animation',     description: 'Broken-pulldown judder — wrong telecine timing makes frames stutter and comb', args: [] },
      { id: 'bad_contrast',      label: 'Bad Contrast',      description: 'Harsh blend-mode contrast corruption (hard-mix, vivid-light, exclusion)', args: [] },
      { id: 'digital_boss',      label: 'Digital Boss',      description: 'Hue/saturation shift plus extreme frame-difference amplification — a busted, blown-out digital look', args: [] },
      { id: 'xrgb',              label: 'XRGB',              description: 'Stacked red/green/blue channel displacements — heavy RGB tearing', args: [] },
      {
        id: 'crossmosh',
        label: 'Crossmosh',
        description: 'Real datamosh: decoder state corruption between two clips',
        args: [
          { name: 'b-input',  label: 'B Clip (Second Video)', type: 'file', subtype: 'video', required: true,  help: 'The second clip that gets datamoshed into' },
          { name: 'codec',    label: 'Codec',                 type: 'select', required: false, choices: ['libxvid', 'mpeg4'], default: 'mpeg4',
            help: 'libxvid gives better results but needs an ffmpeg build with it — most Homebrew installs don\'t have it' },
          { name: 'mode',     label: 'Mode',                  type: 'select', required: false, choices: ['proto', 'smear'], default: 'proto' },
          { name: 'qscale',   label: 'Q Scale',               type: 'number', required: false, default: 3.0,  min: 1,   max: 31,  help: 'Quality scale — lower is better' },
          { name: 'gop',      label: 'GOP Size',              type: 'number', required: false, default: 9999, min: 1,              help: 'GOP interval (keyframe distance)' },
          { name: 'frames',   label: 'Smear Frames',          type: 'number', required: false, default: 9,    min: 1,              help: '[smear] tmix frame count' },
          { name: 'decay',    label: 'Smear Decay',           type: 'number', required: false, default: 0.90, min: 0,   max: 1,   help: '[smear] lagfun decay 0–1' }
        ]
      },
      { id: 'pixel_sort',        label: 'Pixel Sort',        description: 'Glitch-art pixel sorting — bright pixels smear into sorted streaks', args: [] },
      { id: 'vhs_tracking',      label: 'VHS Tracking Error', description: 'Horizontal tracking-jitter wobble plus chroma bleed, like a worn VHS tape', args: [] },
      { id: 'chromatic_pulse',   label: 'Chromatic Pulse',   description: 'Animated chromatic aberration that pulses over time', args: [] },
      { id: 'deep_fry',          label: 'Deep Fry',          description: 'Blown-out saturation/contrast, oversharpened, deep-fried meme look', args: [] },
      { id: 'twociz',            label: 'Twociz',            description: 'Extreme frame-difference amplification with a blue chroma-key knockout', args: [] },
      { id: 'twociz_pro',        label: 'Twociz Pro',        description: 'Frame-difference amplification and blue chroma-key knockout, with controls', args: [] },
      { id: 'splitting',   label: 'Splitting',     description: 'Shuffles vertical pixel slices and blends them with the original — damaged-tape tearing', args: [] },
      { id: 'splitting_pro', label: 'Splitting Pro', description: 'Pixel-slice shuffling with direction (vertical/horizontal/block) and slice-size controls', args: [] },
      { id: 'slight_smear',        label: 'Slight Smear',       description: 'Small red/green/blue channel offsets with wrapped edges — a subtle colour smear', args: [] },
      { id: 'blur_pix',            label: 'Blur Pix',           description: 'Pixelization with frame lag/mixing and chroma shift — smeared blocky blur', args: [] },
      { id: 'warp', label: 'Warp', description: 'Swirl, bulge, pinch, ripple, kaleidoscope and mirror distortions, optionally animated', args: [] },
      { id: 'flow_warp', label: 'Flow Warp', description: 'Optical-flow smear/push — pixels drag along motion like a datamosh melt — or a color flow view', args: [] },
      { id: 'glitch_tear', label: 'Glitch Tear', description: 'RGB channel split plus horizontal tears and scanline dimming, re-rolled every frame', args: [] },
      { id: 'weak_signal', label: 'Weak Signal', description: 'Edge-of-reception transmission: skew, colour misregistration, noise, streaks and bursts of static', args: [] },
      { id: 'vhs_camcorder', label: 'VHS Camcorder', description: 'Home-video camcorder look: soft chroma, tape noise, a rolling tracking band and the on-screen PLAY / date stamp', args: [] },
      { id: 'crt_monitor', label: 'CRT Monitor', description: 'Old TV tube: curved glass, scanlines, RGB shadow mask, glow and a dark vignette', args: [] }
    ]
  },
  {
    id: 'trails',
    label: 'Trails & Echoes',
    color: '#ff9f1c',
    programs: [
      { id: 'ghostee',           label: 'Ghostee',           description: 'Frame-difference amplification with colour balance — moving edges glow and ghost', args: [] },
      { id: 'lsd_feedback',      label: 'LSD Feedback',      description: 'Weighted multi-frame blend (including negative weights) — trippy feedback trails', args: [] },
      { id: 'lsd_feedback_pro',  label: 'LSD Feedback Pro',  description: 'Multi-frame feedback blend with a configurable frame count', args: [] },
      { id: 'double_cup',        label: 'Double Cup',        description: 'Heavy median smear blended with a weighted multi-frame mix — sludgy double image', args: [] },
      { id: 'mirror_delay',         label: 'Mirror Delay',         description: 'A mirrored copy blended with a weighted multi-frame delay mix', args: [] },
      { id: 'frame_delay_pro1',     label: 'Frame Delay Pro 1',    description: 'Blends a configurable number of past frames into the output — dreamy echo trail', args: [] },
      { id: 'frame_delay_pro2',     label: 'Frame Delay Pro 2',    description: 'Lagging trail with configurable decay and YUV plane selection', args: [] },
      { id: 'fever',                label: 'Fever',                description: 'Channel-plane shuffling with a frame-difference boost — feverish dream look', args: [] },
      { id: 't1000',             label: 'T-1000',            description: 'Temporal median smoothing with RGB offsets — liquid-mercury shimmer on motion', args: [] },
      { id: 'smudge',              label: 'Smudge',             description: 'Temporal median — moving subjects smear and melt into the background', args: [] },
      { id: 'repainting',          label: 'Repainting',         description: 'Median repaint blended with a multi-frame mix — painterly, smeared motion', args: [] },
      { id: 'long_exposure', label: 'Long Exposure', description: 'A slowly fading average of past frames — moving things smear into ghostly trails', args: [] },
      { id: 'rgb_time_split', label: 'RGB Time Split', description: 'Red channel is now, green and blue lag behind — motion leaves rainbow fringes', args: [] },
      { id: 'feedback_loop', label: 'Feedback Loop', description: 'Video feedback: the output is fed back zoomed, rotated, shifted and hue-shifted each frame so the picture spirals into itself', args: [] },
      { id: 'key_feedback', label: 'Key Feedback', description: 'Video feedback with two keys — a luma/color Insert key picks what enters the loop, a Feedback key picks what survives each pass — plus zoom, rotate, shift and hue shift', args: [] }
    ]
  },
  {
    id: 'temporal',
    label: 'Time & Motion',
    color: '#ff6847',
    programs: [
      {
        id: 'speed',
        label: 'Speed',
        description: 'Change playback speed without pitch-shifting audio',
        args: [
          {
            name: 'speed_factor',
            label: 'Speed Factor',
            type: 'number',
            required: true,
            default: 1.0,
            min: 0.5,
            help: '>1 speeds up, <1 slows down. Must be ≥ 0.5'
          }
        ]
      },
      { id: 'reverse',              label: 'Reverse',              description: 'Reverse the video', args: [] },
      { id: 'boomerang',            label: 'Boomerang',            description: 'Forward-then-reverse ping-pong loop', args: [] },
      { id: 'time_ramp',            label: 'Time Ramp',            description: 'Variable speed ramp within one clip (e.g. slow-mo into a speed-up), unlike the flat Speed effect', args: [] },
      { id: 'freeze_punch',         label: 'Freeze Punch',         description: 'Freezes on detected audio peaks then resumes — a punchy freeze-frame emphasis edit', args: [] },
      { id: 'strobe_cut',           label: 'Strobe Cut',           description: 'Periodic flash/strobe brightness spikes at a configurable interval', args: [] },
      { id: 'stutter_pro',          label: 'Stutter Pro',          description: 'Replaces frames with random picks from the last N frames', args: [] },
      { id: 'nostalgic_stutter',    label: 'Nostalgic Stutter',    description: 'Random-frame stutter with chroma shift and multi-frame mixing, like a corrupted file', args: [] },
      { id: 'overexposed_stutter',  label: 'Overexposed Stutter',  description: 'Hard blend modes with random-frame repeats and lag — blown-out corrupted stutter', args: [] },
      { id: 'looper_pro',           label: 'Looper Pro',           description: 'Repeats a chosen segment (start frame + length) a set number of times', args: [] },
      { id: 'frame_interpolate', label: 'Frame Interpolate', description: 'Paints in-between frames: smoother motion (30→60 fps) or smooth slow motion. Slow on long clips',          args: [] },
      { id: 'scrolling_pro',        label: 'Scrolling Pro',        description: 'Scroll the picture horizontally and/or vertically at a set speed', args: [] },
      { id: 'broken_scroll',        label: 'Broken Scroll',        description: 'Amplified frame differences plus a slow vertical scroll — rolling broken-tracking look', args: [] },
      { id: 'slit_scan', label: 'Slit-Scan', description: 'Different parts of the frame show different moments in time — rows, rings, columns or waves of delay', args: [] },
      { id: 'tunnel', label: 'Tunnel', description: 'The picture wrapped around the inside of a tunnel you fly down', args: [] },
      { id: 'little_planet', label: 'Little Planet', description: 'Polar-coordinate \'tiny planet\' — the bottom of the picture becomes a small round world with sky all around', args: [] },
      { id: 'strobe_hold', label: 'Strobe Hold', description: 'Stroboscope: hold each picture for N frames (stuttering low-frame-rate look), with optional blink color and random holds', args: [] },
      { id: 'freeze_frame', label: 'Freeze Frame', description: 'Freeze the picture at a chosen moment — hold in place (same length) or insert the still (longer clip, silence under it)', args: [] }
    ]
  },
  {
    id: 'look',
    label: 'Color & Look',
    color: '#8654aa',
    programs: [
      {
        id: 'gamma_fix',
        label: 'Gamma Fix',
        description: 'Adjust gamma, brightness, contrast, and saturation',
        args: []
      },
      {
        id: 'lut_apply',
        label: 'LUT Apply',
        description: 'Apply a 3D LUT (.cube / .3dl) with optional colour adjustments',
        args: [
          { name: 'lut',        label: 'LUT File',    type: 'file',   required: false, help: '3D LUT file (.cube, .3dl)' },
          { name: 'interp',     label: 'Interpolation', type: 'select', required: false, choices: ['tetrahedral', 'trilinear', 'nearest'], default: 'tetrahedral' },
          { name: 'intensity',  label: 'LUT Intensity', type: 'number', required: false, default: 1.0, min: 0, max: 1 },
          { name: 'brightness', label: 'Brightness',  type: 'number', required: false, default: 0.0, min: -1, max: 1 },
          { name: 'contrast',   label: 'Contrast',    type: 'number', required: false, default: 1.0, min: 0, max: 2 },
          { name: 'saturation', label: 'Saturation',  type: 'number', required: false, default: 1.0, min: 0, max: 3 },
          { name: 'gamma',      label: 'Gamma',       type: 'number', required: false, default: 1.0, min: 0.1, max: 10 }
        ]
      },
      { id: 'duotone',             label: 'Duotone',            description: 'Maps luminance to a 2-color gradient — a stylized-poster look', args: [] },
      { id: 'night_vision',        label: 'Night Vision',       description: 'Green-phosphor night-vision-goggle look with grain and vignette', args: [] },
      { id: 'old_film_damage',     label: 'Old Film Damage',    description: 'Vintage film-print scratches, dust, flicker, and gate-weave', args: [] },
      { id: 'halftone',            label: 'Halftone',           description: 'Newsprint-style halftone dot pattern, dot size driven by brightness', args: [] },
      { id: 'steel_wash',          label: 'Steel Wash',         description: 'Shear plus a cold steel-blue vibrance grade', args: [] },
      { id: 'pickle_juice',      label: 'Pickle Juice',      description: 'Shear plus a strongly green-skewed vibrance grade', args: [] },
      { id: 'septic',            label: 'Septic',            description: 'Green/magenta-skewed vibrance grade — a sickly colour cast', args: [] },
      { id: 'wbflare',             label: 'WB Flare',           description: 'Wide bilateral blur — soft, blown-out white-balance glow', args: [] },
      { id: 'wbflare_pro',         label: 'WB Flare Pro',       description: 'Bilateral blur with a configurable sigma', args: [] },
      { id: 'xpiritualism',      label: 'Xpiritualism',      description: 'Multi-layer bloom with a pastel colour pass — soft, dreamy glow', args: [] },
      { id: 'zapruder',          label: 'Zapruder',          description: 'Frame-difference amplification with colour correction and DCT denoise — degraded found-footage look', args: [] },
      { id: 'bad_predator',      label: 'Bad Predator',      description: 'Heat-vision look — amplified frame differences with a hot false-colour grade', args: [] },
      { id: 'ball_point_pen',      label: 'Ball Point Pen',     description: 'Frame-difference edges with deinterlace artifacts and colour balance — inked sketch look', args: [] },
      { id: 'light_snow',          label: 'Light Snow',         description: 'Motion-interpolated frames with chroma shift and debanding — a light static shimmer', args: [] },
      { id: 'rb_blur',             label: 'RB Blur',            description: 'Debanding (gradfun) — smooths banding in flat gradients like skies and shadows', args: [] },
      { id: 'rb_blur_pro',         label: 'RB Blur Pro',        description: 'Debanding (gradfun) with strength and radius controls', args: [] },
      { id: 'recalled_sensor',     label: 'Recalled Sensor',    description: 'Strong frame-difference bloom — edges burn bright like overexposure', args: [] },
      { id: 'recalled_sensor_pro', label: 'Recalled Sensor Pro', description: 'Frame-difference bloom with radius and intensity controls', args: [] },
      { id: 'soapblind',           label: 'Soapblind',          description: 'Heavy wavelet denoise — plasticky, smoothed, soap-in-the-eyes look', args: [] },
      { id: 'dither', label: 'Dither', description: 'Adaptive-palette dithering — Floyd-Steinberg, Atkinson, Sierra, Bayer and more, with chunky Pixel Size', args: [] },
      { id: 'retro_dither', label: 'Retro Dither', description: 'Dither onto a classic fixed palette — 1-bit B&W, Game Boy, CGA, EGA, C64, PICO-8, phosphors, or your own colors', args: [] },
      { id: 'ordered_dither', label: 'Ordered Dither', description: 'Bayer, clustered-dot, blue-noise and static dither patterns onto a palette or posterized colors, optionally animated', args: [] },
      { id: 'neon_edges', label: 'Neon Edges', description: 'Glowing colored edge outlines over a dimmed, original or black background', args: [] },
      { id: 'cartoon', label: 'Cartoon', description: 'Flat posterized colors with inked outlines', args: [] },
      { id: 'sketch', label: 'Sketch', description: 'Pencil, colored-pencil, watercolor-style and painterly looks', args: [] },
      { id: 'kmeans_palette', label: 'K-Means Palette', description: 'Snap the video to its N dominant colors, optionally dithered', args: [] },
      { id: 'photobooth', label: 'Filter Library', description: 'Every photo-booth filter in one list — plus any you drop into ~/.videobeaux/filters/ (Negative, Game Boy, VHS, CRT, halftone, comic, fisheye…)', args: [] },
      { id: 'ascii_art', label: 'ASCII Art', description: 'Rebuild the video from text characters — choose character set, colors (matrix green, amber…), size and edge boost', args: [] },
      { id: 'negative', label: 'Negative', description: 'Invert the picture like a photo negative — or flip only the brightness and keep the colors', args: [] },
      { id: 'black_white', label: 'Black & White', description: 'High-contrast black and white with local contrast boost (faces and texture pop), optional film grain', args: [] },
      { id: 'sepia', label: 'Sepia & Tones', description: 'Antique single-tone looks: sepia, cyanotype blue, rose, forest or gold', args: [] },
      { id: 'thermal', label: 'Thermal', description: 'Thermal-camera false color — pick the heat palette (inferno, jet, turbo, hot, plasma…)', args: [] },
      { id: 'infrared', label: 'Infrared Film', description: 'False-color infrared film look — foliage turns pink and red, skies go dark', args: [] },
      { id: 'solarize', label: 'Solarize', description: 'Darkroom solarization — tones above the threshold flip, giving glowing metallic edges', args: [] },
      { id: 'posterize', label: 'Posterize', description: 'Reduce each color channel to a few flat levels', args: [] },
      { id: 'lomo', label: 'Lomo', description: 'Cross-processed toy-camera look: punchy curves, color cast and dark vignette corners', args: [] },
      { id: 'hue_cycle', label: 'Hue Cycle', description: 'Rotate every color around the color wheel continuously', args: [] },
      { id: 'pop_art', label: 'Pop Art', description: 'Warhol-style flat-color panels — four colorways in a 2×2 grid, or one palette over the whole frame', args: [] },
      { id: 'blueprint', label: 'Blueprint', description: 'Technical-drawing look — white edge lines on blueprint blue, with an optional grid', args: [] },
      { id: 'emboss', label: 'Emboss', description: 'Raised-relief emboss lit from any angle, in gray or keeping the colors', args: [] },
      { id: 'oil_paint', label: 'Oil Paint', description: 'Painterly oil-paint look: smoothed brush regions, posterized tones and a little canvas relief', args: [] },
      { id: 'led_wall', label: 'LED Wall', description: 'The picture rebuilt from a grid of round glowing LEDs, like a stadium video wall', args: [] },
      { id: 'pixelate', label: 'Pixelate', description: 'Chunky square pixels — a mosaic of any block size', args: [] },
      { id: 'color_pass', label: 'Color Pass', description: 'Keep one color range and turn everything else gray (or remove just that color) — a red dress in a gray world', args: [] },
      { id: 'proc_amp', label: 'Proc Amp', description: 'Video processing amp: brightness, contrast, saturation, hue rotation, gamma, black/white levels, color temperature, broadcast-safe clamp', args: [] },
      { id: 'beauxtrix', label: 'Beauxtrix', description: 'A video blending matrix (homage to the LZX Video Blending Matrix): three R/G/B mixers summing videos A–D with −2…+2 levels, bias, and sum or absolute (solarize) outputs', args: [] }
    ]
  },
  {
    id: 'vision',
    label: 'Vision & Tracking',
    color: '#2ec4b6',
    programs: [
      { id: 'face_track', label: 'Face Track', description: 'Detect and track faces with boxes, brackets, IDs, trails, a spotlight, or an image pasted on each face', args: [] },
      { id: 'face_redact', label: 'Face Redact', description: 'Blur, pixelate, fill or dither over tracked faces — or hide everything except the faces', args: [] },
      { id: 'face_follow', label: 'Face Follow', description: 'Smart reframe: a smoothed virtual camera that pans and zooms to keep a face in shot', args: [] },
      { id: 'motion_ghost', label: 'Motion Ghost', description: 'Isolate what moves — tint it, show only the movers, or leave glowing motion trails', args: [] },
      { id: 'feature_trails', label: 'Feature Trails', description: 'Tracking-HUD look: tracked points, trails and connecting lines over the video', args: [] },
      { id: 'face_warp', label: 'Face Warp', description: 'Big head, tiny head or big eyes — warps tracked faces (works on several faces at once)', args: [] },
      { id: 'face_swap', label: 'Face Swap', description: 'Swap the two biggest faces in the shot, colour-matched with a soft edge', args: [] }
    ]
  },
  {
    id: 'layout',
    label: 'Layout & Overlay',
    color: '#32b9df',
    programs: [
      {
        id: 'watermark',
        label: 'Watermark / Image Overlay',
        description: 'Overlay a watermark or image onto the video — 9-point placement or custom X/Y, scale or exact pixel sizing, opacity, spin, and a timed enable window',
        args: []
      },
      { id: 'remove_background', label: 'Remove Background', description: 'Cut the subject out and put anything behind it — or export transparent WebM/MOV. Static-camera mode needs no download; optional local AI models for harder shots', args: [] },
      { id: 'chroma_key', label: 'Chroma Key', description: 'Remove a green/blue screen (or any solid color) and put a color, image or another video behind — or export transparent WebM/MOV. Auto-detects the screen color', args: [] },
      { id: 'luma_key', label: 'Luma Key', description: 'Knock out the darks or brights (black backgrounds, white skies); screen/add blend modes for fire, smoke and light leaks', args: [] },
      {
        id: 'stack_2x',
        label: 'Stack 2×',
        description: 'Stack two videos vertically (input on top, input2 on bottom)',
        args: [
          { name: 'input2', label: 'Second Video', type: 'file', subtype: 'video', required: true,
            help: 'Path to the video to place on the bottom of the stack' }
        ]
      },
      {
        id: 'triptych',
        label: 'Triptych',
        description: 'Arrange three videos in a symmetric hstack or vstack layout',
        args: [
          { name: 'input2',       label: 'Second Video',  type: 'file', subtype: 'video', required: true },
          { name: 'input3',       label: 'Third Video',   type: 'file', subtype: 'video', required: true },
          { name: 'layout',       label: 'Layout',        type: 'select', required: false, choices: ['hstack', 'vstack'], default: 'hstack' },
          { name: 'zoom1',        label: 'Zoom 1',        type: 'number', required: false, default: 1.0, min: 0.1, max: 5.0 },
          { name: 'zoom2',        label: 'Zoom 2',        type: 'number', required: false, default: 1.0, min: 0.1, max: 5.0 },
          { name: 'zoom3',        label: 'Zoom 3',        type: 'number', required: false, default: 1.0, min: 0.1, max: 5.0 },
          { name: 'audio-mode',   label: 'Audio Mode',    type: 'select', required: false, choices: ['1','2','3','4','5','6'], default: '1',
            help: '1=video1 audio, 2=video2, 3=video3, 4=mix all, 5=mute, 6=external' },
          { name: 'audio-external', label: 'External Audio', type: 'file', required: false, help: 'Used when Audio Mode = 6 (external)' },
          { name: 'vol1',         label: 'Volume 1',      type: 'number', required: false, default: 1.0, min: 0 },
          { name: 'vol2',         label: 'Volume 2',      type: 'number', required: false, default: 1.0, min: 0 },
          { name: 'vol3',         label: 'Volume 3',      type: 'number', required: false, default: 1.0, min: 0 }
        ]
      },
      { id: 'lagkage',     label: 'Lagkage',       description: 'JSON-driven multilayer compositor', args: [] },
      { id: 'layer_blend', label: 'Layer Blend', description: 'Layer two videos with per-layer opacity and a blend mode — multiply, screen, color burn, difference, overlay and more. Choose whose audio to keep', args: [] },
      { id: 'picture_in_picture', label: 'Picture-in-Picture', description: 'A small second video inset over the main one — pick the corner, size, border, opacity and whose audio you hear; swap to flip which is full-screen', args: [] },
      { id: 'quad_split', label: 'Quad Split', description: 'Split screen: up to four videos in a 2×2 grid, side by side, stacked, or one big plus three small, with adjustable gaps', args: [] },
      { id: 'video_wall', label: 'Video Wall', description: 'The picture repeated in a grid of tiles — plain repeats, mirrored tiles, or a delay wall where each tile lags a bit more', args: [] }
    ]
  },
  {
    id: 'edit',
    label: 'Cut & Assemble',
    color: '#c5d92d',
    programs: [
      {
        id: 'trim',
        label: 'Trim',
        description: 'Extracts a single section of a video by timestamp — grab a clip from the middle, or trim off the start.',
        args: [
          { name: 'start', label: 'Start', type: 'text', required: false, default: '0',
            help: 'Seconds (12.5) or HH:MM:SS(.ms). Default: start of video.' },
          { name: 'end', label: 'End', type: 'text', required: false,
            help: 'End timestamp. Mutually exclusive with Duration.' },
          { name: 'duration', label: 'Duration', type: 'text', required: false,
            help: 'Length to keep, from Start. Mutually exclusive with End.' },
          { name: 'copy', label: 'Stream Copy (no re-encode)', type: 'checkbox', required: false,
            help: 'Much faster, but the cut snaps to the nearest keyframe rather than the exact timestamp.' }
        ]
      },
      { id: 'qwikchop',         label: 'Qwikchop',         description: 'Split a video into exactly N equal segments, exported as separate files. Optional seamless-head trimming to avoid black flashes at cuts.', args: [], batchOutput: true },
      {
        id: 'mince',
        label: 'Mince',
        description: 'Merge a folder of videos into one output in a chosen order',
        args: [
          { name: 'mode', label: 'Order Mode', type: 'select', required: true,
            choices: ['forward','backward','lenfor','lenback','randn','randfib'],
            help: 'forward/backward=filename order, lenfor/lenback=by duration, randn/randfib=random' },
          { name: 'engine', label: 'Engine', type: 'select', required: false,
            choices: ['demuxer','filter'], default: 'demuxer' },
          { name: 'seed', label: 'Random Seed', type: 'number', required: false,
            help: 'Seed for randn/randfib modes' }
        ]
      },
      {
        id: 'concat',
        label: 'Concat',
        description: 'Join two videos back to back — first then second. Good for adding a slate before the main video.',
        args: [
          { name: 'input2', label: 'Second Video', type: 'file', subtype: 'video', required: true,
            help: 'Plays after the first video — connect a node or pick a file' },
          { name: 'crossfade', label: 'Crossfade (s)', type: 'number', required: false,
            help: 'Crossfade duration at the join. 0 = hard cut. Cannot be combined with Gap' },
          { name: 'gap', label: 'Gap (s)', type: 'number', required: false,
            help: 'Blank black + silent gap between the two clips. 0 = none. Cannot be combined with Crossfade' }
        ]
      },
      {
        id: 'insert_clip',
        label: 'Insert Clip',
        description: 'Inserts a second video into the master at a chosen timestamp, then picks up the master from where it left off — e.g. an intermission slate. Independent transition control at each boundary.',
        args: [
          { name: 'input2', label: 'Insert Video', type: 'file', subtype: 'video', required: true,
            help: 'Video to insert into the master — connect a node or pick a file' },
          { name: 'insert_at', label: 'Insert At', type: 'text', required: true,
            help: 'Timestamp in the master to insert at. Seconds (12.5) or HH:MM:SS(.ms)' },
          { name: 'entry_transition', label: 'Entry Transition', type: 'select', required: false, default: 'cut',
            choices: ['cut', 'crossfade', 'gap'], help: 'Master → insert boundary' },
          { name: 'entry_duration', label: 'Entry Duration (s)', type: 'number', required: false, default: 0.5,
            help: 'Crossfade or gap length at the entry boundary. Ignored for cut' },
          { name: 'exit_transition', label: 'Exit Transition', type: 'select', required: false, default: 'cut',
            choices: ['cut', 'crossfade', 'gap'], help: 'Insert → master boundary' },
          { name: 'exit_duration', label: 'Exit Duration (s)', type: 'number', required: false, default: 0.5,
            help: 'Crossfade or gap length at the exit boundary. Ignored for cut' }
        ]
      },
      {
        id: 'wipe_transitions',
        label: 'Wipe Transitions',
        description: "Combine two videos with a transitional wipe using ffmpeg's xfade filter",
        args: [
          { name: 'input2', label: 'Second Video', type: 'file', subtype: 'video', required: true,
            help: 'Video that transitions in — connect a node or pick a file' },
          { name: 'preset', label: 'Transition Preset', type: 'select', required: true, default: 'fade',
            choices: [
              'fade', 'wipeleft', 'wiperight', 'wipeup', 'wipedown',
              'slideleft', 'slideright', 'slideup', 'slidedown',
              'circlecrop', 'circleclose', 'circleopen',
              'horizopen', 'horizclose', 'vertopen', 'vertclose',
              'dissolve', 'pixelize',
              'diagtl', 'diagtr', 'diagbl', 'diagbr',
              'hlslice', 'hrslice', 'vuslice', 'vdslice',
              'hblur', 'fadeblack', 'fadewhite',
              'radial', 'smoothleft', 'smoothright', 'smoothup', 'smoothdown',
              'rectcrop', 'distance', 'fadegrays',
              'squeezeh', 'squeezev', 'zoomin'
            ] },
          { name: 'duration', label: 'Transition Duration (s)', type: 'number', required: false, default: 1.0, min: 0,
            help: 'Can be long for artistic effect, but may be capped by clip lengths' },
          { name: 'offset', label: 'Transition Offset (s)', type: 'number', required: false, default: 3.0,
            help: 'Where the transition starts in the first video' }
        ]
      },
      { id: 'fade_flash', label: 'Fade & Flash', description: 'Fade in/out from black, white or any color, plus timed flashes that decay or snap on/off; optionally fades the audio too', args: [] }
    ]
  },
  {
    id: 'speech',
    label: 'Speech & Captions',
    color: '#ffe500',
    programs: [
      {
        id: 'transcraibe',
        label: 'Transcraibe',
        description: 'AI speech-to-text transcription (Vosk)',
        outputType: 'json',
        args: [
          { name: 'stt_model', label: 'Vosk Model', type: 'file', subtype: 'model', required: true,
            help: 'Path to the extracted Vosk model directory' },
          { name: 'emit_txt',  label: 'Also Write .txt', type: 'checkbox', required: false,
            help: 'Write a plain-text version of the transcript alongside the JSON' },
          { name: 'overwrite', label: 'Overwrite Existing', type: 'checkbox', required: false }
        ]
      },
      { id: 'kinetic_captions',  label: 'Kinetic Captions',  description: 'Per-frame rendered captions with a true size pop on the active word', args: [] },
      { id: 'captburn',          label: 'Captburn',          description: 'Burn subtitles / captions into video',      args: [] },
      {
        id: 'auto_narrate',
        label: 'Auto Narrate',
        description: 'Adds AI-narrated captions to a video — type your own script (offline, default) or draft one from a topic via an optional local Ollama model. Synthesizes speech (kokoro-tts), transcribes it locally (Vosk), mixes it over the original audio, and burns kinetic-typography captions (the spoken word pops larger, per-frame rendered — see Kinetic Captions).',
        args: [
          { name: 'script', label: 'Script', type: 'text', required: false,
            help: 'Your own narration text, used verbatim. The default, no-setup path — works fully offline.' },
          { name: 'topic', label: 'Topic (optional)', type: 'text', required: false,
            help: 'Alternative to Script: draft narration from a topic via the optional Ollama Model below.' },
          { name: 'llm_model', label: 'Ollama Model (optional)', type: 'file', subtype: 'ollama_model', required: false,
            help: 'Only used with Topic — pick a locally-pulled Ollama model. Leave blank if using Script.' },
          { name: 'duration', label: 'Target Duration (s)', type: 'number', required: false, default: 30,
            help: 'Only steers Ollama generation when Topic is used' },
          { name: 'voice', label: 'Voice', type: 'file', subtype: 'kokoro_voice', required: false, default: 'am_adam',
            help: 'kokoro-tts voice — listed live from your local kokoro-tts install' },
          { name: 'voice_speed', label: 'Voice Speed', type: 'number', required: false, default: 1.0,
            help: 'kokoro-tts speech speed multiplier' },
          { name: 'stt_model', label: 'Vosk Model', type: 'file', subtype: 'model', required: true,
            help: 'Used to transcribe the synthesized narration' },
          { name: 'original_volume', label: 'Original Audio Volume', type: 'number', required: false, default: 0.2,
            help: 'Background level of the original audio under the narration, 0-1' },
          { name: 'font', label: 'Font', type: 'file', required: false, default: 'Arial',
            help: 'Caption font name (or a path to a .ttf/.otf file)' },
          { name: 'font_size', label: 'Font Size', type: 'number', required: false, default: 76,
            help: 'Requested caption font size in px — auto-shrunk as needed to fit the frame' },
          { name: 'primary_color', label: 'Text Color', type: 'color', required: false, default: '#FFFFFF',
            help: 'Color of words that are not currently being spoken' },
          { name: 'highlight_color', label: 'Highlight Color', type: 'color', required: false, default: '#FFE128',
            help: 'Color of the word currently being spoken' },
          { name: 'outline_color', label: 'Outline Color', type: 'color', required: false, default: '#000000',
            help: 'Caption text outline color' }
        ]
      },
      {
        id: 'grep_supercut',
        label: 'Grep Supercut',
        description: 'Searches a transcript for a word, phrase, or regex and cuts together every match — the classic "videogrep": find every time someone says X.',
        args: [
          { name: 'stt_model', label: 'Vosk Model', type: 'file', subtype: 'model', required: true,
            help: 'Used to transcribe the video first, if no transcript for it exists yet' },
          { name: 'query', label: 'Search Query', type: 'text', required: true,
            help: 'Word, phrase, or regex to search for. Comma-separated for multiple queries.' },
          { name: 'search_type', label: 'Search Type', type: 'select', required: false, default: 'sentence',
            choices: ['sentence', 'fragment', 'mash'],
            help: 'sentence: whole matching lines. fragment: exact matched phrase. mash: random word-mashup.' },
          { name: 'whole_word', label: 'Whole Word Only', type: 'checkbox', required: false, default: true,
            help: 'Match "cut" as a whole word only — turn off to search as a raw regex/substring (e.g. "cut.*ing"). No effect in mash mode.' },
          { name: 'padding', label: 'Padding (s)', type: 'number', required: false, default: 0,
            help: 'Seconds added before/after each matched clip' },
          { name: 'max_clips', label: 'Max Clips', type: 'number', required: false, default: 0,
            help: '0 = unlimited' },
          { name: 'randomize', label: 'Randomize Order', type: 'checkbox', required: false,
            help: 'Shuffle the matched clips before assembling the supercut' }
        ]
      },
      { id: 'qwikchop_deluxe',  label: 'Qwikchop Deluxe',  description: 'Content-aware highlight extraction: scores candidate excerpts from the transcript (local centrality + audio energy + keyword hooks — no network) and exports the best ones, each as its own file.', args: [], batchOutput: true },
      {
        id: 'silence_xtraction',
        label: 'Silence Xtraction',
        description: 'Remove speech segments, keeping what\'s left (not exactly silence, but no discernable words)',
        args: [
          { name: 'stt_model', label: 'Vosk Model', type: 'file', subtype: 'model', required: true,
            help: 'Used to transcribe the video first, if no transcript for it exists yet' },
          { name: 'min_d', label: 'Min Silence Duration (s)', type: 'number', required: true,
            help: 'Minimum duration of a silence to consider' },
          { name: 'max_d', label: 'Max Silence Duration (s)', type: 'number', required: true,
            help: 'Maximum duration of a silence to consider' },
          { name: 'adjuster', label: 'End Adjuster (s)', type: 'number', required: true,
            help: 'Offset to shorten the silence from the end — closer to 0 includes more non-word sounds' }
        ]
      },
      {
        id: 'word_xtraction_vad',
        label: 'Word Xtraction VAD',
        description: 'Remove recognized speech (Vosk) and optionally local Silero VAD detections, keeping applause, laughter, music, noise, and other non-speech audio.',
        args: [
          { name: 'stt_model', label: 'Vosk Model', type: 'file', subtype: 'model', required: true,
            help: 'Used to transcribe the video first, if no transcript for it exists yet' },
          { name: 'min_d', label: 'Min Region Duration (s)', type: 'number', required: true,
            help: 'Minimum duration of a kept region' },
          { name: 'max_d', label: 'Max Region Duration (s)', type: 'number', required: true,
            help: 'Maximum duration of a kept region. With Keep Non-Speech, use 0 or negative for no maximum' },
          { name: 'adjuster', label: 'End Adjuster (s)', type: 'number', required: true,
            help: 'Legacy-mode offset that shortens a gap from the end. Ignored with Keep Non-Speech — use Speech Padding instead' },
          { name: 'keep_nonspeech', label: 'Keep Non-Speech', type: 'checkbox', required: false, default: true,
            help: 'Keep everything outside recognized speech, including material before the first word and after the last — the preferred mode for retaining applause, laughter, music, ambience, and noise' },
          { name: 'max_word_d', label: 'Max Word Duration (s)', type: 'number', required: false, default: 1.5,
            help: 'In Keep Non-Speech mode, longer Vosk word timestamps are treated as suspicious and clamped' },
          { name: 'speech_pad', label: 'Speech Padding (s)', type: 'number', required: false, default: 0.08,
            help: 'Padding added before/after each recognized word in Keep Non-Speech mode, to avoid clipped syllables' },
          { name: 'merge_gap', label: 'Merge Gap (s)', type: 'number', required: false, default: 0.2,
            help: 'Merge neighboring kept regions separated by this many seconds or less' },
          { name: 'use_vad', label: 'Use Silero VAD', type: 'checkbox', required: false, default: false,
            help: 'Locally detect speech even when Vosk cannot recognize the words (requires the silero-vad package; runs entirely locally)' },
          { name: 'vad_threshold', label: 'VAD Threshold', type: 'number', required: false, default: 0.45,
            help: 'Silero speech probability threshold — lower is more aggressive' },
          { name: 'vad_min_speech', label: 'VAD Min Speech (ms)', type: 'number', required: false, default: 150 },
          { name: 'vad_min_silence', label: 'VAD Min Silence (ms)', type: 'number', required: false, default: 120 },
          { name: 'vad_pad', label: 'VAD Padding (ms)', type: 'number', required: false, default: 120,
            help: 'Padding around each VAD speech region' },
          { name: 'vad_keep_short', label: 'VAD Keep Short (s)', type: 'number', required: false, default: 0.40,
            help: 'Preserve brief VAD-only vocal texture (ums, uhs, breaths) at or below this duration; recognized Vosk words are still removed regardless. 0 disables' }
        ]
      },
      {
        id: 'ngrams',
        label: 'Ngrams',
        description: 'Lists the most common word sequences spoken in a transcript — useful for finding good search terms before running Grep Supercut.',
        args: [
          { name: 'stt_model', label: 'Vosk Model', type: 'file', subtype: 'model', required: true,
            help: 'Used to transcribe the video first, if no transcript for it exists yet' },
          { name: 'n', label: 'N-gram Size', type: 'number', required: false, default: 2,
            help: '1 for single words, 2 for word pairs, etc.' },
          { name: 'top', label: 'Top Results', type: 'number', required: false, default: 30,
            help: 'How many ranked results to keep' }
        ],
        outputType: 'json'
      }
    ]
  },
  {
    id: 'media',
    label: 'Media Tools',
    color: '#a8ad23',
    programs: [
      {
        id: 'convert_mux',
        label: 'Convert',
        description: 'General-purpose converter — codec, quality, and format control. Output container is set by the Output node.',
        args: [
          { name: 'profile', label: 'Quick Preset', type: 'select', required: false,
            choices: [
              'mp4_h264', 'mp4_hevc', 'mp4_av1',
              'webm_vp9', 'webm_av1',
              'prores_422', 'prores_4444', 'dnxhr_hq',
              'lossless_ffv1',
              'avi_mjpeg_fast', 'avi_mpeg4_fast'
            ],
            help: 'Overrides the codec/quality settings below. Leave blank to use them instead. Must match the Output node\'s format.' },
          { name: 'vcodec', label: 'Video Codec', type: 'select', required: false, default: 'libx264',
            choices: ['libx264', 'libx265', 'libvpx-vp9', 'libsvtav1', 'prores_ks', 'mpeg4', 'mjpeg', 'ffv1', 'dnxhd'] },
          { name: 'acodec', label: 'Audio Codec', type: 'select', required: false, default: 'aac',
            choices: ['aac', 'libmp3lame', 'libopus', 'flac', 'pcm_s16le', 'pcm_s24le'] },
          { name: 'crf', label: 'Quality (CRF)', type: 'number', required: false, default: 23,
            help: 'Lower = higher quality. Tuned for the default libx264 codec — x265/VP9/AV1 typically want higher values (~28-35).' },
          { name: 'bitrate', label: 'Video Bitrate', type: 'text', required: false,
            help: 'e.g. 5M. Overrides CRF-based quality if set.' },
          { name: 'maxrate', label: 'Video Max Rate', type: 'text', required: false },
          { name: 'bufsize', label: 'VBV Buffer Size', type: 'text', required: false },
          { name: 'preset', label: 'Encoder Preset', type: 'select', required: false, default: 'medium',
            choices: ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
            help: 'x264/x265 speed-vs-quality preset. Leave blank for other codecs.' },
          { name: 'profile-v', label: 'Codec Profile', type: 'select', required: false,
            choices: ['baseline', 'main', 'high', 'high10', 'high422', 'high444'],
            help: 'x264/x265 profile restriction. Leave blank to let the encoder choose.' },
          { name: 'level', label: 'Codec Level', type: 'select', required: false,
            choices: ['3.0', '3.1', '4.0', '4.1', '4.2', '5.0', '5.1', '5.2'],
            help: 'Leave blank to let the encoder choose.' },
          { name: 'pix-fmt', label: 'Pixel Format', type: 'select', required: false, default: 'yuv420p',
            choices: ['yuv420p', 'yuv422p', 'yuv444p', 'yuv420p10le', 'yuv422p10le', 'yuva444p10le'] },
          { name: 'gop', label: 'GOP Size', type: 'number', required: false, help: 'Keyframe interval in frames.' },
          { name: 'r', label: 'Frame Rate', type: 'select', required: false,
            choices: ['23.976', '24', '25', '29.97', '30', '50', '59.94', '60'],
            help: 'Leave blank to keep the source frame rate.' },
          { name: 'vf', label: 'Video Filtergraph', type: 'text', required: false },
          { name: 'tagv', label: 'Video Tag (fourcc)', type: 'text', required: false, help: 'e.g. hvc1 for HEVC in MP4.' },
          { name: 'abitrate', label: 'Audio Bitrate', type: 'text', required: false, default: '192k' },
          { name: 'ac', label: 'Audio Channels', type: 'select', required: false, default: '2',
            choices: ['1', '2', '6', '8'] },
          { name: 'ar', label: 'Audio Sample Rate', type: 'select', required: false, default: '48000',
            choices: ['22050', '44100', '48000', '96000'] },
          { name: 'copy', label: 'Stream Copy (no re-encode)', type: 'checkbox', required: false,
            help: 'Skip re-encoding entirely when the source is already compatible. Ignores every setting above.' }
        ]
      },
      {
        id: 'convert_dims',
        label: 'Convert Dims',
        description: 'Convert and change video dimensions',
        args: []
      },
      {
        id: 'resize',
        label: 'Resize',
        description: 'Resize video to specific dimensions',
        args: [
          { name: 'new_width',  label: 'Width (px)',  type: 'text', required: true,  help: 'Target width in pixels' },
          { name: 'new_height', label: 'Height (px)', type: 'text', required: true,  help: 'Target height in pixels' }
        ]
      },
      {
        id: 'shortify',
        label: 'Shortify',
        description: 'Converts a video to vertical Shorts/Reels format with a blurred, enlarged background fill instead of black bars.',
        args: [
          { name: 'preset', label: 'Format', type: 'select', required: false, default: 'shorts_1080x1920',
            choices: ['shorts_1080x1920', 'portrait_1080x1350', 'square_1080x1080'],
            help: 'Ignored if Custom Width/Height are both set.' },
          { name: 'width', label: 'Custom Width', type: 'number', required: false,
            help: 'Overrides Format when set together with Custom Height.' },
          { name: 'height', label: 'Custom Height', type: 'number', required: false },
          { name: 'blur-sigma', label: 'Blur Strength', type: 'number', required: false, default: 20,
            help: '0 = sharp enlarged background, no blur.' }
        ]
      },
      { id: 'tonemap_hdr_sdr',  label: 'Tonemap HDR→SDR',  description: 'Tonemap HDR content to SDR', args: [] },
      { id: 'extract_frames',   label: 'Extract Frames',   description: 'Extract frames from video as images',          args: [], outputType: 'image' },
      { id: 'extract_sound',    label: 'Extract Sound',    description: 'Extract audio track from video',                args: [], outputType: 'audio' },
      { id: 'thumbs',           label: 'Thumbs',           description: 'Generate thumbnail grid from video',           args: [], outputType: 'image' },
      { id: 'subs_convert',     label: 'Subs Convert',     description: 'Convert subtitle format',                      args: [], outputType: 'text'  },
      { id: 'download_yt',      label: 'Download YT',      description: 'Download video from YouTube / yt-dlp', args: [] },
      { id: 'media_info',       label: 'Media Info',       description: 'Concise report of dimensions, duration, fps, codecs and size — printed to the log and saved as JSON', args: [], outputType: 'json' },
      { id: 'meta_extraction',  label: 'Meta Extraction',  description: 'Extract video metadata / ffprobe info',         args: [], outputType: 'json'  },
      { id: 'hash_fingerprint', label: 'Hash Fingerprint', description: 'Generate a perceptual hash fingerprint',        args: [], outputType: 'json'  },
      { id: 'stabilize', label: 'Stabilize', description: 'Remove camera shake with feature tracking and a smoothed camera path', args: [] }
    ]
  }
]

// ── Flat lookup map ─────────────────────────────────────────────────────────
export const PROGRAM_MAP = {}

CATEGORIES.forEach(cat => {
  cat.programs.forEach(prog => {
    PROGRAM_MAP[prog.id] = {
      ...prog,
      categoryId:    cat.id,
      categoryLabel: cat.label,
      categoryColor: cat.color
    }
  })
})

// ── Programs to hide from the GUI sidebar ────────────────────────────────────
// These programs remain fully functional in the CLI but won't appear as
// draggable nodes.  Add any program id that is CLI-only or not useful in the
// node-editor workflow.
export const EXCLUDED_FROM_GUI = new Set([
  'chain_builder',   'chain_builder_pro',
  // superseded by convert_mux ("Convert") above — still fully usable from the CLI
  'convert'
])

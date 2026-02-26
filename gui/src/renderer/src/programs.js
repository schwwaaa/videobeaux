/**
 * Program registry for videobeaux GUI.
 * Each program matches a Python module in videobeaux/programs/.
 *
 * Arg types: 'text' | 'number' | 'select' | 'file' | 'checkbox'
 */

export const CATEGORIES = [
  {
    id: 'glitch',
    label: 'Glitch & Corruption',
    color: '#ef4444',
    programs: [
      { id: 'bad_animation',     label: 'Bad Animation',     description: 'Corrupt animation frames glitch effect', args: [] },
      { id: 'bad_contrast',      label: 'Bad Contrast',      description: 'Corrupt contrast glitch effect', args: [] },
      { id: 'bad_predator',      label: 'Bad Predator',      description: 'Predator-style thermal glitch effect', args: [] },
      { id: 'digital_boss',      label: 'Digital Boss',      description: 'Digital corruption effect', args: [] },
      { id: 'double_cup',        label: 'Double Cup',        description: 'Double-image corruption effect', args: [] },
      { id: 'ghostee',           label: 'Ghostee',           description: 'Ghost trail glitch effect', args: [] },
      { id: 'lsd_feedback',      label: 'LSD Feedback',      description: 'Psychedelic feedback loop effect', args: [] },
      { id: 'lsd_feedback_pro',  label: 'LSD Feedback Pro',  description: 'Psychedelic feedback loop (pro)', args: [] },
      { id: 'pickle_juice',      label: 'Pickle Juice',      description: 'Green tinted corruption effect', args: [] },
      { id: 'septic',            label: 'Septic',            description: 'Organic decay glitch effect', args: [] },
      { id: 't1000',             label: 'T-1000',            description: 'Liquid metal morphing glitch', args: [] },
      { id: 'twociz',            label: 'Twociz',            description: 'Double-vision corruption effect', args: [] },
      { id: 'twociz_pro',        label: 'Twociz Pro',        description: 'Double-vision corruption (pro)', args: [] },
      { id: 'xpiritualism',      label: 'Xpiritualism',      description: 'Spiritual glitch effect', args: [] },
      { id: 'xrgb',              label: 'XRGB',              description: 'RGB channel corruption effect', args: [] },
      { id: 'zapruder',          label: 'Zapruder',          description: 'Zapruder-style shaky cam effect', args: [] },
      {
        id: 'crossmosh',
        label: 'Crossmosh',
        description: 'Real datamosh: decoder state corruption between two clips',
        args: [
          { name: 'b-input',  label: 'B Clip (Second Video)', type: 'file',   required: true,  help: 'The second clip that gets datamoshed into' },
          { name: 'codec',    label: 'Codec',                 type: 'select', required: false, choices: ['libxvid', 'mpeg4'], default: 'libxvid' },
          { name: 'mode',     label: 'Mode',                  type: 'select', required: false, choices: ['proto', 'smear'], default: 'proto' },
          { name: 'qscale',   label: 'Q Scale',               type: 'number', required: false, default: 3.0,  min: 1,   max: 31,  help: 'Quality scale — lower is better' },
          { name: 'gop',      label: 'GOP Size',              type: 'number', required: false, default: 9999, min: 1,              help: 'GOP interval (keyframe distance)' },
          { name: 'frames',   label: 'Smear Frames',          type: 'number', required: false, default: 9,    min: 1,              help: '[smear] tmix frame count' },
          { name: 'decay',    label: 'Smear Decay',           type: 'number', required: false, default: 0.90, min: 0,   max: 1,   help: '[smear] lagfun decay 0–1' }
        ]
      }
    ]
  },
  {
    id: 'temporal',
    label: 'Temporal Effects',
    color: '#f97316',
    programs: [
      { id: 'broken_scroll',        label: 'Broken Scroll',        description: 'Broken scrolling effect', args: [] },
      { id: 'fever',                label: 'Fever',                description: 'Fever dream visual effect', args: [] },
      { id: 'frame_delay_pro1',     label: 'Frame Delay Pro 1',    description: 'Frame delay effect (variant 1)', args: [] },
      { id: 'frame_delay_pro2',     label: 'Frame Delay Pro 2',    description: 'Frame delay effect (variant 2)', args: [] },
      { id: 'looper_pro',           label: 'Looper Pro',           description: 'Advanced video looping effect', args: [] },
      { id: 'mirror_delay',         label: 'Mirror Delay',         description: 'Mirrored frame delay effect', args: [] },
      { id: 'nostalgic_stutter',    label: 'Nostalgic Stutter',    description: 'VHS-style nostalgic stutter', args: [] },
      { id: 'overexposed_stutter',  label: 'Overexposed Stutter',  description: 'Overexposed frame stutter effect', args: [] },
      { id: 'reverse',              label: 'Reverse',              description: 'Reverse the video', args: [] },
      { id: 'scrolling_pro',        label: 'Scrolling Pro',        description: 'Advanced scrolling effect', args: [] },
      { id: 'stutter_pro',          label: 'Stutter Pro',          description: 'Advanced stutter effect', args: [] },
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
      }
    ]
  },
  {
    id: 'visual',
    label: 'Visual Filters',
    color: '#a855f7',
    programs: [
      { id: 'ball_point_pen',      label: 'Ball Point Pen',     description: 'Ballpoint pen sketch effect', args: [] },
      { id: 'blur_pix',            label: 'Blur Pix',           description: 'Pixel blur / blocky blur effect', args: [] },
      { id: 'light_snow',          label: 'Light Snow',         description: 'Subtle noise/snow overlay', args: [] },
      { id: 'qwikchop',            label: 'Qwikchop',           description: 'Quick chop visual effect', args: [] },
      { id: 'rb_blur',             label: 'RB Blur',            description: 'Red-blue channel blur effect', args: [] },
      { id: 'rb_blur_pro',         label: 'RB Blur Pro',        description: 'Red-blue channel blur (pro)', args: [] },
      { id: 'recalled_sensor',     label: 'Recalled Sensor',    description: 'Sensor recall / dead pixel effect', args: [] },
      { id: 'recalled_sensor_pro', label: 'Recalled Sensor Pro', description: 'Sensor recall effect (pro)', args: [] },
      { id: 'repainting',          label: 'Repainting',         description: 'Stylized repainting effect', args: [] },
      { id: 'slight_smear',        label: 'Slight Smear',       description: 'Subtle frame smear effect', args: [] },
      { id: 'smudge',              label: 'Smudge',             description: 'Smudge / blur effect', args: [] },
      { id: 'soapblind',           label: 'Soapblind',          description: 'Soap opera effect (frame interpolated look)', args: [] },
      { id: 'steel_wash',          label: 'Steel Wash',         description: 'Cold steel colour wash effect', args: [] },
      { id: 'wbflare',             label: 'WB Flare',           description: 'White balance flare effect', args: [] },
      { id: 'wbflare_pro',         label: 'WB Flare Pro',       description: 'White balance flare effect (pro)', args: [] }
    ]
  },
  {
    id: 'composition',
    label: 'Composition',
    color: '#3b82f6',
    programs: [
      { id: 'lagkage',     label: 'Lagkage',       description: 'JSON-driven multilayer compositor', args: [] },
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
      { id: 'splitting',   label: 'Splitting',     description: 'Split video into segments', args: [] },
      { id: 'splitting_pro', label: 'Splitting Pro', description: 'Advanced video splitting', args: [] },
      {
        id: 'stack_2x',
        label: 'Stack 2×',
        description: 'Stack two videos vertically (input on top, input2 on bottom)',
        args: [
          { name: 'input2', label: 'Second Video', type: 'file', required: true,
            help: 'Path to the video to place on the bottom of the stack' }
        ]
      },
      { id: 'wipe_transitions', label: 'Wipe Transitions', description: 'Add wipe transition effects', args: [] },
      {
        id: 'overlay_img_pro',
        label: 'Overlay Image Pro',
        description: 'Overlay an image on the video',
        args: [
          { name: 'image', label: 'Overlay Image', type: 'file', required: true, help: 'Image file to overlay (PNG/JPG)' }
        ]
      },
      {
        id: 'watermark',
        label: 'Watermark',
        description: 'Add an image watermark to the video',
        args: [
          { name: 'watermark',  label: 'Watermark Image', type: 'file',   required: true,  help: 'Path to watermark image (PNG/JPG/GIF)' },
          { name: 'placement',  label: 'Placement',       type: 'select', required: false, choices: ['bottom-right', 'bottom-left', 'top-right', 'top-left', 'center'], default: 'bottom-right' },
          { name: 'margin',     label: 'Margin (px)',     type: 'number', required: false, default: 24,   min: 0,  help: 'Margin from edges in pixels' },
          { name: 'scale',      label: 'Scale',           type: 'number', required: false, default: 0.25, min: 0.01, max: 2.0, help: 'Scale relative to video width' },
          { name: 'opacity',    label: 'Opacity',         type: 'number', required: false, default: 0.8,  min: 0,  max: 1.0 },
          { name: 'spin',       label: 'Spin (deg/s)',    type: 'number', required: false, default: 0.0,            help: 'Rotation speed in degrees/sec' }
        ]
      },
      {
        id: 'triptych',
        label: 'Triptych',
        description: 'Arrange three videos in a symmetric hstack or vstack layout',
        args: [
          { name: 'input2',       label: 'Second Video',  type: 'file',   required: true },
          { name: 'input3',       label: 'Third Video',   type: 'file',   required: true },
          { name: 'layout',       label: 'Layout',        type: 'select', required: false, choices: ['hstack', 'vstack'], default: 'hstack' },
          { name: 'zoom1',        label: 'Zoom 1',        type: 'number', required: false, default: 1.0, min: 0.1, max: 5.0 },
          { name: 'zoom2',        label: 'Zoom 2',        type: 'number', required: false, default: 1.0, min: 0.1, max: 5.0 },
          { name: 'zoom3',        label: 'Zoom 3',        type: 'number', required: false, default: 1.0, min: 0.1, max: 5.0 },
          { name: 'audio-mode',   label: 'Audio Mode',    type: 'select', required: false, choices: ['1','2','3','4','5','6'], default: '1',
            help: '1=video1 audio, 2=video2, 3=video3, 4=mix all, 5=mute, 6=external' },
          { name: 'vol1',         label: 'Volume 1',      type: 'number', required: false, default: 1.0, min: 0 },
          { name: 'vol2',         label: 'Volume 2',      type: 'number', required: false, default: 1.0, min: 0 },
          { name: 'vol3',         label: 'Volume 3',      type: 'number', required: false, default: 1.0, min: 0 }
        ]
      }
    ]
  },
  {
    id: 'utility',
    label: 'Utility',
    color: '#22c55e',
    programs: [
      { id: 'download_yt',      label: 'Download YT',      description: 'Download video from YouTube / yt-dlp', args: [] },
      { id: 'extract_frames',   label: 'Extract Frames',   description: 'Extract frames from video as images',          args: [], outputType: 'image' },
      { id: 'extract_sound',    label: 'Extract Sound',    description: 'Extract audio track from video',                args: [], outputType: 'audio' },
      { id: 'hash_fingerprint', label: 'Hash Fingerprint', description: 'Generate a perceptual hash fingerprint',        args: [], outputType: 'json'  },
      { id: 'meta_extraction',  label: 'Meta Extraction',  description: 'Extract video metadata / ffprobe info',         args: [], outputType: 'json'  },
      { id: 'num_edits',        label: 'Num Edits',        description: 'Count cut / edit points in a video',            args: [], outputType: 'json'  },
      { id: 'silence_xtraction', label: 'Silence Xtraction', description: 'Detect / extract silence segments',          args: [] },
      { id: 'subs_convert',     label: 'Subs Convert',     description: 'Convert subtitle format',                      args: [], outputType: 'text'  },
      { id: 'thumbs',           label: 'Thumbs',           description: 'Generate thumbnail grid from video',           args: [], outputType: 'image' },
      { id: 'tonemap_hdr_sdr',  label: 'Tonemap HDR→SDR',  description: 'Tonemap HDR content to SDR', args: [] },
      {
        id: 'convert',
        label: 'Convert',
        description: 'Re-encode video with configurable codec, preset, and quality',
        args: [
          { name: 'pix-fmt',       label: 'Pixel Format', type: 'select', required: false, choices: ['yuv420p', 'yuv422p', 'yuv444p'], default: 'yuv420p' },
          { name: 'x264-preset',   label: 'Preset',       type: 'select', required: false,
            choices: ['ultrafast','superfast','veryfast','faster','fast','medium','slow','slower','veryslow'], default: 'medium' },
          { name: 'crf',           label: 'CRF Quality',  type: 'number', required: false, default: 18, min: 0, max: 51, help: 'Lower = higher quality' },
          { name: 'copy-audio',    label: 'Copy Audio',   type: 'checkbox', required: false, help: 'Copy audio stream without re-encoding' }
        ]
      },
      {
        id: 'convert_dims',
        label: 'Convert Dims',
        description: 'Convert and change video dimensions',
        args: []
      },
      {
        id: 'convert_mux',
        label: 'Convert Mux',
        description: 'Re-mux video streams',
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
      }
    ]
  },
  {
    id: 'ai',
    label: 'AI & Advanced',
    color: '#06b6d4',
    programs: [
      { id: 'captburn',          label: 'Captburn',          description: 'Burn subtitles / captions into video',      args: [] },
      { id: 'frame_interpolate', label: 'Frame Interpolate', description: 'AI frame interpolation (RIFE/DAIN)',          args: [] },
      {
        id: 'transcraibe',
        label: 'Transcraibe',
        description: 'AI speech-to-text transcription (Vosk)',
        outputType: 'json',
        args: [
          { name: 'stt_model', label: 'Vosk Model Dir', type: 'file', subtype: 'dir', required: true,
            help: 'Path to the extracted Vosk model directory' },
          { name: 'emit_txt',  label: 'Also Write .txt', type: 'checkbox', required: false,
            help: 'Write a plain-text version of the transcript alongside the JSON' },
          { name: 'overwrite', label: 'Overwrite Existing', type: 'checkbox', required: false }
        ]
      }
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
  'chain_builder',   'chain_builder_pro'
])

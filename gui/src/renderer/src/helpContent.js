/** Content of the Help window — edit here. Keep it short: enough to get started or unstuck. */
export const HELP_SECTIONS = [
  {
    title: 'Getting started',
    steps: [
      'Pick your video in the blue **Input** node (Browse…).',
      'Add programs: drag one from the list on the left onto the canvas, or double-click its name.',
      'Connect them: click the dot on the right edge of one box, then click the dot on the left edge of the next. A line follows your cursor in between. Chain it Input → programs → **Output**.',
      'In the orange **Output** node choose where to save (Save As…) and a format.',
      'Press **▶ Run Pipeline**. Progress shows in the *Signal Out* bar at the bottom.'
    ]
  },
  {
    title: 'Handy to know',
    bullets: [
      '**Branching & extra videos** — one output can feed several programs. Programs that need a second video (Layer Blend, Stack 2×…) show an extra dot, or drag **+ Input video** onto the canvas for another source.',
      '**Numbers** — drag the slider or type a value (the box can be emptied and retyped). The faint strip under a slider is a good starting range; the black tick is the default; **↺** resets. Some programs have **Presets** chips that fill several values at once.',
      '**Select several** — ⌘/Ctrl-click or Shift-drag a box around them. **⌘G** groups them so they move together; the caret on a group folds it into one card.',
      '**Copy & paste** — ⌘C / ⌘V copy programs and the connections between them; ⌘D duplicates. **⌘Z** undoes (also after Clear).',
      '**Clear** empties the canvas after asking you to confirm. **Save/Load Preset** keeps a whole setup.',
      '**Fold a program** — ▾ (or double-click its header) hides its settings; **▤ / ▦** in the bottom-left controls fold or unfold all. Folded state is saved in presets.',
      '**Look & lines** — 🎨 Appearance changes the *Look* (Classic is the original), the colour of connection lines, and puts an image behind the canvas.',
      '**Visual editors** — a ✎ button next to a field opens a purpose-built editor: Lagkage → Layout JSON (drop in images), Topobeaux → Cut points (drag band dividers), Stackadelic → Layer 1 left (drag three boxes).'
    ]
  },
  {
    title: 'Keyboard shortcuts',
    keys: [
      ['Delete / Backspace', 'Delete the selected programs or connection'],
      ['⌘A', 'Select everything'],
      ['⌘C  ⌘V  ⌘D', 'Copy, paste, duplicate'],
      ['⌘G  /  ⇧⌘G', 'Group / ungroup'],
      ['⌘Z  /  ⇧⌘Z', 'Undo / redo'],
      ['Esc', 'Cancel a connection in progress, or clear the selection'],
      ['⌘B', 'Show / hide the program list'],
      ['⌘J', 'Show / hide the console'],
      ['F1  or  ?', 'Open this help']
    ]
  },
  {
    title: 'When something goes wrong',
    bullets: [
      'Read the **Signal Out** console — the last red line usually says what happened.',
      'Nothing runs, or a red “not ready” message: open **⚙ Setup** and press **Repair**.',
      'Phone or HDR clips misbehaving: run **Convert** first (to mp4), then use that file.',
      'AI features (speech, narration, background removal) need a one-time download in **Setup → Local AI features**; afterwards everything works offline.',
      'A field says “max …”: that value is out of range and was set to the limit.'
    ]
  },
  {
    title: 'Licenses & source',
    bullets: [
      'Videobeaux runs **ffmpeg** as a separate program. The bundled build is a GPL build (libx264 / libx265) that is never built with the non-redistributable `--enable-nonfree` option.',
      'The exact source code of that ffmpeg and every library in it is published alongside each release of the build; the licence summary ships in the app\'s `LICENSES` folder.',
      'You can use your own ffmpeg instead (Setup). AI models you download (speech, narration, background removal) keep their own licences.'
    ]
  }
]

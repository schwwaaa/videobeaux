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
      '**Layout editors** — a ✎ button next to a field (e.g. Lagkage → Layout JSON) opens a visual editor.'
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
  }
]

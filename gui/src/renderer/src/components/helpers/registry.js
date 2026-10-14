import LagkageEditor from './LagkageEditor'
import BandEditor from './BandEditor'
import StackEditor from './StackEditor'
import TrimEditor from './TrimEditor'
import KeyColorPicker from './KeyColorPicker'

/**
 * Helper windows: a small ✎ button appears next to an argument field and opens a purpose-built
 * editor that fills that argument in for you (instead of making you hand-write a file).
 *
 *   ARG_HELPERS[programId][argName] = { title, Component }
 *
 * `Component` receives { value, onChange, onClose, nodeId, programId } — call onChange(newValue) to set
 * the argument — plus { values, setArgs(patch) } for editors that fill several args at once (the node's
 * current args, defaults included) and `inputPath` (the file of the Input node wired to this program, if any).
 * Editors must call lockModal() so the canvas ignores the keyboard. Lagkage's layout editor is the first one; add more here (e.g. a crop picker, a LUT
 * previewer) and any program/arg pair gets the button automatically.
 */
export const ARG_HELPERS = {
  lagkage: {
    'layout-json': { title: 'Open the layout editor', Component: LagkageEditor }
  },
  topobeaux: {
    cuts: { title: 'Drag the band dividers on a gradient strip', Component: BandEditor }
  },
  trim: {
    start: { title: 'Pick the start and end on a timeline', Component: TrimEditor }
  },
  chroma_key: {
    key_color: { title: 'Click the screen color in a frame of your video', Component: KeyColorPicker }
  },
  stackadelic: {
    l1_left: { title: 'Drag the three layers on a stand-in frame', Component: StackEditor }
  }
}

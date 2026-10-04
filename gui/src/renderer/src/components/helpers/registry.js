import LagkageEditor from './LagkageEditor'

/**
 * Helper windows: a small ✎ button appears next to an argument field and opens a purpose-built
 * editor that fills that argument in for you (instead of making you hand-write a file).
 *
 *   ARG_HELPERS[programId][argName] = { title, Component }
 *
 * `Component` receives { value, onChange, onClose, nodeId, programId } — call onChange(newValue) to set
 * the argument. Lagkage's layout editor is the first one; add more here (e.g. a crop picker, a LUT
 * previewer) and any program/arg pair gets the button automatically.
 */
export const ARG_HELPERS = {
  lagkage: {
    'layout-json': { title: 'Open the layout editor', Component: LagkageEditor }
  }
}

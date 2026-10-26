// BUG-REPORT (test phase) — the "Send a bug report" button. Shown only while gui/feature-flags.json has bugReport: true.
// To remove the feature, delete this folder, gui/src/main/bugReport.js and gui/feature-flags.json, and the lines marked BUG-REPORT.
import React, { useState } from 'react'
import flags from '../../../../feature-flags.json'
import BugReportDialog from './BugReportDialog'

export default function BugReportButton({ logText = '', canvasJson = '', style }) {
  const [open, setOpen] = useState(false)
  if (!flags.bugReport) return null
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="Make a report file you can send to the person who gave you the app"
        style={{ padding: '6px 12px', fontSize: 12, ...style }}
      >
        🐞 Send a bug report
      </button>
      {open && <BugReportDialog onClose={() => setOpen(false)} logText={logText} canvasJson={canvasJson} />}
    </>
  )
}

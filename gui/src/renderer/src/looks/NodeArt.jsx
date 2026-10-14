import React from 'react'
import { glyphFor } from './signatures/glyphs'
import { artFor, useArtVersion } from './output-art/art'

// Tiny, inert-by-default pieces the "Signatures" look turns on. Both elements are display:none (index.css) unless a look
// that uses them is active, so the Classic appearance is unchanged.

/** Small icon chip shown in a module header. */
export function NodeGlyph({ programId, family }) {
  return <span className="node-glyph" aria-hidden="true" dangerouslySetInnerHTML={{ __html: glyphFor(programId, family) }} />
}

/** Strip under a collapsed module's header: big glyph + the one-line description. */
export function NodeArt({ programId, family, motif, description }) {
  useArtVersion()          // re-render when the user's preview thumbnails change
  return (
    <div className="node-art" data-family={family} data-motif={motif || undefined} title={description || ''}>
      <span className="node-art-glyph" aria-hidden="true" dangerouslySetInnerHTML={{ __html: glyphFor(programId, family) }} />
      {artFor(programId) && <img className="node-art-thumb" src={artFor(programId)} alt="" draggable={false} />}
      <span className="node-art-text">{description || ''}</span>
    </div>
  )
}

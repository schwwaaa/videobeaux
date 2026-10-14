import React, { useEffect, useState } from 'react'
import { useSettings } from '../SettingsContext'
import { resolveLook } from '../looks'

/**
 * Replaces the grey operating-system tooltip with a Videobeaux one (paper, ink outline, mono type, offset shadow) in every
 * non-Classic look. One delegated listener: on hover it moves an element's `title` into `data-tip` (so the native tooltip
 * never appears) and shows its own after a short delay. Elements marked `data-no-tip` get nothing (the sidebar rows
 * have their own preview card). Switching back to Classic puts every title back.
 */
export default function BrandedTooltips() {
  const { look } = useSettings()
  const active = resolveLook(look) !== 'classic'
  const [tip, setTip] = useState(null)

  useEffect(() => {
    if (!active) return undefined
    let timer = null
    let current = null

    const hide = () => { clearTimeout(timer); current = null; setTip(null) }

    const onOver = (e) => {
      const el = e.target && e.target.closest ? e.target.closest('[title],[data-tip]') : null
      if (!el) return
      if (el.hasAttribute('title')) {
        const t = el.getAttribute('title')
        el.removeAttribute('title')
        if (t) el.setAttribute('data-tip', t)
      }
      const text = el.getAttribute('data-tip')
      if (!text || el.hasAttribute('data-no-tip') || el === current) return
      current = el
      clearTimeout(timer)
      timer = setTimeout(() => setTip({ text, rect: el.getBoundingClientRect() }), 380)
    }
    const onOut = (e) => {
      if (current && !(e.relatedTarget && current.contains(e.relatedTarget))) hide()
    }

    document.addEventListener('mouseover', onOver, true)
    document.addEventListener('mouseout', onOut, true)
    document.addEventListener('mousedown', hide, true)
    document.addEventListener('wheel', hide, true)
    return () => {
      document.removeEventListener('mouseover', onOver, true)
      document.removeEventListener('mouseout', onOut, true)
      document.removeEventListener('mousedown', hide, true)
      document.removeEventListener('wheel', hide, true)
      clearTimeout(timer)
      setTip(null)
      // give every element its native title back (Classic)
      document.querySelectorAll('[data-tip]').forEach(el => {
        if (!el.hasAttribute('title')) el.setAttribute('title', el.getAttribute('data-tip'))
        el.removeAttribute('data-tip')
      })
    }
  }, [active])

  if (!tip) return null
  const W = 260
  const left = Math.max(8, Math.min(window.innerWidth - W - 8, tip.rect.left + tip.rect.width / 2 - W / 2))
  const below = tip.rect.bottom + 8
  const top = below + 80 > window.innerHeight ? Math.max(8, tip.rect.top - 8) : below
  const flipped = below + 80 > window.innerHeight
  return (
    <div className="vb-tip" style={{ left, top, width: 'max-content', maxWidth: W, transform: flipped ? 'translateY(-100%)' : 'none' }}>
      {tip.text}
    </div>
  )
}

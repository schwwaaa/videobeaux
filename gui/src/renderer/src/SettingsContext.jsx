import React, { createContext, useContext, useEffect, useState } from 'react'

const SettingsContext = createContext(null)

const DEFAULTS = {
  theme: 'light',
  shadowOffset: 5,
  shadowColor: '#080808',
  shadowsEnabled: true,
  setupSeen: false,
  showSelectionBar: true
}

/**
 * Persisted app-wide appearance settings (dark mode, drop-shadow style),
 * unrelated to any one pipeline — backed by settings:get/settings:set IPC
 * (gui/src/main/index.js), which stores a small JSON file under userData.
 *
 * Applies theme + shadow tokens directly onto the document root as a
 * data-theme attribute and CSS custom-property overrides, so every
 * existing var(--shadow)/var(--ink) consumer picks up changes for free.
 */
export function SettingsProvider({ children }) {
  const [settings, setSettingsState] = useState(DEFAULTS)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    window.electronAPI.getSettings()
      .then(s => setSettingsState({ ...DEFAULTS, ...s }))
      .catch(() => {})
      .finally(() => setReady(true))
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', settings.theme === 'dark' ? 'dark' : 'light')
    const offset = settings.shadowsEnabled ? settings.shadowOffset : 0
    root.style.setProperty('--shadow-offset', `${offset}px`)
    root.style.setProperty('--shadow-offset-sm', `${Math.round(offset * 0.6)}px`)
    root.style.setProperty('--shadow-color', settings.shadowColor)
  }, [settings.theme, settings.shadowOffset, settings.shadowColor, settings.shadowsEnabled])

  function update(patch) {
    setSettingsState(prev => {
      const next = { ...prev, ...patch }
      window.electronAPI.setSettings(next).catch(() => {})
      return next
    })
  }

  const value = {
    ...settings,
    ready,
    setTheme: (theme) => update({ theme }),
    toggleTheme: () => update({ theme: settings.theme === 'dark' ? 'light' : 'dark' }),
    setShadowOffset: (shadowOffset) => update({ shadowOffset }),
    setShadowColor: (shadowColor) => update({ shadowColor }),
    setShadowsEnabled: (shadowsEnabled) => update({ shadowsEnabled }),
    setSetupSeen: (setupSeen) => update({ setupSeen }),
    setShowSelectionBar: (showSelectionBar) => update({ showSelectionBar })
  }

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used inside <SettingsProvider>')
  return ctx
}

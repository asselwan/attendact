import { useState, type ReactNode } from 'react'

const STORAGE_KEY = 'noshight_access'
const ACCESS_CODE = 'assel'

function readUnlocked(): boolean {
  if (typeof window === 'undefined') return false
  const params = new URLSearchParams(window.location.search)
  if (params.get('preview') === 'ok') {
    try { window.localStorage.setItem(STORAGE_KEY, '1') } catch { /* ignore */ }
    return true
  }
  try { return window.localStorage.getItem(STORAGE_KEY) === '1' } catch { return false }
}

export function AccessGate({ children }: { children: ReactNode }) {
  const [unlocked, setUnlocked] = useState(readUnlocked)
  const [code, setCode] = useState('')
  const [error, setError] = useState(false)

  if (unlocked) return <>{children}</>

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (code.trim().toLowerCase() === ACCESS_CODE) {
      try { window.localStorage.setItem(STORAGE_KEY, '1') } catch { /* ignore */ }
      setUnlocked(true)
      setError(false)
    } else {
      setError(true)
    }
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <form onSubmit={submit} className="w-full max-w-sm px-6 text-center">
        <p className="text-sm uppercase tracking-widest text-text-secondary mb-3">
          Private preview
        </p>
        <h2 className="text-xl font-medium mb-6">Access code</h2>
        <input
          type="password"
          value={code}
          onChange={(e) => { setCode(e.target.value); setError(false) }}
          autoFocus
          className="w-full bg-surface-raised border border-white/20 rounded px-3 py-2 text-center tracking-widest focus:outline-none focus:border-gold/60"
          placeholder="••••••"
        />
        {error && (
          <p className="text-xs text-red-400 mt-2">That code didn't match.</p>
        )}
        <button
          type="submit"
          className="mt-4 w-full px-3 py-2 rounded bg-gold/10 text-gold border border-gold/30 hover:bg-gold/15 transition-colors text-sm"
        >
          Enter
        </button>
        <p className="text-text-secondary text-xs mt-6 leading-relaxed">
          Don't have a code? Email{' '}
          <a
            href="mailto:assel@nomoi.ai?subject=Noshight%20access"
            className="text-gold hover:underline"
          >
            assel@nomoi.ai
          </a>
          .
        </p>
      </form>
    </div>
  )
}

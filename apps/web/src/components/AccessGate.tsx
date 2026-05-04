import type { ReactNode } from 'react'

const BYPASS_KEY = 'noshight_preview'

function isUnlocked(): boolean {
  if (typeof window === 'undefined') return false
  const params = new URLSearchParams(window.location.search)
  if (params.get('preview') === 'ok') {
    try { window.localStorage.setItem(BYPASS_KEY, '1') } catch { /* ignore */ }
    return true
  }
  try { return window.localStorage.getItem(BYPASS_KEY) === '1' } catch { return false }
}

export function AccessGate({ children }: { children: ReactNode }) {
  if (isUnlocked()) return <>{children}</>
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <p className="text-sm uppercase tracking-widest text-text-secondary mb-3">
          Private preview
        </p>
        <h2 className="text-xl font-medium mb-3">Access by request</h2>
        <p className="text-text-secondary text-sm leading-relaxed">
          Email{' '}
          <a
            href="mailto:assel@nomoi.ai?subject=Noshight%20access"
            className="text-gold hover:underline"
          >
            assel@nomoi.ai
          </a>{' '}
          to request access. The Demo tab is open.
        </p>
      </div>
    </div>
  )
}

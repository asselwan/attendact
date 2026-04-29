import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/score', label: 'Score' },
  { to: '/bulk', label: 'Bulk' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/insights', label: 'Insights' },
  { to: '/audit', label: 'Audit' },
]

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-gold font-black text-lg tracking-tight">NOSHIGHT</span>
          <span className="text-text-secondary text-sm">by NOMOI</span>
        </div>
        <nav className="flex gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-sm transition-colors ${
                  isActive
                    ? 'bg-gold/10 text-gold'
                    : 'text-text-secondary hover:text-text-primary'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
      <footer className="border-t border-white/10 px-6 py-3 text-text-secondary text-xs">
        Noshight v0.1.0 — Heuristic baseline. Not a clinical decision tool.
      </footer>
    </div>
  )
}

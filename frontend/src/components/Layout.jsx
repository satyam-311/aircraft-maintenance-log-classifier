import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/classify', label: 'Classify' },
  { to: '/search', label: 'Search' },
  { to: '/ask', label: 'Ask' },
  { to: '/performance', label: 'Model Performance' },
]

export default function Layout() {
  return (
    <div className="min-h-screen bg-bg-offwhite flex">
      {/* Fixed left sidebar, 240px, per spec */}
      <nav className="w-[240px] shrink-0 bg-aviation-navy min-h-screen p-24 fixed left-0 top-0 bottom-0">
        <h1 className="text-white font-bold text-lg mb-32">Maintenance Log Classifier</h1>
        <ul className="flex flex-col gap-8">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `block px-16 py-8 rounded-button text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-signal-blue text-white'
                      : 'text-white/70 hover:text-white hover:bg-white/10'
                  }`
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Fluid content area, max-width 1040px, centered, per spec */}
      <main className="flex-1 ml-[240px] px-32 py-32">
        <div className="max-w-content mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

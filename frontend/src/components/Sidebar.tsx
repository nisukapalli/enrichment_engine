import { NavLink } from 'react-router-dom'
import {
  Workflow,
  BriefcaseBusiness,
  FileUp,
  Zap,
} from 'lucide-react'

const nav = [
  { to: '/workflows', icon: Workflow, label: 'Workflows' },
  { to: '/jobs', icon: BriefcaseBusiness, label: 'Jobs' },
  { to: '/files', icon: FileUp, label: 'Files' },
]

export function Sidebar() {
  return (
    <aside className="flex flex-col w-72 min-h-screen bg-white border-r border-gray-200 px-5 py-7 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-2 mb-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-sm">
          <Zap size={20} className="text-white" />
        </div>
        <span className="font-semibold text-xl text-gray-900 tracking-tight">
          Sixtyfour
        </span>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1.5">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-colors ${
                isActive
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`
            }
          >
            <Icon size={20} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="mt-auto px-2 pt-4 border-t border-gray-100">
        <p className="text-sm text-gray-400">Workflow Engine v1.0</p>
      </div>
    </aside>
  )
}

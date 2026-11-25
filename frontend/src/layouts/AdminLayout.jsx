import { Suspense } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Boxes,
  ClipboardList,
  CreditCard,
  ExternalLink,
  LayoutDashboard,
  LogOut,
  Package,
  Tag,
  Users,
} from 'lucide-react'
import { PageLoader } from '../components/Feedback'
import Logo from '../components/Logo'
import { useAuth } from '../contexts/AuthContext'

const NAV = [
  { to: '/admin', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/admin/products', label: 'Products', icon: Package },
  { to: '/admin/categories', label: 'Categories', icon: Tag },
  { to: '/admin/inventory', label: 'Inventory', icon: Boxes },
  { to: '/admin/bookings', label: 'Bookings', icon: ClipboardList },
  { to: '/admin/customers', label: 'Customers', icon: Users },
  { to: '/admin/payments', label: 'Payments', icon: CreditCard },
]

const itemClass = ({ isActive }) =>
  `flex items-center gap-3 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-primary text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
  }`

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <aside className="bg-ink px-3 py-4 lg:w-60 lg:shrink-0">
        <div className="px-2 pb-4 lg:pb-6">
          <Logo to="/admin" light />
          <p className="mt-1 text-xs text-slate-400">Admin dashboard</p>
        </div>
        <nav className="flex gap-1 overflow-x-auto lg:flex-col" aria-label="Admin">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={itemClass}>
              <item.icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end gap-4 border-b border-line bg-white px-4 py-3 sm:px-6">
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted hover:text-primary">
            View site <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
          <span className="text-sm font-medium">{user.full_name}</span>
          <button onClick={handleLogout} className="inline-flex items-center gap-1 text-sm text-muted hover:text-primary">
            <LogOut className="h-4 w-4" aria-hidden="true" /> Log out
          </button>
        </header>
        <main className="flex-1 p-4 sm:p-6">
          <Suspense fallback={<PageLoader />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}

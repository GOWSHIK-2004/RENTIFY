import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ClipboardList, LayoutDashboard, LogOut, Menu, Search, User, X } from 'lucide-react'
import { categoryApi } from '../api'
import { useAuth } from '../contexts/AuthContext'
import useFetch from '../hooks/useFetch'
import Button from './Button'
import Logo from './Logo'

const linkClass = ({ isActive }) =>
  `text-sm font-medium transition-colors hover:text-primary ${isActive ? 'text-primary' : 'text-ink'}`

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('')
  const { data: categories } = useFetch(() => categoryApi.list(), [])

  const search = (event) => {
    event.preventDefault()
    const trimmed = query.trim()
    navigate(trimmed ? `/products?q=${encodeURIComponent(trimmed)}` : '/products')
    setMenuOpen(false)
  }

  const handleLogout = () => {
    logout()
    setMenuOpen(false)
    navigate('/')
  }

  const searchForm = (
    <form onSubmit={search} role="search" className="relative w-full">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden="true" />
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search cameras, consoles, drones..."
        aria-label="Search equipment"
        className="w-full rounded-lg border border-line bg-surface py-2 pl-9 pr-3 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
      />
    </form>
  )

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        <Logo />
        <nav className="ml-4 hidden items-center gap-6 md:flex" aria-label="Main">
          <NavLink to="/products" className={linkClass}>
            Browse
          </NavLink>
          <NavLink to="/about" className={linkClass}>
            About
          </NavLink>
          <NavLink to="/faq" className={linkClass}>
            FAQ
          </NavLink>
        </nav>
        <div className="mx-auto hidden max-w-md flex-1 md:block">{searchForm}</div>

        <div className="ml-auto hidden items-center gap-2 md:flex">
          {user ? (
            <>
              {isAdmin && (
                <Button to="/admin" variant="ghost" size="sm">
                  <LayoutDashboard className="h-4 w-4" /> Admin
                </Button>
              )}
              <Button to="/bookings" variant="ghost" size="sm">
                <ClipboardList className="h-4 w-4" /> My bookings
              </Button>
              <Button to="/profile" variant="ghost" size="sm">
                <User className="h-4 w-4" /> {user.full_name.split(' ')[0]}
              </Button>
              <Button variant="secondary" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" /> Log out
              </Button>
            </>
          ) : (
            <>
              <Button to="/login" variant="ghost" size="sm">
                Log in
              </Button>
              <Button to="/register" size="sm">
                Sign up
              </Button>
            </>
          )}
        </div>

        <button
          className="ml-auto rounded p-2 hover:bg-slate-100 md:hidden"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {categories?.length > 0 && (
        <nav className="hidden border-t border-line md:block" aria-label="Categories">
          <ul className="mx-auto flex max-w-7xl gap-6 overflow-x-auto px-6 py-2">
            {categories.map((category) => (
              <li key={category.id}>
                <Link
                  to={`/products?category=${category.slug}`}
                  className="whitespace-nowrap text-sm text-muted hover:text-primary"
                >
                  {category.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}

      {menuOpen && (
        <div className="space-y-4 border-t border-line bg-white px-4 py-4 md:hidden">
          {searchForm}
          <div className="flex flex-col gap-3" onClick={() => setMenuOpen(false)}>
            <Link to="/products" className="text-sm font-medium">
              Browse equipment
            </Link>
            {categories?.map((category) => (
              <Link key={category.id} to={`/products?category=${category.slug}`} className="pl-3 text-sm text-muted">
                {category.name}
              </Link>
            ))}
            <Link to="/about" className="text-sm font-medium">
              About
            </Link>
            <Link to="/faq" className="text-sm font-medium">
              FAQ
            </Link>
            {user ? (
              <>
                {isAdmin && (
                  <Link to="/admin" className="text-sm font-medium">
                    Admin dashboard
                  </Link>
                )}
                <Link to="/bookings" className="text-sm font-medium">
                  My bookings
                </Link>
                <Link to="/profile" className="text-sm font-medium">
                  Profile
                </Link>
              </>
            ) : (
              <div className="flex gap-2">
                <Button to="/login" variant="secondary" size="sm">
                  Log in
                </Button>
                <Button to="/register" size="sm">
                  Sign up
                </Button>
              </div>
            )}
          </div>
          {user && (
            <Button variant="secondary" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" /> Log out
            </Button>
          )}
        </div>
      )}
    </header>
  )
}

import { Link } from 'react-router-dom'
import Logo from './Logo'

export default function Footer() {
  return (
    <footer className="mt-20 bg-ink text-slate-300">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-3">
        <div>
          <Logo light />
          <p className="mt-3 text-sm">Rent More. Own Less.</p>
          <p className="mt-2 max-w-xs text-sm text-slate-400">
            Premium equipment, rented by the day from our own inventory.
          </p>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Explore</h2>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link to="/products" className="hover:text-white">
                Browse equipment
              </Link>
            </li>
            <li>
              <Link to="/about" className="hover:text-white">
                About Rentify
              </Link>
            </li>
            <li>
              <Link to="/faq" className="hover:text-white">
                FAQ
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Demo project</h2>
          <p className="mt-3 text-sm text-slate-400">
            Rentify is a demonstration application. No real payments are taken and no equipment will be delivered.
          </p>
        </div>
      </div>
      <div className="border-t border-slate-700 py-4 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} Rentify demo. Built for learning.
      </div>
    </footer>
  )
}

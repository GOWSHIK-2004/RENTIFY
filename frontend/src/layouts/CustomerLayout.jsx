import { Outlet, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Footer from '../components/Footer'
import Navbar from '../components/Navbar'

export default function CustomerLayout() {
  const { pathname } = useLocation()

  // Start every page at the top when navigating.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="flex min-h-screen flex-col">
      <div className="bg-ink px-4 py-1.5 text-center text-xs text-slate-200">
        Demo project: bookings and payments are simulated. No real transactions occur.
      </div>
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

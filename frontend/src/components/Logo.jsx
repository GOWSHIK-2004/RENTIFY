import { Link } from 'react-router-dom'

export default function Logo({ to = '/', light = false }) {
  return (
    <Link to={to} className="inline-flex items-center gap-2" aria-label="Rentify home">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-lg font-bold text-white">R</span>
      <span className={`text-xl font-bold tracking-tight ${light ? 'text-white' : 'text-ink'}`}>
        Rent<span className="text-primary">ify</span>
      </span>
    </Link>
  )
}

import { titleCase } from '../utils/format'

const STYLES = {
  // booking
  CONFIRMED: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  PICKED_UP: 'bg-orange-50 text-orange-700 ring-orange-600/20',
  RETURNED: 'bg-green-50 text-green-700 ring-green-600/20',
  CANCELLED: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  OVERDUE: 'bg-red-50 text-red-700 ring-red-600/20',
  // payment
  SUCCESS: 'bg-green-50 text-green-700 ring-green-600/20',
  REFUNDED: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  // inventory
  ACTIVE: 'bg-green-50 text-green-700 ring-green-600/20',
  MAINTENANCE: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  RETIRED: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  EXCELLENT: 'bg-green-50 text-green-700 ring-green-600/20',
  GOOD: 'bg-teal-50 text-teal-700 ring-teal-600/20',
  FAIR: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  DAMAGED: 'bg-red-50 text-red-700 ring-red-600/20',
  ARCHIVED: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  FEATURED: 'bg-orange-50 text-orange-700 ring-orange-600/20',
}

/** Coloured pill. The text always carries the meaning; colour is only a hint. */
export default function StatusBadge({ status, label }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[status] ?? STYLES.CANCELLED}`}
    >
      {label ?? titleCase(status)}
    </span>
  )
}

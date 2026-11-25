import { useState } from 'react'
import { Link } from 'react-router-dom'
import { bookingApi } from '../../api'
import Button from '../../components/Button'
import ConfirmModal from '../../components/ConfirmModal'
import { EmptyState, ErrorState, PageLoader } from '../../components/Feedback'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'
import useFetch from '../../hooks/useFetch'
import { formatDate, formatMoney, imageSrc } from '../../utils/format'

const TABS = [
  { id: 'CONFIRMED', label: 'Upcoming', empty: 'No upcoming bookings.' },
  { id: 'PICKED_UP', label: 'Active rentals', empty: 'You have nothing rented out right now.' },
  { id: 'RETURNED', label: 'Completed', empty: 'No completed rentals yet.' },
  { id: 'CANCELLED', label: 'Cancelled', empty: 'No cancelled bookings.' },
]

export default function MyBookings() {
  const toast = useToast()
  const { data: bookings, loading, error, reload } = useFetch(() => bookingApi.list(), [])
  const [tab, setTab] = useState('CONFIRMED')
  const [cancelling, setCancelling] = useState(null)

  if (loading) return <PageLoader />
  if (error) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <ErrorState message={error} onRetry={reload} />
      </div>
    )
  }

  const visible = bookings.filter((booking) => booking.status === tab)
  const activeTab = TABS.find((item) => item.id === tab)

  const cancel = async (reason) => {
    await bookingApi.cancel(cancelling.id, reason)
    toast.success(`Booking ${cancelling.booking_reference} cancelled. Your simulated payment was refunded.`)
    reload()
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold">My bookings</h1>

      <div role="tablist" aria-label="Booking status" className="mt-6 flex gap-1 overflow-x-auto border-b border-line">
        {TABS.map((item) => {
          const count = bookings.filter((booking) => booking.status === item.id).length
          return (
            <button
              key={item.id}
              role="tab"
              aria-selected={tab === item.id}
              onClick={() => setTab(item.id)}
              className={`whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium ${tab === item.id ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-ink'}`}
            >
              {item.label} ({count})
            </button>
          )
        })}
      </div>

      <div className="mt-6" role="tabpanel">
        {visible.length === 0 ? (
          <EmptyState
            title={activeTab.empty}
            action={
              tab === 'CONFIRMED' && (
                <Button to="/products" variant="secondary">
                  Browse equipment
                </Button>
              )
            }
          />
        ) : (
          <ul className="space-y-4">
            {visible.map((booking) => (
              <li key={booking.id} className="flex flex-col gap-4 rounded-xl border border-line bg-white p-4 sm:flex-row">
                <img src={imageSrc(booking.product.image_url)} alt="" className="h-24 w-full rounded-lg object-cover sm:w-32" />
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link to={`/bookings/${booking.id}`} className="font-semibold hover:text-primary">
                      {booking.product.name}
                    </Link>
                    <StatusBadge status={booking.status} />
                    {booking.is_overdue && <StatusBadge status="OVERDUE" />}
                  </div>
                  <p className="mt-1 font-mono text-xs text-muted">{booking.booking_reference}</p>
                  <p className="mt-2 text-sm">
                    {formatDate(booking.pickup_date)} to {formatDate(booking.return_date)} · {booking.rental_days} day
                    {booking.rental_days === 1 ? '' : 's'}
                  </p>
                  <p className="text-sm font-semibold">{formatMoney(booking.total_amount)}</p>
                </div>
                <div className="flex gap-2 sm:flex-col">
                  <Button to={`/bookings/${booking.id}`} variant="secondary" size="sm">
                    View details
                  </Button>
                  {booking.can_cancel && (
                    <Button variant="ghost" size="sm" onClick={() => setCancelling(booking)}>
                      Cancel
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {cancelling && (
        <ConfirmModal
          title={`Cancel ${cancelling.booking_reference}?`}
          message="Your equipment will be released and the simulated payment refunded. This cannot be undone."
          confirmLabel="Cancel booking"
          danger
          askReason
          onConfirm={cancel}
          onClose={() => setCancelling(null)}
        />
      )}
    </div>
  )
}

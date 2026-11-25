import { Link, useParams } from 'react-router-dom'
import { CircleCheck } from 'lucide-react'
import { bookingApi } from '../../api'
import BookingDetails from '../../components/BookingDetails'
import Button from '../../components/Button'
import { ErrorState, PageLoader } from '../../components/Feedback'
import useFetch from '../../hooks/useFetch'

export default function BookingConfirmation() {
  const { id } = useParams()
  const { data: booking, loading, error, reload } = useFetch(() => bookingApi.get(id), [id])

  if (loading) return <PageLoader />
  if (error) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <ErrorState message={error} onRetry={reload} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <div className="text-center">
        <CircleCheck className="mx-auto h-14 w-14 text-green-600" aria-hidden="true" />
        <h1 className="mt-3 text-3xl font-bold">Booking confirmed</h1>
        <p className="mt-1 text-muted">
          Your reference is <span className="font-mono font-semibold text-ink">{booking.booking_reference}</span>. Keep it
          handy for pickup.
        </p>
      </div>
      <div className="mt-8">
        <BookingDetails booking={booking} />
      </div>
      <p className="mt-4 text-center text-xs text-muted">This is a demo: the payment above was simulated.</p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Button to="/bookings">Go to my bookings</Button>
        <Button to="/products" variant="secondary">
          Keep browsing
        </Button>
      </div>
      <p className="mt-4 text-center text-sm">
        <Link to={`/bookings/${booking.id}`} className="text-primary hover:underline">
          View booking details
        </Link>
      </p>
    </div>
  )
}

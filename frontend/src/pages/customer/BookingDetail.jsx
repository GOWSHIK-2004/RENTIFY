import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { bookingApi, reviewApi } from '../../api'
import BookingDetails from '../../components/BookingDetails'
import Button from '../../components/Button'
import ConfirmModal from '../../components/ConfirmModal'
import { Alert, ErrorState, PageLoader } from '../../components/Feedback'
import ReviewForm from '../../components/ReviewForm'
import { useToast } from '../../contexts/ToastContext'
import useFetch from '../../hooks/useFetch'

export default function BookingDetail() {
  const { id } = useParams()
  const toast = useToast()
  const { data: booking, loading, error, reload } = useFetch(() => bookingApi.get(id), [id])
  const [cancelling, setCancelling] = useState(false)

  if (loading) return <PageLoader />
  if (error) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <ErrorState message={error} onRetry={reload} />
        <p className="mt-4 text-center">
          <Link to="/bookings" className="text-sm text-primary hover:underline">
            Back to my bookings
          </Link>
        </p>
      </div>
    )
  }

  const cancel = async (reason) => {
    await bookingApi.cancel(booking.id, reason)
    toast.success('Booking cancelled. Your simulated payment was refunded.')
    reload()
  }

  const submitReview = async ({ rating, comment }) => {
    await reviewApi.create({ booking_id: booking.id, rating, comment })
    toast.success('Thanks for your review!')
    reload()
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <Link to="/bookings" className="inline-flex items-center gap-1 text-sm text-muted hover:text-primary">
        <ArrowLeft className="h-4 w-4" /> My bookings
      </Link>
      <h1 className="mt-3 text-3xl font-bold">Booking details</h1>

      <div className="mt-6 space-y-6">
        <BookingDetails booking={booking} />

        {booking.status === 'CONFIRMED' && (
          <div className="flex flex-wrap items-center gap-3">
            {booking.can_cancel ? (
              <Button variant="danger" onClick={() => setCancelling(true)}>
                Cancel booking
              </Button>
            ) : (
              <Alert type="info">Cancellation is only possible before the pickup date.</Alert>
            )}
          </div>
        )}
        {booking.status === 'PICKED_UP' && (
          <Alert type="info">Enjoy your rental! Please return it by the return date shown above.</Alert>
        )}

        {booking.status === 'RETURNED' && (
          <section className="rounded-xl border border-line bg-white p-5" aria-labelledby="review-heading">
            <h2 id="review-heading" className="font-semibold">
              {booking.review_id ? 'Your review' : 'How was it?'}
            </h2>
            {booking.review_id ? (
              <p className="mt-2 text-sm text-muted">
                You have reviewed this rental. You can edit or delete your review on the{' '}
                <Link to={`/products/${booking.product.id}`} className="text-primary hover:underline">
                  product page
                </Link>
                .
              </p>
            ) : (
              <div className="mt-3">
                <ReviewForm submitLabel="Submit review" onSubmit={submitReview} />
              </div>
            )}
          </section>
        )}
      </div>

      {cancelling && (
        <ConfirmModal
          title="Cancel this booking?"
          message="Your equipment will be released and the simulated payment refunded. This cannot be undone."
          confirmLabel="Cancel booking"
          danger
          askReason
          onConfirm={cancel}
          onClose={() => setCancelling(false)}
        />
      )}
    </div>
  )
}

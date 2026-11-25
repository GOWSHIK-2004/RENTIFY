import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CircleCheck, CircleX, Pencil, Trash2 } from 'lucide-react'
import { productApi, reviewApi } from '../../api'
import Button from '../../components/Button'
import ConfirmModal from '../../components/ConfirmModal'
import { Alert, EmptyState, ErrorState, PageLoader, Spinner } from '../../components/Feedback'
import Input from '../../components/Input'
import Modal from '../../components/Modal'
import ReviewForm from '../../components/ReviewForm'
import StarRating from '../../components/StarRating'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import useFetch from '../../hooks/useFetch'
import useQuote from '../../hooks/useQuote'
import { addDays, formatDate, formatMoney, imageSrc, todayInBusinessZone } from '../../utils/format'

const MAX_DAYS = 30

const daysBetween = (from, to) => Math.round((new Date(to) - new Date(from)) / 86_400_000)

export default function ProductDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const product = useFetch(() => productApi.get(id), [id])
  const reviews = useFetch(() => productApi.reviews(id), [id])

  const today = todayInBusinessZone()
  const [pickup, setPickup] = useState(addDays(today, 1))
  const [returnDate, setReturnDate] = useState(addDays(today, 4))
  const [editingReview, setEditingReview] = useState(null)
  const [deletingReview, setDeletingReview] = useState(null)

  // Client-side checks give instant feedback; the backend re-validates everything.
  const days = pickup && returnDate ? daysBetween(pickup, returnDate) : 0
  let dateError = ''
  if (!pickup || !returnDate) dateError = 'Choose pickup and return dates.'
  else if (pickup < today) dateError = 'Pickup date cannot be in the past.'
  else if (days < 1) dateError = 'Return date must be after the pickup date.'
  else if (days > MAX_DAYS) dateError = `The maximum rental is ${MAX_DAYS} days.`

  const { quote, loading: quoting, error: quoteError } = useQuote(id, dateError ? '' : pickup, dateError ? '' : returnDate)

  const changePickup = (value) => {
    setPickup(value)
    if (value && returnDate <= value) setReturnDate(addDays(value, 1))
  }

  const rentNow = () => {
    const checkoutUrl = `/checkout?product=${id}&pickup=${pickup}&return=${returnDate}`
    if (!user) navigate('/login', { state: { from: checkoutUrl } })
    else navigate(checkoutUrl)
  }

  if (product.loading) return <PageLoader />
  if (product.error) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16">
        <ErrorState message={product.error} onRetry={product.reload} />
        <p className="mt-4 text-center">
          <Link to="/products" className="text-sm text-primary hover:underline">
            Back to all equipment
          </Link>
        </p>
      </div>
    )
  }

  const item = product.data

  const saveReview = async ({ rating, comment }) => {
    await reviewApi.update(editingReview.id, { rating, comment })
    toast.success('Review updated.')
    setEditingReview(null)
    reviews.reload()
    product.reload()
  }

  const removeReview = async () => {
    await reviewApi.remove(deletingReview.id)
    toast.success('Review deleted.')
    reviews.reload()
    product.reload()
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <nav className="mb-6 text-sm text-muted" aria-label="Breadcrumb">
        <Link to="/products" className="hover:text-primary">
          Equipment
        </Link>
        {' / '}
        <Link to={`/products?category=${item.category.slug}`} className="hover:text-primary">
          {item.category.name}
        </Link>
      </nav>

      <div className="grid gap-10 lg:grid-cols-2">
        <div className="self-start overflow-hidden rounded-xl border border-line bg-white">
          <img src={imageSrc(item.image_url)} alt={item.name} className="aspect-[4/3] w-full object-cover" />
        </div>

        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-muted">
            {item.brand} · {item.model}
          </p>
          <h1 className="mt-1 text-3xl font-bold">{item.name}</h1>
          <div className="mt-2 flex items-center gap-2 text-sm text-muted">
            <StarRating value={item.average_rating ?? 0} />
            {item.average_rating ? (
              <span>
                {item.average_rating.toFixed(1)} ({item.review_count} review{item.review_count === 1 ? '' : 's'})
              </span>
            ) : (
              <span>No reviews yet</span>
            )}
          </div>
          <p className="mt-4 text-muted">{item.short_description}</p>
          <p className="mt-4 text-3xl font-bold">
            {formatMoney(item.daily_price)}
            <span className="text-base font-normal text-muted"> / day</span>
          </p>

          <section className="mt-6 rounded-xl border border-line bg-white p-5" aria-labelledby="rental-heading">
            <h2 id="rental-heading" className="font-semibold">
              Choose your rental dates
            </h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Input
                type="date"
                label="Pickup date"
                min={today}
                value={pickup}
                onChange={(event) => changePickup(event.target.value)}
              />
              <Input
                type="date"
                label="Return date"
                min={pickup ? addDays(pickup, 1) : today}
                max={pickup ? addDays(pickup, MAX_DAYS) : undefined}
                value={returnDate}
                onChange={(event) => setReturnDate(event.target.value)}
              />
            </div>

            <div className="mt-4 min-h-24" aria-live="polite">
              {dateError ? (
                <Alert type="warning">{dateError}</Alert>
              ) : quoting ? (
                <p className="flex items-center gap-2 text-sm text-muted">
                  <Spinner /> Checking availability...
                </p>
              ) : quoteError ? (
                <Alert>{quoteError}</Alert>
              ) : quote ? (
                <div className="space-y-3">
                  {quote.available ? (
                    <p className="flex items-center gap-2 text-sm font-medium text-green-700">
                      <CircleCheck className="h-5 w-5" aria-hidden="true" /> Available for these dates
                      {quote.available_units <= 2 && ` (only ${quote.available_units} left)`}
                    </p>
                  ) : (
                    <p className="flex items-center gap-2 text-sm font-medium text-red-700">
                      <CircleX className="h-5 w-5" aria-hidden="true" /> Not available for these dates. Try different dates.
                    </p>
                  )}
                  <dl className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted">
                        {formatMoney(quote.daily_price)} × {quote.rental_days} day{quote.rental_days === 1 ? '' : 's'}
                      </dt>
                      <dd>{formatMoney(quote.total_amount)}</dd>
                    </div>
                    <div className="flex justify-between border-t border-line pt-2 text-base font-bold">
                      <dt>Total</dt>
                      <dd>{formatMoney(quote.total_amount)}</dd>
                    </div>
                  </dl>
                  <p className="text-xs text-muted">
                    {formatDate(quote.pickup_date)} to {formatDate(quote.return_date)}. The return day is not charged.
                  </p>
                </div>
              ) : null}
            </div>

            <Button size="lg" className="mt-4 w-full" onClick={rentNow} disabled={!quote?.available || quoting || Boolean(dateError)}>
              Rent now
            </Button>
          </section>
        </div>
      </div>

      <div className="mt-12 grid gap-10 lg:grid-cols-2">
        <section aria-labelledby="about-heading">
          <h2 id="about-heading" className="text-xl font-bold">
            About this equipment
          </h2>
          <p className="mt-3 whitespace-pre-line text-muted">{item.description}</p>
          <h3 className="mt-8 text-lg font-semibold">Technical specifications</h3>
          {Object.keys(item.specifications).length === 0 ? (
            <p className="mt-2 text-sm text-muted">No specifications listed.</p>
          ) : (
            <dl className="mt-3 divide-y divide-line rounded-xl border border-line bg-white">
              {Object.entries(item.specifications).map(([name, value]) => (
                <div key={name} className="grid grid-cols-2 gap-4 px-4 py-3 text-sm">
                  <dt className="text-muted">{name}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          )}
        </section>

        <section aria-labelledby="reviews-heading">
          <h2 id="reviews-heading" className="text-xl font-bold">
            Customer reviews
          </h2>
          <div className="mt-3">
            {reviews.loading ? (
              <PageLoader />
            ) : reviews.error ? (
              <ErrorState message={reviews.error} onRetry={reviews.reload} />
            ) : reviews.data.length === 0 ? (
              <EmptyState title="No reviews yet" description="Rent this item and be the first to review it." />
            ) : (
              <ul className="space-y-4">
                {reviews.data.map((review) => (
                  <li key={review.id} className="rounded-xl border border-line bg-white p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <StarRating value={review.rating} />
                        <p className="mt-1 text-sm font-medium">{review.reviewer_name}</p>
                      </div>
                      {user?.id === review.user_id && (
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" onClick={() => setEditingReview(review)} aria-label="Edit your review">
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => setDeletingReview(review)} aria-label="Delete your review">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </div>
                    {review.comment && <p className="mt-2 text-sm text-muted">{review.comment}</p>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      {editingReview && (
        <Modal title="Edit your review" onClose={() => setEditingReview(null)}>
          <ReviewForm
            initialRating={editingReview.rating}
            initialComment={editingReview.comment ?? ''}
            submitLabel="Save review"
            onSubmit={saveReview}
            onCancel={() => setEditingReview(null)}
          />
        </Modal>
      )}
      {deletingReview && (
        <ConfirmModal
          title="Delete review"
          message="This permanently removes your review."
          confirmLabel="Delete review"
          danger
          onConfirm={removeReview}
          onClose={() => setDeletingReview(null)}
        />
      )}
    </div>
  )
}

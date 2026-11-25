import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Info } from 'lucide-react'
import { bookingApi, productApi } from '../../api'
import Button from '../../components/Button'
import { Alert, ErrorState, PageLoader } from '../../components/Feedback'
import { useAuth } from '../../contexts/AuthContext'
import useFetch from '../../hooks/useFetch'
import useQuote from '../../hooks/useQuote'
import { errorMessage, formatDate, formatMoney, imageSrc } from '../../utils/format'

const OUTCOMES = [
  { value: 'success', label: 'Payment successful', hint: 'The booking will be confirmed.' },
  { value: 'failure', label: 'Payment fails', hint: 'Try this to see how a declined payment is handled.' },
]

export default function Checkout() {
  const [params] = useSearchParams()
  const productId = params.get('product')
  const pickup = params.get('pickup')
  const returnDate = params.get('return')

  const { user } = useAuth()
  const navigate = useNavigate()
  const product = useFetch(() => productApi.get(productId), [productId])
  const { quote, loading: quoting, error: quoteError, reload: reloadQuote } = useQuote(productId, pickup, returnDate)

  // One key per checkout attempt: if the same request is sent twice (double click,
  // retry after a network drop) the server returns the first booking instead of a second one.
  const [idempotencyKey] = useState(() => crypto.randomUUID())
  const [outcome, setOutcome] = useState('success')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const [priceChange, setPriceChange] = useState(null)

  if (!productId || !pickup || !returnDate) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <Alert type="warning">
          Choose a product and rental dates first. <Link to="/products" className="font-medium underline">Browse equipment</Link>
        </Alert>
      </div>
    )
  }
  if (product.loading || (quoting && !quote)) return <PageLoader />
  if (product.error || quoteError) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16">
        <ErrorState message={product.error || quoteError} onRetry={() => (product.error ? product.reload() : reloadQuote())} />
      </div>
    )
  }
  if (!quote) return <PageLoader />

  const item = product.data

  const confirm = async () => {
    setSubmitting(true)
    setFormError('')
    try {
      const booking = await bookingApi.create({
        product_id: Number(productId),
        pickup_date: pickup,
        return_date: returnDate,
        // The total the customer is looking at. The server re-prices and compares.
        expected_total: quote.total_amount,
        idempotency_key: idempotencyKey,
        payment_outcome: outcome,
      })
      navigate(`/bookings/${booking.id}/confirmation`, { replace: true })
    } catch (error) {
      const status = error.response?.status
      const detail = error.response?.data?.detail
      if (status === 409 && detail?.code === 'PRICE_CHANGED') {
        setPriceChange({ from: quote.total_amount, to: detail.total_amount })
        reloadQuote()
      } else if (status === 402) {
        setFormError('Your simulated payment failed. No booking was made and nothing was reserved. You can try again.')
      } else if (status === 409) {
        setFormError(errorMessage(error))
        reloadQuote()
      } else {
        setFormError(errorMessage(error))
      }
      setSubmitting(false)
    }
  }

  const unavailable = !quote.available

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold">Checkout</h1>

      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="space-y-6">
          <section className="rounded-xl border border-line bg-white p-5" aria-labelledby="summary-heading">
            <h2 id="summary-heading" className="font-semibold">
              Equipment
            </h2>
            <div className="mt-4 flex gap-4">
              <img src={imageSrc(item.image_url)} alt="" className="h-24 w-32 rounded-lg object-cover" />
              <div>
                <p className="font-semibold">{item.name}</p>
                <p className="text-sm text-muted">
                  {item.brand} · {item.category.name}
                </p>
                <p className="mt-2 text-sm">
                  {formatDate(quote.pickup_date)} to {formatDate(quote.return_date)}
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-line bg-white p-5" aria-labelledby="customer-heading">
            <h2 id="customer-heading" className="font-semibold">
              Your details
            </h2>
            <p className="mt-3 text-sm">{user.full_name}</p>
            <p className="text-sm text-muted">{user.email}</p>
            <h3 className="mt-5 text-sm font-semibold">Pickup instructions</h3>
            <p className="mt-1 text-sm text-muted">
              Collect your equipment from the Rentify store on your pickup date with a photo ID and your booking
              reference. Return it by the return date to avoid it being flagged as overdue.
            </p>
          </section>

          <section className="rounded-xl border border-line bg-white p-5" aria-labelledby="payment-heading">
            <h2 id="payment-heading" className="font-semibold">
              Payment
            </h2>
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-blue-50 p-3 text-sm text-blue-900">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <p>
                <strong>Simulated payment.</strong> No actual financial transaction will occur and no card details are
                collected. Choose the outcome you want to test.
              </p>
            </div>
            <fieldset className="mt-4 space-y-2" disabled={submitting}>
              <legend className="sr-only">Simulated payment outcome</legend>
              {OUTCOMES.map((option) => (
                <label
                  key={option.value}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 ${outcome === option.value ? 'border-primary bg-orange-50/50' : 'border-line'}`}
                >
                  <input
                    type="radio"
                    name="outcome"
                    value={option.value}
                    checked={outcome === option.value}
                    onChange={() => setOutcome(option.value)}
                    className="mt-1 accent-primary"
                  />
                  <span>
                    <span className="block text-sm font-medium">{option.label}</span>
                    <span className="block text-xs text-muted">{option.hint}</span>
                  </span>
                </label>
              ))}
            </fieldset>
          </section>
        </div>

        <aside className="h-fit rounded-xl border border-line bg-white p-5 lg:sticky lg:top-32" aria-labelledby="total-heading">
          <h2 id="total-heading" className="font-semibold">
            Order summary
          </h2>
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted">Daily rental price</dt>
              <dd>{formatMoney(quote.daily_price)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Rental duration</dt>
              <dd>
                {quote.rental_days} day{quote.rental_days === 1 ? '' : 's'}
              </dd>
            </div>
            <div className="flex justify-between border-t border-line pt-3 text-lg font-bold">
              <dt>Total</dt>
              <dd>{formatMoney(quote.total_amount)}</dd>
            </div>
          </dl>

          <div className="mt-4 space-y-3" aria-live="polite">
            {priceChange && (
              <Alert type="warning">
                The price changed from {formatMoney(priceChange.from)} to <strong>{formatMoney(priceChange.to)}</strong>.
                Please review it and confirm again.
              </Alert>
            )}
            {unavailable && !formError && (
              <Alert>This equipment is no longer available for these dates. <Link to={`/products/${productId}`} className="font-medium underline">Choose other dates</Link></Alert>
            )}
            {formError && <Alert>{formError}</Alert>}
          </div>

          <Button size="lg" className="mt-4 w-full" onClick={confirm} loading={submitting} disabled={unavailable}>
            {priceChange ? 'Accept new price and confirm' : 'Confirm booking'}
          </Button>
          <p className="mt-3 text-center text-xs text-muted">Demo only. You will not be charged.</p>
        </aside>
      </div>
    </div>
  )
}

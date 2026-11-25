import { Link } from 'react-router-dom'
import { formatDate, formatDateTime, formatMoney, imageSrc } from '../utils/format'
import StatusBadge from './StatusBadge'

function Row({ label, children }) {
  return (
    <div className="flex justify-between gap-4 py-2.5 text-sm">
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-medium">{children}</dd>
    </div>
  )
}

/** Read-only summary of one booking, shared by the confirmation and detail pages. */
export default function BookingDetails({ booking }) {
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-white">
      <div className="flex gap-4 border-b border-line p-5">
        <img
          src={imageSrc(booking.product.image_url)}
          alt=""
          className="h-20 w-24 shrink-0 rounded-lg object-cover"
        />
        <div className="min-w-0">
          <Link to={`/products/${booking.product.id}`} className="font-semibold hover:text-primary">
            {booking.product.name}
          </Link>
          <p className="text-sm text-muted">
            {booking.product.brand} · Unit {booking.asset_code}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <StatusBadge status={booking.status} />
            {booking.is_overdue && <StatusBadge status="OVERDUE" label="Overdue: please return it" />}
          </div>
        </div>
      </div>
      <dl className="divide-y divide-line px-5">
        <Row label="Booking reference">
          <span className="font-mono">{booking.booking_reference}</span>
        </Row>
        <Row label="Pickup date">{formatDate(booking.pickup_date)}</Row>
        <Row label="Return date">{formatDate(booking.return_date)}</Row>
        <Row label="Rental duration">
          {booking.rental_days} day{booking.rental_days === 1 ? '' : 's'}
        </Row>
        <Row label="Daily rental price">{formatMoney(booking.daily_price)}</Row>
        <Row label="Total amount">
          <span className="text-base font-bold">{formatMoney(booking.total_amount)}</span>
        </Row>
        <Row label="Payment status">
          {booking.payment_status ? <StatusBadge status={booking.payment_status} /> : '-'}
        </Row>
        {booking.transaction_reference && (
          <Row label="Transaction (simulated)">
            <span className="font-mono text-xs">{booking.transaction_reference}</span>
          </Row>
        )}
        {booking.actual_pickup_at && <Row label="Picked up">{formatDateTime(booking.actual_pickup_at)}</Row>}
        {booking.actual_return_at && <Row label="Returned">{formatDateTime(booking.actual_return_at)}</Row>}
        {booking.cancellation_reason && <Row label="Cancellation reason">{booking.cancellation_reason}</Row>}
      </dl>
    </div>
  )
}

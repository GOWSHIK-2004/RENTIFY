import { useState } from 'react'
import { PackageCheck, PackageOpen, Search, TriangleAlert, XCircle } from 'lucide-react'
import { adminApi } from '../../api'
import Button from '../../components/Button'
import ConfirmModal from '../../components/ConfirmModal'
import DataTable from '../../components/DataTable'
import { Alert, ErrorState, PageLoader } from '../../components/Feedback'
import Input from '../../components/Input'
import Modal from '../../components/Modal'
import PageHeader from '../../components/PageHeader'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'
import useFetch from '../../hooks/useFetch'
import { errorMessage, formatDate, formatMoney, titleCase } from '../../utils/format'

const STATUSES = ['CONFIRMED', 'PICKED_UP', 'RETURNED', 'CANCELLED']
const CONDITIONS = ['EXCELLENT', 'GOOD', 'FAIR', 'DAMAGED']

function ReturnModal({ booking, onDone, onClose }) {
  const [condition, setCondition] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    setSubmitting(true)
    setError('')
    try {
      await adminApi.returnBooking(booking.id, condition || null)
      onDone()
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <Modal title={`Record return: ${booking.booking_reference}`} onClose={submitting ? () => {} : onClose}>
      <div className="space-y-4">
        {error && <Alert>{error}</Alert>}
        <p className="text-sm text-muted">
          {booking.product.name} ({booking.asset_code}) from {booking.customer.full_name}.
        </p>
        <Input as="select" label="Condition after return" value={condition} onChange={(event) => setCondition(event.target.value)}>
          <option value="">Unchanged</option>
          {CONDITIONS.map((value) => (
            <option key={value} value={value}>
              {titleCase(value)}
            </option>
          ))}
        </Input>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={submit} loading={submitting}>
            Record return
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default function Bookings() {
  const toast = useToast()
  const [status, setStatus] = useState('')
  const [overdueOnly, setOverdueOnly] = useState(false)
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [action, setAction] = useState(null) // { type: 'pickup' | 'return' | 'cancel', booking }

  const bookings = useFetch(
    () =>
      adminApi.bookings({
        status_filter: status || undefined,
        overdue: overdueOnly || undefined,
        search: query || undefined,
        page,
        page_size: 15,
      }),
    [status, overdueOnly, query, page],
  )

  const finish = (message) => {
    toast.success(message)
    setAction(null)
    bookings.reload()
  }

  const columns = [
    { header: 'Reference', render: (b) => <span className="whitespace-nowrap font-mono text-xs">{b.booking_reference}</span> },
    {
      header: 'Customer',
      render: (b) => (
        <div>
          <p className="font-medium">{b.customer.full_name}</p>
          <p className="text-xs text-muted">{b.customer.email}</p>
        </div>
      ),
    },
    { header: 'Product', render: (b) => b.product.name },
    { header: 'Asset', render: (b) => <span className="whitespace-nowrap font-mono text-xs">{b.asset_code}</span> },
    {
      header: 'Dates',
      render: (b) => (
        <div className="whitespace-nowrap">
          <p>{formatDate(b.pickup_date)}</p>
          <p className="text-xs text-muted">to {formatDate(b.return_date)}</p>
        </div>
      ),
    },
    { header: 'Total', render: (b) => formatMoney(b.total_amount) },
    {
      header: 'Status',
      render: (b) => (
        <div className="flex flex-col items-start gap-1">
          <StatusBadge status={b.status} />
          {b.is_overdue && <StatusBadge status="OVERDUE" />}
          {b.affected_by_overdue && (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700">
              <TriangleAlert className="h-3.5 w-3.5" aria-hidden="true" /> Unit still out (overdue)
            </span>
          )}
        </div>
      ),
    },
    {
      header: 'Actions',
      render: (b) => (
        <div className="flex flex-wrap gap-1">
          {b.status === 'CONFIRMED' && (
            <>
              <Button variant="ghost" size="sm" onClick={() => setAction({ type: 'pickup', booking: b })}>
                <PackageOpen className="h-4 w-4" /> Pickup
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setAction({ type: 'cancel', booking: b })}>
                <XCircle className="h-4 w-4" /> Cancel
              </Button>
            </>
          )}
          {b.status === 'PICKED_UP' && (
            <Button variant="ghost" size="sm" onClick={() => setAction({ type: 'return', booking: b })}>
              <PackageCheck className="h-4 w-4" /> Return
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Bookings" description="Process pickups and returns, or cancel confirmed bookings." />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <form
          onSubmit={(event) => {
            event.preventDefault()
            setPage(1)
            setQuery(search.trim())
          }}
          className="flex gap-2"
          role="search"
        >
          <Input type="search" aria-label="Search bookings" placeholder="Reference, customer or product" value={search} onChange={(event) => setSearch(event.target.value)} className="w-72" />
          <Button type="submit" variant="secondary">
            <Search className="h-4 w-4" /> Search
          </Button>
        </form>
        <Input
          as="select"
          aria-label="Filter by status"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value)
            setPage(1)
          }}
        >
          <option value="">All statuses</option>
          {STATUSES.map((value) => (
            <option key={value} value={value}>
              {titleCase(value)}
            </option>
          ))}
        </Input>
        <label className="flex items-center gap-2 pb-2 text-sm">
          <input
            type="checkbox"
            className="accent-primary"
            checked={overdueOnly}
            onChange={(event) => {
              setOverdueOnly(event.target.checked)
              setPage(1)
            }}
          />
          Overdue only
        </label>
      </div>

      {bookings.loading ? (
        <PageLoader />
      ) : bookings.error ? (
        <ErrorState message={bookings.error} onRetry={bookings.reload} />
      ) : (
        <>
          <DataTable columns={columns} rows={bookings.data.items} emptyTitle="No bookings match" />
          <Pagination page={bookings.data.page} pages={bookings.data.pages} onChange={setPage} />
        </>
      )}

      {action?.type === 'pickup' && (
        <ConfirmModal
          title={`Hand over ${action.booking.booking_reference}?`}
          message={`Mark ${action.booking.product.name} (${action.booking.asset_code}) as picked up by ${action.booking.customer.full_name}. This is only allowed during the scheduled rental period.`}
          confirmLabel="Mark as picked up"
          onConfirm={async () => {
            await adminApi.pickup(action.booking.id)
            finish('Pickup recorded.')
          }}
          onClose={() => setAction(null)}
        />
      )}
      {action?.type === 'cancel' && (
        <ConfirmModal
          title={`Cancel ${action.booking.booking_reference}?`}
          message="The unit is released and the simulated payment is refunded."
          confirmLabel="Cancel booking"
          danger
          askReason
          onConfirm={async (reason) => {
            await adminApi.cancelBooking(action.booking.id, reason)
            finish('Booking cancelled and payment refunded.')
          }}
          onClose={() => setAction(null)}
        />
      )}
      {action?.type === 'return' && (
        <ReturnModal booking={action.booking} onClose={() => setAction(null)} onDone={() => finish('Return recorded.')} />
      )}
    </>
  )
}

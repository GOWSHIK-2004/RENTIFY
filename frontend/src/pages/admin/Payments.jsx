import { useState } from 'react'
import { adminApi } from '../../api'
import DataTable from '../../components/DataTable'
import { ErrorState, PageLoader } from '../../components/Feedback'
import Input from '../../components/Input'
import PageHeader from '../../components/PageHeader'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import useFetch from '../../hooks/useFetch'
import { formatDateTime, formatMoney } from '../../utils/format'

const columns = [
  { header: 'Transaction', render: (p) => <span className="font-mono text-xs">{p.transaction_reference}</span> },
  { header: 'Booking', render: (p) => <span className="font-mono text-xs">{p.booking_reference}</span> },
  { header: 'Customer', render: (p) => p.customer_name },
  { header: 'Product', render: (p) => p.product_name },
  { header: 'Amount', render: (p) => formatMoney(p.amount) },
  { header: 'Status', render: (p) => <StatusBadge status={p.status} /> },
  { header: 'Date', render: (p) => formatDateTime(p.created_at) },
]

export default function Payments() {
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const payments = useFetch(() => adminApi.payments({ status_filter: status || undefined, page, page_size: 20 }), [status, page])

  return (
    <>
      <PageHeader title="Payments" description="Simulated payment records. No real money moves." />
      <div className="mb-4">
        <Input
          as="select"
          aria-label="Filter by status"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value)
            setPage(1)
          }}
        >
          <option value="">All payments</option>
          <option value="SUCCESS">Successful</option>
          <option value="REFUNDED">Refunded</option>
        </Input>
      </div>
      {payments.loading ? (
        <PageLoader />
      ) : payments.error ? (
        <ErrorState message={payments.error} onRetry={payments.reload} />
      ) : (
        <>
          <DataTable columns={columns} rows={payments.data.items} emptyTitle="No payments found" />
          <Pagination page={payments.data.page} pages={payments.data.pages} onChange={setPage} />
        </>
      )}
    </>
  )
}

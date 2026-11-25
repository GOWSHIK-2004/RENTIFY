import { useState } from 'react'
import { Search } from 'lucide-react'
import { adminApi } from '../../api'
import Button from '../../components/Button'
import DataTable from '../../components/DataTable'
import { ErrorState, PageLoader } from '../../components/Feedback'
import Input from '../../components/Input'
import PageHeader from '../../components/PageHeader'
import Pagination from '../../components/Pagination'
import useFetch from '../../hooks/useFetch'
import { formatDateTime } from '../../utils/format'

const columns = [
  { header: 'Name', render: (c) => <span className="font-medium">{c.full_name}</span> },
  { header: 'Email', render: (c) => c.email },
  { header: 'Joined', render: (c) => formatDateTime(c.created_at) },
  { header: 'Bookings', render: (c) => c.booking_count },
]

export default function Customers() {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const customers = useFetch(() => adminApi.customers({ search: query || undefined, page, page_size: 20 }), [query, page])

  return (
    <>
      <PageHeader title="Customers" description="Registered customer accounts." />
      <form
        onSubmit={(event) => {
          event.preventDefault()
          setPage(1)
          setQuery(search.trim())
        }}
        className="mb-4 flex max-w-md gap-2"
        role="search"
      >
        <Input type="search" aria-label="Search customers" placeholder="Name or email" value={search} onChange={(event) => setSearch(event.target.value)} className="flex-1" />
        <Button type="submit" variant="secondary">
          <Search className="h-4 w-4" /> Search
        </Button>
      </form>
      {customers.loading ? (
        <PageLoader />
      ) : customers.error ? (
        <ErrorState message={customers.error} onRetry={customers.reload} />
      ) : (
        <>
          <DataTable columns={columns} rows={customers.data.items} emptyTitle="No customers found" />
          <Pagination page={customers.data.page} pages={customers.data.pages} onChange={setPage} />
        </>
      )}
    </>
  )
}

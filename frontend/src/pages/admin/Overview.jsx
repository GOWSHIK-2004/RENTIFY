import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { adminApi } from '../../api'
import { ErrorState, PageLoader } from '../../components/Feedback'
import PageHeader from '../../components/PageHeader'
import useFetch from '../../hooks/useFetch'
import { formatMoney, titleCase } from '../../utils/format'

// Status colours. The legend and tooltips also carry the names, so colour is never the only cue.
const STATUS_COLORS = { CONFIRMED: '#2563EB', PICKED_UP: '#F97316', RETURNED: '#16A34A', CANCELLED: '#94A3B8' }
const AXIS = { fontSize: 12, fill: '#64748B' }

const monthLabel = (month) => {
  const [year, number] = month.split('-').map(Number)
  return new Date(year, number - 1).toLocaleDateString('en-IN', { month: 'short' })
}

function StatCard({ label, value, tone = 'text-ink' }) {
  return (
    <div className="rounded-xl border border-line bg-white p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <section className="rounded-xl border border-line bg-white p-5">
      <h2 className="font-semibold">{title}</h2>
      <div className="mt-4 h-72">{children}</div>
    </section>
  )
}

export default function Overview() {
  const { data, loading, error, reload } = useFetch(() => adminApi.dashboard(), [])

  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const revenue = data.monthly_revenue.map((row) => ({ month: monthLabel(row.month), revenue: Number(row.revenue) }))
  const statuses = data.status_distribution.map((row) => ({
    key: row.status,
    name: titleCase(row.status),
    value: row.count,
  }))
  const hasBookings = statuses.some((row) => row.value > 0)

  return (
    <>
      <PageHeader title="Overview" description="Live figures from the Rentify database." />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Active products" value={data.active_products} />
        <StatCard label="Physical inventory units" value={data.inventory_units} />
        <StatCard label="Confirmed bookings" value={data.confirmed_bookings} />
        <StatCard label="Active rentals" value={data.active_rentals} />
        <StatCard label="Completed bookings" value={data.completed_bookings} />
        <StatCard
          label="Overdue rentals"
          value={data.overdue_rentals}
          tone={data.overdue_rentals > 0 ? 'text-red-600' : 'text-ink'}
        />
        <div className="sm:col-span-2">
          <StatCard label="Total simulated rental revenue" value={formatMoney(data.total_revenue)} tone="text-primary-dark" />
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <ChartCard title="Monthly rental revenue (last 12 months)">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={revenue} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="#E2E8F0" />
              <XAxis dataKey="month" tick={AXIS} axisLine={false} tickLine={false} />
              <YAxis tick={AXIS} axisLine={false} tickLine={false} width={56} tickFormatter={(v) => formatMoney(v)} />
              <Tooltip formatter={(value) => [formatMoney(value), 'Revenue']} cursor={{ fill: '#F1F5F9' }} />
              <Bar dataKey="revenue" fill="#F97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Booking status distribution">
          {hasBookings ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statuses} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
                  {statuses.map((row) => (
                    <Cell key={row.key} fill={STATUS_COLORS[row.key]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
                <Legend formatter={(name, entry) => `${name} (${entry.payload.value})`} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted">No bookings yet.</p>
          )}
        </ChartCard>

        <div className="xl:col-span-2">
          <ChartCard title="Most rented equipment (excludes cancelled)">
            {data.top_products.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.top_products} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
                  <CartesianGrid horizontal={false} stroke="#E2E8F0" />
                  <XAxis type="number" allowDecimals={false} tick={AXIS} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={AXIS} width={170} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(value) => [value, 'Bookings']} cursor={{ fill: '#F1F5F9' }} />
                  <Bar dataKey="bookings" fill="#0F172A" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted">No bookings yet.</p>
            )}
          </ChartCard>
        </div>
      </div>
    </>
  )
}

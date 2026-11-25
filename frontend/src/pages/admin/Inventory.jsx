import { useState } from 'react'
import { Pencil, Plus } from 'lucide-react'
import { adminApi, productApi } from '../../api'
import Button from '../../components/Button'
import DataTable from '../../components/DataTable'
import { Alert, ErrorState, PageLoader } from '../../components/Feedback'
import Input from '../../components/Input'
import Modal from '../../components/Modal'
import PageHeader from '../../components/PageHeader'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'
import useFetch from '../../hooks/useFetch'
import { errorMessage, formatDateTime, titleCase } from '../../utils/format'

const CONDITIONS = ['EXCELLENT', 'GOOD', 'FAIR', 'DAMAGED']
const STATUSES = ['ACTIVE', 'MAINTENANCE', 'RETIRED']

function UnitForm({ unit, products, onSaved, onClose }) {
  const toast = useToast()
  const [form, setForm] = useState({
    product_id: unit ? String(unit.product_id) : '',
    asset_code: unit?.asset_code ?? '',
    condition: unit?.condition ?? 'EXCELLENT',
    operational_status: unit?.operational_status ?? 'ACTIVE',
  })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  const submit = async (event) => {
    event.preventDefault()
    setFormError('')
    const next = {}
    if (!unit && !form.product_id) next.product_id = 'Choose a product.'
    if (!unit && form.asset_code.trim().length < 2) next.asset_code = 'Enter an asset code, for example CAM-004.'
    setErrors(next)
    if (Object.keys(next).length) return

    setSaving(true)
    try {
      if (unit) {
        await adminApi.updateUnit(unit.id, { condition: form.condition, operational_status: form.operational_status })
      } else {
        await adminApi.createUnit({ ...form, product_id: Number(form.product_id), asset_code: form.asset_code.trim() })
      }
      toast.success(unit ? 'Unit updated.' : 'Unit added.')
      onSaved()
    } catch (error) {
      setFormError(errorMessage(error))
      setSaving(false)
    }
  }

  return (
    <Modal title={unit ? `Update ${unit.asset_code}` : 'Add inventory unit'} onClose={onClose}>
      <form onSubmit={submit} noValidate className="space-y-4">
        {formError && <Alert>{formError}</Alert>}
        {unit ? (
          <p className="text-sm text-muted">{unit.product_name}</p>
        ) : (
          <>
            <Input as="select" label="Product" value={form.product_id} onChange={set('product_id')} error={errors.product_id}>
              <option value="">Choose...</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </Input>
            <Input label="Asset code" value={form.asset_code} onChange={set('asset_code')} error={errors.asset_code} hint="Must be unique, for example CAM-004." />
          </>
        )}
        <Input as="select" label="Condition" value={form.condition} onChange={set('condition')}>
          {CONDITIONS.map((value) => (
            <option key={value} value={value}>
              {titleCase(value)}
            </option>
          ))}
        </Input>
        <Input
          as="select"
          label="Operational status"
          value={form.operational_status}
          onChange={set('operational_status')}
          hint="Only active, non-damaged units can be assigned to new bookings."
        >
          {STATUSES.map((value) => (
            <option key={value} value={value}>
              {titleCase(value)}
            </option>
          ))}
        </Input>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            {unit ? 'Save changes' : 'Add unit'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default function Inventory() {
  const [productId, setProductId] = useState('')
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState(null) // null | 'new' | unit

  const products = useFetch(() => productApi.all(), [])
  const units = useFetch(
    () => adminApi.inventory({ product_id: productId || undefined, search: search.trim() || undefined }),
    [productId, search],
  )

  const columns = [
    { header: 'Asset code', render: (u) => <span className="font-mono font-medium">{u.asset_code}</span> },
    { header: 'Product', render: (u) => u.product_name },
    { header: 'Condition', render: (u) => <StatusBadge status={u.condition} /> },
    { header: 'Operational status', render: (u) => <StatusBadge status={u.operational_status} /> },
    { header: 'Added', render: (u) => formatDateTime(u.created_at) },
    {
      header: 'Actions',
      render: (u) => (
        <Button variant="ghost" size="sm" onClick={() => setEditing(u)}>
          <Pencil className="h-4 w-4" /> Update
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Inventory" description="Each row is one physical item that can be rented.">
        <Button onClick={() => setEditing('new')} disabled={!products.data}>
          <Plus className="h-4 w-4" /> Add unit
        </Button>
      </PageHeader>

      <div className="mb-4 flex flex-wrap gap-3">
        <Input as="select" aria-label="Filter by product" value={productId} onChange={(event) => setProductId(event.target.value)}>
          <option value="">All products</option>
          {products.data?.map((product) => (
            <option key={product.id} value={product.id}>
              {product.name}
            </option>
          ))}
        </Input>
        <Input type="search" aria-label="Search asset code" placeholder="Search asset code" value={search} onChange={(event) => setSearch(event.target.value)} />
      </div>

      {units.loading ? (
        <PageLoader />
      ) : units.error ? (
        <ErrorState message={units.error} onRetry={units.reload} />
      ) : (
        <DataTable columns={columns} rows={units.data} emptyTitle="No inventory units found" />
      )}

      {editing && products.data && (
        <UnitForm
          unit={editing === 'new' ? null : editing}
          products={products.data}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            units.reload()
          }}
        />
      )}
    </>
  )
}

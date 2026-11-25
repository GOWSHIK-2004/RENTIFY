import { useState } from 'react'
import { Archive, Pencil, Plus, RotateCcw, Search } from 'lucide-react'
import { categoryApi, productApi } from '../../api'
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
import { errorMessage, formatMoney, imageSrc } from '../../utils/format'

const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

// "Sensor: APS-C" per line <-> { Sensor: "APS-C" }
const specsToText = (specs) =>
  Object.entries(specs)
    .map(([name, value]) => `${name}: ${value}`)
    .join('\n')

const textToSpecs = (text) => {
  const specs = {}
  for (const line of text.split('\n').filter((l) => l.trim())) {
    const separator = line.indexOf(':')
    if (separator < 1 || !line.slice(separator + 1).trim()) {
      throw new Error(`Specification "${line.trim()}" must look like "Name: Value".`)
    }
    specs[line.slice(0, separator).trim()] = line.slice(separator + 1).trim()
  }
  return specs
}

const emptyForm = {
  name: '',
  brand: '',
  model: '',
  category_id: '',
  daily_price: '',
  short_description: '',
  description: '',
  specs: '',
  is_featured: false,
  is_active: true,
}

function ProductForm({ product, categories, onSaved, onClose }) {
  const toast = useToast()
  const [form, setForm] = useState(
    product
      ? {
          name: product.name,
          brand: product.brand,
          model: product.model,
          category_id: String(product.category.id),
          daily_price: product.daily_price,
          short_description: product.short_description,
          description: product.description,
          specs: specsToText(product.specifications),
          is_featured: product.is_featured,
          is_active: product.is_active,
        }
      : emptyForm,
  )
  const [image, setImage] = useState(null)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (field) => (event) =>
    setForm({ ...form, [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value })

  const chooseImage = (event) => {
    const file = event.target.files[0]
    if (!file) return setImage(null)
    if (!IMAGE_TYPES.includes(file.type)) {
      setErrors({ ...errors, image: 'Choose a JPEG, PNG or WebP image.' })
      return setImage(null)
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setErrors({ ...errors, image: 'The image must be 5 MB or smaller.' })
      return setImage(null)
    }
    setErrors({ ...errors, image: undefined })
    setImage(file)
  }

  const validate = () => {
    const next = {}
    if (form.name.trim().length < 2) next.name = 'Enter a product name.'
    if (!form.brand.trim()) next.brand = 'Enter a brand.'
    if (!form.model.trim()) next.model = 'Enter a model.'
    if (!form.category_id) next.category_id = 'Choose a category.'
    if (!(Number(form.daily_price) > 0)) next.daily_price = 'Enter a price above 0.'
    if (!form.short_description.trim()) next.short_description = 'Enter a short description.'
    if (!form.description.trim()) next.description = 'Enter a detailed description.'
    try {
      textToSpecs(form.specs)
    } catch (error) {
      next.specs = error.message
    }
    setErrors((current) => ({ image: current.image, ...next }))
    return Object.keys(next).length === 0 && !errors.image
  }

  const submit = async (event) => {
    event.preventDefault()
    setFormError('')
    if (!validate()) return
    setSaving(true)
    const payload = {
      name: form.name.trim(),
      brand: form.brand.trim(),
      model: form.model.trim(),
      category_id: Number(form.category_id),
      daily_price: form.daily_price,
      short_description: form.short_description.trim(),
      description: form.description.trim(),
      specifications: textToSpecs(form.specs),
      is_featured: form.is_featured,
      is_active: form.is_active,
    }
    try {
      const saved = product ? await productApi.update(product.id, payload) : await productApi.create(payload)
      if (image) {
        try {
          await productApi.uploadImage(saved.id, image)
        } catch (error) {
          toast.error(`Product saved, but the image failed: ${errorMessage(error)}`)
          onSaved()
          return
        }
      }
      toast.success(product ? 'Product updated.' : 'Product created.')
      onSaved()
    } catch (error) {
      setFormError(errorMessage(error))
      setSaving(false)
    }
  }

  return (
    <Modal title={product ? `Edit ${product.name}` : 'Add product'} onClose={onClose} wide>
      <form onSubmit={submit} noValidate className="space-y-4">
        {formError && <Alert>{formError}</Alert>}
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Name" value={form.name} onChange={set('name')} error={errors.name} />
          <Input label="Brand" value={form.brand} onChange={set('brand')} error={errors.brand} />
          <Input label="Model" value={form.model} onChange={set('model')} error={errors.model} />
          <Input as="select" label="Category" value={form.category_id} onChange={set('category_id')} error={errors.category_id}>
            <option value="">Choose...</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
                {category.is_active ? '' : ' (archived)'}
              </option>
            ))}
          </Input>
          <Input
            label="Daily rental price (₹)"
            type="number"
            min="0"
            step="0.01"
            value={form.daily_price}
            onChange={set('daily_price')}
            error={errors.daily_price}
            hint={product ? 'Existing bookings keep the price they were made at.' : undefined}
          />
          <Input
            label={product ? 'Replace image' : 'Product image'}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={chooseImage}
            error={errors.image}
            hint="JPEG, PNG or WebP, up to 5 MB."
          />
        </div>
        <Input
          label="Short description"
          value={form.short_description}
          onChange={set('short_description')}
          error={errors.short_description}
          maxLength={300}
        />
        <Input as="textarea" rows={4} label="Detailed description" value={form.description} onChange={set('description')} error={errors.description} />
        <Input
          as="textarea"
          rows={4}
          label="Technical specifications"
          value={form.specs}
          onChange={set('specs')}
          error={errors.specs}
          hint="One per line, like “Sensor: APS-C”."
        />
        <div className="flex flex-wrap gap-6">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_featured} onChange={set('is_featured')} className="accent-primary" />
            Featured on the homepage
          </label>
          {product && (
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_active} onChange={set('is_active')} className="accent-primary" />
              Visible to customers
            </label>
          )}
        </div>
        <div className="flex justify-end gap-2 border-t border-line pt-4">
          <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            {product ? 'Save changes' : 'Create product'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default function Products() {
  const toast = useToast()
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState(null) // null | 'new' | product
  const [archiving, setArchiving] = useState(null)

  const categories = useFetch(() => categoryApi.list({ include_inactive: true }), [])
  const products = useFetch(
    () => productApi.list({ q: query || undefined, include_inactive: true, page, page_size: 15 }),
    [query, page],
  )

  const runSearch = (event) => {
    event.preventDefault()
    setPage(1)
    setQuery(search.trim())
  }

  const restore = async (product) => {
    try {
      await productApi.update(product.id, { is_active: true })
      toast.success(`${product.name} is visible again.`)
      products.reload()
    } catch (error) {
      toast.error(errorMessage(error))
    }
  }

  const archive = async () => {
    await productApi.archive(archiving.id)
    toast.success(`${archiving.name} archived. Booking history is kept.`)
    products.reload()
  }

  const columns = [
    {
      header: 'Product',
      render: (p) => (
        <div className="flex items-center gap-3">
          <img src={imageSrc(p.image_url)} alt="" className="h-10 w-14 rounded object-cover" />
          <div>
            <p className="font-medium">{p.name}</p>
            <p className="text-xs text-muted">{p.brand}</p>
          </div>
        </div>
      ),
    },
    { header: 'Category', render: (p) => p.category.name },
    { header: 'Daily price', render: (p) => formatMoney(p.daily_price) },
    {
      header: 'Status',
      render: (p) => (
        <div className="flex flex-wrap gap-1">
          <StatusBadge status={p.is_active ? 'ACTIVE' : 'ARCHIVED'} label={p.is_active ? 'Active' : 'Archived'} />
          {p.is_featured && <StatusBadge status="FEATURED" label="Featured" />}
        </div>
      ),
    },
    {
      header: 'Actions',
      render: (p) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={() => setEditing(p)}>
            <Pencil className="h-4 w-4" /> Edit
          </Button>
          {p.is_active ? (
            <Button variant="ghost" size="sm" onClick={() => setArchiving(p)}>
              <Archive className="h-4 w-4" /> Archive
            </Button>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => restore(p)}>
              <RotateCcw className="h-4 w-4" /> Restore
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Products" description="Add equipment, change prices and archive items.">
        <Button onClick={() => setEditing('new')} disabled={!categories.data}>
          <Plus className="h-4 w-4" /> Add product
        </Button>
      </PageHeader>

      <form onSubmit={runSearch} className="mb-4 flex max-w-md gap-2" role="search">
        <Input
          type="search"
          aria-label="Search products"
          placeholder="Search by name or brand"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="flex-1"
        />
        <Button type="submit" variant="secondary">
          <Search className="h-4 w-4" /> Search
        </Button>
      </form>

      {products.loading ? (
        <PageLoader />
      ) : products.error ? (
        <ErrorState message={products.error} onRetry={products.reload} />
      ) : (
        <>
          <DataTable columns={columns} rows={products.data.items} emptyTitle="No products found" />
          <Pagination page={products.data.page} pages={products.data.pages} onChange={setPage} />
        </>
      )}

      {editing && categories.data && (
        <ProductForm
          product={editing === 'new' ? null : editing}
          categories={categories.data}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            products.reload()
          }}
        />
      )}
      {archiving && (
        <ConfirmModal
          title={`Archive ${archiving.name}?`}
          message="It will disappear from the customer catalog. Existing bookings, payments and reviews are kept, and you can restore it later."
          confirmLabel="Archive"
          danger
          onConfirm={archive}
          onClose={() => setArchiving(null)}
        />
      )}
    </>
  )
}

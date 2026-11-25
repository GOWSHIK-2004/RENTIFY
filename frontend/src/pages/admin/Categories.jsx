import { useState } from 'react'
import { Archive, Pencil, Plus, RotateCcw } from 'lucide-react'
import { categoryApi } from '../../api'
import Button from '../../components/Button'
import ConfirmModal from '../../components/ConfirmModal'
import DataTable from '../../components/DataTable'
import { Alert, ErrorState, PageLoader } from '../../components/Feedback'
import Input from '../../components/Input'
import Modal from '../../components/Modal'
import PageHeader from '../../components/PageHeader'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'
import useFetch from '../../hooks/useFetch'
import { errorMessage } from '../../utils/format'

function CategoryForm({ category, onSaved, onClose }) {
  const toast = useToast()
  const [name, setName] = useState(category?.name ?? '')
  const [description, setDescription] = useState(category?.description ?? '')
  const [error, setError] = useState('')
  const [nameError, setNameError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    if (name.trim().length < 2) return setNameError('Enter a category name.')
    setNameError('')
    setSaving(true)
    const payload = { name: name.trim(), description: description.trim() || null }
    try {
      if (category) await categoryApi.update(category.id, payload)
      else await categoryApi.create(payload)
      toast.success(category ? 'Category updated.' : 'Category created.')
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
      setSaving(false)
    }
  }

  return (
    <Modal title={category ? `Edit ${category.name}` : 'Add category'} onClose={onClose}>
      <form onSubmit={submit} noValidate className="space-y-4">
        {error && <Alert>{error}</Alert>}
        <Input label="Name" value={name} onChange={(event) => setName(event.target.value)} error={nameError} />
        <Input as="textarea" rows={3} label="Description" value={description} onChange={(event) => setDescription(event.target.value)} />
        {category && <p className="text-xs text-muted">URL slug: {category.slug} (kept stable when renaming)</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            {category ? 'Save changes' : 'Create category'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default function Categories() {
  const toast = useToast()
  const { data, loading, error, reload } = useFetch(() => categoryApi.list({ include_inactive: true }), [])
  const [editing, setEditing] = useState(null) // null | 'new' | category
  const [archiving, setArchiving] = useState(null)

  const restore = async (category) => {
    try {
      await categoryApi.update(category.id, { is_active: true })
      toast.success(`${category.name} is active again.`)
      reload()
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const archive = async () => {
    await categoryApi.archive(archiving.id)
    toast.success(`${archiving.name} archived.`)
    reload()
  }

  const columns = [
    { header: 'Name', render: (c) => <span className="font-medium">{c.name}</span> },
    { header: 'Slug', render: (c) => <span className="font-mono text-xs">{c.slug}</span> },
    { header: 'Description', render: (c) => <span className="text-muted">{c.description || '-'}</span> },
    {
      header: 'Status',
      render: (c) => <StatusBadge status={c.is_active ? 'ACTIVE' : 'ARCHIVED'} label={c.is_active ? 'Active' : 'Archived'} />,
    },
    {
      header: 'Actions',
      render: (c) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={() => setEditing(c)}>
            <Pencil className="h-4 w-4" /> Edit
          </Button>
          {c.is_active ? (
            <Button variant="ghost" size="sm" onClick={() => setArchiving(c)}>
              <Archive className="h-4 w-4" /> Archive
            </Button>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => restore(c)}>
              <RotateCcw className="h-4 w-4" /> Restore
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Categories" description="Categories are archived, never deleted, because products refer to them.">
        <Button onClick={() => setEditing('new')}>
          <Plus className="h-4 w-4" /> Add category
        </Button>
      </PageHeader>

      {loading ? <PageLoader /> : error ? <ErrorState message={error} onRetry={reload} /> : <DataTable columns={columns} rows={data} emptyTitle="No categories yet" />}

      {editing && (
        <CategoryForm
          category={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            reload()
          }}
        />
      )}
      {archiving && (
        <ConfirmModal
          title={`Archive ${archiving.name}?`}
          message="Its products will be hidden from customers until the category is restored. Nothing is deleted."
          confirmLabel="Archive"
          danger
          onConfirm={archive}
          onClose={() => setArchiving(null)}
        />
      )}
    </>
  )
}

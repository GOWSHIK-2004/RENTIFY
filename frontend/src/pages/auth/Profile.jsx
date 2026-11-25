import { useState } from 'react'
import { Alert } from '../../components/Feedback'
import Button from '../../components/Button'
import Input from '../../components/Input'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { errorMessage, formatDateTime, titleCase } from '../../utils/format'

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const toast = useToast()
  const [fullName, setFullName] = useState(user.full_name)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const save = async (event) => {
    event.preventDefault()
    setError('')
    if (fullName.trim().length < 2) {
      setError('Enter your full name.')
      return
    }
    setSaving(true)
    try {
      await updateProfile(fullName.trim())
      toast.success('Profile updated.')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <h1 className="text-2xl font-bold">Your profile</h1>
      <div className="mt-6 rounded-xl border border-line bg-white p-6 shadow-sm">
        <form onSubmit={save} noValidate className="space-y-4">
          {error && <Alert>{error}</Alert>}
          <Input label="Full name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
          <Input label="Email" value={user.email} disabled hint="Your email is your login and cannot be changed here." />
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-muted">Account type</dt>
              <dd className="font-medium">{titleCase(user.role)}</dd>
            </div>
            <div>
              <dt className="text-muted">Member since</dt>
              <dd className="font-medium">{formatDateTime(user.created_at)}</dd>
            </div>
          </dl>
          <Button type="submit" loading={saving} disabled={fullName.trim() === user.full_name}>
            Save changes
          </Button>
        </form>
      </div>
      <p className="mt-4 text-xs text-muted">
        Note: for this demo your login is kept in memory only, so refreshing the page signs you out.
      </p>
    </div>
  )
}

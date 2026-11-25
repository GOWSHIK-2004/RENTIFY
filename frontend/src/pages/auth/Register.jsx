import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Alert } from '../../components/Feedback'
import Button from '../../components/Button'
import Input from '../../components/Input'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { errorMessage } from '../../utils/format'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Register() {
  const { user, register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const destination = location.state?.from || '/'

  if (user) return <Navigate to={destination} replace />

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  const validate = () => {
    const next = {}
    if (form.full_name.trim().length < 2) next.full_name = 'Enter your full name.'
    if (!EMAIL_PATTERN.test(form.email.trim())) next.email = 'Enter a valid email address.'
    if (form.password.length < 8) next.password = 'Use at least 8 characters.'
    if (form.confirm_password !== form.password) next.confirm_password = 'Passwords do not match.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const submit = async (event) => {
    event.preventDefault()
    setFormError('')
    if (!validate()) return
    setSubmitting(true)
    try {
      await register({ ...form, full_name: form.full_name.trim(), email: form.email.trim() })
      toast.success('Your account is ready. Welcome to Rentify!')
      navigate(destination, { replace: true })
    } catch (error) {
      setFormError(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-14">
      <div className="rounded-xl border border-line bg-white p-6 shadow-sm sm:p-8">
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="mt-1 text-sm text-muted">Rent More. Own Less.</p>
        <form onSubmit={submit} noValidate className="mt-6 space-y-4">
          {formError && <Alert>{formError}</Alert>}
          <Input label="Full name" autoComplete="name" value={form.full_name} onChange={update('full_name')} error={errors.full_name} />
          <Input label="Email" type="email" autoComplete="email" value={form.email} onChange={update('email')} error={errors.email} />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={update('password')}
            error={errors.password}
            hint="At least 8 characters."
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={update('confirm_password')}
            error={errors.confirm_password}
          />
          <Button type="submit" loading={submitting} className="w-full">
            Create account
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">
          Already have an account?{' '}
          <Link to="/login" state={location.state} className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}

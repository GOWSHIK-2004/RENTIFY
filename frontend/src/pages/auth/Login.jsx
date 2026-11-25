import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Alert } from '../../components/Feedback'
import Button from '../../components/Button'
import Input from '../../components/Input'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { errorMessage } from '../../utils/format'

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const { user, login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const destination = location.state?.from

  if (user) return <Navigate to={destination || (user.role === 'ADMIN' ? '/admin' : '/')} replace />

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  const validate = () => {
    const next = {}
    if (!EMAIL_PATTERN.test(form.email.trim())) next.email = 'Enter a valid email address.'
    if (!form.password) next.password = 'Enter your password.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const submit = async (event) => {
    event.preventDefault()
    setFormError('')
    if (!validate()) return
    setSubmitting(true)
    try {
      const loggedIn = await login(form.email.trim(), form.password)
      toast.success(`Welcome back, ${loggedIn.full_name.split(' ')[0]}!`)
      navigate(destination || (loggedIn.role === 'ADMIN' ? '/admin' : '/'), { replace: true })
    } catch (error) {
      setFormError(errorMessage(error))
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-14">
      <div className="rounded-xl border border-line bg-white p-6 shadow-sm sm:p-8">
        <h1 className="text-2xl font-bold">Log in</h1>
        <p className="mt-1 text-sm text-muted">Welcome back to Rentify.</p>
        {destination && (
          <div className="mt-4">
            <Alert type="info">Please log in to continue.</Alert>
          </div>
        )}
        <form onSubmit={submit} noValidate className="mt-6 space-y-4">
          {formError && <Alert>{formError}</Alert>}
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={update('email')}
            error={errors.email}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={update('password')}
            error={errors.password}
          />
          <Button type="submit" loading={submitting} className="w-full">
            Log in
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">
          New to Rentify?{' '}
          <Link to="/register" state={location.state} className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  )
}

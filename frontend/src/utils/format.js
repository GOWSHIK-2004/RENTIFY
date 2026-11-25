import { API_ORIGIN } from '../api/client'

const BUSINESS_TIMEZONE = 'Asia/Kolkata'

// Money arrives from the API as a string ("2697.00"); format it for display only.
export const formatMoney = (value) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(Number(value))

// "2026-12-01" -> "1 Dec 2026". Parsed as a plain date so the timezone cannot shift it.
export const formatDate = (isoDate) => {
  if (!isoDate) return '-'
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export const formatDateTime = (isoTimestamp) =>
  isoTimestamp
    ? new Date(isoTimestamp).toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: BUSINESS_TIMEZONE,
      })
    : '-'

// Today's date in the business timezone as YYYY-MM-DD (matches the backend's rule).
export const todayInBusinessZone = () =>
  new Intl.DateTimeFormat('en-CA', { timeZone: BUSINESS_TIMEZONE }).format(new Date())

export const addDays = (isoDate, days) => {
  const [year, month, day] = isoDate.split('-').map(Number)
  const date = new Date(Date.UTC(year, month - 1, day + days))
  return date.toISOString().slice(0, 10)
}

export const imageSrc = (imageUrl) => (imageUrl ? `${API_ORIGIN}${imageUrl}` : '/placeholder-product.svg')

// Turn any API error into one readable sentence.
export const errorMessage = (error, fallback = 'Something went wrong. Please try again.') => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0]
    const field = first.loc?.at(-1)
    return field && field !== 'body' ? `${field.replace(/_/g, ' ')}: ${first.msg}` : first.msg
  }
  if (detail?.message) return detail.message
  if (error?.code === 'ERR_NETWORK') return 'Cannot reach the server. Is the backend running?'
  return fallback
}

export const titleCase = (value) =>
  value.toLowerCase().replace(/_/g, ' ').replace(/^\w/, (char) => char.toUpperCase())

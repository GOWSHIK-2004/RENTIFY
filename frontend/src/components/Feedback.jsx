import { Loader2, SearchX, TriangleAlert } from 'lucide-react'
import Button from './Button'

export function Spinner({ className = 'h-5 w-5' }) {
  return <Loader2 className={`animate-spin text-primary ${className}`} aria-hidden="true" />
}

export function PageLoader({ label = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-24 text-muted" role="status">
      <Spinner className="h-6 w-6" />
      <span>{label}</span>
    </div>
  )
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-dashed border-line bg-white px-6 py-14 text-center">
      <SearchX className="h-10 w-10 text-muted" aria-hidden="true" />
      <h3 className="mt-3 text-base font-semibold">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center rounded-xl border border-red-200 bg-red-50 px-6 py-10 text-center" role="alert">
      <TriangleAlert className="h-8 w-8 text-red-600" aria-hidden="true" />
      <p className="mt-2 text-sm text-red-800">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}

/** Inline banner for form-level errors and notices. */
export function Alert({ type = 'error', children }) {
  const styles =
    type === 'error'
      ? 'border-red-200 bg-red-50 text-red-800'
      : type === 'warning'
        ? 'border-amber-200 bg-amber-50 text-amber-900'
        : 'border-blue-200 bg-blue-50 text-blue-900'
  return (
    <div role={type === 'error' ? 'alert' : 'status'} className={`rounded-lg border px-4 py-3 text-sm ${styles}`}>
      {children}
    </div>
  )
}

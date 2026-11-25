import { useId } from 'react'

const CONTROL =
  'block w-full rounded-lg border bg-white px-3 py-2 text-sm text-ink placeholder:text-muted/70 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:bg-slate-50 disabled:text-muted'

/** Label + control + error/hint. `as` picks the element: input (default), select or textarea. */
export default function Input({ label, error, hint, as: Element = 'input', className = '', children, ...props }) {
  const id = useId()
  const messageId = `${id}-message`
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="mb-1 block text-sm font-medium">
          {label}
        </label>
      )}
      <Element
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? messageId : undefined}
        className={`${CONTROL} ${error ? 'border-red-500' : 'border-line'}`}
        {...props}
      >
        {children}
      </Element>
      {(error || hint) && (
        <p id={messageId} className={`mt-1 text-xs ${error ? 'text-red-600' : 'text-muted'}`}>
          {error || hint}
        </p>
      )}
    </div>
  )
}

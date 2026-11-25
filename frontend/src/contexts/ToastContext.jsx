import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { CircleCheck, CircleX, X } from 'lucide-react'

const ToastContext = createContext(null)

let nextToastId = 1

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => setToasts((current) => current.filter((t) => t.id !== id)), [])

  const show = useCallback(
    (message, type = 'success') => {
      const id = nextToastId++
      setToasts((current) => [...current, { id, message, type }])
      setTimeout(() => dismiss(id), 5000)
    },
    [dismiss],
  )

  const value = useMemo(
    () => ({
      success: (message) => show(message, 'success'),
      error: (message) => show(message, 'error'),
    }),
    [show],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-[100] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2" aria-live="polite">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className="flex items-start gap-3 rounded-lg border border-line bg-white p-3 shadow-lg"
          >
            {toast.type === 'success' ? (
              <CircleCheck className="mt-0.5 h-5 w-5 shrink-0 text-green-600" />
            ) : (
              <CircleX className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
            )}
            <p className="flex-1 text-sm">{toast.message}</p>
            <button onClick={() => dismiss(toast.id)} aria-label="Dismiss" className="text-muted hover:text-ink">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(ToastContext)

import { useCallback, useEffect, useRef, useState } from 'react'
import { errorMessage } from '../utils/format'

/**
 * Runs an async loader and tracks loading / error state.
 * Re-runs when `deps` change; call `reload()` to refetch manually.
 * Responses from outdated requests are ignored (fast typing, quick navigation).
 */
export default function useFetch(loader, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const requestId = useRef(0)

  const run = useCallback(() => {
    const id = ++requestId.current
    setLoading(true)
    setError(null)
    return loader()
      .then((result) => {
        if (id === requestId.current) setData(result)
      })
      .catch((err) => {
        if (id === requestId.current) setError(errorMessage(err))
      })
      .finally(() => {
        if (id === requestId.current) setLoading(false)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
  }, [run])

  return { data, loading, error, reload: run, setData }
}

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import { setAccessToken, setUnauthorizedHandler } from '../api/client'
import { useToast } from './ToastContext'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Only the user object is React state; the token is held in api/client.js memory.
  const [user, setUser] = useState(null)
  const navigate = useNavigate()
  const toast = useToast()

  const logout = useCallback(() => {
    setAccessToken(null)
    setUser(null)
  }, [])

  // If any request comes back 401 while logged in, the token has expired.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout()
      toast.error('Your session has expired. Please log in again.')
      navigate('/login')
    })
  }, [logout, navigate, toast])

  const login = useCallback(async (email, password) => {
    const result = await authApi.login({ email, password })
    setAccessToken(result.access_token)
    setUser(result.user)
    return result.user
  }, [])

  const register = useCallback(
    async (form) => {
      await authApi.register(form)
      return login(form.email, form.password)
    },
    [login],
  )

  const updateProfile = useCallback(async (fullName) => {
    const updated = await authApi.updateProfile({ full_name: fullName })
    setUser(updated)
    return updated
  }, [])

  const value = useMemo(
    () => ({ user, isAdmin: user?.role === 'ADMIN', login, register, logout, updateProfile }),
    [user, login, register, logout, updateProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext)

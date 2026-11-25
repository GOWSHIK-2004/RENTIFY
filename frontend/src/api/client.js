import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Origin of the backend (for /uploads/... image URLs).
export const API_ORIGIN = new URL(API_BASE_URL).origin

// The access token lives only in memory for this MVP, so refreshing the
// browser logs the user out. See README "Known limitations".
let accessToken = null
let onUnauthorized = null

export const setAccessToken = (token) => {
  accessToken = token
}

export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler
}

const client = axios.create({ baseURL: API_BASE_URL })

client.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    // A 401 while we hold a token means it expired or was revoked.
    // (A failed login has no token yet, so it is not treated as expiry.)
    if (error.response?.status === 401 && accessToken && onUnauthorized) {
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

export default client

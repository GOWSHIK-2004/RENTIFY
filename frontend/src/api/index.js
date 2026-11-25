import client from './client'

const data = (request) => request.then((response) => response.data)

export const authApi = {
  register: (payload) => data(client.post('/auth/register', payload)),
  login: (payload) => data(client.post('/auth/login', payload)),
  updateProfile: (payload) => data(client.patch('/users/me', payload)),
}

export const categoryApi = {
  list: (params) => data(client.get('/categories', { params })),
  create: (payload) => data(client.post('/categories', payload)),
  update: (id, payload) => data(client.patch(`/categories/${id}`, payload)),
  archive: (id) => data(client.delete(`/categories/${id}`)),
}

export const productApi = {
  list: (params) => data(client.get('/products', { params })),
  featured: () => data(client.get('/products/featured')),
  get: (id) => data(client.get(`/products/${id}`)),
  reviews: (id) => data(client.get(`/products/${id}/reviews`)),
  // Every product including archived ones, for admin pickers (the API caps a page at 50).
  all: async () => {
    const items = []
    for (let page = 1; ; page++) {
      const result = await data(client.get('/products', { params: { include_inactive: true, page, page_size: 50 } }))
      items.push(...result.items)
      if (page >= result.pages) return items
    }
  },
  create: (payload) => data(client.post('/products', payload)),
  update: (id, payload) => data(client.patch(`/products/${id}`, payload)),
  archive: (id) => data(client.delete(`/products/${id}`)),
  uploadImage: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return data(client.post(`/admin/products/${id}/image`, form))
  },
}

export const bookingApi = {
  quote: (payload) => data(client.post('/bookings/quote', payload)),
  create: (payload) => data(client.post('/bookings', payload)),
  list: () => data(client.get('/bookings')),
  get: (id) => data(client.get(`/bookings/${id}`)),
  cancel: (id, reason) => data(client.post(`/bookings/${id}/cancel`, { reason })),
}

export const reviewApi = {
  create: (payload) => data(client.post('/reviews', payload)),
  update: (id, payload) => data(client.patch(`/reviews/${id}`, payload)),
  remove: (id) => client.delete(`/reviews/${id}`),
}

export const adminApi = {
  dashboard: () => data(client.get('/admin/dashboard')),
  customers: (params) => data(client.get('/admin/users', { params })),
  payments: (params) => data(client.get('/admin/payments', { params })),
  bookings: (params) => data(client.get('/admin/bookings', { params })),
  pickup: (id) => data(client.post(`/admin/bookings/${id}/pickup`)),
  returnBooking: (id, condition) => data(client.post(`/admin/bookings/${id}/return`, { condition })),
  cancelBooking: (id, reason) => data(client.post(`/admin/bookings/${id}/cancel`, { reason })),
  inventory: (params) => data(client.get('/admin/inventory', { params })),
  createUnit: (payload) => data(client.post('/admin/inventory', payload)),
  updateUnit: (id, payload) => data(client.patch(`/admin/inventory/${id}`, payload)),
}

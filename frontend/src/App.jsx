import { lazy } from 'react'
import { Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AdminLayout from './layouts/AdminLayout'
import CustomerLayout from './layouts/CustomerLayout'
import Login from './pages/auth/Login'
import Profile from './pages/auth/Profile'
import Register from './pages/auth/Register'
import About from './pages/customer/About'
import BookingConfirmation from './pages/customer/BookingConfirmation'
import BookingDetail from './pages/customer/BookingDetail'
import Checkout from './pages/customer/Checkout'
import Faq from './pages/customer/Faq'
import Home from './pages/customer/Home'
import MyBookings from './pages/customer/MyBookings'
import NotFound from './pages/customer/NotFound'
import ProductDetail from './pages/customer/ProductDetail'
import Products from './pages/customer/Products'

// Admin pages (and the charting library) are only downloaded when an admin opens them.
const AdminOverview = lazy(() => import('./pages/admin/Overview'))
const AdminProducts = lazy(() => import('./pages/admin/Products'))
const AdminCategories = lazy(() => import('./pages/admin/Categories'))
const AdminInventory = lazy(() => import('./pages/admin/Inventory'))
const AdminBookings = lazy(() => import('./pages/admin/Bookings'))
const AdminCustomers = lazy(() => import('./pages/admin/Customers'))
const AdminPayments = lazy(() => import('./pages/admin/Payments'))

export default function App() {
  return (
    <Routes>
      <Route element={<CustomerLayout />}>
        <Route index element={<Home />} />
        <Route path="products" element={<Products />} />
        <Route path="products/:id" element={<ProductDetail />} />
        <Route path="about" element={<About />} />
        <Route path="faq" element={<Faq />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />

        <Route element={<ProtectedRoute />}>
          <Route path="checkout" element={<Checkout />} />
          <Route path="bookings" element={<MyBookings />} />
          <Route path="bookings/:id" element={<BookingDetail />} />
          <Route path="bookings/:id/confirmation" element={<BookingConfirmation />} />
          <Route path="profile" element={<Profile />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Route>

      <Route path="admin" element={<ProtectedRoute adminOnly />}>
        <Route element={<AdminLayout />}>
          <Route index element={<AdminOverview />} />
          <Route path="products" element={<AdminProducts />} />
          <Route path="categories" element={<AdminCategories />} />
          <Route path="inventory" element={<AdminInventory />} />
          <Route path="bookings" element={<AdminBookings />} />
          <Route path="customers" element={<AdminCustomers />} />
          <Route path="payments" element={<AdminPayments />} />
        </Route>
      </Route>
    </Routes>
  )
}

import { bookingApi } from '../api'
import useFetch from './useFetch'

/**
 * Price and availability for a product and dates, always computed by the backend.
 * Pass empty dates to skip the request (for example while the form is invalid).
 */
export default function useQuote(productId, pickupDate, returnDate) {
  const enabled = Boolean(productId && pickupDate && returnDate)
  const { data, loading, error, reload } = useFetch(
    () =>
      enabled
        ? bookingApi.quote({ product_id: Number(productId), pickup_date: pickupDate, return_date: returnDate })
        : Promise.resolve(null),
    [productId, pickupDate, returnDate],
  )
  return { quote: enabled ? data : null, loading: enabled && loading, error: enabled ? error : null, reload }
}

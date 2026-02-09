import { get, post } from './client'
import type { Booking } from './types'

export async function bookSeat(tripId: number, seats_count: number, comment?: string) {
  return post<Booking>(`/api/trips/${tripId}/book/`, { seats_count, comment: comment || '' })
}

export async function cancelBooking(bookingId: number) {
  return post<{ message: string }>(`/api/bookings/${bookingId}/cancel/`)
}

export async function rejectBooking(bookingId: number, rejection_reason?: string) {
  return post<{ message: string }>(`/api/bookings/${bookingId}/reject/`, {
    rejection_reason: rejection_reason || '',
  })
}

/** Backend returns paginated { results: Booking[] }; normalize to array */
function unwrapPaginatedBookings(data: unknown): Booking[] {
  if (Array.isArray(data)) return data
  const obj = data as { results?: Booking[] }
  return Array.isArray(obj?.results) ? obj.results : []
}

export async function userBookings() {
  const data = await get<unknown>('/api/my-bookings/')
  return unwrapPaginatedBookings(data)
}

export async function tripBookings(tripId: number) {
  const data = await get<unknown>(`/api/trips/${tripId}/bookings/`)
  return unwrapPaginatedBookings(data)
}

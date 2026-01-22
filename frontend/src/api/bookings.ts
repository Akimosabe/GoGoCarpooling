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

export async function userBookings() {
  return get<Booking[]>('/api/my-bookings/')
}

export async function tripBookings(tripId: number) {
  return get<Booking[]>(`/api/trips/${tripId}/bookings/`)
}

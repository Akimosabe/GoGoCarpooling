import { get, post } from './client'
import type { Booking, BookingCreateResponse, Paginated } from './types'

export async function bookSeat(tripId: number, seats_count: number, comment?: string) {
  return post<Booking | BookingCreateResponse>(`/api/trips/${tripId}/book/`, {
    seats_count,
    comment: comment || '',
  })
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

export interface UserBookingsParams {
  page?: number
  page_size?: number
  archive?: boolean
}

/** Пагинированный список бронирований. archive=true — только архив. Сортировка по дате поездки: новые сверху. */
export async function userBookingsPage(params?: UserBookingsParams): Promise<Paginated<Booking>> {
  const p: Record<string, string> = {}
  if (params?.page != null) p.page = String(params.page)
  if (params?.page_size != null) p.page_size = String(params.page_size)
  if (params?.archive === true) p.archive = '1'
  const data = await get<Paginated<Booking>>('/api/my-bookings/', Object.keys(p).length ? p : undefined)
  return {
    count: data?.count ?? 0,
    next: data?.next ?? null,
    previous: data?.previous ?? null,
    results: Array.isArray(data?.results) ? data.results : [],
  }
}

/** Первая страница активных бронирований (для обратной совместимости) */
export async function userBookings(): Promise<Booking[]> {
  const data = await userBookingsPage({ page: 1, archive: false })
  return data.results
}

export async function tripBookings(tripId: number) {
  const data = await get<unknown>(`/api/trips/${tripId}/bookings/`)
  return unwrapPaginatedBookings(data)
}

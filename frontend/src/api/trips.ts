import { get, post, put } from './client'
import type { Trip, Paginated } from './types'

export interface TripListParams {
  origin?: string
  origin_id?: string
  destination?: string
  destination_id?: string
  date?: string
  min_seats?: number
  max_price?: number
  page?: number
  page_size?: number
}

export async function tripList(params?: TripListParams) {
  const p: Record<string, string> = {}
  if (params?.origin) p.origin = params.origin
  if (params?.origin_id) p.origin_id = params.origin_id
  if (params?.destination) p.destination = params.destination
  if (params?.destination_id) p.destination_id = params.destination_id
  if (params?.date) p.date = params.date
  if (params?.min_seats != null) p.min_seats = String(params.min_seats)
  if (params?.max_price != null) p.max_price = String(params.max_price)
  if (params?.page != null) p.page = String(params.page)
  if (params?.page_size != null) p.page_size = String(params.page_size)
  return get<Paginated<Trip>>('/api/trips/', Object.keys(p).length ? p : undefined)
}

export async function tripDetail(id: number) {
  return get<Trip>(`/api/trips/${id}/`)
}

export interface TripCreateUpdate {
  car?: number | null
  new_car?: { brand: string; model: string; year: number; color: string; license_plate?: string }
  origin: number
  destination: number
  departure_datetime: string
  price: string | number
  total_seats: number
  available_seats: number
  description?: string
  smoking_allowed?: boolean
  pets_allowed?: boolean
  luggage_size?: 'small' | 'medium' | 'large'
}

export async function createTrip(data: TripCreateUpdate) {
  const payload = { ...data, price: String(data.price) }
  return post<Trip>('/api/trips/create/', payload)
}

export async function editTrip(id: number, data: Partial<TripCreateUpdate>) {
  const payload = data.price != null ? { ...data, price: String(data.price) } : data
  return put<Trip>(`/api/trips/${id}/edit/`, payload)
}

export async function cancelTrip(id: number) {
  return post<{ message: string }>(`/api/trips/${id}/cancel/`)
}

export async function myTrips() {
  return get<Trip[]>('/api/my-trips/')
}

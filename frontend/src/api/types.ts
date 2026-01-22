export interface User {
  id: number
  email: string
  first_name: string
  phone?: string | null
  avatar?: string | null
  date_of_birth?: string | null
  trips_as_driver?: number
  trips_as_passenger?: number
  average_rating?: number
  total_ratings_count?: number
  cars?: Car[]
  is_staff?: boolean
  is_superuser?: boolean
  created_at?: string
  updated_at?: string
}

export interface Car {
  id: number
  brand: string
  model: string
  year: number
  color: string
  license_plate?: string | null
  is_active: boolean
}

export interface City {
  id: number
  name: string
  region: string
  timezone?: string
  display_name?: string
  geoname_id?: number
  country?: string
  country_code?: string
  latitude?: string | null
  longitude?: string | null
  population?: number
  is_popular?: boolean
}

export interface CitySuggestion {
  value: string
  data: {
    id: number
    city: string
    region: string
    country: string
    country_code: string
    geo_lat?: string | null
    geo_lon?: string | null
    population?: number
    geoname_id?: number
  }
}

export interface Trip {
  id: number
  driver: User
  driver_rating?: number
  car?: Car | null
  origin: City
  destination: City
  departure_datetime: string
  price: string
  total_seats: number
  available_seats: number
  description?: string | null
  smoking_allowed: boolean
  pets_allowed: boolean
  luggage_size: 'small' | 'medium' | 'large'
  status: string
  effective_status: string
  is_expired: boolean
  bookings_count?: number
  created_at?: string
  updated_at?: string
}

export interface Booking {
  id: number
  trip: Trip
  passenger: User
  seats_count: number
  status: string
  comment?: string | null
  rejection_reason?: string | null
  created_at: string
  updated_at?: string
}

export interface Notification {
  id: number
  notification_type: string
  title: string
  message: string
  trip?: number | null
  booking?: number | null
  is_read: boolean
  created_at: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

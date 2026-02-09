import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { myTrips, userBookings } from '@/api'
import type { Trip, Booking } from '@/api/types'
import { formatDate } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { TripOptionIcons } from '@/components/TripOptionIcons'
import { cn } from '@/lib/utils'

type Tab = 'driver' | 'passenger'

function isActiveTrip(t: Trip) {
  return t.effective_status === 'active' && !t.is_expired
}

export function ProfileTrips() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [trips, setTrips] = useState<Trip[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [tab, setTab] = useState<Tab>('driver')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      navigate('/auth')
      return
    }
    setLoading(true)
    Promise.all([myTrips(), userBookings()])
      .then(([t, b]) => {
        setTrips(t)
        setBookings(b)
        const hasActiveDriver = t.some(isActiveTrip)
        const hasActivePassenger = b.some((bk) => isActiveTrip(bk.trip))
        setTab(hasActiveDriver ? 'driver' : hasActivePassenger ? 'passenger' : 'driver')
      })
      .finally(() => setLoading(false))
  }, [user, navigate])

  if (!user) return null
  if (loading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center text-slate-500">
        Загрузка…
      </div>
    )
  }

  const activeTrips = trips.filter(isActiveTrip)
  const archiveTrips = trips.filter((t) => !isActiveTrip(t))
  const activeBookings = bookings.filter((b) => isActiveTrip(b.trip))
  const archiveBookings = bookings.filter((b) => !isActiveTrip(b.trip))

  const renderTripCard = (t: Trip) => {
    const price = typeof t.price === 'string' ? parseFloat(t.price) : t.price
    return (
      <Link key={t.id} to={`/trips/${t.id}`}>
        <Card className="transition hover:shadow-md">
          <div className="flex flex-wrap justify-between gap-2">
            <span className="font-medium text-slate-800">
              {t.origin.display_name ?? t.origin.name} →{' '}
              {t.destination.display_name ?? t.destination.name}
            </span>
            <span className="text-base font-semibold text-slate-800">
              {formatDate(t.departure_datetime)}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            {t.available_seats} / {t.total_seats} мест · {price.toLocaleString('ru-RU')} ₽
          </p>
          <TripOptionIcons trip={t} className="mt-2" />
        </Card>
      </Link>
    )
  }

  const renderBookingCard = (b: Booking) => {
    const price = typeof b.trip.price === 'string' ? parseFloat(b.trip.price) : b.trip.price
    return (
      <Link key={b.id} to={`/trips/${b.trip.id}`}>
        <Card className="transition hover:shadow-md">
          <div className="flex flex-wrap justify-between gap-2">
            <span className="font-medium text-slate-800">
              {b.trip.origin.display_name ?? b.trip.origin.name} →{' '}
              {b.trip.destination.display_name ?? b.trip.destination.name}
            </span>
            <span className="text-base font-semibold text-slate-800">
              {formatDate(b.trip.departure_datetime)}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            Забронировано мест: {b.seats_count} · {price.toLocaleString('ru-RU')} ₽
          </p>
          <TripOptionIcons trip={b.trip} className="mt-2" />
        </Card>
      </Link>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Мои поездки</h1>
        <Link to="/profile" className="text-sm font-medium text-green-600 hover:underline">
          ← В профиль
        </Link>
      </div>

      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={() => setTab('driver')}
          className={cn(
            'rounded-xl px-4 py-2 text-sm font-medium',
            tab === 'driver'
              ? 'bg-green-500 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          )}
        >
          Водитель
        </button>
        <button
          type="button"
          onClick={() => setTab('passenger')}
          className={cn(
            'rounded-xl px-4 py-2 text-sm font-medium',
            tab === 'passenger'
              ? 'bg-green-500 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          )}
        >
          Пассажир
        </button>
      </div>

      {tab === 'driver' && (
        <div className="space-y-6">
          {activeTrips.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Активные
              </h2>
              <div className="space-y-3">
                {activeTrips.map(renderTripCard)}
              </div>
            </div>
          )}
          {archiveTrips.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Архив
              </h2>
              <div className="space-y-3">
                {archiveTrips.map(renderTripCard)}
              </div>
            </div>
          )}
          {trips.length === 0 && (
            <p className="py-8 text-center text-slate-500">Нет поездок как водитель</p>
          )}
        </div>
      )}

      {tab === 'passenger' && (
        <div className="space-y-6">
          {activeBookings.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Активные
              </h2>
              <div className="space-y-3">
                {activeBookings.map(renderBookingCard)}
              </div>
            </div>
          )}
          {archiveBookings.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Архив
              </h2>
              <div className="space-y-3">
                {archiveBookings.map(renderBookingCard)}
              </div>
            </div>
          )}
          {bookings.length === 0 && (
            <p className="py-8 text-center text-slate-500">Нет поездок как пассажир</p>
          )}
        </div>
      )}
    </div>
  )
}

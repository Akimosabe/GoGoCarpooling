import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Archive, ChevronLeft, ChevronRight } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { myTripsPage, userBookingsPage } from '@/api'
import type { Trip, Booking } from '@/api/types'
import { formatTripDeparture } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { TripOptionIcons } from '@/components/TripOptionIcons'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 10

type Tab = 'driver' | 'passenger'

export function ProfileTrips() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('driver')

  const [activeTrips, setActiveTrips] = useState<Trip[]>([])
  const [activeCount, setActiveCount] = useState(0)
  const [activePage, setActivePage] = useState(1)
  const [activeLoading, setActiveLoading] = useState(false)

  const [activeBookings, setActiveBookings] = useState<Booking[]>([])
  const [activeBookingsCount, setActiveBookingsCount] = useState(0)
  const [activeBookingsPage, setActiveBookingsPage] = useState(1)
  const [activeBookingsLoading, setActiveBookingsLoading] = useState(false)

  const loadDriverActive = useCallback(async (page: number) => {
    setActiveLoading(true)
    try {
      const data = await myTripsPage({ archive: false, page, page_size: PAGE_SIZE })
      setActiveTrips(data.results)
      setActiveCount(data.count)
    } finally {
      setActiveLoading(false)
    }
  }, [])

  const loadPassengerActive = useCallback(async (page: number) => {
    setActiveBookingsLoading(true)
    try {
      const data = await userBookingsPage({ archive: false, page, page_size: PAGE_SIZE })
      setActiveBookings(data.results)
      setActiveBookingsCount(data.count)
    } finally {
      setActiveBookingsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      navigate('/auth')
      return
    }
    if (tab === 'driver') {
      loadDriverActive(activePage)
    } else {
      loadPassengerActive(activeBookingsPage)
    }
  }, [user, authLoading, navigate, tab, activePage, activeBookingsPage, loadDriverActive, loadPassengerActive])

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
              {formatTripDeparture(t.departure_datetime, t.departure_datetime_display)}
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
              {formatTripDeparture(b.trip.departure_datetime, b.trip.departure_datetime_display)}
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

  function Pagination({
    page,
    count,
    pageSize,
    onPageChange,
    loading,
  }: {
    page: number
    count: number
    pageSize: number
    onPageChange: (p: number) => void
    loading: boolean
  }) {
    const totalPages = Math.max(1, Math.ceil(count / pageSize))
    const hasPrev = page > 1
    const hasNext = page < totalPages
    return (
      <div className="mt-3 flex items-center justify-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={!hasPrev || loading}
          onClick={() => onPageChange(page - 1)}
          className="gap-1"
        >
          <ChevronLeft className="h-4 w-4" />
          Назад
        </Button>
        <span className="text-sm text-slate-600">
          {count === 0 ? '0' : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, count)} из {count}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={!hasNext || loading}
          onClick={() => onPageChange(page + 1)}
          className="gap-1"
        >
          Вперёд
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  if (authLoading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center text-slate-500">
        Загрузка…
      </div>
    )
  }
  if (!user) return null

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
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Активные
          </h2>
          {activeLoading ? (
            <p className="py-6 text-center text-slate-500">Загрузка…</p>
          ) : activeTrips.length > 0 ? (
            <>
              <div className="space-y-3">
                {activeTrips.map(renderTripCard)}
              </div>
              <Pagination
                page={activePage}
                count={activeCount}
                pageSize={PAGE_SIZE}
                onPageChange={setActivePage}
                loading={activeLoading}
              />
            </>
          ) : (
            <p className="py-6 text-center text-slate-500">Нет активных поездок</p>
          )}
        </section>
      )}

      {tab === 'passenger' && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Активные
          </h2>
          {activeBookingsLoading ? (
            <p className="py-6 text-center text-slate-500">Загрузка…</p>
          ) : activeBookings.length > 0 ? (
            <>
              <div className="space-y-3">
                {activeBookings.map(renderBookingCard)}
              </div>
              <Pagination
                page={activeBookingsPage}
                count={activeBookingsCount}
                pageSize={PAGE_SIZE}
                onPageChange={setActiveBookingsPage}
                loading={activeBookingsLoading}
              />
            </>
          ) : (
            <p className="py-6 text-center text-slate-500">Нет активных поездок</p>
          )}
        </section>
      )}

      <div className="mt-10 border-t border-slate-200 pt-8">
        <Link
          to="/profile/trips/archive"
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-left transition hover:bg-slate-100 hover:border-slate-300"
        >
          <Archive className="h-5 w-5 shrink-0 text-slate-500" aria-hidden />
          <span className="font-medium text-slate-700">Архив поездок</span>
          <span className="ml-auto text-sm text-slate-500">Открыть →</span>
        </Link>
      </div>
    </div>
  )
}

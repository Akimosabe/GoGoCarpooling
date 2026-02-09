import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Archive, ChevronLeft, ChevronRight } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { myTripsPage, userBookingsPage } from '@/api'
import type { Trip, Booking } from '@/api/types'
import { formatDate } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { TripOptionIcons } from '@/components/TripOptionIcons'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 10

type Tab = 'driver' | 'passenger'

export function ProfileArchive() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('driver')

  const [archiveTrips, setArchiveTrips] = useState<Trip[]>([])
  const [archiveCount, setArchiveCount] = useState(0)
  const [archivePage, setArchivePage] = useState(1)
  const [archiveLoading, setArchiveLoading] = useState(false)

  const [archiveBookings, setArchiveBookings] = useState<Booking[]>([])
  const [archiveBookingsCount, setArchiveBookingsCount] = useState(0)
  const [archiveBookingsPage, setArchiveBookingsPage] = useState(1)
  const [archiveBookingsLoading, setArchiveBookingsLoading] = useState(false)

  const loadDriverArchive = useCallback(async (page: number) => {
    setArchiveLoading(true)
    try {
      const data = await myTripsPage({ archive: true, page, page_size: PAGE_SIZE })
      setArchiveTrips(data.results)
      setArchiveCount(data.count)
    } finally {
      setArchiveLoading(false)
    }
  }, [])

  const loadPassengerArchive = useCallback(async (page: number) => {
    setArchiveBookingsLoading(true)
    try {
      const data = await userBookingsPage({ archive: true, page, page_size: PAGE_SIZE })
      setArchiveBookings(data.results)
      setArchiveBookingsCount(data.count)
    } finally {
      setArchiveBookingsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!user) {
      navigate('/auth')
      return
    }
    if (tab === 'driver') {
      loadDriverArchive(archivePage)
    } else {
      loadPassengerArchive(archiveBookingsPage)
    }
  }, [user, navigate, tab, archivePage, archiveBookingsPage, loadDriverArchive, loadPassengerArchive])

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

  if (!user) return null

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
          <Archive className="h-7 w-7 text-slate-500" aria-hidden />
          Архив поездок
        </h1>
        <Link to="/profile/trips" className="text-sm font-medium text-green-600 hover:underline">
          ← Все поездки
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

      <p className="mb-4 text-sm text-slate-500">
        Отменённые и завершённые поездки. Сортировка: новые сверху.
      </p>

      {tab === 'driver' && (
        <section>
          {archiveLoading ? (
            <p className="py-6 text-center text-slate-500">Загрузка…</p>
          ) : archiveTrips.length > 0 ? (
            <>
              <div className="space-y-3">
                {archiveTrips.map(renderTripCard)}
              </div>
              <Pagination
                page={archivePage}
                count={archiveCount}
                pageSize={PAGE_SIZE}
                onPageChange={setArchivePage}
                loading={archiveLoading}
              />
            </>
          ) : (
            <p className="py-8 text-center text-slate-500">В архиве водителя пока нет поездок</p>
          )}
        </section>
      )}

      {tab === 'passenger' && (
        <section>
          {archiveBookingsLoading ? (
            <p className="py-6 text-center text-slate-500">Загрузка…</p>
          ) : archiveBookings.length > 0 ? (
            <>
              <div className="space-y-3">
                {archiveBookings.map(renderBookingCard)}
              </div>
              <Pagination
                page={archiveBookingsPage}
                count={archiveBookingsCount}
                pageSize={PAGE_SIZE}
                onPageChange={setArchiveBookingsPage}
                loading={archiveBookingsLoading}
              />
            </>
          ) : (
            <p className="py-8 text-center text-slate-500">В архиве пассажира пока нет поездок</p>
          )}
        </section>
      )}
    </div>
  )
}

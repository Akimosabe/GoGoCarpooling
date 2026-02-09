import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, MapPin } from 'lucide-react'
import { tripList } from '@/api/trips'
import type { Trip, Paginated } from '@/api/types'
import { formatTripDeparture, getAvatarUrl } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { TripOptionIcons } from '@/components/TripOptionIcons'

function TripCard({ t }: { t: Trip }) {
  const price = typeof t.price === 'string' ? parseFloat(t.price) : t.price
  return (
    <Link to={`/trips/${t.id}`}>
      <Card className="transition hover:shadow-md">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <div className="flex items-center gap-2 text-slate-600">
              <MapPin className="h-4 w-4" />
              <span>
                {t.origin.display_name ?? `${t.origin.name}, ${t.origin.region}`} →{' '}
                {t.destination.display_name ?? `${t.destination.name}, ${t.destination.region}`}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {formatTripDeparture(t.departure_datetime, t.departure_datetime_display)}
            </p>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-green-600">
              {price.toLocaleString('ru-RU')} ₽
            </div>
            <div className="text-sm text-slate-500">
              {t.available_seats} из {t.total_seats} мест
            </div>
          </div>
        </div>
        <TripOptionIcons trip={t} className="mt-2" />
        <div className="mt-3 flex items-center gap-2 border-t border-slate-100 pt-3">
          {getAvatarUrl(t.driver.avatar) ? (
            <img
              src={getAvatarUrl(t.driver.avatar)!}
              alt=""
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-sm font-medium text-slate-600">
              {(t.driver.first_name || '?')[0]}
            </div>
          )}
          <span className="font-medium text-slate-800">
            {t.driver.first_name || t.driver.email}
          </span>
          {typeof t.driver_rating === 'number' && t.driver_rating > 0 && (
            <span className="text-amber-500">★ {t.driver_rating}</span>
          )}
        </div>
      </Card>
    </Link>
  )
}

export function SearchResults() {
  const [params, setSearchParams] = useSearchParams()
  const [data, setData] = useState<Paginated<Trip> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const page = parseInt(params.get('page') ?? '1', 10)
  const origin = params.get('origin') ?? ''
  const originId = params.get('origin_id') ?? ''
  const destination = params.get('destination') ?? ''
  const destinationId = params.get('destination_id') ?? ''
  const date = params.get('date') ?? ''

  useEffect(() => {
    setLoading(true)
    setError('')
    const q: Record<string, string> = { page: String(page) }
    if (originId) q.origin_id = originId
    else if (origin) q.origin = origin
    if (destinationId) q.destination_id = destinationId
    else if (destination) q.destination = destination
    if (date) q.date = date

    tripList(q as unknown as Parameters<typeof tripList>[0])
      .then((r) => {
        setData(r)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [page, origin, originId, destination, destinationId, date])

  const pageSize = 20
  const totalPages = data ? Math.ceil(data.count / pageSize) || 1 : 1
  const hasNext = !!data?.next
  const hasPrev = !!data?.previous

  const go = (p: number) => {
    const next = new URLSearchParams(params)
    next.set('page', String(p))
    setSearchParams(next)
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Результаты поиска</h1>
      {loading && (
        <div className="py-12 text-center text-slate-500">Загрузка…</div>
      )}
      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-red-700">{error}</div>
      )}
      {!loading && !error && data && (
        <>
          {data.results.length === 0 ? (
            <p className="rounded-xl bg-slate-100 py-8 text-center text-slate-600">
              Поездок не найдено. Измените параметры поиска.
            </p>
          ) : (
            <div className="space-y-4">
              {data.results.map((t) => (
                <TripCard key={t.id} t={t} />
              ))}
            </div>
          )}
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!hasPrev}
                onClick={() => go(page - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
                Назад
              </Button>
              <span className="text-sm text-slate-600">
                Страница {page} из {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={!hasNext}
                onClick={() => go(page + 1)}
              >
                Вперёд
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Baby, ChevronLeft, ChevronRight, Cigarette, Dog, MapPin, Package, Search, Users2 } from 'lucide-react'
import { tripList } from '@/api/trips'
import type { Trip, Paginated } from '@/api/types'
import { formatTripDeparture, getAvatarUrl, getTodayISO, getSearchMaxDateISO } from '@/lib/utils'
import { loadLastSearch, saveLastSearch } from '@/lib/lastSearch'
import type { LastSearch } from '@/lib/lastSearch'
import { CityAutocomplete } from '@/components/CityAutocomplete'
import { DatePicker } from '@/components/DatePicker'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { TripOptionIcons } from '@/components/TripOptionIcons'
import { cn } from '@/lib/utils'

const OPTION_FILTERS = [
  { key: 'two_rear_seats', Icon: Users2, title: '2 места сзади' },
  { key: 'smoking_allowed', Icon: Cigarette, title: 'Можно курить' },
  { key: 'pets_allowed', Icon: Dog, title: 'С животными' },
  { key: 'child_seat_available', Icon: Baby, title: 'Детское кресло' },
  { key: 'parcel_allowed', Icon: Package, title: 'Посылка' },
] as const

function TripCard({ t }: { t: Trip }) {
  const price = typeof t.price === 'string' ? parseFloat(t.price) : t.price
  return (
    <Link to={`/trips/${t.id}`}>
      <Card className="transition hover:shadow-md">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-slate-600">
              <MapPin className="h-4 w-4 shrink-0" />
              <span className="truncate">
                {t.origin.display_name ?? `${t.origin.name}, ${t.origin.region}`} →{' '}
                {t.destination.display_name ?? `${t.destination.name}, ${t.destination.region}`}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {formatTripDeparture(t.departure_datetime, t.departure_datetime_display)}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <div className="text-lg font-semibold text-green-600">
              {price.toLocaleString('ru-RU')} ₽
            </div>
            <div className="text-sm text-slate-500">
              {t.available_seats} из {t.total_seats} мест
            </div>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3">
          <div className="flex items-center gap-2">
            {getAvatarUrl(t.driver.avatar) ? (
              <img
                src={getAvatarUrl(t.driver.avatar)!}
                alt=""
                className="h-8 w-8 shrink-0 rounded-full object-cover"
              />
            ) : (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-sm font-medium text-slate-600">
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
          <TripOptionIcons trip={t} className="shrink-0" iconClassName="h-4 w-4 text-slate-500" />
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
  const [lastSearch, setLastSearch] = useState<LastSearch | null>(null)

  const page = parseInt(params.get('page') ?? '1', 10)
  const originParam = params.get('origin') ?? ''
  const originIdParam = params.get('origin_id') ?? ''
  const destinationParam = params.get('destination') ?? ''
  const destinationIdParam = params.get('destination_id') ?? ''
  const dateParam = params.get('date') ?? ''
  const optionFilter = (key: (typeof OPTION_FILTERS)[number]['key']) =>
    params.get(key) === '1' || params.get(key) === 'true'

  const [origin, setOrigin] = useState(originParam)
  const [destination, setDestination] = useState(destinationParam)
  const [date, setDate] = useState(dateParam || getTodayISO())
  const [originId, setOriginId] = useState<number | null>(
    originIdParam ? parseInt(originIdParam, 10) : null
  )
  const [destId, setDestId] = useState<number | null>(
    destinationIdParam ? parseInt(destinationIdParam, 10) : null
  )

  useEffect(() => {
    setLastSearch(loadLastSearch())
  }, [])

  useEffect(() => {
    setOrigin(originParam)
    setDestination(destinationParam)
    setDate(dateParam || getTodayISO())
    setOriginId(originIdParam ? parseInt(originIdParam, 10) : null)
    setDestId(destinationIdParam ? parseInt(destinationIdParam, 10) : null)
  }, [originParam, originIdParam, destinationParam, destinationIdParam, dateParam])

  const handleSearch = useCallback(() => {
    if (origin || destination || date) {
      saveLastSearch(origin, originId, destination, destId)
      setLastSearch(loadLastSearch())
    }
    const next = new URLSearchParams()
    if (originId != null && originId !== 0) next.set('origin_id', String(originId))
    if (origin) next.set('origin', origin)
    if (destId != null && destId !== 0) next.set('destination_id', String(destId))
    if (destination) next.set('destination', destination)
    if (date) next.set('date', date)
    next.set('page', '1')
    setSearchParams(next)
  }, [origin, destination, date, originId, destId, setSearchParams])

  const setOptionFilter = useCallback(
    (key: (typeof OPTION_FILTERS)[number]['key'], enabled: boolean) => {
      const next = new URLSearchParams(params)
      if (enabled) next.set(key, '1')
      else next.delete(key)
      next.set('page', '1')
      setSearchParams(next)
    },
    [params, setSearchParams]
  )

  useEffect(() => {
    setLoading(true)
    setError('')
    const q: Record<string, string | number> = { page }
    if (originIdParam) q.origin_id = originIdParam
    else if (originParam) q.origin = originParam
    if (destinationIdParam) q.destination_id = destinationIdParam
    else if (destinationParam) q.destination = destinationParam
    if (dateParam) q.date = dateParam
    if (optionFilter('smoking_allowed')) q.smoking_allowed = true
    if (optionFilter('pets_allowed')) q.pets_allowed = true
    if (optionFilter('child_seat_available')) q.child_seat_available = true
    if (optionFilter('two_rear_seats')) q.two_rear_seats = true
    if (optionFilter('parcel_allowed')) q.parcel_allowed = true

    tripList(q as Parameters<typeof tripList>[0])
      .then((r) => {
        setData(r)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [
    page,
    originParam,
    originIdParam,
    destinationParam,
    destinationIdParam,
    dateParam,
    params.get('smoking_allowed'),
    params.get('pets_allowed'),
    params.get('child_seat_available'),
    params.get('two_rear_seats'),
    params.get('parcel_allowed'),
  ])

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
      <div className="mb-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2">
          <CityAutocomplete
            value={origin}
            onChange={setOrigin}
            onSelect={(o) => setOriginId(o.id)}
            placeholder="Откуда"
            suggestedOption={
              lastSearch?.origin
                ? { id: lastSearch.originId ?? 0, value: lastSearch.origin }
                : undefined
            }
          />
          <CityAutocomplete
            value={destination}
            onChange={setDestination}
            onSelect={(o) => setDestId(o.id)}
            placeholder="Куда"
            suggestedOption={
              lastSearch?.destination
                ? { id: lastSearch.destId ?? 0, value: lastSearch.destination }
                : undefined
            }
          />
        </div>
        <div className="mt-4 flex flex-col gap-4 sm:flex-row">
          <DatePicker
            value={date}
            onChange={setDate}
            min={getTodayISO()}
            max={getSearchMaxDateISO()}
            placeholder="Дата"
            className="flex-1"
          />
          <Button
            variant="primary"
            size="lg"
            className="gap-2"
            onClick={handleSearch}
          >
            <Search className="h-5 w-5" />
            Найти поездки
          </Button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-slate-900">Результаты поиска</h1>
        <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Фильтр по опциям">
          {OPTION_FILTERS.map(({ key, Icon, title }) => (
            <button
              key={key}
              type="button"
              title={title}
              onClick={() => setOptionFilter(key, !optionFilter(key))}
              className={cn(
                'rounded-lg p-2 transition',
                optionFilter(key)
                  ? 'bg-green-100 text-green-700 ring-1 ring-green-300'
                  : 'bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700'
              )}
            >
              <Icon className="h-5 w-5" />
            </button>
          ))}
        </div>
      </div>

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

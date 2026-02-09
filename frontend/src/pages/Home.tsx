import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { CityAutocomplete } from '@/components/CityAutocomplete'
import { DatePicker } from '@/components/DatePicker'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { loadLastSearch, saveLastSearch } from '@/lib/lastSearch'
import { cn, getTodayISO, getSearchMaxDateISO } from '@/lib/utils'
import { HERO_BG_URL } from '@/constants'

export function Home() {
  const navigate = useNavigate()
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [originId, setOriginId] = useState<number | null>(null)
  const [destId, setDestId] = useState<number | null>(null)
  const [date, setDate] = useState(getTodayISO())
  const [lastSearch, setLastSearch] = useState<LastSearch | null>(null)

  useEffect(() => {
    setLastSearch(loadLastSearch())
  }, [])

  const runSearch = useCallback(
    (o: string, d: string, dt: string, oId: number | null, dId: number | null) => {
      const params = new URLSearchParams()
      if (oId != null && oId !== 0) params.set('origin_id', String(oId))
      if (o) params.set('origin', o)
      if (dId != null && dId !== 0) params.set('destination_id', String(dId))
      if (d) params.set('destination', d)
      if (dt) params.set('date', dt)
      navigate(`/search?${params.toString()}`)
    },
    [navigate]
  )

  const handleSearch = () => {
    if (origin || destination || date) {
      saveLastSearch(origin, originId, destination, destId)
      setLastSearch(loadLastSearch())
    }
    runSearch(origin, destination, date, originId, destId)
  }

  return (
    <div
      className={cn('hero-bg relative min-h-[calc(100vh-57px)]')}
      style={{
        backgroundColor: '#1e2d3a',
        backgroundImage: `radial-gradient(ellipse 85% 45% at 50% -8%, rgba(34,197,94,0.12), transparent 50%), linear-gradient(180deg, rgba(15,23,42,0.35) 0%, rgba(22,101,52,0.42) 100%), url(${HERO_BG_URL})`,
        backgroundSize: 'cover',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
      }}
    >
      <div className="relative mx-auto flex max-w-2xl flex-col items-center justify-center px-4 py-20 text-center">
        <h1 className="mb-2 text-4xl font-bold tracking-tight text-white drop-shadow md:text-5xl">
          GoGo – совместные поездки
        </h1>
        <p className="mb-10 text-lg font-medium text-green-200 drop-shadow-sm">
          Едем вместе – проще и выгоднее
        </p>

        <div className="w-full max-w-xl rounded-2xl border border-slate-200/80 bg-white/95 p-6 shadow-xl backdrop-blur">
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
      </div>
    </div>
  )
}

import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { CityAutocomplete } from '@/components/CityAutocomplete'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'
import { HERO_BG_URL } from '@/constants'

const RECENT_SEARCHES_KEY = 'gogo_recent_searches'
const RECENT_SEARCHES_MAX = 5

export interface RecentSearch {
  origin: string
  destination: string
  date: string
  originId: number | null
  destId: number | null
}

function loadRecentSearches(): RecentSearch[] {
  try {
    const raw = localStorage.getItem(RECENT_SEARCHES_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as RecentSearch[]
    return Array.isArray(parsed) ? parsed.slice(0, RECENT_SEARCHES_MAX) : []
  } catch {
    return []
  }
}

function saveRecentSearch(item: RecentSearch) {
  const list = loadRecentSearches()
  const filtered = list.filter(
    (s) => s.origin !== item.origin || s.destination !== item.destination || s.date !== item.date
  )
  const next = [item, ...filtered].slice(0, RECENT_SEARCHES_MAX)
  localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(next))
}

export function Home() {
  const navigate = useNavigate()
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [originId, setOriginId] = useState<number | null>(null)
  const [destId, setDestId] = useState<number | null>(null)
  const [date, setDate] = useState('')
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([])

  useEffect(() => {
    setRecentSearches(loadRecentSearches())
  }, [])

  const runSearch = useCallback(
    (o: string, d: string, dt: string, oId: number | null, dId: number | null) => {
      const params = new URLSearchParams()
      if (oId) params.set('origin_id', String(oId))
      else if (o) params.set('origin', o)
      if (dId) params.set('destination_id', String(dId))
      else if (d) params.set('destination', d)
      if (dt) params.set('date', dt)
      navigate(`/search?${params.toString()}`)
    },
    [navigate]
  )

  const handleSearch = () => {
    if (origin || destination || date) {
      saveRecentSearch({
        origin,
        destination,
        date,
        originId,
        destId,
      })
      setRecentSearches(loadRecentSearches())
    }
    runSearch(origin, destination, date, originId, destId)
  }

  const handleRecentClick = (s: RecentSearch) => {
    setOrigin(s.origin)
    setDestination(s.destination)
    setDate(s.date)
    setOriginId(s.originId)
    setDestId(s.destId)
    runSearch(s.origin, s.destination, s.date, s.originId, s.destId)
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
            />
            <CityAutocomplete
              value={destination}
              onChange={setDestination}
              onSelect={(o) => setDestId(o.id)}
              placeholder="Куда"
            />
          </div>
          <div className="mt-4 flex flex-col gap-4 sm:flex-row">
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
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
          {recentSearches.length > 0 && (
            <div className="mt-4 border-t border-slate-200/80 pt-4">
              <p className="mb-2 text-left text-sm font-medium text-slate-600">
                Предыдущие поиски
              </p>
              <div className="flex flex-wrap gap-2">
                {recentSearches.map((s, i) => (
                  <button
                    key={`${s.origin}-${s.destination}-${s.date}-${i}`}
                    type="button"
                    onClick={() => handleRecentClick(s)}
                    className="rounded-lg border border-slate-200 bg-white/80 px-3 py-1.5 text-left text-sm text-slate-700 shadow-sm transition hover:bg-white hover:shadow"
                  >
                    {[s.origin || '…', s.destination || '…'].join(' → ')}
                    {s.date ? `, ${s.date}` : ''}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

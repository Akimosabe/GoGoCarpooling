import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { CityAutocomplete } from '@/components/CityAutocomplete'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'

export function Home() {
  const navigate = useNavigate()
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [originId, setOriginId] = useState<number | null>(null)
  const [destId, setDestId] = useState<number | null>(null)
  const [date, setDate] = useState('')

  const handleSearch = () => {
    const params = new URLSearchParams()
    if (originId) params.set('origin_id', String(originId))
    else if (origin) params.set('origin', origin)
    if (destId) params.set('destination_id', String(destId))
    else if (destination) params.set('destination', destination)
    if (date) params.set('date', date)
    navigate(`/search?${params.toString()}`)
  }

  return (
    <div
      className={cn(
        'relative min-h-[calc(100vh-57px)] bg-cover bg-center bg-no-repeat'
      )}
      style={{
        backgroundImage: `linear-gradient(rgba(15,23,42,0.4), rgba(15,23,42,0.5)), url(https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=1920)`,
      }}
    >
      <div className="relative mx-auto flex max-w-2xl flex-col items-center justify-center px-4 py-20 text-center">
        <h1 className="mb-2 text-4xl font-bold tracking-tight text-white drop-shadow md:text-5xl">
          GoGo — карпулинг
        </h1>
        <p className="mb-10 text-lg text-slate-200">
          Находите попутчиков или делите дорогу
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
        </div>
      </div>
    </div>
  )
}

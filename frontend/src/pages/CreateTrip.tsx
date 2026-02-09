import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { createTrip, carList } from '@/api'
import type { Car as CarType, Trip } from '@/api/types'
import { Baby, Cigarette, Dog, Package, Users2 } from 'lucide-react'
import { CityAutocomplete } from '@/components/CityAutocomplete'
import { DatePicker } from '@/components/DatePicker'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { loadLastSearch, saveLastSearch } from '@/lib/lastSearch'
import { getTodayISO, getSearchMaxDateISO } from '@/lib/utils'

export function CreateTrip() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const copyFromTrip = (location.state as { copyFromTrip?: Trip } | null)?.copyFromTrip
  const [cars, setCars] = useState<CarType[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [useNewCar, setUseNewCar] = useState(true)
  const [carId, setCarId] = useState<number | null>(null)
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [originId, setOriginId] = useState<number | null>(null)
  const [destId, setDestId] = useState<number | null>(null)
  const [lastSearch, setLastSearch] = useState(loadLastSearch())
  const [departureDate, setDepartureDate] = useState(getTodayISO())
  const [departureTime, setDepartureTime] = useState('')
  const [price, setPrice] = useState('')
  const [totalSeats, setTotalSeats] = useState(3)
  const [availableSeats, setAvailableSeats] = useState(3)
  const [description, setDescription] = useState('')
  const [smokingAllowed, setSmokingAllowed] = useState(false)
  const [petsAllowed, setPetsAllowed] = useState(false)
  const [childSeatAvailable, setChildSeatAvailable] = useState(false)
  const [twoRearSeats, setTwoRearSeats] = useState(false)
  const [parcelAllowed, setParcelAllowed] = useState(false)
  const [newCar, setNewCar] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    color: '',
    license_plate: '',
  })

  useEffect(() => {
    setLastSearch(loadLastSearch())
  }, [])

  useEffect(() => {
    if (!user) {
      navigate('/auth')
      return
    }
    carList()
      .then((list) => {
        setCars(list)
        if (list.length > 0) {
          setUseNewCar(false)
          setCarId(list[0].id)
        }
        if (copyFromTrip) {
          const t = copyFromTrip
          const originDisplay = t.origin.display_name ?? `${t.origin.name}, ${t.origin.region}`
          const destDisplay = t.destination.display_name ?? `${t.destination.name}, ${t.destination.region}`
          setOrigin(originDisplay)
          setOriginId(t.origin.id)
          setDestination(destDisplay)
          setDestId(t.destination.id)
          setPrice(typeof t.price === 'string' ? t.price : String(t.price))
          setTotalSeats(t.total_seats)
          setAvailableSeats(t.available_seats)
          setDescription(t.description ?? '')
          setSmokingAllowed(t.smoking_allowed)
          setPetsAllowed(t.pets_allowed)
          setChildSeatAvailable(t.child_seat_available)
          setTwoRearSeats(t.two_rear_seats)
          setParcelAllowed(t.parcel_allowed)
          if (t.car?.id && list.some((c) => c.id === t.car!.id)) {
            setCarId(t.car.id)
            setUseNewCar(false)
          }
        }
      })
      .catch(() => setCars([]))
      .finally(() => setLoading(false))
  }, [user, navigate, copyFromTrip])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!originId || !destId) {
      setError('Укажите города отправления и назначения')
      return
    }
    const dt = `${departureDate}T${departureTime}:00`
    const departureMs = new Date(dt).getTime()
    if (Number.isNaN(departureMs) || departureMs <= Date.now()) {
      setError('Дата и время отправления должны быть в будущем')
      return
    }
    setSubmitting(true)
    try {
      const payload: Parameters<typeof createTrip>[0] = {
        origin: originId,
        destination: destId,
        departure_datetime: dt,
        price: price.replace(/\s/g, ''),
        total_seats: totalSeats,
        available_seats: availableSeats,
        description: description || undefined,
        smoking_allowed: smokingAllowed,
        pets_allowed: petsAllowed,
        child_seat_available: childSeatAvailable,
        two_rear_seats: twoRearSeats,
        parcel_allowed: parcelAllowed,
        luggage_size: 'medium',
      }
      if (useNewCar) {
        payload.new_car = {
          brand: newCar.brand,
          model: newCar.model,
          year: newCar.year,
          color: newCar.color,
          license_plate: newCar.license_plate || undefined,
        }
      } else if (carId) {
        payload.car = carId
      } else {
        setError('Выберите автомобиль или заполните данные нового')
        setSubmitting(false)
        return
      }
      const trip = await createTrip(payload)
      saveLastSearch(origin, originId, destination, destId)
      navigate(`/trips/${trip.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка создания поездки')
    } finally {
      setSubmitting(false)
    }
  }

  if (!user) return null
  if (loading) {
    return (
      <div className="mx-auto max-w-xl px-4 py-12 text-center text-slate-500">
        Загрузка…
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Создать поездку</h1>
      {error && (
        <div className="mb-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</div>
      )}
      <form onSubmit={handleSubmit}>
        <Card className="mb-6">
          <h2 className="mb-4 font-semibold text-slate-800">Маршрут</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <CityAutocomplete
              value={origin}
              onChange={setOrigin}
              onSelect={(o) => setOriginId(o.id)}
              placeholder="Откуда"
              suggestedOption={
                lastSearch?.origin && lastSearch.originId != null
                  ? { id: lastSearch.originId, value: lastSearch.origin }
                  : undefined
              }
            />
            <CityAutocomplete
              value={destination}
              onChange={setDestination}
              onSelect={(o) => setDestId(o.id)}
              placeholder="Куда"
              suggestedOption={
                lastSearch?.destination && lastSearch.destId != null
                  ? { id: lastSearch.destId, value: lastSearch.destination }
                  : undefined
              }
            />
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-slate-600">Дата</label>
              <DatePicker
                value={departureDate}
                onChange={setDepartureDate}
                min={getTodayISO()}
                max={getSearchMaxDateISO()}
                placeholder="Выберите дату"
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">Время</label>
              <Input
                type="time"
                value={departureTime}
                onChange={(e) => setDepartureTime(e.target.value)}
                required
              />
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <h2 className="mb-4 font-semibold text-slate-800">Места и цена</h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm text-slate-600">Цена (₽)</label>
              <Input
                type="text"
                inputMode="numeric"
                placeholder="500"
                value={price}
                onChange={(e) => setPrice(e.target.value.replace(/\D/g, ''))}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">Всего мест</label>
              <Input
                type="number"
                min={1}
                max={9}
                value={totalSeats}
                onChange={(e) => {
                  const v = parseInt(e.target.value, 10) || 1
                  setTotalSeats(v)
                  setAvailableSeats((a) => Math.min(a, v))
                }}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">Доступно</label>
              <Input
                type="number"
                min={0}
                max={9}
                value={availableSeats}
                onChange={(e) =>
                  setAvailableSeats(Math.min(totalSeats, parseInt(e.target.value, 10) || 0))
                }
              />
            </div>
          </div>
        </Card>

        <Card className="mb-6">
          <h2 className="mb-4 font-semibold text-slate-800">Автомобиль</h2>
          <div className="flex gap-4">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                checked={useNewCar}
                onChange={() => setUseNewCar(true)}
              />
              Новый
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                checked={!useNewCar}
                onChange={() => setUseNewCar(false)}
              />
              Из списка
            </label>
          </div>
          {useNewCar ? (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Марка</label>
                <Input
                  value={newCar.brand}
                  onChange={(e) =>
                    setNewCar((c) => ({ ...c, brand: e.target.value }))
                  }
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Модель</label>
                <Input
                  value={newCar.model}
                  onChange={(e) =>
                    setNewCar((c) => ({ ...c, model: e.target.value }))
                  }
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Год</label>
                <Input
                  type="number"
                  min={1990}
                  max={new Date().getFullYear() + 1}
                  value={newCar.year}
                  onChange={(e) =>
                    setNewCar((c) => ({
                      ...c,
                      year: parseInt(e.target.value, 10) || new Date().getFullYear(),
                    }))
                  }
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Цвет</label>
                <Input
                  value={newCar.color}
                  onChange={(e) =>
                    setNewCar((c) => ({ ...c, color: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label className="mb-1 block text-sm text-slate-600">
                  Гос. номер (необяз.)
                </label>
                <Input
                  value={newCar.license_plate}
                  onChange={(e) =>
                    setNewCar((c) => ({ ...c, license_plate: e.target.value }))
                  }
                />
              </div>
            </div>
          ) : (
            <div className="mt-4">
              <label className="mb-1 block text-sm text-slate-600">
                Выберите авто
              </label>
              <select
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5"
                value={carId ?? ''}
                onChange={(e) =>
                  setCarId(e.target.value ? parseInt(e.target.value, 10) : null)
                }
              >
                <option value="">—</option>
                {cars.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.brand} {c.model} ({c.year})
                  </option>
                ))}
              </select>
              {cars.length === 0 && (
                <p className="mt-1 text-sm text-slate-500">
                  Нет автомобилей. Добавьте в разделе «Мои авто» или укажите новый.
                </p>
              )}
            </div>
          )}
        </Card>

        <Card className="mb-6">
          <h2 className="mb-4 font-semibold text-slate-800">Дополнительно</h2>
          <div className="space-y-2">
            <label className="mb-2 block text-sm text-slate-600">Описание</label>
            <textarea
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Удобства, остановки по пути…"
            />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={smokingAllowed}
                onChange={(e) => setSmokingAllowed(e.target.checked)}
              />
              <Cigarette className="h-4 w-4 text-slate-600" aria-hidden />
              <span className="text-sm">Курение</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={petsAllowed}
                onChange={(e) => setPetsAllowed(e.target.checked)}
              />
              <Dog className="h-4 w-4 text-slate-600" aria-hidden />
              <span className="text-sm">С животными</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={childSeatAvailable}
                onChange={(e) => setChildSeatAvailable(e.target.checked)}
              />
              <Baby className="h-4 w-4 text-slate-600" aria-hidden />
              <span className="text-sm">Детское кресло</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={twoRearSeats}
                onChange={(e) => setTwoRearSeats(e.target.checked)}
              />
              <Users2 className="h-4 w-4 text-slate-600" aria-hidden />
              <span className="text-sm">2 места сзади</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={parcelAllowed}
                onChange={(e) => setParcelAllowed(e.target.checked)}
              />
              <Package className="h-4 w-4 text-slate-600" aria-hidden />
              <span className="text-sm">Посылка</span>
            </label>
          </div>
        </Card>

        <div className="flex gap-3">
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? 'Создание…' : 'Опубликовать поездку'}
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate('/')}
          >
            Отмена
          </Button>
        </div>
      </form>
    </div>
  )
}

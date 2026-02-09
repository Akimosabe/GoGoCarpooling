import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Baby, ChevronDown, ChevronUp, Copy, Cigarette, Dog, MapPin, Package, Pencil, Phone, Trash2, User, Users, Users2, Minus, Plus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  tripDetail,
  cancelTrip,
  editTrip,
  bookSeat,
  cancelBooking,
  rejectBooking,
  userBookings,
} from '@/api'
import type { Trip, Booking, SeatPassenger } from '@/api/types'
import { formatDate, getAvatarUrl } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

export function TripDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [trip, setTrip] = useState<Trip | null>(null)
  const [myBooking, setMyBooking] = useState<Booking | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [bookingSeats, setBookingSeats] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Trip>>({})
  const [showDriverPhone, setShowDriverPhone] = useState(false)
  const [previousBookingMessage, setPreviousBookingMessage] = useState<string | null>(null)
  const [passengersExpanded, setPassengersExpanded] = useState(false)
  const [rejectingBookingId, setRejectingBookingId] = useState<number | null>(null)

  const tripId = id ? parseInt(id, 10) : NaN
  const isDriver = user && trip && trip.driver.id === user.id
  const canBook =
    user &&
    trip &&
    !isDriver &&
    trip.effective_status === 'active' &&
    !trip.is_expired &&
    trip.available_seats > 0 &&
    !myBooking

  useEffect(() => {
    if (!trip || !canBook) return
    setBookingSeats((n) => Math.min(trip.available_seats, Math.max(1, n)))
  }, [trip?.id, trip?.available_seats, canBook])

  useEffect(() => {
    if (!id || Number.isNaN(tripId)) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    Promise.all([tripDetail(tripId), user ? userBookings() : Promise.resolve([])])
      .then(([t, bookings]) => {
        setTrip(t)
        setEditForm({
          price: t.price,
          total_seats: t.total_seats,
          available_seats: t.available_seats,
          description: t.description ?? '',
          smoking_allowed: t.smoking_allowed,
          pets_allowed: t.pets_allowed,
          child_seat_available: t.child_seat_available,
          two_rear_seats: t.two_rear_seats,
          parcel_allowed: t.parcel_allowed,
          luggage_size: t.luggage_size,
        })
        const b = bookings.find(
          (x) => x.trip.id === t.id && (x.status === 'confirmed' || x.status === 'pending')
        )
        setMyBooking(b ?? null)
        setPreviousBookingMessage(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки')
        setPreviousBookingMessage(null)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [id, tripId, user])

  const handleBook = async () => {
    if (!trip || !user || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const created = await bookSeat(trip.id, bookingSeats, undefined)
      setMyBooking(created)
      const t = await tripDetail(trip.id)
      setTrip(t)
    } catch (err) {
      const e = err as Error & { code?: string }
      if (e?.code === 'previous_booking_cancelled' || e?.code === 'previous_booking_rejected') {
        setPreviousBookingMessage(e.message)
        setError('')
      } else {
        setPreviousBookingMessage(null)
        setError(e instanceof Error ? e.message : 'Ошибка бронирования')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancelBooking = async () => {
    if (!myBooking || submitting) return
    setSubmitting(true)
    setError('')
    try {
      await cancelBooking(myBooking.id)
      const t = await tripDetail(trip!.id)
      setTrip(t)
      setMyBooking(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRejectBooking = async (bookingId: number) => {
    if (!trip || submitting) return
    if (!confirm('Отклонить бронирование? Пассажиру придёт уведомление.')) return
    setRejectingBookingId(bookingId)
    setError('')
    try {
      await rejectBooking(bookingId)
      const t = await tripDetail(trip.id)
      setTrip(t)
      if (myBooking?.id === bookingId) setMyBooking(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setRejectingBookingId(null)
    }
  }

  const handleCancelTrip = async () => {
    if (!trip || !isDriver || submitting) return
    if (!confirm('Отменить поездку? Все бронирования будут отменены.')) return
    setSubmitting(true)
    setError('')
    try {
      await cancelTrip(trip.id)
      navigate('/profile')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSaveEdit = async () => {
    if (!trip || !isDriver || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const updated = await editTrip(trip.id, {
        price: editForm.price as string,
        total_seats: editForm.total_seats,
        available_seats: editForm.available_seats,
        description: editForm.description ?? undefined,
        smoking_allowed: editForm.smoking_allowed,
        pets_allowed: editForm.pets_allowed,
        child_seat_available: editForm.child_seat_available,
        two_rear_seats: editForm.two_rear_seats,
        parcel_allowed: editForm.parcel_allowed,
        luggage_size: editForm.luggage_size,
      })
      setTrip(updated)
      setEditMode(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || !trip) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center text-slate-500">
        {loading ? 'Загрузка…' : 'Поездка не найдена'}
      </div>
    )
  }

  const price = typeof trip.price === 'string' ? parseFloat(trip.price) : trip.price

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      {error && (
        <div className="mb-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</div>
      )}

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 text-slate-700">
              <MapPin className="h-7 w-7 shrink-0 text-green-600" aria-hidden />
              <span className="text-lg font-medium">
                {trip.origin.display_name ?? `${trip.origin.name}, ${trip.origin.region}`} →{' '}
                {trip.destination.display_name ??
                  `${trip.destination.name}, ${trip.destination.region}`}
              </span>
            </div>
            <p className="mt-3 text-base font-medium text-slate-800">
              {formatDate(trip.departure_datetime)}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-green-600">
              {price.toLocaleString('ru-RU')} ₽
            </div>
            <div className="text-sm text-slate-500">
              {trip.available_seats} из {trip.total_seats} мест
            </div>
          </div>
        </div>

        {trip.description && (
          <div className="mt-4">
            <div className="rounded-xl border-2 border-slate-200 bg-slate-50/50 px-4 py-3">
              <p className="text-sm font-medium text-slate-600">Комментарий водителя</p>
              <p className="mt-1 text-slate-800">{trip.description}</p>
            </div>
          </div>
        )}

        <ul className="mt-4 flex flex-col gap-2 border-t border-slate-100 pt-4 text-base">
          <li
            className={`flex items-center gap-3 ${trip.smoking_allowed ? 'text-slate-600' : 'text-slate-400 line-through'}`}
          >
            <Cigarette className={`h-5 w-5 shrink-0 ${trip.smoking_allowed ? '' : 'opacity-50'}`} />
            Можно курить
          </li>
          <li
            className={`flex items-center gap-3 ${trip.pets_allowed ? 'text-slate-600' : 'text-slate-400 line-through'}`}
          >
            <Dog className={`h-5 w-5 shrink-0 ${trip.pets_allowed ? '' : 'opacity-50'}`} />
            С животными
          </li>
          <li
            className={`flex items-center gap-3 ${trip.parcel_allowed ? 'text-slate-600' : 'text-slate-400 line-through'}`}
          >
            <Package className={`h-5 w-5 shrink-0 ${trip.parcel_allowed ? '' : 'opacity-50'}`} />
            Посылка
          </li>
          <li
            className={`flex items-center gap-3 ${trip.child_seat_available ? 'text-slate-600' : 'text-slate-400 line-through'}`}
          >
            <Baby className={`h-5 w-5 shrink-0 ${trip.child_seat_available ? '' : 'opacity-50'}`} />
            Детское кресло
          </li>
          <li
            className={`flex items-center gap-3 ${trip.two_rear_seats ? 'text-slate-600' : 'text-slate-400 line-through'}`}
          >
            <Users2 className={`h-5 w-5 shrink-0 ${trip.two_rear_seats ? '' : 'opacity-50'}`} />
            2 места сзади
          </li>
        </ul>

        <div className="mt-6 flex items-center gap-3 border-t border-slate-100 pt-6">
{getAvatarUrl(trip.driver.avatar) ? (
              <img
              src={getAvatarUrl(trip.driver.avatar)!}
              alt=""
              className="h-12 w-12 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-200">
              <User className="h-6 w-6 text-slate-600" />
            </div>
          )}
          <div>
            <Link
              to={`/profile/${trip.driver.id}`}
              className="font-medium text-slate-900 hover:underline"
            >
              {trip.driver.first_name || trip.driver.email}
            </Link>
            {typeof trip.driver.average_rating === 'number' &&
              trip.driver.average_rating > 0 && (
                <p className="text-sm text-amber-600">
                  ★ {trip.driver.average_rating}
                </p>
              )}
          </div>
        </div>

        {trip.car && (
          <div className="mt-4 border-t border-slate-100 pt-4">
            <p className="text-sm text-slate-600">
              {trip.car.brand} {trip.car.model}, {trip.car.year}, {trip.car.color}
              {trip.car.license_plate && ` · ${trip.car.license_plate}`}
            </p>
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <p className="text-sm text-slate-600">Всего: <strong className="text-slate-800">{trip.total_seats}</strong> мест, осталось: <strong className="text-slate-800">{trip.available_seats}</strong></p>
        {(trip.seat_passengers ?? []).length > 0 && (
          <div className="mt-4 border-t border-slate-100 pt-6">
            {isDriver ? (
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  className="flex w-full items-center gap-3 text-left hover:opacity-90"
                  onClick={() => setPassengersExpanded((e) => !e)}
                >
                  <div className="flex -space-x-3">
                    {(trip.seat_passengers ?? []).map((p: SeatPassenger) => (
                      <Link
                        key={p.booking_id}
                        to={`/profile/${p.passenger.id}`}
                        onClick={(ev) => ev.stopPropagation()}
                        className="ring-2 ring-white rounded-full overflow-hidden"
                      >
                        {getAvatarUrl(p.passenger.avatar) ? (
                          <img src={getAvatarUrl(p.passenger.avatar)!} alt="" className="h-12 w-12 object-cover" />
                        ) : (
                          <div className="h-12 w-12 flex items-center justify-center bg-slate-200 text-slate-600 text-base font-medium">
                            {(p.passenger.first_name || '?')[0]}
                          </div>
                        )}
                      </Link>
                    ))}
                  </div>
                  <span className="text-sm font-medium text-slate-600">Пассажиры</span>
                  {passengersExpanded ? <ChevronUp className="h-5 w-5 shrink-0 text-slate-500" /> : <ChevronDown className="h-5 w-5 shrink-0 text-slate-500" />}
                </button>
                {passengersExpanded && (
                  <ul className="mt-2 space-y-2">
                    {(trip.seat_passengers ?? []).map((p: SeatPassenger) => (
                      <li key={p.booking_id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2">
                        <div className="flex items-center gap-3">
                          {getAvatarUrl(p.passenger.avatar) ? (
                            <img src={getAvatarUrl(p.passenger.avatar)!} alt="" className="h-10 w-10 rounded-full object-cover" />
                          ) : (
                            <div className="h-10 w-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-medium">
                              {(p.passenger.first_name || '?')[0]}
                            </div>
                          )}
                          <div>
                            <Link to={`/profile/${p.passenger.id}`} className="font-medium text-slate-900 hover:underline">
                              {p.passenger.first_name || 'Пассажир'}
                            </Link>
                            <p className="text-sm text-slate-600">{p.seats_count} мест</p>
                          </div>
                          {p.phone && (
                            <a href={`tel:${p.phone}`} className="text-sm text-green-600 hover:underline">{p.phone}</a>
                          )}
                        </div>
                        <Button
                          variant="danger"
                          size="sm"
                          className="shrink-0"
                          disabled={rejectingBookingId === p.booking_id}
                          onClick={() => handleRejectBooking(p.booking_id)}
                        >
                          Отклонить бронирование
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="flex -space-x-3">
                {(trip.seat_passengers ?? []).map((p: SeatPassenger) => (
                  <Link
                    key={p.booking_id}
                    to={`/profile/${p.passenger.id}`}
                    className="ring-2 ring-white rounded-full overflow-hidden"
                  >
                    {getAvatarUrl(p.passenger.avatar) ? (
                      <img src={getAvatarUrl(p.passenger.avatar)!} alt="" className="h-12 w-12 object-cover" />
                    ) : (
                      <div className="h-12 w-12 flex items-center justify-center bg-slate-200 text-slate-600 text-base font-medium">
                        {(p.passenger.first_name || '?')[0]}
                      </div>
                    )}
                  </Link>
                ))}
                </div>
                <span className="text-sm font-medium text-slate-600">Пассажиры</span>
              </div>
            )}
          </div>
        )}
      </Card>

      {isDriver && (
        <div className="mt-6 flex flex-wrap gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setEditMode(!editMode)}
            className="gap-1.5"
          >
            <Pencil className="h-4 w-4" />
            Редактировать
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/trips/create', { state: { copyFromTrip: trip } })}
            className="gap-1.5"
          >
            <Copy className="h-4 w-4" />
            Копировать поездку
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleCancelTrip}
            disabled={submitting}
            className="gap-1.5"
          >
            <Trash2 className="h-4 w-4" />
            Отменить поездку
          </Button>
        </div>
      )}

      {editMode && isDriver && (
        <Card className="mt-4">
          <h3 className="mb-4 font-semibold">Изменение параметров</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm text-slate-600">Цена (₽)</label>
              <Input
                type="number"
                min={0}
                value={editForm.price ?? ''}
                onChange={(e) =>
                  setEditForm((f) => ({ ...f, price: e.target.value }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">Всего мест</label>
              <Input
                type="number"
                min={1}
                max={9}
                value={editForm.total_seats ?? ''}
                onChange={(e) =>
                  setEditForm((f) => ({
                    ...f,
                    total_seats: parseInt(e.target.value, 10) || 0,
                  }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">
                Доступно мест
              </label>
              <Input
                type="number"
                min={0}
                max={9}
                value={editForm.available_seats ?? ''}
                onChange={(e) =>
                  setEditForm((f) => ({
                    ...f,
                    available_seats: parseInt(e.target.value, 10) || 0,
                  }))
                }
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm text-slate-600">
                Описание
              </label>
              <textarea
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-slate-900 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
                rows={3}
                value={editForm.description ?? ''}
                onChange={(e) =>
                  setEditForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button
              variant="primary"
              onClick={handleSaveEdit}
              disabled={submitting}
            >
              Сохранить
            </Button>
            <Button variant="ghost" onClick={() => setEditMode(false)}>
              Отмена
            </Button>
          </div>
        </Card>
      )}

      {previousBookingMessage && user && trip && !isDriver && !myBooking && (
        <Card className="mt-6">
          <p className="text-slate-700">{previousBookingMessage}</p>
        </Card>
      )}

      {canBook && !previousBookingMessage && (
        <Card className="mt-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-lg border border-slate-300 bg-white">
              <button
                type="button"
                aria-label="Уменьшить количество"
                className="flex h-9 w-9 items-center justify-center rounded-l-md text-slate-600 hover:bg-slate-100 disabled:opacity-50 disabled:hover:bg-transparent"
                disabled={bookingSeats <= 1 || submitting}
                onClick={() => setBookingSeats((n) => Math.max(1, n - 1))}
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="flex h-9 w-9 items-center justify-center border-x border-slate-200" aria-hidden>
                <Users className="h-5 w-5 text-slate-500" />
              </span>
              <button
                type="button"
                aria-label="Увеличить количество"
                className="flex h-9 w-9 items-center justify-center rounded-r-md text-slate-600 hover:bg-slate-100 disabled:opacity-50 disabled:hover:bg-transparent"
                disabled={bookingSeats >= trip.available_seats || submitting}
                onClick={() => setBookingSeats((n) => Math.min(trip.available_seats, n + 1))}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <Input
              type="number"
              min={1}
              max={trip.available_seats}
              className="w-14 text-center"
              value={bookingSeats}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10)
                if (Number.isNaN(v) || v < 1) setBookingSeats(1)
                else setBookingSeats(Math.min(trip.available_seats, v))
              }}
              aria-label="Количество мест"
            />
            <Button
              variant="primary"
              size="lg"
              onClick={handleBook}
              disabled={submitting}
            >
              Забронироваться
            </Button>
          </div>
        </Card>
      )}

      {myBooking && !isDriver && (
        <Card className="mt-6">
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="danger"
              size="sm"
              onClick={handleCancelBooking}
              disabled={submitting}
            >
              Отменить бронирование
            </Button>
            {showDriverPhone ? (
              <span className="flex items-center gap-2 rounded-lg bg-green-50 py-2 pl-3 pr-4 text-green-800">
                <Phone className="h-4 w-4 shrink-0" />
                <a href={`tel:${trip.driver_phone}`} className="font-medium underline">
                  {trip.driver_phone}
                </a>
              </span>
            ) : (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={() => setShowDriverPhone(true)}
              >
                <Phone className="h-4 w-4" />
                Показать номер
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { MapPin, Pencil, Trash2, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  tripDetail,
  cancelTrip,
  editTrip,
  bookSeat,
  cancelBooking,
  userBookings,
} from '@/api'
import type { Trip, Booking } from '@/api/types'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

const MEDIA = '/media'

export function TripDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [trip, setTrip] = useState<Trip | null>(null)
  const [myBooking, setMyBooking] = useState<Booking | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [bookingSeats, setBookingSeats] = useState(1)
  const [bookingComment, setBookingComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Trip>>({})

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
          luggage_size: t.luggage_size,
        })
        const b = (bookings as Booking[]).find(
          (x) => x.trip.id === t.id && (x.status === 'confirmed' || x.status === 'pending')
        )
        setMyBooking(b ?? null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки')
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
      await bookSeat(trip.id, bookingSeats, bookingComment || undefined)
      const [t, bookings] = await Promise.all([
        tripDetail(trip.id),
        userBookings(),
      ])
      setTrip(t)
      const b = (bookings as Booking[]).find(
        (x) => x.trip.id === trip.id && (x.status === 'confirmed' || x.status === 'pending')
      )
      setMyBooking(b ?? null)
      setBookingComment('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка бронирования')
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
            <div className="flex items-center gap-2 text-slate-600">
              <MapPin className="h-5 w-5" />
              <span className="text-lg">
                {trip.origin.display_name ?? `${trip.origin.name}, ${trip.origin.region}`} →{' '}
                {trip.destination.display_name ??
                  `${trip.destination.name}, ${trip.destination.region}`}
              </span>
            </div>
            <p className="mt-2 text-slate-500">{formatDate(trip.departure_datetime)}</p>
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
          <div className="mt-4 border-t border-slate-100 pt-4">
            <p className="text-slate-700">{trip.description}</p>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
          {trip.smoking_allowed && (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">
              Можно курить
            </span>
          )}
          {trip.pets_allowed && (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">
              С животными
            </span>
          )}
          <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600">
            Багаж: {trip.luggage_size === 'small' ? 'малый' : trip.luggage_size === 'large' ? 'большой' : 'средний'}
          </span>
        </div>

        <div className="mt-6 flex items-center gap-3 border-t border-slate-100 pt-6">
          {trip.driver.avatar ? (
            <img
              src={`${MEDIA}/${trip.driver.avatar}`}
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

      {canBook && (
        <Card className="mt-6">
          <h3 className="mb-4 font-semibold">Забронировать место</h3>
          <div className="flex flex-wrap gap-4">
            <div className="w-24">
              <label className="mb-1 block text-sm text-slate-600">Мест</label>
              <Input
                type="number"
                min={1}
                max={trip.available_seats}
                value={bookingSeats}
                onChange={(e) =>
                  setBookingSeats(Math.min(trip.available_seats, parseInt(e.target.value, 10) || 1))
                }
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="mb-1 block text-sm text-slate-600">
                Комментарий (необяз.)
              </label>
              <Input
                value={bookingComment}
                onChange={(e) => setBookingComment(e.target.value)}
                placeholder="Комментарий водителю"
              />
            </div>
          </div>
          <Button
            variant="primary"
            className="mt-4"
            onClick={handleBook}
            disabled={submitting}
          >
            Забронировать
          </Button>
        </Card>
      )}

      {myBooking && !isDriver && (
        <Card className="mt-6">
          <p className="text-slate-700">
            Ваше бронирование: {myBooking.seats_count} мест.
            Статус: {myBooking.status === 'confirmed' ? 'подтверждено' : 'ожидание'}
          </p>
          <Button
            variant="danger"
            size="sm"
            className="mt-3"
            onClick={handleCancelBooking}
            disabled={submitting}
          >
            Отменить бронирование
          </Button>
        </Card>
      )}
    </div>
  )
}

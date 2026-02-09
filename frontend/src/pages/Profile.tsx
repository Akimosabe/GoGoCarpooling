import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Archive, Car, LogOut, Pencil, Settings, Star, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import {
  userProfile,
  updateProfile,
  myTrips,
  userBookings,
} from '@/api'
import type { User as UserType, Trip, Booking } from '@/api/types'
import { TripOptionIcons } from '@/components/TripOptionIcons'
import { formatDate, formatTripDeparture, getAvatarUrl } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'


type Tab = 'driver' | 'passenger'

export function Profile() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const { user: currentUser, loading: authLoading, logout } = useAuth()
  const [profile, setProfile] = useState<UserType | null>(null)
  const [trips, setTrips] = useState<Trip[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [tab, setTab] = useState<Tab>('driver')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [editForm, setEditForm] = useState({
    first_name: '',
    phone: '',
    date_of_birth: '',
  })
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const profileId = id ? parseInt(id, 10) : currentUser?.id
  const isOwner = !!currentUser && profileId === currentUser.id

  useEffect(() => {
    if (authLoading) return
    if (!profileId) {
      if (!currentUser) navigate('/auth')
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    const load = async () => {
      try {
        const [u] = await Promise.all([userProfile(profileId)])
        setProfile(u)
        setEditForm({
          first_name: u.first_name ?? '',
          phone: u.phone ?? '',
          date_of_birth: u.date_of_birth ?? '',
        })
        if (isOwner) {
          const [t, b] = await Promise.all([myTrips(), userBookings()])
          setTrips(t)
          setBookings(b)
          const hasActivePassenger = b.some((bk) => bk.trip.effective_status === 'active' && !bk.trip.is_expired)
          setTab(hasActivePassenger ? 'passenger' : 'driver')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [profileId, isOwner, currentUser, authLoading, navigate])

  useEffect(() => {
    if (authLoading) return
    if (!currentUser && !id) navigate('/auth')
  }, [currentUser, id, authLoading, navigate])

  const handleSaveProfile = async () => {
    if (!currentUser || !isOwner || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const updated = await updateProfile({
        first_name: editForm.first_name,
        phone: editForm.phone || undefined,
        date_of_birth: editForm.date_of_birth || null,
        avatar: avatarFile ?? undefined,
      })
      setProfile(updated)
      setEditMode(false)
      setAvatarFile(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSubmitting(false)
    }
  }

  if ((authLoading || loading) && !profile) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center text-slate-500">
        Загрузка…
      </div>
    )
  }
  if (!profile) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="text-slate-600">Пользователь не найден</p>
        <Link to="/" className="mt-2 inline-block text-green-600 hover:underline">
          На главную
        </Link>
      </div>
    )
  }

  const avatarUrl = avatarFile
    ? URL.createObjectURL(avatarFile)
    : getAvatarUrl(profile.avatar) ?? null

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      {error && (
        <div className="mb-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</div>
      )}

      <Card>
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
          <div className="relative shrink-0">
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt=""
                className="h-24 w-24 rounded-full object-cover"
              />
            ) : (
              <div className="flex h-24 w-24 items-center justify-center rounded-full bg-slate-200">
                <User className="h-12 w-12 text-slate-500" />
              </div>
            )}
            {isOwner && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={async (e) => {
                    const f = e.target.files?.[0]
                    if (!f || !currentUser || !isOwner || submitting) return
                    setAvatarFile(f)
                    setSubmitting(true)
                    setError('')
                    try {
                      const updated = await updateProfile({
                        first_name: profile.first_name ?? undefined,
                        phone: profile.phone ?? undefined,
                        date_of_birth: profile.date_of_birth ?? null,
                        avatar: f,
                      })
                      setProfile(updated)
                      setAvatarFile(null)
                    } catch (err) {
                      setError(err instanceof Error ? err.message : 'Ошибка загрузки фото')
                    } finally {
                      setSubmitting(false)
                    }
                    e.target.value = ''
                  }}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute -bottom-1 -right-1 rounded-full p-1.5 shadow"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={submitting}
                  aria-label="Изменить фото"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
          <div className="min-w-0 flex-1">
            {editMode && isOwner ? (
              <div className="space-y-3">
                <div>
                  <label className="mb-1 block text-sm text-slate-600">Имя</label>
                  <Input
                    value={editForm.first_name}
                    onChange={(e) =>
                      setEditForm((f) => ({ ...f, first_name: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    Телефон
                  </label>
                  <Input
                    type="tel"
                    value={editForm.phone}
                    onChange={(e) =>
                      setEditForm((f) => ({ ...f, phone: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    Дата рождения
                  </label>
                  <Input
                    type="date"
                    value={editForm.date_of_birth}
                    onChange={(e) =>
                      setEditForm((f) => ({
                        ...f,
                        date_of_birth: e.target.value,
                      }))
                    }
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    onClick={handleSaveProfile}
                    disabled={submitting}
                  >
                    Сохранить
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setEditMode(false)
                      setAvatarFile(null)
                      setEditForm({
                        first_name: profile.first_name ?? '',
                        phone: profile.phone ?? '',
                        date_of_birth: profile.date_of_birth ?? '',
                      })
                    }}
                  >
                    Отмена
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-bold text-slate-900">
                    {profile.first_name || profile.email}
                  </h1>
                  {isOwner && (
                    <button
                      type="button"
                      onClick={() => setEditMode(true)}
                      className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                      aria-label="Редактировать"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                  )}
                </div>
                {profile.phone && (
                  <p
                    className={cn(
                      'mt-1 text-slate-600',
                      profile.phone_masked && 'select-none blur-sm'
                    )}
                    title={profile.phone_masked ? 'Номер виден только при бронировании в поездку этого водителя' : undefined}
                  >
                    {profile.phone_masked ? (
                      profile.phone
                    ) : (
                      <a href={`tel:${profile.phone}`} className="text-green-600 hover:underline">
                        {profile.phone}
                      </a>
                    )}
                  </p>
                )}
                {profile.email && (
                  <p
                    className={cn(
                      'text-sm text-slate-500',
                      profile.email_masked && 'select-none blur-sm'
                    )}
                    title={profile.email_masked ? 'Почта видна только при бронировании в поездку этого водителя' : undefined}
                  >
                    {profile.email_masked ? (
                      profile.email
                    ) : (
                      <a href={`mailto:${profile.email}`} className="text-green-600 hover:underline">
                        {profile.email}
                      </a>
                    )}
                  </p>
                )}
                <div className="mt-2 flex items-center gap-1 text-amber-500">
                  <Star className="h-5 w-5 fill-current" />
                  <span className="font-medium">
                    {profile.average_rating ?? 0}
                  </span>
                  <span className="text-sm text-slate-500">
                    ({profile.total_ratings_count ?? 0} оценок)
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {isOwner && (
          <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-6">
            <Link to="/profile/settings">
              <Button variant="outline" size="sm" className="gap-1.5">
                <Settings className="h-4 w-4" />
                Настройки
              </Button>
            </Link>
            <Link to="/profile/cars">
              <Button variant="outline" size="sm" className="gap-1.5">
                <Car className="h-4 w-4" />
                Мои авто
              </Button>
            </Link>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 text-red-600 hover:bg-red-50 hover:text-red-700"
              onClick={async () => {
                await logout()
                navigate('/')
              }}
            >
              <LogOut className="h-4 w-4" />
              Выход
            </Button>
          </div>
        )}
      </Card>

      {isOwner && (trips.length > 0 || bookings.length > 0) && (
        <div className="mt-8">
          <div className="mb-4 flex flex-wrap items-center gap-2">
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
            <Link
              to="/profile/trips"
              className="ml-auto text-sm font-medium text-green-600 hover:underline"
            >
              Все поездки
            </Link>
          </div>
          <div className="space-y-3">
            {tab === 'driver' &&
              trips.map((t) => {
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
              })}
            {tab === 'passenger' &&
              bookings.map((b) => {
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
              })}
          </div>
        </div>
      )}

      {isOwner && (
        <div className="mt-8 border-t border-slate-200 pt-8">
          <Link
            to="/profile/trips/archive"
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-left transition hover:bg-slate-100 hover:border-slate-300"
          >
            <Archive className="h-5 w-5 shrink-0 text-slate-500" aria-hidden />
            <span className="font-medium text-slate-700">Архив поездок</span>
            <span className="ml-auto text-sm text-slate-500">Открыть →</span>
          </Link>
        </div>
      )}
    </div>
  )
}

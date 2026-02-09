import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { carList, carCreate, carUpdate, carDelete } from '@/api'
import type { Car as CarType } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { CarCatalogAutocomplete } from '@/components/CarCatalogAutocomplete'
import { ColorSelect } from '@/components/ColorSelect'
import { Input } from '@/components/ui/Input'
import { Pencil, Trash2 } from 'lucide-react'

export function ProfileCars() {
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  const [cars, setCars] = useState<CarType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    color: '',
    license_plate: '',
  })

  useEffect(() => {
    if (authLoading) return
    if (!user) {
      navigate('/auth')
      return
    }
    carList()
      .then(setCars)
      .catch(() => setCars([]))
      .finally(() => setLoading(false))
  }, [user, authLoading, navigate])

  const resetForm = () => {
    setForm({
      brand: '',
      model: '',
      year: new Date().getFullYear(),
      color: '',
      license_plate: '',
    })
    setAdding(false)
    setEditing(null)
  }

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!form.brand?.trim() || !form.model?.trim()) {
      setError('Выберите марку и модель из списка.')
      return
    }
    setSubmitting(true)
    try {
      await carCreate(form)
      const list = await carList()
      setCars(list)
      resetForm()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = async (e: React.FormEvent, id: number) => {
    e.preventDefault()
    setError('')
    if (!form.brand?.trim() || !form.model?.trim()) {
      setError('Выберите марку и модель из списка.')
      return
    }
    setSubmitting(true)
    try {
      await carUpdate(id, form)
      const list = await carList()
      setCars(list)
      resetForm()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить автомобиль?')) return
    setError('')
    setSubmitting(true)
    try {
      await carDelete(id)
      setCars((prev) => prev.filter((c) => c.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center text-slate-500">
        Загрузка…
      </div>
    )
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
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Мои авто</h1>
        <Link to="/profile">
          <Button variant="ghost" size="sm">
            ← В кабинет
          </Button>
        </Link>
      </div>
      {error && (
        <div className="mb-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</div>
      )}

      {!adding && !editing && (
        <Button
          variant="primary"
          size="sm"
          className="mb-4"
          onClick={() => {
            setAdding(true)
            setForm({
              brand: '',
              model: '',
              year: new Date().getFullYear(),
              color: '',
              license_plate: '',
            })
          }}
        >
          Добавить авто
        </Button>
      )}

      {(adding || editing) && (
        <Card className="mb-6">
          <h2 className="mb-4 font-semibold">
            {editing ? 'Редактировать' : 'Новый автомобиль'}
          </h2>
          <form
            onSubmit={(e) => {
              if (editing) handleEdit(e, editing)
              else handleAdd(e)
            }}
            className="grid gap-4 sm:grid-cols-2"
          >
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm text-slate-600">
                Марка и модель (выберите из списка)
              </label>
              <CarCatalogAutocomplete
                value={
                  form.brand && form.model
                    ? { make: form.brand, model: form.model }
                    : null
                }
                onChange={(opt) =>
                  setForm((f) => ({
                    ...f,
                    brand: opt?.make ?? '',
                    model: opt?.model ?? '',
                  }))
                }
                placeholder="Введите 2+ буквы и выберите из списка"
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">Год</label>
              <Input
                type="number"
                min={1990}
                max={new Date().getFullYear() + 1}
                value={form.year}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    year: parseInt(e.target.value, 10) || new Date().getFullYear(),
                  }))
                }
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-600">Цвет</label>
              <ColorSelect
                value={form.color}
                onChange={(color) => setForm((f) => ({ ...f, color }))}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm text-slate-600">
                Гос. номер (необяз.)
              </label>
              <Input
                value={form.license_plate}
                onChange={(e) =>
                  setForm((f) => ({ ...f, license_plate: e.target.value }))
                }
              />
            </div>
            <div className="flex gap-2 sm:col-span-2">
              <Button type="submit" variant="primary" disabled={submitting}>
                {submitting ? 'Сохранение…' : 'Сохранить'}
              </Button>
              <Button type="button" variant="ghost" onClick={resetForm}>
                Отмена
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className="space-y-3">
        {cars.map((c) =>
          editing === c.id ? null : (
            <Card key={c.id} className="flex items-center justify-between">
              <div>
                <p className="font-medium">
                  {c.brand} {c.model}, {c.year}
                </p>
                <p className="text-sm text-slate-500">
                  {c.color}
                  {c.license_plate && ` · ${c.license_plate}`}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setEditing(c.id)
                    setForm({
                      brand: c.brand,
                      model: c.model,
                      year: c.year,
                      color: c.color,
                      license_plate: c.license_plate ?? '',
                    })
                  }}
                  className="rounded-full p-2 text-slate-500 hover:bg-slate-100"
                  aria-label="Редактировать"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(c.id)}
                  disabled={submitting}
                  className="rounded-full p-2 text-red-500 hover:bg-red-50"
                  aria-label="Удалить"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          )
        )}
      </div>
      {cars.length === 0 && !adding && (
        <p className="rounded-xl bg-slate-100 py-8 text-center text-slate-600">
          Нет автомобилей. Добавьте первый.
        </p>
      )}
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/contexts/AuthContext'
import { changePassword, deleteAccount } from '@/api/auth'

export function ProfileSettings() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [changeMsg, setChangeMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [changeLoading, setChangeLoading] = useState(false)

  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [deleteMsg, setDeleteMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setChangeMsg(null)
    if (newPassword !== newPasswordConfirm) {
      setChangeMsg({ type: 'error', text: 'Новые пароли не совпадают' })
      return
    }
    if (newPassword.length < 8) {
      setChangeMsg({ type: 'error', text: 'Пароль должен содержать минимум 8 символов' })
      return
    }
    setChangeLoading(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      })
      setChangeMsg({ type: 'success', text: 'Пароль успешно изменён' })
      setCurrentPassword('')
      setNewPassword('')
      setNewPasswordConfirm('')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ошибка при смене пароля'
      setChangeMsg({ type: 'error', text: msg })
    } finally {
      setChangeLoading(false)
    }
  }

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    setDeleteMsg(null)
    if (deleteConfirm.toLowerCase() !== 'удалить') {
      setDeleteMsg({ type: 'error', text: 'Введите слово «удалить» для подтверждения' })
      return
    }
    setDeleteLoading(true)
    try {
      await deleteAccount(deletePassword)
      await logout()
      navigate('/', { replace: true })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ошибка при удалении аккаунта'
      setDeleteMsg({ type: 'error', text: msg })
    } finally {
      setDeleteLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6 px-4 py-8">
      <div className="flex items-center gap-4">
        <Link to="/profile" className="text-slate-600 hover:text-slate-900">
          ← В личный кабинет
        </Link>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Сменить пароль</h2>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Текущий пароль</label>
            <Input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Новый пароль</label>
            <Input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Повторите новый пароль</label>
            <Input
              type="password"
              value={newPasswordConfirm}
              onChange={(e) => setNewPasswordConfirm(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>
          {changeMsg && (
            <p className={changeMsg.type === 'success' ? 'text-green-600' : 'text-red-600'}>
              {changeMsg.text}
            </p>
          )}
          <Button type="submit" disabled={changeLoading}>
            {changeLoading ? 'Сохранение…' : 'Сохранить пароль'}
          </Button>
        </form>
      </Card>

      <Card className="border-red-200 bg-red-50/30">
        <h2 className="mb-2 text-lg font-semibold text-red-800">Удалить аккаунт</h2>
        <p className="mb-4 text-sm text-slate-600">
          Это действие необратимо. Будут удалены ваш профиль, поездки и бронирования.
        </p>
        <form onSubmit={handleDeleteAccount} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Пароль</label>
            <Input
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              required
              placeholder="Введите пароль для подтверждения"
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Введите слово <strong>удалить</strong> для подтверждения
            </label>
            <Input
              type="text"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              required
              placeholder="удалить"
              autoComplete="off"
            />
          </div>
          {deleteMsg && (
            <p className="text-red-600">{deleteMsg.text}</p>
          )}
          <Button
            type="submit"
            variant="danger"
            disabled={deleteLoading}
          >
            {deleteLoading ? 'Удаление…' : 'Удалить аккаунт'}
          </Button>
        </form>
      </Card>
    </div>
  )
}

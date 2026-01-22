import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import {
  passwordResetRequest,
  passwordResetConfirm,
} from '@/api/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

type Tab = 'login' | 'register' | 'reset' | 'reset-confirm'

export function Auth() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login: doLogin, register: doRegister } = useAuth()
  const [tab, setTab] = useState<Tab>(() => {
    const uid = searchParams.get('uid')
    const token = searchParams.get('token')
    if (uid && token) return 'reset-confirm'
    return 'login'
  })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [phone, setPhone] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')

  const uid = searchParams.get('uid') ?? ''
  const token = searchParams.get('token') ?? ''

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await doLogin(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка входа')
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password !== passwordConfirm) {
      setError('Пароли не совпадают')
      return
    }
    try {
      await doRegister({
        email,
        first_name: firstName,
        phone,
        password,
        password_confirm: passwordConfirm,
      })
      navigate('/')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Ошибка регистрации'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
  }

  const handleResetRequest = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    try {
      await passwordResetRequest({ email })
      setMessage(
        'Если пользователь с таким email существует, на него отправлена ссылка для восстановления пароля.'
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const handleResetConfirm = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (newPassword !== newPasswordConfirm) {
      setError('Пароли не совпадают')
      return
    }
    if (newPassword.length < 8) {
      setError('Пароль должен быть не менее 8 символов')
      return
    }
    try {
      await passwordResetConfirm(uid, token, {
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      })
      setMessage('Пароль успешно изменён. Войдите с новым паролем.')
      setTab('login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    }
  }

  const bgStyle = {
    backgroundImage: `linear-gradient(rgba(15,23,42,0.5), rgba(15,23,42,0.6)), url(https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=1920)`,
  }

  return (
    <div
      className="flex min-h-[calc(100vh-57px)] flex-col items-center justify-center bg-cover bg-center bg-no-repeat px-4 py-12"
      style={bgStyle}
    >
      <div className="w-full max-w-md rounded-2xl border border-slate-200/80 bg-white/95 p-8 shadow-xl backdrop-blur">
        <h1 className="mb-6 text-center text-2xl font-bold text-slate-900">
          {tab === 'login' && 'Вход'}
          {tab === 'register' && 'Регистрация'}
          {tab === 'reset' && 'Восстановление пароля'}
          {tab === 'reset-confirm' && 'Новый пароль'}
        </h1>

        {error && (
          <div className="mb-4 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        {message && (
          <div className="mb-4 rounded-xl bg-green-50 px-4 py-2 text-sm text-green-800">
            {message}
          </div>
        )}

        {tab === 'login' && (
          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button type="submit" variant="primary" className="w-full">
              Войти
            </Button>
            <div className="flex flex-wrap gap-2 text-sm">
              <button
                type="button"
                onClick={() => setTab('register')}
                className="text-green-600 hover:underline"
              >
                Регистрация
              </button>
              <span className="text-slate-400">·</span>
              <button
                type="button"
                onClick={() => setTab('reset')}
                className="text-green-600 hover:underline"
              >
                Забыли пароль?
              </button>
            </div>
          </form>
        )}

        {tab === 'register' && (
          <form onSubmit={handleRegister} className="space-y-4">
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              placeholder="Имя"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
            <Input
              type="tel"
              placeholder="Телефон (+79001234567)"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Пароль (мин. 8 символов)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
            <Input
              type="password"
              placeholder="Повторите пароль"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              required
            />
            <Button type="submit" variant="primary" className="w-full">
              Зарегистрироваться
            </Button>
            <p className="text-center text-sm text-slate-600">
              Есть аккаунт?{' '}
              <button
                type="button"
                onClick={() => setTab('login')}
                className="text-green-600 hover:underline"
              >
                Войти
              </button>
            </p>
          </form>
        )}

        {tab === 'reset' && (
          <form onSubmit={handleResetRequest} className="space-y-4">
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Button type="submit" variant="primary" className="w-full">
              Отправить ссылку
            </Button>
            <p className="text-center text-sm">
              <button
                type="button"
                onClick={() => setTab('login')}
                className="text-green-600 hover:underline"
              >
                Назад к входу
              </button>
            </p>
          </form>
        )}

        {tab === 'reset-confirm' && (
          <form onSubmit={handleResetConfirm} className="space-y-4">
            <Input
              type="password"
              placeholder="Новый пароль (мин. 8)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
            <Input
              type="password"
              placeholder="Повторите пароль"
              value={newPasswordConfirm}
              onChange={(e) => setNewPasswordConfirm(e.target.value)}
              required
            />
            <Button type="submit" variant="primary" className="w-full">
              Сохранить пароль
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}

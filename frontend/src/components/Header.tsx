import { useState, useCallback, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bell, Car, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { notificationsList, markNotificationRead, markAllNotificationsRead } from '@/api/notifications'
import type { Notification } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { cn, getAvatarUrl } from '@/lib/utils'

export function Header() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unread, setUnread] = useState(0)
  const [dropdown, setDropdown] = useState(false)

  const load = useCallback(async () => {
    try {
      const res = await notificationsList(false)
      setNotifications(res.notifications)
      setUnread(res.unread_count)
    } catch {
      setNotifications([])
      setUnread(0)
    }
  }, [])

  useEffect(() => {
    if (!user) return
    load()
    const interval = setInterval(load, 15000) // обновление уведомлений каждые 15 с
    return () => clearInterval(interval)
  }, [user, load])

  const markRead = async (id: number) => {
    try {
      await markNotificationRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      setUnread((c) => Math.max(0, c - 1))
    } catch {}
  }

  const markAllRead = async () => {
    try {
      await markAllNotificationsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnread(0)
      setDropdown(false)
    } catch {}
  }

  return (
    <header className="sticky top-0 z-40 flex min-h-0 items-center justify-between gap-2 border-b border-slate-200 bg-white/95 px-3 py-2 backdrop-blur sm:gap-4 sm:px-6 sm:py-3">
      <Link to="/" className="shrink-0 text-lg font-bold text-green-600 sm:text-xl">
        GoGo
      </Link>

      <nav className="flex min-w-0 shrink items-center gap-1 sm:gap-4">
        <Link to="/trips/create" className="shrink-0" aria-label="Создать поездку">
          <Button variant="primary" size="sm" className="gap-1.5 px-2.5 py-1.5 sm:px-3">
            <Car className="h-4 w-4 shrink-0" />
            <span className="hidden sm:inline">Создать поездку</span>
          </Button>
        </Link>

        {user ? (
          <>
            <div className="relative">
              <button
                type="button"
                onClick={() => setDropdown(!dropdown)}
                className="relative rounded-full p-2 text-slate-600 hover:bg-slate-100"
                aria-label="Уведомления"
              >
                <Bell className="h-5 w-5" />
                {unread > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white">
                    {unread > 99 ? '99+' : unread}
                  </span>
                )}
              </button>
              {dropdown && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    aria-hidden="true"
                    onClick={() => setDropdown(false)}
                  />
                  <div className="absolute right-0 top-full z-50 mt-1 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
                    <div className="border-b border-slate-100 px-4 py-2 font-medium text-slate-800">
                      Уведомления
                    </div>
                    <div className="max-h-64 overflow-auto">
                      {notifications.length === 0 ? (
                        <div className="px-4 py-6 text-center text-sm text-slate-500">
                          Нет уведомлений
                        </div>
                      ) : (
                        notifications.slice(0, 20).map((n) => (
                          <button
                            key={n.id}
                            type="button"
                            onClick={() => {
                              markRead(n.id)
                              if (n.notification_type === 'leave_rating' && n.target_user != null && n.trip != null) {
                                navigate(`/profile/${n.target_user}?rate=1&trip_id=${n.trip}`)
                              } else if (n.trip) {
                                navigate(`/trips/${n.trip}`)
                              }
                              setDropdown(false)
                            }}
                            className={cn(
                              'w-full border-b border-slate-50 px-4 py-3 text-left text-sm last:border-0 hover:bg-slate-50',
                              !n.is_read && 'bg-green-50/50'
                            )}
                          >
                            <div className="font-medium text-slate-800">{n.title}</div>
                            <div className="mt-0.5 text-slate-600">{n.message}</div>
                          </button>
                        ))
                      )}
                    </div>
                    {notifications.length > 0 && (
                      <div className="border-t border-slate-100 px-2 py-2">
                        <button
                          type="button"
                          onClick={markAllRead}
                          className="w-full rounded-lg px-3 py-2 text-center text-sm font-medium text-slate-600 hover:bg-slate-100"
                        >
                          Прочитано
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            <Link to="/profile" className="shrink-0" aria-label="Профиль">
              <Button variant="ghost" size="sm" className="gap-1.5 px-2 sm:px-3">
                {getAvatarUrl(user.avatar) ? (
                  <img
                    src={getAvatarUrl(user.avatar)!}
                    alt=""
                    className="h-6 w-6 shrink-0 rounded-full object-cover"
                  />
                ) : (
                  <User className="h-5 w-5 shrink-0" />
                )}
                <span className="hidden sm:inline">{user.first_name || 'Профиль'}</span>
              </Button>
            </Link>
          </>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/auth')}
          >
            Войти
          </Button>
        )}
      </nav>
    </header>
  )
}

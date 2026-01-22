import { get, post } from './client'
import type { Notification } from './types'

export async function notificationsList(unreadOnly = false) {
  const params = unreadOnly ? { unread: 'true' } : undefined
  return get<{ unread_count: number; notifications: Notification[] }>(
    '/api/notifications/',
    params
  )
}

export async function notificationsRealtime() {
  return get<{ count: number; notifications: unknown[] }>('/api/notifications/realtime/')
}

export async function clearRealtimeNotifications() {
  return post<{ message: string }>('/api/notifications/clear-realtime/')
}

export async function markNotificationRead(id: number) {
  return post<{ message: string }>(`/api/notifications/${id}/read/`)
}

export async function markAllNotificationsRead() {
  return post<{ message: string }>('/api/notifications/read-all/')
}

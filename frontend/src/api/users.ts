import { get } from './client'
import type { User } from './types'

export async function userProfile(userId: number) {
  return get<User>(`/api/users/${userId}/profile/`)
}

export interface UpdateProfilePayload {
  first_name?: string
  phone?: string
  date_of_birth?: string | null
  avatar?: File | null
}

export async function updateProfile(data: UpdateProfilePayload) {
  const form = new FormData()
  if (data.first_name != null) form.append('first_name', data.first_name)
  if (data.phone != null) form.append('phone', data.phone)
  if (data.date_of_birth != null) form.append('date_of_birth', data.date_of_birth || '')
  if (data.avatar instanceof File) form.append('avatar', data.avatar)
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1]
  const headers: Record<string, string> = {}
  if (csrf) headers['X-CSRFToken'] = decodeURIComponent(csrf)
  const res = await fetch('/api/profile/update/', {
    method: 'POST',
    credentials: 'include',
    headers,
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { message?: string }).message || res.statusText)
  }
  return res.json() as Promise<User>
}

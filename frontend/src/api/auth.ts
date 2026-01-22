import { get, post } from './client'
import type { User } from './types'

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  first_name: string
  phone: string
  password: string
  password_confirm: string
}

export interface PasswordResetPayload {
  email: string
}

export interface PasswordResetConfirmPayload {
  new_password: string
  new_password_confirm: string
}

export async function login(data: LoginPayload) {
  const res = await post<{ message: string; user: User }>('/api/auth/login/', data)
  return res
}

export async function register(data: RegisterPayload) {
  const res = await post<{ message: string; user: User }>('/api/auth/register/', data)
  return res
}

export async function logout() {
  return post<{ message: string }>('/api/auth/logout/')
}

export async function me() {
  return get<User>('/api/auth/me/')
}

export async function passwordResetRequest(data: PasswordResetPayload) {
  return post<{ message: string }>('/api/auth/password-reset/', data)
}

export async function passwordResetConfirm(
  uidb64: string,
  token: string,
  data: PasswordResetConfirmPayload
) {
  return post<{ message: string }>(`/api/auth/password-reset/${uidb64}/${token}/`, data)
}

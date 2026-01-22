import { get, post, put, del } from './client'
import type { Car } from './types'

export interface CarCreate {
  brand: string
  model: string
  year: number
  color: string
  license_plate?: string
}

export async function carList() {
  return get<Car[]>('/api/cars/')
}

export async function carDetail(id: number) {
  return get<Car>(`/api/cars/${id}/`)
}

export async function carCreate(data: CarCreate) {
  return post<Car>('/api/cars/', data)
}

export async function carUpdate(id: number, data: Partial<CarCreate>) {
  return put<Car>(`/api/cars/${id}/`, data)
}

export async function carDelete(id: number) {
  return del<{ message: string }>(`/api/cars/${id}/`)
}

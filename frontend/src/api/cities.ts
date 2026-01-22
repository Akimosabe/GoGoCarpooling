import { get } from './client'
import type { City, CitySuggestion } from './types'

export interface CityListParams {
  search?: string
  popular?: 'true' | 'false'
  country?: string
  limit?: number
}

export async function cityList(params?: CityListParams) {
  const p: Record<string, string> = {}
  if (params?.search) p.search = params.search
  if (params?.popular) p.popular = params.popular
  if (params?.country) p.country = params.country
  if (params?.limit != null) p.limit = String(params.limit)
  return get<City[]>('/api/cities/', Object.keys(p).length ? p : undefined)
}

export async function cityAutocomplete(query: string, country?: string, limit = 10) {
  if (!query || query.length < 2) return { suggestions: [] as CitySuggestion[] }
  const params: Record<string, string> = { query, limit: String(limit) }
  if (country) params.country = country
  const res = await get<{ suggestions: CitySuggestion[] }>('/api/cities/autocomplete/', params)
  return res
}

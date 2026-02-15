import { post } from './client'

export interface CreateRatingPayload {
  trip: number
  to_user: number
  rating: number
  comment?: string
}

export interface RatingResponse {
  id: number
  trip: number
  from_user: unknown
  to_user: unknown
  rating: number
  comment: string | null
  created_at: string
}

export async function createRating(data: CreateRatingPayload) {
  return post<RatingResponse>('/api/ratings/create/', data)
}

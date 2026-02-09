const LAST_SEARCH_KEY = 'gogo_last_search'

export interface LastSearch {
  origin: string
  originId: number | null
  destination: string
  destId: number | null
}

export function loadLastSearch(): LastSearch | null {
  try {
    const raw = localStorage.getItem(LAST_SEARCH_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as LastSearch
    if (parsed?.origin != null && parsed?.destination != null) return parsed
    return null
  } catch {
    return null
  }
}

export function saveLastSearch(
  origin: string,
  originId: number | null,
  destination: string,
  destId: number | null
) {
  if (!origin && !destination) return
  localStorage.setItem(
    LAST_SEARCH_KEY,
    JSON.stringify({ origin, originId, destination, destId })
  )
}

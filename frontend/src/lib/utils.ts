import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const INVALID_DATE_LABEL = '—'

/** Normalize ISO-like string for parsing (e.g. trim microseconds for older engines) */
function parseDateLike(s: string): Date {
  const d = new Date(s)
  if (!Number.isNaN(d.getTime())) return d
  // Fallback: Python/DRF often sends .123456 or .123456+00:00 — shorten to .123 for Safari
  const normalized = s.replace(/(\.\d{4,})(Z|[+-]\d{2}:?\d{2})?$/i, (_, frac, tz) => {
    const ms = frac.slice(0, 4)
    return `${ms}${tz ?? ''}`
  })
  const d2 = new Date(normalized)
  if (!Number.isNaN(d2.getTime())) return d2
  return d
}

export function formatDate(s: string | null | undefined): string {
  if (s == null || s === '') return INVALID_DATE_LABEL
  const d = parseDateLike(String(s).trim())
  if (Number.isNaN(d.getTime())) return INVALID_DATE_LABEL
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDateOnly(s: string | null | undefined): string {
  if (s == null || s === '') return INVALID_DATE_LABEL
  const d = parseDateLike(String(s).trim())
  if (Number.isNaN(d.getTime())) return INVALID_DATE_LABEL
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

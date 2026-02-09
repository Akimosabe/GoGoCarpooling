import { useCallback, useEffect, useRef, useState } from 'react'
import { cityAutocomplete } from '@/api/cities'
import type { CitySuggestion } from '@/api/types'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'

export interface CityOption {
  id: number
  value: string
}

interface CityAutocompleteProps {
  value: string
  onChange: (v: string) => void
  onSelect?: (opt: CityOption) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  /** Город из последнего поиска — показывается в подсказках при фокусе на поле */
  suggestedOption?: CityOption
}

export function CityAutocomplete({
  value,
  onChange,
  onSelect,
  placeholder = 'Город',
  className,
  disabled,
  suggestedOption,
}: CityAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<CitySuggestion[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wrapRef = useRef<HTMLDivElement>(null)

  const fetchSuggestions = useCallback(async (q: string) => {
    if (!q || q.length < 2) {
      setSuggestions([])
      return
    }
    setLoading(true)
    try {
      const res = await cityAutocomplete(q, undefined, 10)
      setSuggestions(res.suggestions || [])
      setOpen(true)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 250)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [value, fetchSuggestions])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  return (
    <div ref={wrapRef} className={cn('relative', className)}>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => {
        if (value.length >= 2) setOpen(true)
        else if (suggestedOption && value !== suggestedOption.value) setOpen(true)
      }}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
      />
      {open && (suggestions.length > 0 || loading || (suggestedOption && value !== suggestedOption.value)) && (
        <ul
          className="absolute left-0 z-50 mt-1 max-h-48 w-full overflow-auto rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
          role="listbox"
        >
          {suggestedOption && value !== suggestedOption.value && (
            <li
              role="option"
              tabIndex={0}
              className="cursor-pointer px-4 py-2 text-left leading-tight hover:bg-slate-100"
              onClick={() => {
                onChange(suggestedOption.value)
                onSelect?.({ id: suggestedOption.id, value: suggestedOption.value })
                setOpen(false)
              }}
            >
              {(() => {
                const comma = suggestedOption.value.indexOf(',')
                const cityPart = comma >= 0 ? suggestedOption.value.slice(0, comma).trim() : suggestedOption.value
                const regionPart = comma >= 0 ? suggestedOption.value.slice(comma + 1).trim() : ''
                return (
                  <>
                    <div className="font-semibold text-slate-900">{cityPart},</div>
                    {regionPart && (
                      <div className="truncate text-xs text-slate-500">{regionPart}</div>
                    )}
                  </>
                )
              })()}
            </li>
          )}
          {loading && (
            <li className="px-4 py-2 text-sm text-slate-500">Загрузка…</li>
          )}
          {!loading &&
            suggestions
              .filter((s) => !suggestedOption || s.data.id !== suggestedOption.id)
              .map((s) => (
                <li
                  key={s.data.id}
                  role="option"
                  tabIndex={0}
                  className="cursor-pointer px-4 py-2 text-left leading-tight hover:bg-slate-100"
                  onClick={() => {
                    onChange(s.value)
                    onSelect?.({ id: s.data.id, value: s.value })
                    setOpen(false)
                  }}
                >
                  <div className="font-semibold text-slate-900">{s.data.city},</div>
                  {s.data.region && (
                    <div className="truncate text-xs text-slate-500">{s.data.region}</div>
                  )}
                </li>
              ))}
        </ul>
      )}
    </div>
  )
}

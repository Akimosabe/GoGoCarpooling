import { useCallback, useEffect, useRef, useState } from 'react'
import { carCatalogSearch, type CarCatalogEntry } from '@/api/cars'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'

export interface CarCatalogOption {
  make: string
  model: string
}

function displayOption(opt: CarCatalogOption) {
  return `${opt.make} ${opt.model}`
}

interface CarCatalogAutocompleteProps {
  /** Текущая выбранная пара (марка + модель) — только из списка */
  value: CarCatalogOption | null
  onChange: (opt: CarCatalogOption | null) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  required?: boolean
}

export function CarCatalogAutocomplete({
  value,
  onChange,
  placeholder = 'Начните вводить марку или модель…',
  className,
  disabled,
  required,
}: CarCatalogAutocompleteProps) {
  const [inputText, setInputText] = useState(value ? displayOption(value) : '')
  const [suggestions, setSuggestions] = useState<CarCatalogEntry[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wrapRef = useRef<HTMLDivElement>(null)

  // Синхронизируем поле с выбранным значением (например при редактировании)
  useEffect(() => {
    if (value) setInputText(displayOption(value))
    else setInputText('')
  }, [value])

  const fetchSuggestions = useCallback(async (q: string) => {
    if (!q || q.length < 2) {
      setSuggestions([])
      return
    }
    setLoading(true)
    try {
      const list = await carCatalogSearch(q)
      setSuggestions(list)
      setOpen(true)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(inputText), 250)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [inputText, fetchSuggestions])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  const handleSelect = (opt: CarCatalogEntry) => {
    const option = { make: opt.make, model: opt.model }
    onChange(option)
    setInputText(displayOption(option))
    setOpen(false)
    setSuggestions([])
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setInputText(v)
    if (!v) onChange(null)
    // Не записываем в value произвольный текст — только выбор из списка
  }

  return (
    <div ref={wrapRef} className={cn('relative', className)}>
      <Input
        value={inputText}
        onChange={handleInputChange}
        onFocus={() => {
          if (inputText.length >= 2) setOpen(true)
        }}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
        required={required}
        aria-expanded={open}
        aria-haspopup="listbox"
        role="combobox"
      />
      {open && (suggestions.length > 0 || loading) && (
        <ul
          className="absolute left-0 z-50 mt-1 max-h-48 w-full overflow-auto rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
          role="listbox"
        >
          {loading && (
            <li className="px-4 py-2 text-sm text-slate-500">Загрузка…</li>
          )}
          {!loading &&
            suggestions.map((s, i) => (
              <li
                key={`${s.make}-${s.model}-${i}`}
                role="option"
                tabIndex={0}
                className="cursor-pointer px-4 py-2 text-left text-slate-800 hover:bg-slate-100"
                onClick={() => handleSelect(s)}
              >
                {s.make} {s.model}
              </li>
            ))}
        </ul>
      )}
    </div>
  )
}

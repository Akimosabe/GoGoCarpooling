import { useRef, useEffect, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { CAR_COLORS } from '@/constants'

interface ColorSelectProps {
  value: string
  onChange: (value: string) => void
  required?: boolean
  id?: string
}

export function ColorSelect({ value, onChange, required: _required, id }: ColorSelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const options: { name: string; hex: string }[] = [...CAR_COLORS]
  const currentInList = CAR_COLORS.find((c) => c.name === value)
  if (value && !currentInList) {
    options.unshift({ name: value, hex: '#9ca3af' })
  }

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('click', close)
    return () => document.removeEventListener('click', close)
  }, [])

  const displayHex: string | undefined = currentInList?.hex ?? (value ? '#9ca3af' : undefined)

  return (
    <div ref={ref} className="relative" id={id}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-left text-slate-900 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {displayHex && (
          <span
            className="h-5 w-5 shrink-0 rounded-full border border-slate-200"
            style={{ backgroundColor: displayHex }}
            aria-hidden
          />
        )}
        <span className="flex-1">{value || 'Выберите цвет'}</span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-slate-500 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <ul
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-56 overflow-auto rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
          role="listbox"
        >
          {options.map((c) => (
            <li key={c.name} role="option" aria-selected={value === c.name}>
              <button
                type="button"
                onClick={() => {
                  onChange(c.name)
                  setOpen(false)
                }}
                className="flex w-full items-center gap-2 px-4 py-2 text-left hover:bg-slate-50"
              >
                <span
                  className="h-5 w-5 shrink-0 rounded-full border border-slate-200"
                  style={{ backgroundColor: c.hex }}
                  aria-hidden
                />
                <span>{c.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

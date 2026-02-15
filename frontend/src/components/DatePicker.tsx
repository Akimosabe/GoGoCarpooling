import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

const MONTHS_RU = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]
const WEEKDAYS_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

/** YYYY-MM-DD в локальной дате (без перевода в UTC, чтобы последний день месяца не перескакивал) */
function toLocalDateString(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatDisplay(iso: string): string {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  const day = String(d).padStart(2, '0')
  const month = String(m).padStart(2, '0')
  return `${day}.${month}.${y}`
}

/** Дни одного месяца для сетки: первый понедельник и все дни до конца месяца */
function getMonthGrid(year: number, month: number): (string | null)[] {
  const first = new Date(year, month, 1)
  const last = new Date(year, month + 1, 0)
  // Понедельник = 1, воскресенье = 0 -> сдвиг: пн=0, вск=6
  const firstDay = first.getDay()
  const startOffset = firstDay === 0 ? 6 : firstDay - 1
  const daysInMonth = last.getDate()
  const grid: (string | null)[] = []
  for (let i = 0; i < startOffset; i++) grid.push(null)
  for (let d = 1; d <= daysInMonth; d++) {
    grid.push(toLocalDateString(new Date(year, month, d)))
  }
  return grid
}

export interface DatePickerProps {
  value: string
  onChange: (value: string) => void
  min: string
  max: string
  placeholder?: string
  className?: string
  required?: boolean
}

export function DatePicker({
  value,
  onChange,
  min,
  max,
  placeholder = 'Выберите дату',
  className,
  required: _required,
}: DatePickerProps) {
  const [open, setOpen] = useState(false)
  const [viewYear, setViewYear] = useState(() => {
    if (value) {
      const [y] = value.split('-').map(Number)
      return y
    }
    return new Date().getFullYear()
  })
  const [viewMonth, setViewMonth] = useState(() => {
    if (value) {
      const [, m] = value.split('-').map(Number)
      return m - 1
    }
    return new Date().getMonth()
  })
  const wrapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  const today = new Date()
  const minYear = today.getFullYear()
  const minMonth = today.getMonth()
  const maxDate = new Date(max)
  const maxYear = maxDate.getFullYear()
  const maxMonth = maxDate.getMonth()
  const canPrev = viewYear > minYear || (viewYear === minYear && viewMonth > minMonth)
  const canNext = viewYear < maxYear || (viewYear === maxYear && viewMonth < maxMonth)

  const goPrev = () => {
    if (viewMonth === 0) {
      setViewMonth(11)
      setViewYear((y) => y - 1)
    } else {
      setViewMonth((m) => m - 1)
    }
  }
  const goNext = () => {
    if (viewMonth === 11) {
      setViewMonth(0)
      setViewYear((y) => y + 1)
    } else {
      setViewMonth((m) => m + 1)
    }
  }

  const grid = getMonthGrid(viewYear, viewMonth)

  return (
    <div ref={wrapRef} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          'w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-left text-slate-900 shadow-sm transition placeholder:text-slate-400',
          'focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/20',
          !value && 'text-slate-400'
        )}
      >
        {value ? formatDisplay(value) : placeholder}
      </button>

      {open && (
        <div className="absolute left-0 z-50 mt-1 w-full min-w-[280px] max-w-[320px] rounded-xl border border-slate-200 bg-white p-3 shadow-lg">
          <div className="mb-3 flex items-center justify-between">
            <button
              type="button"
              onClick={goPrev}
              disabled={!canPrev}
              className="rounded p-1 text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:pointer-events-none"
              aria-label="Предыдущий месяц"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span className="text-sm font-medium text-slate-800">
              {MONTHS_RU[viewMonth]} {viewYear}
            </span>
            <button
              type="button"
              onClick={goNext}
              disabled={!canNext}
              className="rounded p-1 text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:pointer-events-none"
              aria-label="Следующий месяц"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-7 gap-0.5 text-center text-sm">
            {WEEKDAYS_RU.map((wd) => (
              <div key={wd} className="py-1 text-xs font-medium text-slate-500">
                {wd}
              </div>
            ))}
            {grid.map((iso, i) => {
              if (!iso) {
                return <div key={`e-${i}`} />
              }
              const isBeforeMin = iso < min
              const isAfterMax = iso > max
              const disabled = isBeforeMin || isAfterMax
              const isSelected = value === iso
              return (
                <button
                  key={iso}
                  type="button"
                  disabled={disabled}
                  onClick={() => {
                    if (!disabled) {
                      onChange(iso)
                      setOpen(false)
                    }
                  }}
                  className={cn(
                    'rounded py-1.5 transition',
                    disabled && 'cursor-not-allowed text-slate-300',
                    isAfterMax && 'bg-slate-100 text-slate-400',
                    isBeforeMin && 'text-slate-300',
                    !disabled && 'hover:bg-slate-100 text-slate-800',
                    isSelected && !disabled && 'bg-green-500 text-white hover:bg-green-600'
                  )}
                >
                  {parseInt(iso.slice(8, 10), 10)}
                </button>
              )
            })}
          </div>
        </div>
      )}

    </div>
  )
}

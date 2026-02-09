import { Baby, Cigarette, Dog, Package, Users2 } from 'lucide-react'
import type { Trip } from '@/api/types'

interface TripOptionIconsProps {
  trip: Trip
  className?: string
  iconClassName?: string
}

/** Иконки опций поездки без подписей (для карточек в поиске и профиле) */
export function TripOptionIcons({ trip, className = '', iconClassName = 'h-4 w-4 text-slate-500' }: TripOptionIconsProps) {
  const hasAny =
    trip.smoking_allowed ||
    trip.pets_allowed ||
    trip.child_seat_available ||
    trip.two_rear_seats ||
    trip.parcel_allowed
  if (!hasAny) return null

  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${className}`} aria-hidden>
      {trip.smoking_allowed && (
        <span title="Остановки на перекур">
          <Cigarette className={iconClassName} />
        </span>
      )}
      {trip.pets_allowed && (
        <span title="Можно с животными">
          <Dog className={iconClassName} />
        </span>
      )}
      {trip.child_seat_available && (
        <span title="Детское кресло">
          <Baby className={iconClassName} />
        </span>
      )}
      {trip.two_rear_seats && (
        <span title="2 места сзади">
          <Users2 className={iconClassName} />
        </span>
      )}
      {trip.parcel_allowed && (
        <span title="Перевозка посылок">
          <Package className={iconClassName} />
        </span>
      )}
    </div>
  )
}

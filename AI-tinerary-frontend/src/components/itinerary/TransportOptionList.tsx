/**
 * @file TransportOptionList.tsx
 * @description Compact list of transport options between two itinerary activities.
 */

import { Car, Footprints, TramFront, Bike } from 'lucide-react'
import type { TransportOption } from '../../types/trip'

interface TransportOptionListProps {
  /** Transport options for the leg between activities. */
  options: TransportOption[]
}

/**
 * Horizontal pill-style list of travel options (walk, taxi, transit, etc.).
 */
export function TransportOptionList({ options }: TransportOptionListProps) {
  const iconForMode = (mode: TransportOption['mode']) => {
    switch (mode) {
      case 'walk':
        return Footprints
      case 'bike':
        return Bike
      case 'transit':
        return TramFront
      case 'taxi':
      default:
        return Car
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const Icon = iconForMode(option.mode)
        return (
          <div
            key={option.id}
            className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] text-emerald-900/90 ring-1 ring-emerald-100"
          >
            <Icon className="h-3 w-3" />
            <span>{option.label}</span>
            <span className="text-emerald-700/90">
              · {option.durationMinutes} min
            </span>
            <span className="text-emerald-700/80">· {option.priceText}</span>
          </div>
        )
      })}
    </div>
  )
}

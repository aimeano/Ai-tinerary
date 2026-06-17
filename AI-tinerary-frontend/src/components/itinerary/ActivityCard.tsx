/**
 * @file ActivityCard.tsx
 * @description Card representing a single activity within a generated itinerary day,
 *              including nearby restaurant suggestions and travel-from-previous details.
 */

import { Car, Clock, Footprints, TramFront } from 'lucide-react'
import type {
  GeneratedItineraryActivity,
  GeneratedTravelFromPrevious,
} from '../../types/itinerary'

interface ActivityCardProps {
  /** Activity data to display inside the day timeline. */
  activity: GeneratedItineraryActivity
}

/**
 * Resolve visual style (badge color + icon) for an activity category.
 */
function getCategoryVisuals(category: string) {
  const normalized = category.toLowerCase()

  if (normalized.includes('restaurant') || normalized.includes('food')) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '🍜',
    }
  }

  if (normalized.includes('park') || normalized.includes('nature')) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '🌳',
    }
  }

  if (normalized.includes('museum') || normalized.includes('gallery')) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '🏛️',
    }
  }

  if (normalized.includes('shopping') || normalized.includes('mall')) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '🛍️',
    }
  }

  if (
    normalized.includes('religious') ||
    normalized.includes('temple') ||
    normalized.includes('mosque') ||
    normalized.includes('church')
  ) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '🕌',
    }
  }

  if (normalized.includes('airport') || normalized.includes('flight')) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '✈️',
    }
  }

  if (normalized.includes('travel') || normalized.includes('route')) {
    return {
      badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
      icon: '🧭',
    }
  }

  return {
    badgeClass: 'bg-[#DBEAFE] text-[#1D4ED8] ring-1 ring-[#93C5FD]',
    icon: '📍',
  }
}

/**
 * Check whether the activity has any travel-from-previous information.
 */
function hasTravelInfo(travel?: GeneratedTravelFromPrevious | null) {
  if (!travel) return false
  return Boolean(travel.driving || travel.walking || travel.transit)
}

/**
 * Visual representation of a single generated activity within the itinerary.
 * Layout:
 * - Left column: category chip at top, time chip below.
 * - Main content: title + right-aligned location on the first row, description below.
 * - Divider and nearby places remain unchanged.
 */
export function ActivityCard({ activity }: ActivityCardProps) {
  const { badgeClass, icon } = getCategoryVisuals(activity.category || '')
  const hasNearby =
    activity.nearby_restaurants && activity.nearby_restaurants.length > 0
  const hasTravel = hasTravelInfo(activity.travel_from_previous)

  return (
    <div className="rounded-2xl bg-white p-4 shadow-[0_8px_20px_rgba(1,89,250,0.06)] ring-1 ring-[#93C5FD]">
      <div className="flex items-start gap-3">
        {/* Leading pictogram bubble */}
        <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#0159FA] to-[#1458DD] text-sm text-white shadow-sm">
          {icon}
        </div>

        {/* Two-column layout: left meta (category + time), right main content */}
        <div className="flex-1 flex gap-4">
          {/* Left sidebar: category chip and time chip stacked vertically */}
          <div className="flex flex-col items-start gap-2 pt-0.5">
            {activity.category && (
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${badgeClass}`}
              >
                {activity.category}
              </span>
            )}

            {activity.time && (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-[#475569] ring-1 ring-[#BFDBFE]">
                <Clock className="h-3 w-3" />
                {activity.time}
              </span>
            )}
          </div>

          {/* Main content area */}
          <div className="flex-1 space-y-1">
            {/* Header row: title on the left, location on the right */}
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-semibold text-[#0F172A]">
                {activity.title}
              </h4>

              {activity.location_name &&
                activity.location_name.trim().length > 0 && (
                  <p className="ml-auto inline-flex items-center gap-1 whitespace-nowrap text-xs font-medium text-[#475569]">
                    <span aria-hidden="true">📍</span>
                    <span>{activity.location_name}</span>
                  </p>
                )}
            </div>

            {activity.description && activity.description.trim().length > 0 && (
              <p className="text-sm text-[#475569]">
                {activity.description}
              </p>
            )}
          </div>
        </div>
      </div>

      {hasTravel && activity.travel_from_previous && (
        <div className="mt-3 rounded-xl bg-[#EFF6FF] px-3 py-2 ring-1 ring-[#BFDBFE]">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#1D4ED8]">
            Travel from previous activity
          </p>
          <div className="flex flex-wrap gap-1.5 text-[11px] text-[#0F172A]">
            {activity.travel_from_previous.driving && (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 ring-1 ring-[#BFDBFE]">
                <Car className="h-3 w-3 text-[#0F172A]" />
                <span>Driving</span>
                <span className="text-[#475569]">
                  · {activity.travel_from_previous.driving.distance}
                </span>
                <span className="text-[#475569]">
                  · {activity.travel_from_previous.driving.duration}
                </span>
              </span>
            )}
            {activity.travel_from_previous.walking && (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 ring-1 ring-[#BFDBFE]">
                <Footprints className="h-3 w-3 text-[#0F172A]" />
                <span>Walking</span>
                <span className="text-[#475569]">
                  · {activity.travel_from_previous.walking.distance}
                </span>
                <span className="text-[#475569]">
                  · {activity.travel_from_previous.walking.duration}
                </span>
              </span>
            )}
            {activity.travel_from_previous.transit && (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 ring-1 ring-[#BFDBFE]">
                <TramFront className="h-3 w-3 text-[#0F172A]" />
                <span>Transit</span>
                <span className="text-[#475569]">
                  · {activity.travel_from_previous.transit.distance}
                </span>
                <span className="text-[#475569]">
                  · {activity.travel_from_previous.transit.duration}
                </span>
              </span>
            )}
          </div>
        </div>
      )}

      {hasNearby && (
        <div className="mt-3 border-t border-dashed border-[#BFDBFE] pt-3">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#1D4ED8]">
            Nearby places to eat
          </p>

          {/* Nearby restaurant chips remain visually consistent with the original design. */}
          <div className="flex flex-wrap gap-2">
            {activity.nearby_restaurants.map((place, index) => (
              <a
                key={`${place.name}-${index}`}
                href={place.link || '#'}
                target={place.link ? '_blank' : undefined}
                rel={place.link ? 'noreferrer' : undefined}
                role="link"
                aria-label={`Open ${place.name}`}
                title={place.name}
                className="inline-flex max-w-[240px] items-center overflow-hidden whitespace-nowrap rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-1 text-[12px] font-medium text-[#1D4ED8] shadow-sm transition-colors hover:bg-[#DBEAFE] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-[#1D4ED8]"
              >
                <span className="truncate">{place.name}</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
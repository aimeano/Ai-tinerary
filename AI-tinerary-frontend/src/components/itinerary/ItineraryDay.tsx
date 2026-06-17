/**
 * @file ItineraryDay.tsx
 * @description Merged component rendering a single itinerary day card.
 *              Includes:
 *              - Weather summaries & recommendations from real backend data
 *              - Interactive "Adjust day itinerary for rain" flow with undo capability
 *              - Event listeners for real-time local updates and syncing
 *              - Timeline activities with tags and "Nearby places to eat" chips
 */

import { format } from "date-fns";
import { CalendarDays, RefreshCw } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import type {
  GeneratedItineraryDay,
  GeneratedItineraryActivity,
  GeneratedTripProfileMeta,
} from "../../types/itinerary";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type WeatherVariant =
  | "sunny"
  | "cloudy"
  | "rainy"
  | "drizzle"
  | "thunderstorm"
  | "fog"
  | "snow"
  | "unknown";

interface DayWeatherInfo {
  variant: WeatherVariant;
  emoji: string;
  temperature: string;
  title: string;
  advice: string;
}

interface DisplayActivity extends GeneratedItineraryActivity {
  time?: string | null;
  title?: string | null;
  location_name?: string | null;
  category?: string | null;
  description?: string | null;
  nearby_restaurants?: {
    name: string;
    link?: string | null;
  }[];
  /** Weather object attached by the backend weather_enrichment pipeline */
  weather?: {
    weather_category?: string | null;
    weather_description?: string | null;
    temperature_avg?: number | null;
    temperature_max?: number | null;
    temperature_min?: number | null;
    is_bad_weather?: boolean;
    suggestion?: string | null;
  } | null;
}

// ---------------------------------------------------------------------------
// Weather helpers
// ---------------------------------------------------------------------------

/**
 * Map a backend `weather_category` string to a WeatherVariant used for
 * emoji / advice selection.
 */
function categoryToVariant(
  category: string | null | undefined,
): WeatherVariant {
  switch (category) {
    case "clear":
    case "partly_cloudy":
      return category === "clear" ? "sunny" : "cloudy";
    case "drizzle":
      return "drizzle";
    case "rain":
    case "rain_showers":
      return "rainy";
    case "thunderstorm":
      return "thunderstorm";
    case "fog":
      return "fog";
    case "snow":
    case "snow_showers":
      return "snow";
    default:
      return "unknown";
  }
}

/** Emoji map for each WeatherVariant */
const WEATHER_EMOJI: Record<WeatherVariant, string> = {
  sunny: "☀️",
  cloudy: "⛅",
  rainy: "🌧️",
  drizzle: "🌦️",
  thunderstorm: "⛈️",
  fog: "🌫️",
  snow: "❄️",
  unknown: "🌡️",
};

/** Packing / clothing advice per variant */
const WEATHER_ADVICE: Record<WeatherVariant, string> = {
  sunny: "Light, breathable clothes, sunglasses, sunscreen, and a hat.",
  cloudy: "Comfortable clothes; carry a light layer for cooler indoor AC.",
  rainy: "Quick-dry outfit, compact umbrella or light rain jacket, sandals.",
  drizzle: "Quick-dry outfit, compact umbrella or light rain jacket, sandals.",
  thunderstorm:
    "Stay indoors where possible; carry a rain jacket and sturdy footwear.",
  fog: "Drive carefully; carry a light jacket for reduced visibility conditions.",
  snow: "Warm layers, waterproof boots, and a heavy coat.",
  unknown: "Check local forecasts and dress accordingly.",
};

/**
 * Derive DayWeatherInfo from real backend weather data attached to the first
 * activity of the day. Falls back to the deterministic mock if no data exists.
 *
 * Priority:
 *  1. First activity's `weather` field (real backend data)
 *  2. Deterministic mock based on day index (legacy fallback)
 */
function getDayWeatherInfo(day: GeneratedItineraryDay): DayWeatherInfo {
  // --- Attempt to read real weather from the first activity ---
  const activities = Array.isArray((day as any).activities)
    ? ((day as any).activities as DisplayActivity[])
    : [];

  const firstWeather = activities.find(
    (a) => a.weather?.weather_category,
  )?.weather;

  if (firstWeather?.weather_category) {
    const variant = categoryToVariant(firstWeather.weather_category);
    const emoji = WEATHER_EMOJI[variant];
    const advice = WEATHER_ADVICE[variant];

    // Prefer temperature_avg; fall back to max or min
    const tempRaw =
      firstWeather.temperature_avg ??
      firstWeather.temperature_max ??
      firstWeather.temperature_min;

    const temperature = tempRaw != null ? `${Math.round(tempRaw)}°C` : "--°C";

    // Use the human-readable description from the backend (e.g. "Moderate rain")
    const title = firstWeather.weather_description ?? variant;

    return { variant, emoji, temperature, title, advice };
  }

  // --- Legacy deterministic mock (fallback) ---
  const index = (day.day ?? 0) % 3;

  if (index === 0) {
    return {
      variant: "sunny",
      emoji: "☀️",
      temperature: "31°C",
      title: "Sunny & warm",
      advice: "Light, breathable clothes, sunglasses, sunscreen, and a hat.",
    };
  }

  if (index === 1) {
    return {
      variant: "cloudy",
      emoji: "⛅",
      temperature: "29°C",
      title: "Partly cloudy",
      advice: "Comfortable clothes; carry a light layer for cooler indoor AC.",
    };
  }

  return {
    variant: "rainy",
    emoji: "🌧️",
    temperature: "28°C",
    title: "Humid with showers",
    advice: "Quick-dry outfit, compact umbrella or light rain jacket, sandals.",
  };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface DayWeatherBadgeProps {
  day: GeneratedItineraryDay;
}

/**
 * DayWeatherBadge
 * Compact pill displaying emoji, temperature_avg and weather description.
 * Shape is unchanged from the original design.
 */
function DayWeatherBadge({ day }: DayWeatherBadgeProps) {
  const info = getDayWeatherInfo(day);

  return (
    <div className="inline-flex items-center gap-3 rounded-lg bg-[#DBEAFE] px-3 py-1 text-[12px] text-[#0F172A] shadow-sm ring-1 ring-[#93C5FD]">
      <div className="flex items-center gap-2">
        <span aria-hidden="true" className="text-lg leading-none">
          {info.emoji}
        </span>
        <div className="flex flex-col">
          {/* temperature_avg shown here */}
          <span className="font-medium text-[#0F172A]">{info.temperature}</span>
          {/* weather_description shown here */}
          <span className="text-[11px] text-[#475569]">{info.title}</span>
        </div>
      </div>
    </div>
  );
}

interface NearbyRestaurantsRowProps {
  restaurants: { name: string; link?: string | null }[];
}

function NearbyRestaurantsRow({ restaurants }: NearbyRestaurantsRowProps) {
  if (!restaurants || restaurants.length === 0) return null;

  return (
    <div className="mt-3 border-t border-dashed border-[#BFDBFE] pt-3">
      <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-[#1D4ED8]">
        Nearby places to eat 🍝
      </p>
      <div className="flex flex-wrap gap-2">
        {restaurants.map((place, index) => (
          <a
            key={`${place.name}-${index}`}
            href={place.link || "#"}
            target={place.link ? "_blank" : undefined}
            rel={place.link ? "noreferrer" : undefined}
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
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export interface ItineraryDayProps {
  day: GeneratedItineraryDay;
  tripId?: string | null;
  preferences?: GeneratedTripProfileMeta | null;
  index?: number;
  dayIndex?: number;
}

export function ItineraryDay({
  day,
  tripId,
  preferences,
  index,
  dayIndex,
}: ItineraryDayProps) {
  const [localDay, setLocalDay] = useState<GeneratedItineraryDay>(day);
  const [isUpdated, setIsUpdated] = useState(false);
  const [isAdjusting, setIsAdjusting] = useState(false);

  const effectiveIndex = index ?? dayIndex;
  const dayNumber =
    localDay.day ??
    (typeof effectiveIndex === "number" ? effectiveIndex + 1 : undefined);

  const activities: DisplayActivity[] = Array.isArray(
    (localDay as any).activities,
  )
    ? ((localDay as any).activities as DisplayActivity[])
    : [];

  // weatherInfo now uses real data via getDayWeatherInfo
  const weatherInfo = getDayWeatherInfo(localDay);
  const rainy =
    weatherInfo.variant === "rainy" ||
    weatherInfo.variant === "drizzle" ||
    weatherInfo.variant === "thunderstorm";

  const daySummary = useMemo(() => {
    const stops = activities.length;
    const hasManyOutdoor = activities.filter((a) =>
      ["tourist_attraction", "park", "route"].includes(a.category ?? ""),
    ).length;

    if (isUpdated) {
      return `${Math.max(1, stops)} stops · Rain-safe · Shorter walking`;
    }
    if (rainy) {
      return `${Math.max(1, stops)} stops · Moderate walking · Outdoor-heavy`;
    }
    return `${Math.max(1, stops)} stops · Moderate walking · ${hasManyOutdoor > 1 ? "Outdoor-heavy" : "Balanced"}`;
  }, [activities.length, isUpdated, rainy]);

  function categoryLabel(cat?: string | null) {
    if (!cat) return "Other";
    const map: Record<string, string> = {
      food: "Food",
      museum: "Museum",
      tourist_attraction: "Landmark",
      route: "Covered route",
      park: "Park",
      airport: "Travel",
      travel: "Travel",
      restaurant: "Restaurant",
      "covered route": "Covered route",
    };
    return map[cat.toLowerCase()] ?? cat.charAt(0).toUpperCase() + cat.slice(1);
  }

  const historyRef = React.useRef<GeneratedItineraryDay[]>([]);

  useEffect(() => {
    function handleUpdate(e: Event) {
      const ev = e as CustomEvent;
      const updatedDay = ev.detail?.day as GeneratedItineraryDay | undefined;
      if (!updatedDay) return;
      if (updatedDay.day !== localDay.day) return;

      try {
        const prev = JSON.parse(
          JSON.stringify(localDay),
        ) as GeneratedItineraryDay;
        historyRef.current.push(prev);
      } catch {
        // Safe fallback
      }

      setLocalDay((prev) => ({ ...prev, ...updatedDay }));
      setIsUpdated(true);
      setIsAdjusting(false);
    }

    window.addEventListener(
      "itinerary-day-updated",
      handleUpdate as EventListener,
    );
    return () => {
      window.removeEventListener(
        "itinerary-day-updated",
        handleUpdate as EventListener,
      );
    };
  }, [localDay.day, localDay]);

  function getDateLabel(value?: string | null): string | null {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    return format(parsed, "EEE, dd MMM yyyy");
  }

  const dateLabel = getDateLabel(localDay.date);

  function handleRainyDayAdjust(selectedDay: GeneratedItineraryDay) {
    if (!tripId) return;
    setIsAdjusting(true);

    const message = `Adjust Day ${selectedDay.day} itinerary for ${selectedDay.weather?.condition ?? weatherInfo.title}. Please suggest indoor or weather-safe alternatives, shorten walking distances if possible, and preserve user preferences.`;

    const payload = {
      action: "ADJUST_DAY_FOR_RAIN",
      tripId,
      dayNumber: selectedDay.day,
      weatherCondition: selectedDay.weather?.condition ?? weatherInfo.variant,
      temperature: selectedDay.weather?.temperature ?? weatherInfo.temperature,
      weatherRecommendation:
        selectedDay.weather?.recommendation ?? weatherInfo.advice,
      itineraryItems: selectedDay.activities ?? activities,
      message,
      date: selectedDay.date ?? null,
      title: selectedDay.title ?? null,
      preferences: preferences ?? null,
    };

    const ev = new CustomEvent("ai-send-structured", { detail: payload });
    window.dispatchEvent(ev);
  }

  return (
    <section className="rounded-2xl bg-white p-6 shadow-[0_10px_30px_rgba(1,89,250,0.06)] ring-1 ring-[#93C5FD]">
      {/* Header */}
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="h-12 w-12 flex-shrink-0 overflow-hidden rounded-md bg-[#EFF6FF] ring-1 ring-[#BFDBFE]">
            <img
              src="https://pub-cdn.sider.ai/u/U04XHG42AO5/web-coder/6a0b2977a419c8a510478fe3/resource/3ff83e34-f977-4d69-90fd-fefc11632408.jpg"
              alt={`Day ${dayNumber ?? ""} thumbnail`}
              className="h-full w-full object-cover"
            />
          </div>

          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#DBEAFE] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#1D4ED8] ring-1 ring-[#93C5FD]">
              <CalendarDays
                className="h-3 w-3 text-[#1D4ED8]"
                aria-hidden="true"
              />
              <span className="text-[#1D4ED8]">
                Day {dayNumber}
                {dateLabel ? ` · ${dateLabel}` : ""}
              </span>
            </div>

            <h3 className="text-base font-semibold text-[#0F172A]">
              {localDay.title || `Exploring Day ${dayNumber}`}
            </h3>

            {localDay.summary && (
              <p className="text-sm text-[#475569]">{localDay.summary}</p>
            )}
            <p className="mt-1 text-sm text-[#475569] font-medium">
              {daySummary}
            </p>
          </div>
        </div>

        {/* Weather badge + rainy actions */}
        <div className="flex flex-col items-end gap-3">
          <div className="flex flex-col items-end gap-2">
            {/* ← DayWeatherBadge now shows real temperature_avg + weather_description */}
            <DayWeatherBadge day={localDay} />
            {rainy && (
              <span className="text-[12px] text-[#1D4ED8] italic">
                AI recommends an alternative plan.
              </span>
            )}
          </div>

          {rainy && tripId && (
            <div className="flex flex-col items-end gap-2">
              <button
                type="button"
                title="Ask the assistant to adjust this day's plan for rain"
                onClick={() => handleRainyDayAdjust(localDay)}
                className="inline-flex items-center gap-2 rounded-full bg-[#0159FA] px-3 py-1.5 text-sm font-medium text-white shadow-lg shadow-[rgba(1,89,250,0.25)] hover:bg-[#1458DD] disabled:opacity-60"
                disabled={isAdjusting}
              >
                <RefreshCw className="h-4 w-4 text-white" />
                <span className="text-sm">
                  {isAdjusting ? "Planning..." : "Adjust day itinerary"}
                </span>
              </button>

              {historyRef.current.length > 0 && (
                <button
                  onClick={() => {
                    const prev = historyRef.current.pop();
                    if (!prev) return;

                    setLocalDay(prev);
                    setIsAdjusting(false);
                    setIsUpdated(historyRef.current.length > 0);

                    window.dispatchEvent(
                      new CustomEvent("itinerary-day-updated", {
                        detail: { day: prev },
                      }),
                    );

                    const payload = {
                      action: "UNDO_LAST_DAY_CHANGE",
                      tripId,
                      dayNumber: prev.day,
                      message: `Undo the last itinerary change for Day ${prev.day}.`,
                    };
                    window.dispatchEvent(
                      new CustomEvent("ai-send-structured", {
                        detail: payload,
                      }),
                    );
                  }}
                  className="inline-flex items-center gap-2 rounded-full bg-[#DBEAFE] text-[#1D4ED8] border border-[#93C5FD] px-3 py-1.5 text-sm font-medium shadow-sm hover:bg-[#EFF6FF]"
                >
                  Undo last change
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Activity Timeline */}
      {activities.length > 0 && (
        <div className="mt-6 space-y-4">
          {activities.map((activity, index) => {
            const hasNearby =
              activity.nearby_restaurants &&
              activity.nearby_restaurants.length > 0;
            const locationName = (activity.location_name || "").trim();
            let activityMapUrl: string | null = null;

            if (locationName) {
              const explicitUrl =
                (activity as any).googleMapsUrl ??
                (activity as any).google_maps_url ??
                (activity as any).maps_url ??
                (activity as any).map_url ??
                (activity as any).location_url ??
                (activity as any).url;

              if (typeof explicitUrl === "string" && explicitUrl.length > 0) {
                activityMapUrl = explicitUrl;
              } else {
                const lat = (activity as any).latitude;
                const lng = (activity as any).longitude;

                if (typeof lat === "number" && typeof lng === "number") {
                  activityMapUrl = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
                } else {
                  const queryParts: string[] = [locationName];
                  if (preferences?.cities && preferences.cities.length > 0) {
                    queryParts.push(preferences.cities[0]);
                  }
                  if (preferences?.country) {
                    queryParts.push(preferences.country);
                  }
                  const query = encodeURIComponent(queryParts.join(", "));
                  activityMapUrl = `https://www.google.com/maps/search/?api=1&query=${query}`;
                }
              }
            }

            return (
              <div
                key={`${activity.time ?? "time"}-${activity.title ?? index}`}
                className="rounded-lg border border-[#BFDBFE] bg-white px-5 py-4 shadow-sm"
              >
                <div className="grid grid-cols-[96px_minmax(0,1fr)] gap-4">
                  {/* Left column: category chip + time */}
                  <div className="flex flex-col items-start gap-2 pt-0.5">
                    <span className="inline-flex items-center rounded-full bg-[#DBEAFE] px-2 py-0.5 text-[12px] font-medium text-[#1D4ED8] ring-1 ring-[#93C5FD]">
                      {categoryLabel(activity.category)}
                    </span>
                    <span className="text-[15px] font-semibold text-[#0F172A]">
                      {activity.time || "--:--"}
                    </span>
                  </div>

                  {/* Main content column */}
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-start gap-2">
                      <p className="min-w-0 flex-1 text-sm font-semibold text-[#0F172A]">
                        {activity.title || "Activity"}
                      </p>

                      {locationName && activityMapUrl && (
                        <a
                          href={activityMapUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-auto inline-flex shrink-0 items-center gap-1 text-sm font-medium text-[#475569] whitespace-nowrap hover:text-[#1D4ED8] hover:underline"
                          aria-label={`Open ${locationName} in Google Maps`}
                          title={`Open ${locationName} in Google Maps`}
                        >
                          <span aria-hidden="true">📍</span>
                          <span className="truncate">{locationName}</span>
                        </a>
                      )}
                    </div>

                    {activity.description && (
                      <p className="mt-1 text-sm text-[#475569]">
                        {activity.description}
                      </p>
                    )}

                    {hasNearby && (
                      <NearbyRestaurantsRow
                        restaurants={activity.nearby_restaurants!}
                      />
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default ItineraryDay;

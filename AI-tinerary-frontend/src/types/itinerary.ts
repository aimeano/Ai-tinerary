/**
 * @file itinerary.ts
 * @description TypeScript types describing the generated itinerary payload returned from the backend.
 *              The shapes are aligned with the JSON stored in trips_database.db (see generated_itinerary.txt).
 */

/**
 * Trip-level profile metadata for a generated itinerary.
 * This may include additional planning context used by the AI.
 */
export interface GeneratedTripProfileMeta {
  country?: string;
  cities?: string[];
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  travel_style?: string;
  interests?: string[];
  budget?: string;
  must_include?: string[];
  flights?: any[];
}

export interface GeneratedTripProfile {
  country?: string;
  cities?: string[];
  start_date?: string;
  end_date?: string;
  days?: number;
  duration_days?: number;
  travel_style?: string;
  interests?: string[];
  budget?: string;
  must_include?: string[];
  flights?: any[];
  retrieval_locations?: string[];
}
/**
 * Nearby restaurant or place to eat associated with an activity.
 */
export interface GeneratedNearbyRestaurant {
  /** Display name of the restaurant or eatery. */
  name: string;
  /** Optional deep-link URL (e.g. Google Maps). */
  link?: string;
}

/**
 * Category label as returned by the backend for an activity.
 * Examples: "Landmark", "Museum", "Park", "Shopping", "Religious Site", "Restaurant".
 */
export type GeneratedActivityCategory = string;

/**
 * Transport leg information between two activities for a single mode.
 */
export interface GeneratedTransportLeg {
  /** Human-readable distance, e.g. "3.4 km". */
  distance: string;
  /** Human-readable duration, e.g. "12 mins". */
  duration: string;
  /** Duration in seconds, used for calculations if needed. */
  duration_seconds: number;
}

/**
 * Transport options between the previous activity and the current one.
 * All fields are optional and may be null depending on availability.
 */
export interface GeneratedTravelFromPrevious {
  /** Optional driving information between activities. */
  driving?: GeneratedTransportLeg | null;
  /** Optional walking information between activities. */
  walking?: GeneratedTransportLeg | null;
  /** Optional public transit information between activities. */
  transit?: GeneratedTransportLeg | null;
}

/**
 * Single activity within a day of the generated itinerary.
 */
export interface GeneratedItineraryActivity {
  /** Start time (24h format) such as "09:00". */
  time: string;
  /** Title of the activity, e.g. "Visit KL Tower". */
  title: string;
  /** Human-readable location name. Can be empty in transit/airport steps. */
  location_name: string;
  /** Latitude for map integrations (may be null if unknown). */
  latitude: number | null;
  /** Longitude for map integrations (may be null if unknown). */
  longitude: number | null;
  /** Category label from the backend. */
  category: GeneratedActivityCategory;
  /** Optional description or additional details. */
  description: string;
  /** Nearby suggested restaurants for this activity. */
  nearby_restaurants: GeneratedNearbyRestaurant[];
  /** Optional travel summary from the previous activity to this one. */
  travel_from_previous?: GeneratedTravelFromPrevious | null;
  /** Optional backend warning, e.g. unresolved locations. */
  _warning?: string;
}

/**
 * Single day of the generated itinerary.
 */
export interface GeneratedItineraryDay {
  /** 1-based day index within the trip. */
  day: number;
  /** Optional ISO date string for this day, e.g. "2026-08-01". */
  date?: string | null;
  /** Headline/title for the day, describing its theme. */
  title: string;
  /** Optional day-level summary text. */
  summary: string;
  /** Ordered list of activities planned for the day. */
  activities: GeneratedItineraryActivity[];
}

/**
 * Root payload returned by the itinerary generator backend.
 */
export interface GeneratedItinerary {
  trip_id?: string;
  title?: string;
  /** ✅ NEW: Root-level profile from backend */
  profile?: GeneratedTripProfileMeta;
  /** Trip-level metadata (for backward compatibility) */
  trip: GeneratedTripProfileMeta;
  /** Ordered collection of days and activities. */
  days?: GeneratedItineraryDay[];
  itinerary?: {
    days: GeneratedItineraryDay[];
  };
  itinerary_version?: number;
  chat_history?: any[];
  created_at?: string;
  updated_at?: string;
}

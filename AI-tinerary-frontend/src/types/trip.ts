/**
 * @file trip.ts
 * @description Shared TypeScript types for trips, itinerary structure, and preferences.
 */

/**
 * Supported travel style categories used across the app.
 */
export type TravelStyle =
  | "relaxed"
  | "adventurous"
  | "honeymoon"
  | "friends"
  | "family & kids";

/**
 * User preference profile captured from the new trip form.
 */
export interface TripPreferences {
  country: string;
  cities: string[];
  days: number;
  budget: number;
  budgetCurrency: string;
  travelStyle: TravelStyle;
  interests: string[];
  notes?: string;
  startDate?: string;
}

/**
 * High-level summary of a saved trip for listing on the dashboard.
 */
export interface TripSummary {
  trip_id: string; // ✅ Changed from 'id' to 'trip_id'
  title: string;
  profile: {
    country: string;
    cities: string[];
    start_date?: string;
    end_date?: string;
    days?: number;
    travel_style?: string;
    interests?: string[];
    budget?: string;
    must_include?: string[];
  };
  created_at?: string;
  updated_at?: string;
  itinerary_version?: number;
}

/**
 * Transport option between two activities.
 */
export interface TransportOption {
  id: string;
  mode: "walk" | "bike" | "transit" | "taxi";
  label: string;
  durationMinutes: number;
  priceText: string;
}

/**
 * Single activity or card inside a day.
 */
export interface ItineraryActivity {
  id: string;
  category: "sightseeing" | "food" | "shopping" | "transport" | "other";
  startTime?: string;
  title: string;
  subtitle?: string;
  description?: string;
  whyThisFits?: string;
  transportFromPrevious?: TransportOption[];
}

/**
 * Representation of a single day in the itinerary.
 */
export interface ItineraryDay {
  dayNumber: number;
  dateLabel?: string;
  title?: string;
  activities: ItineraryActivity[];
}

/**
 * Full trip detail, including the generated itinerary.
 */
export interface TripDetail extends TripSummary {
  preferences: TripPreferences;
  days: ItineraryDay[];
}

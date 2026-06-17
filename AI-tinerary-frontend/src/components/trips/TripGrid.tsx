/**
 * @file TripGrid.tsx
 * @description Responsive grid for listing multiple trips.
 */

import type { TripSummary } from "../../types/trip";
import { TripCard } from "./TripCard";

interface TripGridProps {
  /** Collection of trips to show on the dashboard. */
  trips: TripSummary[];
}

/**
 * Grid layout mapping trip summaries to individual cards.
 */
export function TripGrid({ trips }: TripGridProps) {
  if (!trips.length) {
    return (
      <div className="rounded-2xl border border-dashed border-sky-100 bg-sky-50/60 px-6 py-10 text-center text-sm text-slate-700">
        You do not have any trips yet. Click &quot;New Trip&quot; to create your
        first AI-crafted itinerary.
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {trips.map((trip) => (
        <TripCard key={trip.trip_id} trip={trip} />
      ))}
    </div>
  );
}

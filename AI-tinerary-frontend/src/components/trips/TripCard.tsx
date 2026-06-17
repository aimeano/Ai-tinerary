/**
 * @file TripCard.tsx
 * @description Card component used to display a single trip on the dashboard.
 */

import { CalendarDays, Clock } from "lucide-react";
import { Link } from "react-router";
import type { TripSummary } from "../../types/trip";

interface TripCardProps {
  /** Trip summary data for the card. */
  trip: TripSummary;
}

/**
 * getFlagForCountry
 * Returns a small flag image URL and alt text for supported countries.
 *
 * @param country - Country name from the trip summary.
 */
function getFlagForCountry(
  country?: string,
): { src: string; alt: string } | null {
  if (!country) return null;
  const c = country.toLowerCase();
  if (c.includes("malaysia")) {
    return { src: "https://flagcdn.com/w80/my.png", alt: "Malaysia flag" };
  }
  if (c.includes("indonesia")) {
    return { src: "https://flagcdn.com/w80/id.png", alt: "Indonesia flag" };
  }
  return null;
}

/**
 * Visual card summarizing a saved or generating trip.
 * Styled to closely match the provided design: soft blue border, rectangular
 * country flag with rounded corners, and a subtle "Ready" status pill.
 */
export function TripCard({ trip }: TripCardProps) {
  const flag = getFlagForCountry(trip.profile.country);

  // ✅ Extract primary city from profile.cities array
  const primaryCity = trip.profile.cities?.[0] || "Unknown";
  const country = trip.profile.country || "Unknown";
  const startDate = trip.profile.start_date || "";
  const endDate = trip.profile.end_date || "";
  const dayCount = trip.profile.days || 0;

  return (
    <Link
      to={`/trip/${trip.trip_id}`} // ✅ Changed from trip.id
      className="relative flex flex-col rounded-3xl border border-[#BFDBFE] bg-white px-5 py-4 shadow-[0_14px_40px_rgba(148,163,184,0.16)] transition hover:-translate-y-0.5 hover:shadow-[0_18px_50px_rgba(148,163,184,0.22)]"
    >
      <div className="mb-3 flex items-center gap-4">
        {flag ? (
          <div className="flex h-9 w-12 items-center justify-center overflow-hidden rounded-md border-[2.5px] border-[#2563EB] bg-white shadow-sm">
            <img
              src={flag.src}
              alt={flag.alt}
              className="h-full w-full object-cover"
            />
          </div>
        ) : (
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EFF6FF] text-lg">
            <span>🌍</span>
          </div>
        )}

        <div className="flex flex-col">
          <p className="text-sm font-semibold text-[#0F172A]">{primaryCity}</p>
          <p className="text-xs text-[#6B7280]">{country}</p>
        </div>
      </div>

      <div className="mt-auto space-y-1 text-xs text-[#4B5563]">
        {startDate && endDate && (
          <p className="flex items-center gap-1">
            <CalendarDays className="h-3 w-3 text-[#2563EB]" />
            <span>
              {startDate} – {endDate}
            </span>
          </p>
        )}
        <p className="flex items-center gap-1">
          <Clock className="h-3 w-3 text-[#2563EB]" />
          <span>{dayCount} days</span>
        </p>
      </div>

      <p className="absolute bottom-4 right-5 flex items-center rounded-full border border-[#93C5FD] bg-[#EFF6FF] px-3 py-1 text-[12px] font-semibold text-[#2563EB]">
        Ready
      </p>
    </Link>
  );
}

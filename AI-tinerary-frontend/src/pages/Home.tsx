/**
 * src/pages/Home.tsx
 * @file Home.tsx
 * @description Dashboard page showing existing trips from FastAPI backend
 */

import { Link } from "react-router";
import { TripGrid } from "../components/trips/TripGrid";
import type { TripSummary } from "../types/trip";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [trips, setTrips] = useState<TripSummary[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setIsLoading(true);

        const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
        const token = localStorage.getItem("access_token");

        // Check if user is authenticated
        if (!token) {
          if (mounted) {
            setError("Please log in first");
            setIsLoading(false);
          }
          return;
        }

        const res = await fetch(`${API_BASE}/trips`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (res.status === 401) {
          // Token expired
          localStorage.removeItem("access_token");
          localStorage.removeItem("user_id");
          if (mounted) {
            setError("Session expired. Please log in again.");
            setIsLoading(false);
          }
          return;
        }

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || "Failed to load trips");
        }

        const data: { user_id: string; trips: TripSummary[] } =
          await res.json();
        if (mounted) setTrips(data.trips);
      } catch (e) {
        if (mounted)
          setError(e instanceof Error ? e.message : "Unable to load trips");
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 rounded-3xl bg-gradient-to-r from-sky-50/80 to-sky-100 px-8 py-8 shadow-[0_20px_50px_rgba(14,63,120,0.06)] md:flex-row md:items-center">
        <div className="max-w-xl space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900 md:text-4xl">
            Your journeys,
            <span className="italic text-indigo-600">
              {" "}
              beautifully planned.
            </span>
          </h1>
          <p className="max-w-lg text-sm text-slate-700/85">
            Tell us about your dream vacation and our AI will craft a
            personalized, day-by-day itinerary that adapts to live weather,
            delays, and your preferences.
          </p>
          <Link
            to="/new"
            className="inline-flex w-fit items-center justify-center rounded-full bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-indigo-600/20 transition hover:bg-indigo-700"
          >
            Start a new trip
          </Link>
        </div>
        <div className="hidden h-32 w-40 overflow-hidden rounded-3xl border border-sky-100 bg-sky-50/60 shadow-inner md:block">
          <img
            src="https://pub-cdn.sider.ai/u/U04XHG42AO5/web-coder/6a0b2977a419c8a510478fe3/resource/8ecc57a6-6dac-4d4e-be7f-fb27172f1d85.jpg"
            alt="Travel collage"
            className="h-full w-full object-cover"
          />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-800">
          Your trips
        </h2>

        {isLoading && (
          <div className="py-8 text-center text-sm text-slate-700">
            Loading trips…
          </div>
        )}

        {error && <div className="py-4 text-sm text-red-600">{error}</div>}

        {trips && <TripGrid trips={trips} />}

        {trips && trips.length === 0 && (
          <div className="py-8 text-center text-sm text-slate-600">
            No trips yet.{" "}
            <Link
              to="/new"
              className="text-indigo-600 hover:underline font-medium"
            >
              Create your first one
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}

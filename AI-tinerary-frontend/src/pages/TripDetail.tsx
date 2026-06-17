/**
 * src/pages/TripDetail.tsx
 * @file TripDetail.tsx
 * @description Trip details page with hero banner, summary, and chat connected to FastAPI
 */

import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
} from "react";
import { useParams } from "react-router";
import { createPortal } from "react-dom";
import {
  CalendarDays,
  Download,
  Heart,
  ListChecks,
  Map,
  MapPin,
  Plane,
  Wallet,
} from "lucide-react";
import { format } from "date-fns";
import type {
  GeneratedItinerary,
  GeneratedItineraryDay,
} from "../types/itinerary";
import { ItineraryDay as ItineraryDayComponent } from "../components/itinerary/ItineraryDay";
import { ChatPanel } from "../components/chat/ChatPanel";
import React from "react";
import malaysiaHero from "../assets/Malaysia.jpg";
import indonesiaHero from "../assets/Indonesia.jpg";

function formatDateLabel(dateString?: string | null): string | null {
  if (!dateString) return null;
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return dateString;
  return format(date, "dd MMM yyyy");
}

interface SaveMenuPortalProps {
  open: boolean;
  anchorEl: HTMLButtonElement | null;
  onClose: () => void;
  onSelect: (path: "export-pdf" | "export-image") => void;
}

function SaveMenuPortal({
  open,
  anchorEl,
  onClose,
  onSelect,
}: SaveMenuPortalProps) {
  const menuRef = useRef<HTMLDivElement | null>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);

  useLayoutEffect(() => {
    if (!open || !anchorEl) {
      setPos(null);
      return;
    }

    const updatePos = () => {
      const rect = anchorEl.getBoundingClientRect();
      const menuWidth = 220;
      const menuHeight = 120;
      const margin = 8;

      let left = rect.right - menuWidth;
      if (left < 8) left = 8;

      let top = rect.bottom + margin;

      if (top + menuHeight > window.innerHeight - 8) {
        top = rect.top - margin - menuHeight;
      }

      if (left + menuWidth > window.innerWidth - 8) {
        left = window.innerWidth - menuWidth - 8;
      }

      if (top < 8) top = 8;
      if (left < 8) left = 8;

      setPos({ top: Math.round(top), left: Math.round(left) });
    };

    const raf = requestAnimationFrame(updatePos);
    window.addEventListener("resize", updatePos);
    window.addEventListener("scroll", updatePos, true);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", updatePos);
      window.removeEventListener("scroll", updatePos, true);
    };
  }, [open, anchorEl]);

  useEffect(() => {
    function handleOutside(e: Event) {
      const el = menuRef.current;
      if (!el) return;

      const target = e.target;
      if (!(target instanceof Node)) return;

      const clickedOutsideMenu = !el.contains(target);
      const clickedOutsideAnchor = !anchorEl || !anchorEl.contains(target);

      if (clickedOutsideMenu && clickedOutsideAnchor) {
        onClose();
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleOutside);
      document.addEventListener("touchstart", handleOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleOutside);
      document.removeEventListener("touchstart", handleOutside);
    };
  }, [open, anchorEl, onClose]);

  if (!open || !pos) return null;

  const inlineStyle: React.CSSProperties = {
    top: pos.top,
    left: pos.left,
    width: 220,
    zIndex: 2_147_483_647,
  };

  return createPortal(
    <div
      ref={menuRef}
      role="menu"
      aria-label="Save itinerary options"
      style={inlineStyle}
      className="fixed pointer-events-auto rounded-xl border border-[#BFDBFE] bg-white py-1 text-xs text-[#0F172A] shadow-2xl"
    >
      <div
        aria-hidden
        className="absolute -top-2 right-6 h-3 w-3 rotate-45 bg-white border-t border-l border-[#BFDBFE]"
        style={{ boxShadow: "-2px -2px 4px rgba(0,0,0,0.04)" }}
      />

      {/*<button
        type="button"
        className="flex w-full items-center gap-2 px-3 py-1.5 text-left hover:bg-[#EFF6FF]"
        onClick={() => onSelect("export-pdf")}
      >
        <Download className="h-3 w-3 text-[#0159FA]" />
        <span>Save as PDF</span>
      </button>*/}
      <button
        type="button"
        className="flex w-full items-center gap-2 px-3 py-1.5 text-left hover:bg-[#EFF6FF]"
        onClick={() => onSelect("export-image")}
      >
        <Download className="h-3 w-3 text-[#0159FA]" />
        <span>Save as image</span>
      </button>
    </div>,
    document.body,
  );
}

function TripHeroHeader({
  country,
  title,
  durationDays,
  primaryCity,
  onSave,
}: {
  country: string | null;
  title: string;
  durationDays: number | null;
  primaryCity: string | null;
  onSave: (path: "export-pdf" | "export-image") => void;
}) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const saveButtonRef = useRef<HTMLButtonElement | null>(null);

  const durationLabel = durationDays
    ? `${durationDays} days`
    : "Flexible dates";

  const template =
    country === "Malaysia"
      ? {
          bg: malaysiaHero,
          label: "🇲🇾 MALAYSIA",
        }
      : country === "Indonesia"
        ? {
            bg: indonesiaHero,
            label: "🇮🇩 INDONESIA",
          }
        : {
            bg: "https://pub-cdn.sider.ai/u/U04XHG42AO5/web-coder/6a0b2977a419c8a510478fe3/resource/92d5c515-1fb1-411f-98f2-1a4d6bb368d8.jpg",
            label: country ? country.toUpperCase() : "DESTINATION",
          };

  const handleSaveClick = (e: ReactMouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    setIsMenuOpen((open) => !open);
  };

  const handleSelect = (path: "export-pdf" | "export-image") => {
    setIsMenuOpen(false);
    onSave(path);
  };

  return (
    <section className="overflow-hidden rounded-3xl text-white shadow-[0_22px_60px_rgba(1,89,250,0.12)]">
      <div className="relative">
        <div className="absolute inset-0">
          <img
            src={template.bg}
            alt={`${template.label} hero`}
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-900/85 via-indigo-800/70 to-indigo-700/40" />
        </div>

        <div className="relative flex flex-col gap-4 px-6 py-6 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-3 rounded-full bg-indigo-900/40 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em]">
              <span className="inline-block h-2 w-2 rounded-full bg-indigo-300" />
              <span>{template.label}</span>
            </div>

            <div>
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                {title}
              </h1>
              <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-indigo-100/90">
                <span className="inline-flex items-center gap-1.5">
                  <CalendarDays className="h-3.5 w-3.5" />
                  <span>{durationLabel}</span>
                </span>
                <span className="hidden text-indigo-200 sm:inline">•</span>
                <span className="text-indigo-100/80">
                  Personalized city itinerary
                </span>
              </p>
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-indigo-100/80">
              {primaryCity && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-900/30 px-2.5 py-1">
                  <MapPin className="h-3 w-3" />
                  <span>{primaryCity}</span>
                </span>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-start gap-2 md:justify-end">
            <div className="relative">
              <button
                type="button"
                ref={saveButtonRef}
                onClick={handleSaveClick}
                className="inline-flex items-center gap-1.5 rounded-full bg-[#0159FA] px-3.5 py-1.5 text-sm font-semibold text-white shadow-lg shadow-[rgba(1,89,250,0.25)] hover:bg-[#1458DD]"
              >
                <Download className="h-3.5 w-3.5 text-white" />
                <span>Save itinerary</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <SaveMenuPortal
        open={isMenuOpen}
        anchorEl={saveButtonRef.current}
        onClose={() => setIsMenuOpen(false)}
        onSelect={handleSelect}
      />
    </section>
  );
}

function TripOverviewCard({ trip }: { trip: GeneratedItinerary["trip"] }) {
  const dayCount = trip.duration_days || null;
  const startDateLabel = formatDateLabel(
    (trip as any).start_date || (trip as any).startDate,
  );
  const endDateLabel = formatDateLabel(
    (trip as any).end_date || (trip as any).endDate,
  );
  const primaryCity = trip.cities && trip.cities[0];

  let durationLabel: string;
  if (startDateLabel && endDateLabel) {
    durationLabel = `${startDateLabel} - ${endDateLabel}`;
  } else if (startDateLabel) {
    durationLabel = startDateLabel;
  } else if (dayCount) {
    durationLabel = `${dayCount} days`;
  } else {
    durationLabel = "To be determined";
  }

  const travelStyle: string =
    (trip as any).travel_style ||
    (trip as any).travelStyle ||
    "To be determined";

  const interests: string[] = Array.isArray((trip as any).interests)
    ? ((trip as any).interests as string[])
    : [];

  const flights: any[] = Array.isArray((trip as any).flights)
    ? ((trip as any).flights as any[])
    : [];

  const departureFlight =
    flights.find((f) => f.type === "arrival") || flights[0];
  const arrivalFlight =
    flights.find((f) => f.type === "departure") || flights[1];

  const formatFlightSummary = (flight: any | undefined | null): string => {
    if (!flight) return "To be determined";
    const number = flight.flight_number || flight.flightNumber;
    const time = flight.time;
    const dateLabel = formatDateLabel(flight.date);

    if (number && time && dateLabel) {
      return `${number} (${time}, ${dateLabel})`;
    }

    const details: string[] = [];
    if (time) details.push(time);
    if (dateLabel) details.push(dateLabel);

    if (number && details.length > 0) {
      return `${number} (${details.join(", ")})`;
    }

    if (number) return number;
    if (details.length > 0) return details.join(", ");
    return "To be determined";
  };

  return (
    <section className="rounded-3xl bg-white p-5 shadow-sm shadow-[0_6px_18px_rgba(1,89,250,0.06)] ring-1 ring-[#93C5FD]">
      <header className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-[#0159FA]" />
          <h2 className="text-sm font-semibold text-[#0F172A]">Trip summary</h2>
        </div>
      </header>

      <dl className="mt-1 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <dt className="flex items-center gap-1 text-xs font-medium text-[#475569]">
            <CalendarDays className="h-3.5 w-3.5 text-[#0159FA]" />
            Duration
          </dt>
          <dd className="mt-0.5 text-[#0F172A]">{durationLabel}</dd>
        </div>

        <div>
          <dt className="flex items-center gap-1 text-xs font-medium text-[#475569]">
            <Heart className="h-3.5 w-3.5 text-[#0159FA]" />
            Preferred travel style
          </dt>
          <dd className="mt-0.5 text-[#0F172A]">{travelStyle}</dd>
        </div>

        <div>
          <dt className="flex items-center gap-1 text-xs font-medium text-[#475569]">
            <Heart className="h-3.5 w-3.5 text-[#0159FA]" />
            Interests
          </dt>
          <dd className="mt-0.5 text-[#0F172A]">
            {interests.length > 0 ? interests.join(", ") : "To be determined"}
          </dd>
        </div>

        <div>
          <dt className="flex items-center gap-1 text-xs font-medium text-[#475569]">
            <Plane className="h-3.5 w-3.5 text-[#0159FA]" />
            Departure Flight
          </dt>
          <dd className="mt-0.5 font-semibold text-[#0F172A]">
            {formatFlightSummary(departureFlight)}
          </dd>
        </div>

        <div>
          <dt className="flex items-center gap-1 text-xs font-medium text-[#475569]">
            <Plane className="h-3.5 w-3.5 text-[#0159FA]" />
            Arrival Flight
          </dt>
          <dd className="mt-0.5 font-semibold text-[#0F172A]">
            {formatFlightSummary(arrivalFlight)}
          </dd>
        </div>
      </dl>
    </section>
  );
}

function NotesCard({ items }: { items: string[] }) {
  if (!items.length) return null;

  return (
    <section className="rounded-3xl bg-white p-5 shadow-sm shadow-[0_6px_18px_rgba(1,89,250,0.06)] ring-1 ring-[#93C5FD]">
      <header className="flex items-center gap-2">
        <ListChecks className="h-4 w-4 text-[#0159FA]" />
        <h2 className="text-sm font-semibold text-[#0F172A]">
          Notes / Must include
        </h2>
      </header>
      <ul className="mt-2 space-y-1.5 text-sm text-[#0F172A]">
        {items.map((item, index) => (
          <li key={`${item}-${index}`} className="flex gap-2">
            <span className="mt-[6px] h-1.5 w-1.5 rounded-full bg-[#0159FA]" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function TripDetailPage() {
  const { tripId } = useParams();
  const [itinerary, setItinerary] = useState<GeneratedItinerary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tripId) return;

    let cancelled = false;

    (async () => {
      try {
        setIsLoading(true);
        setError(null);

        const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
        const token = localStorage.getItem("access_token");

        if (!token) {
          if (!cancelled) {
            setError("Please log in to view this trip.");
            setIsLoading(false);
          }
          return;
        }

        const response = await fetch(`${API_BASE}/trips/${tripId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          if (response.status === 404) {
            if (!cancelled) {
              setError(
                "This trip could not be found. It may have expired or been deleted.",
              );
            }
            return;
          }

          if (!cancelled) {
            setError(
              "We could not load your itinerary due to a server error. Please try again.",
            );
          }
          return;
        }

        const data: GeneratedItinerary = await response.json();
        if (!cancelled) {
          setItinerary(data);
        }
      } catch (e) {
        if (!cancelled) {
          setError(
            "We could not load your itinerary. Please check your connection and try again.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [tripId]);

  useEffect(() => {
    function handleDayUpdated(e: Event) {
      const ev = e as CustomEvent;
      const updated = ev.detail?.day;
      if (!updated || typeof updated.day !== "number") return;

      setItinerary((prev) => {
        if (!prev) return prev;
        const daysArray = prev.days || prev.itinerary?.days || [];
        const daysClone = Array.isArray(prev.days) ? [...prev.days] : [];
        const idx = daysClone.findIndex((d) => d.day === updated.day);
        if (idx >= 0) {
          daysClone[idx] = { ...daysClone[idx], ...updated };
        } else {
          daysClone.push(updated);
          daysClone.sort((a, b) => (a.day ?? 0) - (b.day ?? 0));
        }
        const newItinerary = {
          ...prev,
          days: daysClone,
        };

        if (prev.itinerary) {
          newItinerary.itinerary = { ...prev.itinerary, days: daysClone };
        }

        return newItinerary;
      });
    }

    window.addEventListener(
      "itinerary-day-updated",
      handleDayUpdated as EventListener,
    );
    return () => {
      window.removeEventListener(
        "itinerary-day-updated",
        handleDayUpdated as EventListener,
      );
    };
  }, []);

  if (!tripId) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-red-600">
        Trip ID is missing. Please open this page from a valid trip link.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-2 text-sm text-[#475569]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#0159FA] border-t-transparent" />
        <span>Loading itinerary…</span>
      </div>
    );
  }

  if (error || !itinerary) {
    return (
      <div className="mx-auto max-w-2xl rounded-2xl bg-red-50 p-4 text-sm text-red-800 shadow-sm shadow-red-900/10">
        <p className="font-medium">Unable to load itinerary</p>
        <p className="mt-1 text-xs text-red-700/90">
          {error || "An unknown error occurred while loading this trip."}
        </p>
      </div>
    );
  }

  const tripMeta = itinerary.trip;
  const profile = itinerary.profile;
  const days: GeneratedItineraryDay[] = (() => {
    if (!itinerary) return [];
    return Array.isArray(itinerary.days)
      ? itinerary.days
      : Array.isArray(itinerary.itinerary?.days)
        ? itinerary.itinerary.days
        : [];
  })();
  const primaryCity = profile?.cities?.[0];
  const country = profile?.country || null;
  const dayCount = profile?.days || profile?.duration_days || days.length;
  const tripTitle = primaryCity
    ? `${primaryCity}, ${country ?? ""}`.trim().replace(/,\s*$/, "")
    : country || "Trip itinerary";
  const hasMustInclude =
    Array.isArray(profile?.must_include) && profile.must_include.length > 0;

  const handleSaveItinerary = (path: "export-pdf" | "export-image") => {
    const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
    const token = localStorage.getItem("access_token");

    if (!token) {
      alert("Authentication required. Please log in again.");
      return;
    }

    try {
      const backendPath = path === "export-pdf" ? "export/pdf" : "export/image";
      const url = `${API_BASE}/trips/${tripId}/${backendPath}`;

      const xhr = new XMLHttpRequest();
      xhr.open("GET", url, true);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.responseType = "blob";

      xhr.onload = () => {
        console.log("✅ Response status:", xhr.status);
        console.log("✅ Response headers:", xhr.getAllResponseHeaders());

        if (xhr.status === 200) {
          const blob = xhr.response;
          const linkElement = document.createElement("a");
          const href = URL.createObjectURL(blob);
          linkElement.href = href;

          const fileExt = path === "export-pdf" ? "pdf" : "png";
          linkElement.download = `itinerary_${tripId}.${fileExt}`;

          document.body.appendChild(linkElement);
          linkElement.click();
          document.body.removeChild(linkElement);
          URL.revokeObjectURL(href);
        } else {
          console.error(`Error: ${xhr.status} - ${xhr.statusText}`);
          alert(`Error: ${xhr.status} - ${xhr.statusText}`);
        }
      };

      xhr.onerror = () => {
        console.error("❌ Download failed - Network Error");
        console.error("Status:", xhr.status);
        console.error("Response:", xhr.response);
        alert(
          "Failed to download the itinerary. Check browser console for details.",
        );
      };

      xhr.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = (event.loaded / event.total) * 100;
          console.log(`Download progress: ${percentComplete}%`);
        }
      };

      xhr.timeout = 60000; // 60 second timeout
      xhr.send();
    } catch (error) {
      console.error("❌ Download error:", error);
      alert("An error occurred while downloading. Please try again.");
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,2.1fr)_minmax(0,1fr)]">
      <div className="space-y-4">
        <TripHeroHeader
          country={country}
          title={tripTitle}
          durationDays={dayCount || null}
          primaryCity={primaryCity || null}
          onSave={handleSaveItinerary}
        />

        <TripOverviewCard trip={profile || tripMeta} />

        {hasMustInclude && <NotesCard items={profile?.must_include!} />}

        <section aria-labelledby="daily-breakdown-heading">
          <div className="space-y-4">
            {(() => {
              const allDays = Array.isArray(itinerary?.days)
                ? itinerary.days
                : Array.isArray(itinerary?.itinerary?.days)
                  ? itinerary.itinerary.days
                  : [];

              return allDays.map((day) => (
                <ItineraryDayComponent
                  key={day.day}
                  day={day}
                  tripId={tripId}
                  preferences={itinerary.trip}
                />
              ));
            })()}
          </div>
        </section>
      </div>

      <section className="rounded-3xl bg-white p-4 shadow-sm shadow-[0_6px_18px_rgba(1,89,250,0.06)] ring-1 ring-[#93C5FD]">
        <ChatPanel tripId={tripId} />
      </section>
    </div>
  );
}

/**
 * @file NewTrip.tsx
 * @description Page containing form to capture user preferences for a new itinerary.
 *              Modified to support side-by-side departure and arrival flight codes.
 */

import { FormEvent, useState, ChangeEvent } from "react";
import { useNavigate } from "react-router";
import type { TravelStyle } from "../types/trip";

type SupportedCountry = "Malaysia" | "Indonesia";
type CountryFormValue = "" | SupportedCountry;

interface SelectOption {
  value: string;
  label: string;
}

const COUNTRY_OPTIONS: SelectOption[] = [
  { value: "Malaysia", label: "Malaysia" },
  { value: "Indonesia", label: "Indonesia" },
];

/**
 * Malaysia: grouped by state → cities (from cities list.txt)
 * Indonesia: flat list (no city-level data provided)
 */
const MALAYSIA_CITY_GROUPS: { state: string; cities: string[] }[] = [
  {
    state: "Johor",
    cities: ["Johor Bahru", "Batu Pahat", "Muar", "Kota Tinggi"],
  },
  {
    state: "Kedah",
    cities: ["Sungai Petani", "Alor Setar", "Langkawi"],
  },
  {
    state: "Kelantan",
    cities: ["Kota Bharu", "Tanah Merah", "Gua Musang", "Kuala Krai"],
  },
  {
    state: "Melaka",
    cities: ["Bandaraya Melaka", "Klebang"],
  },
  {
    state: "Negeri Sembilan",
    cities: ["Seremban", "Port Dickson", "Nilai"],
  },
  {
    state: "Pahang",
    cities: ["Kuantan", "Temerloh", "Bentong"],
  },
  {
    state: "Pulau Pinang",
    cities: ["Penang"],
  },
  {
    state: "Perak",
    cities: ["Ipoh", "Taiping", "Teluk Intan", "Kuala Kangsar"],
  },
  {
    state: "Perlis",
    cities: ["Kangar", "Kuala Perlis"],
  },
  {
    state: "Sabah",
    cities: ["Kota Kinabalu", "Sandakan", "Tawau", "Semporna"],
  },
  {
    state: "Sarawak",
    cities: ["Kuching", "Miri", "Bintulu"],
  },
  {
    state: "Selangor",
    cities: [
      "Subang Jaya",
      "Klang",
      "Shah Alam",
      "Petaling Jaya",
      "Cheras",
      "Kajang",
      "Rawang",
      "Banting",
      "Kuala Selangor",
      "Sepang",
    ],
  },
  {
    state: "Terengganu",
    cities: ["Kuala Terengganu", "Chukai", "Dungun", "Kerteh", "Kuala Berang"],
  },
  {
    state: "Kuala Lumpur",
    cities: ["Kuala Lumpur"],
  },
  {
    state: "Labuan",
    cities: ["Labuan"],
  },
  {
    state: "Putrajaya",
    cities: ["Putrajaya"],
  },
];

const INDONESIA_CITY_GROUPS: { state: string; cities: string[] }[] = [
  { state: "Bali", cities: ["Denpasar", "Ubud", "Seminyak", "Kuta"] },
  {
    state: "Jakarta",
    cities: [
      "Jakarta Pusat",
      "Jakarta Selatan",
      "Jakarta Barat",
      "Jakarta Utara",
    ],
  },
  { state: "Yogyakarta", cities: ["Yogyakarta", "Sleman", "Bantul"] },
  { state: "West Java", cities: ["Bandung", "Bogor", "Bekasi", "Sukabumi"] },
  { state: "Central Java", cities: ["Semarang", "Magelang", "Solo"] },
  {
    state: "East Java",
    cities: ["Surabaya", "Malang", "Batu", "Gunung Bromo"],
  },
  { state: "Banten", cities: ["Anyer", "Serang", "Tangerang"] },
  {
    state: "West Nusa Tenggara",
    cities: ["Mataram", "Lombok", "Gili Trawangan"],
  },
  {
    state: "East Nusa Tenggara",
    cities: ["Labuan Bajo", "Komodo Island", "Flores", "Kupang"],
  },
  { state: "North Sumatra", cities: ["Medan", "Lake Toba", "Nias Island"] },
  { state: "West Sumatra", cities: ["Padang", "Bukittinggi", "Payakumbuh"] },
  { state: "South Sulawesi", cities: ["Makassar", "Toraja", "Tanjung Bira"] },
  {
    state: "North Sulawesi",
    cities: ["Manado", "Taman Bunaken", "Danau Linow"],
  },
  {
    state: "Riau Islands",
    cities: ["Batam", "Tanjung Pinang", "Bintan", "Natuna"],
  },
  { state: "Riau", cities: ["Pekanbaru", "Dumai"] },
  { state: "South Kalimantan", cities: ["Banjarmasin", "Banjarbaru"] },
];

const CITY_GROUPS: Record<
  SupportedCountry,
  { state: string; cities: string[] }[]
> = {
  Malaysia: MALAYSIA_CITY_GROUPS,
  Indonesia: INDONESIA_CITY_GROUPS,
};

interface NewTripPayload {
  country: string;
  cities: string[];
  start_date: string;
  end_date: string;
  travel_style: TravelStyle;
  interests: string[];
  budget: string;
  must_include: string[];
  departure_flight_number?: string;
  arrival_flight_number?: string;
}

export default function NewTripPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedCountry, setSelectedCountry] = useState<CountryFormValue>("");
  const [selectedCities, setSelectedCities] = useState<string[]>([]);
  const [isCityDropdownOpen, setIsCityDropdownOpen] = useState(false);
  const [flightDeparture, setFlightDeparture] = useState("");
  const [flightArrival, setFlightArrival] = useState("");

  const handleCountryChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const newCountry = event.target.value as CountryFormValue;
    setSelectedCountry(newCountry);
    setSelectedCities([]);
    setIsCityDropdownOpen(false);
  };

  const toggleCitySelection = (cityValue: string) => {
    setSelectedCities((prev) =>
      prev.includes(cityValue)
        ? prev.filter((c) => c !== cityValue)
        : [...prev, cityValue],
    );
  };

  const removeCitySelection = (cityValue: string) => {
    setSelectedCities((prev) => prev.filter((city) => city !== cityValue));
  };

  const normalizeFlightCode = (val: string): string => {
    return val
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, "")
      .slice(0, 8);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    // ✅ Check if user is authenticated
    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Please sign up or log in first.");
      setIsSubmitting(false);
      return;
    }

    if (!selectedCountry || selectedCities.length === 0) {
      setError("Please select a country and at least one city.");
      setIsSubmitting(false);
      return;
    }

    const formData = new FormData(event.currentTarget);
    const rawStartDate = String(formData.get("startDate") || "").trim();

    if (!rawStartDate) {
      setError("Start date is required to generate your itinerary.");
      setIsSubmitting(false);
      return;
    }

    const interestsRaw = String(formData.get("interests") || "");
    const countryValue = selectedCountry as SupportedCountry;
    const rawNotes = String(formData.get("notes") || "").trim();
    const days = Number(formData.get("days") || 1);

    // ✅ Compute end_date from start_date + days
    const startDate = new Date(rawStartDate);
    const endDate = new Date(startDate.getTime() + (days - 1) * 86400000);
    const endDateString = endDate.toISOString().split("T")[0];

    const cleanDeparture = normalizeFlightCode(flightDeparture) || undefined;
    const cleanArrival = normalizeFlightCode(flightArrival) || undefined;

    const payload: NewTripPayload = {
      country: countryValue,
      cities: selectedCities,
      start_date: rawStartDate,
      end_date: endDateString,
      travel_style: (formData.get("travelStyle") as TravelStyle) || "relaxed",
      interests: interestsRaw
        .split(",")
        .map((i) => i.trim())
        .filter(Boolean),
      budget: (formData.get("budget") as string) || "moderate",
      must_include: rawNotes
        ? rawNotes
            .split(";")
            .map((s) => s.trim())
            .filter(Boolean)
        : [],
      departure_flight_number: cleanArrival,
      arrival_flight_number: cleanDeparture,
    };

    setIsSubmitting(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

      const response = await fetch(`${API_BASE}/trips`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create trip");
      }

      const data: { trip_id: string } = await response.json();
      navigate(`/trip/${data.trip_id}`);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Unable to start itinerary generation.",
      );
      setIsSubmitting(false);
    }
  };

  const cityGroupsForCountry =
    selectedCountry && selectedCountry in CITY_GROUPS
      ? CITY_GROUPS[selectedCountry as SupportedCountry]
      : [];

  return (
    <div className="rounded-3xl bg-blue-50/60 p-6 shadow-[0_20px_60px_rgba(59,130,246,0.12)]">
      <div className="space-y-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-blue-700/80">
            New trip
          </p>
          <h1 className="text-2xl font-semibold tracking-tight text-blue-900">
            Tell us about your dream trip.
          </h1>
          <p className="text-sm text-blue-900/80">
            Your answers help our AI understand your style, constraints, and
            must-visit spots so it can build a personalized itinerary.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="grid gap-6 rounded-2xl border border-blue-100 bg-white/80 p-6 shadow-lg shadow-blue-900/5 md:grid-cols-2"
        >
          <div className="space-y-4">
            {/* Country */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                Country
              </label>
              <select
                name="country"
                required
                value={selectedCountry}
                onChange={handleCountryChange}
                className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              >
                <option value="" disabled>
                  Select country
                </option>
                {COUNTRY_OPTIONS.map((country) => (
                  <option key={country.value} value={country.value}>
                    {country.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Cities — grouped dropdown */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                Cities
              </label>

              {/* Selected city chips */}
              {selectedCities.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {selectedCities.map((city) => (
                    <button
                      key={city}
                      type="button"
                      onClick={() => removeCitySelection(city)}
                      className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-900 hover:bg-blue-200"
                    >
                      <span>{city}</span>
                      <span className="text-[10px] font-semibold text-blue-700">
                        ×
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {/* Hidden inputs for form submission */}
              {selectedCities.map((city) => (
                <input key={city} type="hidden" name="cities" value={city} />
              ))}

              {/* Trigger button */}
              <button
                type="button"
                disabled={!selectedCountry}
                onClick={() =>
                  selectedCountry && setIsCityDropdownOpen((open) => !open)
                }
                className="mt-2 flex w-full items-center justify-between rounded-xl border border-blue-200 bg-white px-3 py-2 text-left text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-blue-50"
              >
                <span className="truncate text-blue-900/90">
                  {!selectedCountry
                    ? "Select country first"
                    : selectedCities.length === 0
                      ? "Select cities"
                      : `${selectedCities.length} cit${selectedCities.length === 1 ? "y" : "ies"} selected`}
                </span>
                <span className="ml-2 text-xs text-blue-700">
                  {isCityDropdownOpen ? "Hide" : "Choose"}
                </span>
              </button>

              {/* Grouped dropdown panel */}
              {isCityDropdownOpen && selectedCountry && (
                <div className="mt-2 w-full rounded-xl border border-blue-200 bg-white shadow-lg">
                  <div className="max-h-64 overflow-y-auto">
                    {cityGroupsForCountry.map((group) => (
                      <div key={group.state}>
                        {/* State header — non-clickable */}
                        <div className="sticky top-0 mx-2 mt-2 rounded-xl bg-[#DBEAFE] px-3 py-2">
                          <span className="text-sm font-bold text-[#1E3A8A]">
                            {group.state}
                          </span>
                        </div>

                        {/* City rows — clickable */}
                        <div className="pb-1">
                          {group.cities.map((city) => {
                            const isSelected = selectedCities.includes(city);
                            return (
                              <button
                                key={city}
                                type="button"
                                onClick={() => toggleCitySelection(city)}
                                className={`flex w-full items-center justify-between px-5 py-2 text-left text-sm transition-colors hover:bg-blue-50 ${
                                  isSelected
                                    ? "text-[#1D4ED8] font-medium"
                                    : "text-[#1E3A8A]"
                                }`}
                              >
                                <span>{city}</span>
                                {isSelected && (
                                  <span className="text-[#1D4ED8] font-bold text-base leading-none">
                                    ✓
                                  </span>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between border-t border-blue-100 px-3 py-2">
                    <p className="text-[11px] text-blue-800/80">
                      Tap to add or remove cities.
                    </p>
                    <button
                      type="button"
                      onClick={() => setIsCityDropdownOpen(false)}
                      className="rounded-full bg-blue-700 px-3 py-1 text-[11px] font-medium text-white shadow-sm hover:bg-blue-800"
                    >
                      Done
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Start date + Trip length */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                  Start date
                </label>
                <input
                  name="startDate"
                  type="date"
                  className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </div>
              <div>
                <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                  Trip length (days)
                </label>
                <input
                  name="days"
                  type="number"
                  min={1}
                  required
                  className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  placeholder="6"
                />
              </div>
            </div>

            {/* Flight numbers */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                Flight number
              </label>
              <div className="mt-2 grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium uppercase text-blue-700 mb-1">
                    Flight to Destination
                  </label>
                  <input
                    name="flightDeparture"
                    type="text"
                    value={flightDeparture}
                    onChange={(e) =>
                      setFlightDeparture(normalizeFlightCode(e.target.value))
                    }
                    className="mt-0 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm uppercase text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                    placeholder="E.g. MH260"
                    autoComplete="off"
                    maxLength={8}
                    aria-label="Departure flight number"
                    inputMode="text"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium uppercase text-blue-700 mb-1">
                    Flight from Destination
                  </label>
                  <input
                    name="flightArrival"
                    type="text"
                    value={flightArrival}
                    onChange={(e) =>
                      setFlightArrival(normalizeFlightCode(e.target.value))
                    }
                    className="mt-0 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm uppercase text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                    placeholder="E.g. MH261"
                    autoComplete="off"
                    maxLength={8}
                    aria-label="Arrival flight number"
                    inputMode="text"
                  />
                </div>
              </div>
              <p className="mt-1 text-[11px] text-blue-800/80">
                Optional. Please input letters and numbers only.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Travel style */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                Travel style
              </label>
              <select
                name="travelStyle"
                required
                className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              >
                <option value="relaxed">Relaxed</option>
                <option value="adventurous">Adventurous</option>
                <option value="honeymoon">Honeymoon</option>
                <option value="friends">Friends</option>
                <option value="family & kids">Family & kids</option>
              </select>
            </div>

            {/* Interests */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                Interests
              </label>
              <input
                name="interests"
                className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                placeholder="Food, temples, shopping"
              />
              <p className="mt-1 text-[11px] text-blue-800/80">
                Separate interests with commas (e.g. food, museums, hiking).
              </p>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-xs font-medium uppercase tracking-[0.22em] text-blue-900">
                Extra notes / must-visit places
              </label>
              <textarea
                name="notes"
                rows={4}
                className="mt-1 w-full rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                placeholder="E.g. Must visit teamLab Planets; need vegan-friendly options; avoid long hikes."
              />
            </div>
          </div>

          <div className="md:col-span-2 flex items-center justify-between pt-2">
            {error && <p className="text-xs text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={isSubmitting}
              className="ml-auto inline-flex items-center justify-center rounded-full bg-blue-700 px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-blue-700/30 transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-blue-400"
            >
              {isSubmitting ? "Creating trip…" : "Generate itinerary"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

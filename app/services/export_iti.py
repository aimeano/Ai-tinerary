# export_iti.py

import os
import json
from html import escape
from tempfile import NamedTemporaryFile





from html import escape
from datetime import datetime


def _format_date_label(date_string: str | None) -> str | None:
    """Format an ISO date string e.g. '2026-08-01' → '1 Aug 2026'."""
    if not date_string:
        return None
    try:
        dt = datetime.strptime(date_string[:10], "%Y-%m-%d")
        return dt.strftime("%-d %b %Y")   # e.g. "1 Aug 2026"
    except ValueError:
        return date_string


def _format_flight_summary(flight: dict | None) -> str:
    """
    Build a human-readable flight line, e.g. 'MH67 (16:35, 1 Aug 2026)'.
    Flight number is always uppercased to match UI behaviour.
    """
    if not flight:
        return "To be determined"

    raw_number = flight.get("flight_number") or flight.get("flightNumber") or ""
    number = raw_number.upper().strip() if raw_number else ""

    # Prefer enriched AirLabs fields, fall back to stored time
    time = flight.get("dep_time") or flight.get("time") or ""
    date_label = _format_date_label(flight.get("date"))

    parts: list[str] = []
    if time:
        parts.append(time)
    if date_label:
        parts.append(date_label)

    if number and parts:
        return f"{number} ({', '.join(parts)})"
    if number:
        return number
    if parts:
        return ", ".join(parts)
    return "To be determined"


def build_itinerary_html(trip_id: str, itinerary: dict, profile: dict | None = None) -> str:
    trip = itinerary.get("trip", {})
    days = itinerary.get("days", [])

    # ── profile holds flights, interests, travel_style etc. ──────────────────
    profile = profile or itinerary.get("profile", {})

    def e(value):
        return escape(str(value)) if value is not None else ""

    def get_restaurant_name(r):
        if isinstance(r, dict):
            return r.get("name", "Restaurant")
        return str(r)

    def get_activity_category(activity):
        return (
            activity.get("category")
            or activity.get("type")
            or activity.get("tag")
            or "Landmark"
        )

    def get_weather(day):
        weather = day.get("weather", {}) or {}

        temp = (
            weather.get("temp")
            or weather.get("temperature")
            or weather.get("temperature_avg")
            or day.get("temperature")
            or "29°C"
        )
        # Append °C if it's a bare number
        if str(temp).replace(".", "").isdigit():
            temp = f"{temp}°C"

        condition = (
            weather.get("condition")
            or weather.get("description")
            or weather.get("weather_description")
            or day.get("weather_condition")
            or "Partly cloudy"
        )

        return temp, condition

    def get_weather_emoji(condition: str) -> str:
        c = condition.lower()
        if any(w in c for w in ("rain", "heavy", "shower")):
            return "🌧️"
        if any(w in c for w in ("drizzle", "mist", "fog")):
            return "🌦️"
        if any(w in c for w in ("cloud", "overcast")):
            return "⛅"
        if any(w in c for w in ("sun", "clear", "fair")):
            return "☀️"
        return "⛅"

    def get_day_image(day):
        return (
            day.get("image_url")
            or day.get("image")
            or day.get("thumbnail")
            or ""
        )

    # ── Trip-level metadata ───────────────────────────────────────────────────
    country = e(trip.get("country", "Unknown destination"))
    cities = trip.get("cities", [])
    # cities might be stored as {"0": "Kuala Lumpur"} object
    if isinstance(cities, dict):
        cities = list(cities.values())
    cities_text = " · ".join(e(city) for city in cities) if cities else "N/A"
    primary_city = cities[0] if cities else ""

    total_days = e(trip.get("duration_days", len(days)))
    travel_style = e(
        profile.get("travel_style")
        or trip.get("travel_style")
        or "Balanced"
    )

    # Dates
    start_date = profile.get("start_date") or trip.get("start_date") or ""
    end_date   = profile.get("end_date")   or trip.get("end_date")   or ""
    start_label = _format_date_label(start_date)
    end_label   = _format_date_label(end_date)

    if start_label and end_label:
        duration_label = f"{start_label} - {end_label}"
    elif start_label:
        duration_label = start_label
    else:
        duration_label = f"{total_days} days"

    # Interests
    raw_interests = profile.get("interests") or trip.get("interests") or []
    if isinstance(raw_interests, dict):
        raw_interests = list(raw_interests.values())
    interests_text = e(", ".join(str(i) for i in raw_interests)) if raw_interests else "To be determined"

    # Flights  ── stored in profile.flights (list or dict)
    raw_flights = profile.get("flights") or trip.get("flights") or []
    if isinstance(raw_flights, dict):
        raw_flights = list(raw_flights.values())

    departure_flight = next((f for f in raw_flights if f.get("type") == "arrival"),  None) or (raw_flights[0] if raw_flights else None)
    arrival_flight   = next((f for f in raw_flights if f.get("type") == "departure"), None) or (raw_flights[1] if len(raw_flights) > 1 else None)

    dep_summary = e(_format_flight_summary(departure_flight))
    arr_summary = e(_format_flight_summary(arrival_flight))

    # ── Trip Summary card HTML ────────────────────────────────────────────────
    trip_summary_html = f"""
    <div class="summary-card">
      <div class="summary-header">
        <span class="summary-icon">&#128197;</span>
        <span class="summary-title">Trip summary</span>
      </div>

      <div class="summary-grid">

        <div class="summary-item">
          <div class="summary-label">
            <span class="summary-icon-sm">&#128197;</span> Duration
          </div>
          <div class="summary-value">{e(duration_label)}</div>
        </div>

        <div class="summary-item">
          <div class="summary-label">
            <span class="summary-icon-sm">&#10084;</span> Preferred travel style
          </div>
          <div class="summary-value summary-capitalize">{travel_style}</div>
        </div>

        <div class="summary-item">
          <div class="summary-label">
            <span class="summary-icon-sm">&#10084;</span> Interests
          </div>
          <div class="summary-value summary-capitalize">{interests_text}</div>
        </div>

        <div class="summary-item">
          <div class="summary-label">
            <span class="summary-icon-sm">&#9992;</span> Departure Flight
          </div>
          <div class="summary-value summary-bold">{dep_summary}</div>
        </div>

        <div class="summary-item">
          <div class="summary-label">
            <span class="summary-icon-sm">&#9992;</span> Arrival Flight
          </div>
          <div class="summary-value summary-bold">{arr_summary}</div>
        </div>

      </div>
    </div>
    """

    # ── Day cards ─────────────────────────────────────────────────────────────
    days_html = ""

    for day in days:
        day_number  = e(day.get("day", ""))
        day_title   = e(day.get("title", "Untitled day"))
        day_summary = e(day.get("summary", ""))

        # Date label  e.g. "TUE, 14 JUL 2026"
        raw_date = day.get("date", "")
        try:
            day_dt = datetime.strptime(raw_date[:10], "%Y-%m-%d")
            day_date_label = day_dt.strftime("%a, %d %b %Y").upper()   # "TUE, 14 JUL 2026"
        except (ValueError, TypeError):
            day_date_label = ""

        activities = day.get("activities", [])
        # activities may be a dict {"0": {...}, "1": {...}}
        if isinstance(activities, dict):
            activities = list(activities.values())

        stop_count = len(activities)
        temp, condition = get_weather(day)
        weather_emoji   = get_weather_emoji(condition)
        image_url       = get_day_image(day)

        if image_url:
            image_html = f'<img class="day-image" src="{e(image_url)}" alt="Day image" />'
        else:
            image_html = '<div class="day-image placeholder"><span>DAY</span></div>'

        # ── Activities ───────────────────────────────────────────────────────
        activities_html = ""

        for activity in activities:
            restaurants     = activity.get("nearby_restaurants", []) or []
            if isinstance(restaurants, dict):
                restaurants = list(restaurants.values())

            restaurants_html = ""
            if restaurants:
                restaurant_chips = "".join(
                    f'<span class="restaurant-chip">{e(get_restaurant_name(r))}</span>'
                    for r in restaurants
                )
                restaurants_html = f"""
                <div class="nearby-section">
                  <div class="dashed-line"></div>
                  <div class="nearby-title">NEARBY PLACES TO EAT &#127837;</div>
                  <div class="restaurant-chips">{restaurant_chips}</div>
                </div>
                """

            category = e(get_activity_category(activity))
            location_name = e(activity.get("location_name", ""))
            description   = e(activity.get("description", ""))

            desc_html = f'<div class="activity-desc">{description}</div>' if description else ""

            activities_html += f"""
            <div class="activity-card">
              <div class="activity-left">
                <span class="activity-badge">{category}</span>
                <span class="activity-time">{e(activity.get("time", ""))}</span>
              </div>

              <div class="activity-main">
                <div class="activity-title">{e(activity.get("title", ""))}</div>

                <div class="activity-location">
                  <span class="location-pin">&#128205;</span>
                  <span>{location_name}</span>
                </div>

                {desc_html}
                {restaurants_html}
              </div>
            </div>
            """

        day_badge_label = f"DAY {day_number}{' · ' + day_date_label if day_date_label else ''}"

        days_html += f"""
        <section class="day-card">
          <div class="day-header">
            <div class="day-left">
              {image_html}
              <div class="day-info">
                <div class="day-badge">
                  <span class="calendar-icon">&#128197;</span>
                  {e(day_badge_label)}
                </div>
                <h2>{day_title}</h2>
                <p class="day-meta">
                  {stop_count} stops &middot; Moderate walking &middot; {travel_style}
                </p>
              </div>
            </div>

            <div class="weather-card">
              <div class="weather-emoji">{weather_emoji}</div>
              <div>
                <div class="weather-temp">{e(str(temp))}</div>
                <div class="weather-condition">{e(condition)}</div>
              </div>
            </div>
          </div>

          {f'<p class="day-summary">{day_summary}</p>' if day_summary else ""}

          <div class="activities-list">
            {activities_html}
          </div>
        </section>
        """

    # ── Hero banner ───────────────────────────────────────────────────────────
    hero_bg = (
        "https://pub-cdn.sider.ai/u/U04XHG42AO5/web-coder/"
        "6a0b2977a419c8a510478fe3/resource/"
        "92d5c515-1fb1-411f-98f2-1a4d6bb368d8.jpg"
    )
    if trip.get("country") == "Indonesia":
        hero_bg = (
            "https://pub-cdn.sider.ai/u/U04XHG42AO5/web-coder/"
            "6a0b2977a419c8a510478fe3/resource/"
            "8c856b2a-b51e-4d64-ae82-8cb0c1308f27.jpg"
        )

    hero_label = f"🌏 {country.upper()}"
    hero_title = f"{e(primary_city)}, {country}" if primary_city else country
    duration_hero = f"{total_days} days"

    # ── Full HTML ─────────────────────────────────────────────────────────────
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        @page {{
          size: A4;
          margin: 20px;
        }}

        * {{
          box-sizing: border-box;
        }}

        body {{
          margin: 0;
          font-family: Arial, Helvetica, sans-serif;
          background: #f4f9ff;
          color: #071425;
        }}

        .pdf-wrapper {{
          width: 100%;
          padding: 12px;
        }}

        /* ── Hero Banner ─────────────────────────────────────────────── */
        .hero-banner {{
          position: relative;
          border-radius: 20px;
          overflow: hidden;
          margin-bottom: 18px;
          box-shadow: 0 22px 60px rgba(1,89,250,0.12);
          min-height: 140px;
        }}

        .hero-bg {{
          width: 100%;
          height: 160px;
          object-fit: cover;
          display: block;
        }}

        .hero-overlay {{
          position: absolute;
          inset: 0;
          background: linear-gradient(
            to right,
            rgba(30, 27, 90, 0.85) 0%,
            rgba(49, 73, 158, 0.70) 55%,
            rgba(67, 92, 184, 0.40) 100%
          );
        }}

        .hero-content {{
          position: absolute;
          inset: 0;
          display: flex;
          flex-direction: column;
          justify-content: center;
          padding: 24px 28px;
          color: #ffffff;
        }}

        .hero-pill {{
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: rgba(30, 27, 90, 0.40);
          border-radius: 999px;
          padding: 4px 12px;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: #c7d7ff;
          margin-bottom: 10px;
          width: fit-content;
        }}

        .hero-pill-dot {{
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #93c5fd;
          flex-shrink: 0;
        }}

        .hero-title {{
          margin: 0 0 6px;
          font-size: 28px;
          font-weight: 700;
          line-height: 1.2;
          color: #ffffff;
        }}

        .hero-subtitle {{
          margin: 0;
          font-size: 13px;
          color: rgba(199, 215, 255, 0.90);
          display: flex;
          align-items: center;
          gap: 6px;
        }}

        .hero-city-pill {{
          display: inline-flex;
          align-items: center;
          gap: 5px;
          background: rgba(30, 27, 90, 0.30);
          border-radius: 999px;
          padding: 3px 10px;
          font-size: 12px;
          color: rgba(199, 215, 255, 0.85);
          margin-top: 8px;
          width: fit-content;
        }}

        /* ── Trip Summary Card ───────────────────────────────────────── */
        .summary-card {{
          background: #ffffff;
          border: 1.5px solid #93c5fd;
          border-radius: 20px;
          padding: 18px 22px;
          margin-bottom: 18px;
          box-shadow: 0 6px 18px rgba(1,89,250,0.06);
        }}

        .summary-header {{
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 14px;
          border-bottom: 1px solid #e0eeff;
          padding-bottom: 10px;
        }}

        .summary-title {{
          font-size: 14px;
          font-weight: 700;
          color: #0f172a;
        }}

        .summary-icon {{
          font-size: 15px;
          color: #0159fa;
        }}

        .summary-grid {{
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px 20px;
        }}

        .summary-item {{
          display: flex;
          flex-direction: column;
          gap: 3px;
        }}

        .summary-label {{
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 11px;
          font-weight: 600;
          color: #475569;
          text-transform: capitalize;
        }}

        .summary-icon-sm {{
          font-size: 12px;
          color: #0159fa;
        }}

        .summary-value {{
          font-size: 13px;
          color: #0f172a;
          margin-top: 1px;
        }}

        .summary-capitalize {{
          text-transform: capitalize;
        }}

        .summary-bold {{
          font-weight: 700;
        }}

        /* ── Day Cards ───────────────────────────────────────────────── */
        .day-card {{
          background: #ffffff;
          border: 1.6px solid #93c5fd;
          border-radius: 20px;
          padding: 22px 24px;
          margin-bottom: 20px;
          box-shadow: 0 8px 20px rgba(37,99,235,0.06);
          page-break-inside: avoid;
          break-inside: avoid;
        }}

        .day-header {{
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 16px;
        }}

        .day-left {{
          display: flex;
          align-items: flex-start;
          gap: 14px;
          min-width: 0;
          flex: 1;
        }}

        .day-image {{
          width: 64px;
          height: 64px;
          border-radius: 10px;
          object-fit: cover;
          border: 1.5px solid #93c5fd;
          flex-shrink: 0;
        }}

        .day-image.placeholder {{
          background: linear-gradient(135deg, #dbeafe, #bfdbfe);
          color: #1d4ed8;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 2px;
        }}

        .day-info {{
          min-width: 0;
          flex: 1;
        }}

        .day-badge {{
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: #dbeafe;
          border: 1.5px solid #83b9ff;
          color: #1557d9;
          border-radius: 999px;
          padding: 5px 14px;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          margin-bottom: 7px;
        }}

        .calendar-icon {{
          font-size: 12px;
        }}

        .day-info h2 {{
          margin: 0 0 5px;
          font-size: 18px;
          font-weight: 700;
          line-height: 1.25;
          color: #030b18;
        }}

        .day-meta {{
          margin: 0;
          font-size: 13px;
          color: #34425f;
          font-weight: 500;
        }}

        .day-summary {{
          margin: 0 0 14px 78px;
          font-size: 13px;
          color: #536179;
          line-height: 1.5;
        }}

        /* ── Weather card ────────────────────────────────────────────── */
        .weather-card {{
          min-width: 140px;
          display: flex;
          align-items: center;
          gap: 10px;
          background: #ddecff;
          border: 1.5px solid #83b9ff;
          border-radius: 12px;
          padding: 10px 14px;
          flex-shrink: 0;
        }}

        .weather-emoji {{
          font-size: 22px;
          line-height: 1;
        }}

        .weather-temp {{
          font-size: 15px;
          font-weight: 800;
          color: #061329;
          margin-bottom: 2px;
        }}

        .weather-condition {{
          font-size: 12px;
          color: #40516f;
        }}

        /* ── Activities ──────────────────────────────────────────────── */
        .activities-list {{
          display: flex;
          flex-direction: column;
          gap: 12px;
        }}

        .activity-card {{
          display: flex;
          align-items: flex-start;
          gap: 14px;
          background: #ffffff;
          border: 1.5px solid #a8d0ff;
          border-radius: 12px;
          padding: 16px 18px;
          box-shadow: 0 4px 10px rgba(37,99,235,0.04);
          page-break-inside: avoid;
          break-inside: avoid;
        }}

        .activity-left {{
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 6px;
          width: 80px;
          flex-shrink: 0;
        }}

        .activity-badge {{
          display: inline-block;
          background: #dbeafe;
          border: 1.5px solid #83b9ff;
          color: #1557d9;
          border-radius: 999px;
          padding: 3px 10px;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }}

        .activity-time {{
          font-size: 15px;
          font-weight: 800;
          color: #030b18;
        }}

        .activity-main {{
          flex: 1;
          min-width: 0;
        }}

        .activity-title {{
          font-size: 14px;
          font-weight: 700;
          color: #030b18;
          margin-bottom: 5px;
        }}

        .activity-location {{
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 12px;
          color: #43536d;
          margin-bottom: 6px;
        }}

        .location-pin {{
          font-size: 12px;
          color: #0159fa;
        }}

        .activity-desc {{
          font-size: 12px;
          color: #536179;
          line-height: 1.5;
          margin-bottom: 6px;
        }}

        /* ── Nearby restaurants ──────────────────────────────────────── */
        .nearby-section {{
          margin-top: 8px;
        }}

        .dashed-line {{
          border-top: 1.5px dashed #b7d7ff;
          margin: 6px 0 10px;
          width: 100%;
        }}

        .nearby-title {{
          font-size: 10px;
          letter-spacing: 0.16em;
          color: #1557d9;
          font-weight: 900;
          margin-bottom: 8px;
          text-transform: uppercase;
        }}

        .restaurant-chips {{
          display: flex;
          flex-wrap: wrap;
          gap: 6px 8px;
        }}

        .restaurant-chip {{
          display: inline-block;
          background: #eff7ff;
          border: 1.5px solid #b4d7ff;
          color: #0f4bd8;
          border-radius: 999px;
          padding: 5px 12px;
          font-size: 11px;
          font-weight: 700;
        }}
      </style>
    </head>

    <body>
      <div class="pdf-wrapper">

        <!-- ── Hero Banner ─────────────────────────────────────────── -->
        <div class="hero-banner">
          <img class="hero-bg" src="{hero_bg}" alt="{hero_label} hero" />
          <div class="hero-overlay"></div>
          <div class="hero-content">
            <div class="hero-pill">
              <span class="hero-pill-dot"></span>
              <span>{hero_label}</span>
            </div>
            <h1 class="hero-title">{hero_title}</h1>
            <p class="hero-subtitle">
              &#128197;&nbsp;{duration_hero}&nbsp;&nbsp;&bull;&nbsp;&nbsp;Personalized city itinerary
            </p>
            <div class="hero-city-pill">
              &#128205;&nbsp;{e(primary_city)}
            </div>
          </div>
        </div>

        <!-- ── Trip Summary Card ───────────────────────────────────── -->
        {trip_summary_html}

        <!-- ── Day Cards ───────────────────────────────────────────── -->
        {days_html}

      </div>
    </body>
    </html>
    """


def generate_pdf_bytes(html: str) -> bytes:
    from weasyprint import HTML
    return HTML(string=html, base_url=".").write_pdf()


async def generate_image_bytes(html: str) -> bytes:
    from playwright.async_api import async_playwright

    with NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        temp_path = tmp.name

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(args=["--no-sandbox"])
            page = await browser.new_page(
                viewport={"width": 1400, "height": 2200},
                device_scale_factor=1,
            )
            await page.set_content(html, wait_until="networkidle")
            await page.screenshot(path=temp_path, full_page=True)
            await browser.close()

        with open(temp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

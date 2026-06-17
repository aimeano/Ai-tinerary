/**
 * @file initMock.ts
 * @description In‑app mock API that intercepts requests to /api/* and returns
 *              in-memory data. This version mirrors the real backend response
 *              shape shown in GENERATED ITINERARY.txt:
 *
 *              {
 *                trip_id: string,
 *                title: string,
 *                profile: { ... },
 *                itinerary: { trip: {...}, days: [...] },
 *                itinerary_version: number,
 *                chat_history: any[],
 *                created_at: string,
 *                updated_at: string
 *              }
 *
 *              The frontend then normalizes this into { trip, days } inside
 *              TripDetail.tsx. Weather fields from the example are preserved
 *              but not dynamically updated.
 */

import type { TripSummary, TripPreferences } from '../types/trip'

/**
 * Sleep helper to simulate network latency.
 * @param ms - milliseconds to wait.
 */
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/**
 * Simple slug generator for created trips.
 * @param parts - input strings to combine.
 */
const slugify = (...parts: string[]) =>
  parts
    .join('-')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')

/**
 * Initial mock trip summaries used for dashboard.
 * These are lightweight cards – the full itinerary is returned
 * only when fetching /api/trips/:id.
 */
const INITIAL_TRIPS: TripSummary[] = [
  {
    id: 'trip_591faf67',
    title: 'Kuala Lumpur Trip',
    primaryCity: 'Kuala Lumpur',
    country: 'Malaysia',
    startDate: '14 Jul 2026',
    endDate: '16 Jul 2026',
    dayCount: 3,
    coverImageUrl:
      'https://pub-cdn.sider.ai/u/U04XHG42AO5/web-coder/6a0b2977a419c8a510478fe3/resource/b22b49ec-9ffb-4ef0-8a7c-6cc716123f37.jpg',
    status: 'ready',
  },
]

/**
 * In-memory storage for trip summaries.
 */
const tripSummaries: TripSummary[] = [...INITIAL_TRIPS]

/**
 * MOCK_TRIP_RESPONSE
 * -------------------
 * Payload adapted directly from GENERATED ITINERARY.txt.
 *
 * NOTE: This is intentionally typed as any to allow extra fields
 * (weather, itinerary_version, timestamps, etc.) without tightening frontend types.
 */
const MOCK_TRIP_RESPONSE: any = {
  trip_id: 'trip_591faf67',
  title: 'Kuala Lumpur Trip',
  profile: {
    country: 'Malaysia',
    cities: ['Kuala Lumpur'],
    start_date: '2026-07-14',
    end_date: '2026-07-16',
    days: 3,
    travel_style: 'relaxed',
    interests: ['food', 'nasi lemak', 'teh tarik'],
    must_include: [],
    flights: [
      {
        type: 'arrival',
        city: 'Kuala Lumpur',
        date: '2026-07-14',
        flight_number: 'mh67',
        time: '16:35',
        resolved_from: 'mh67',
        dep_iata: 'ICN',
        arr_iata: 'KUL',
      },
      {
        type: 'departure',
        city: 'Kuala Lumpur',
        date: '2026-07-16',
        flight_number: 'mh66',
        time: '23:30',
        resolved_from: 'mh66',
        dep_iata: 'KUL',
        arr_iata: 'ICN',
      },
    ],
  },
  itinerary: {
    trip: {
      country: 'Malaysia',
      cities: ['Kuala Lumpur'],
      duration_days: 3,
    },
    days: [
      {
        day: 1,
        date: '2026-07-14',
        title: 'City Centre Exploration',
        summary:
          "Begin your trip with a relaxed exploration of Kuala Lumpur's city centre, visiting cultural landmarks and enjoying some green spaces.",
        activities: [
          {
            time: '18:35',
            title: 'Bank Negara Malaysia Museum &amp; Gallery',
            location_name: 'Bank Negara Malaysia Museum and Art Gallery',
            latitude: 3.1571622,
            longitude: 101.6904754,
            category: 'culture',
            description:
              "Explore Malaysia's monetary history at the Bank Negara Malaysia Museum &amp; Gallery, conveniently located near your arrival point.",
            place_id: 'ChIJnWvAPjFIzDERoFfk1RGfzqc',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJnWvAPjFIzDERoFfk1RGfzqc',
            nearby_restaurants: [
              {
                name: 'Poolside Bistro @ Ideas Kuala Lumpur',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJi2tySLZJzDERv6bGpXDrDUs',
              },
              {
                name: 'The Ship Pertama',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJccoInS5IzDERH0fh4g8zh7o',
              },
              {
                name: 'Tea Garden Sogo KL',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJLRPctgtJzDERbRgLWYm1Mww',
              },
            ],
            travel_from_previous: null,
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-14',
              weather_code: 53,
              weather_category: 'drizzle',
              weather_description: 'Moderate drizzle',
              temperature_max: 32.2,
              temperature_min: 24.5,
              temperature_avg: 28.4,
              precipitation_sum: 1.1,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:16:43.498501',
              original_date: '2026-07-14',
              reference_date: '2025-07-14',
            },
            weather_action_available: false,
          },
          {
            time: '19:30',
            title: 'Tunku Abdul Rahman Memorial',
            location_name: 'Tunku Abdul Rahman Putra Memorial',
            latitude: 3.1564704,
            longitude: 101.6905323,
            category: 'culture',
            description:
              "Pay your respects at the Tunku Abdul Rahman Putra Memorial, a short stroll from the museum, dedicated to Malaysia's first Prime Minister.",
            place_id: 'ChIJB1bYHS5IzDERzuXJS_615Zk',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJB1bYHS5IzDERzuXJS_615Zk',
            nearby_restaurants: [
              {
                name: 'Poolside Bistro @ Ideas Kuala Lumpur',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJi2tySLZJzDERv6bGpXDrDUs',
              },
              {
                name: 'The Ship Pertama',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJccoInS5IzDERH0fh4g8zh7o',
              },
              {
                name: 'Tea Garden Sogo KL',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJLRPctgtJzDERbRgLWYm1Mww',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '0.8 km',
                duration: '3 mins',
                duration_seconds: 179,
              },
              walking: {
                distance: '0.4 km',
                duration: '6 mins',
                duration_seconds: 335,
              },
              transit: {
                distance: '0.4 km',
                duration: '6 mins',
                duration_seconds: 335,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-14',
              weather_code: 53,
              weather_category: 'drizzle',
              weather_description: 'Moderate drizzle',
              temperature_max: 32.2,
              temperature_min: 24.5,
              temperature_avg: 28.4,
              precipitation_sum: 1.1,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:16:47.532063',
              original_date: '2026-07-14',
              reference_date: '2025-07-14',
            },
            weather_action_available: false,
          },
          {
            time: '20:30',
            title: 'KLCC Park',
            location_name: 'KLCC Park',
            latitude: 3.1555902,
            longitude: 101.7147872,
            category: 'nature',
            description:
              'End your first day with a leisurely walk in KLCC Park, offering beautiful landscapes and a peaceful atmosphere after a long journey.',
            place_id: 'ChIJBWbm2tM3zDERTno0px940s4',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJBWbm2tM3zDERTno0px940s4',
            nearby_restaurants: [
              {
                name: 'Cili Kampung - Suria KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJJ1dGR2g3zDERUHSDro7EB1g',
              },
              {
                name: 'The Oriental Park KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJu5u2gJc3zDER9EUtkNOnt-U',
              },
              {
                name: 'Tien Non-Pork by Putien',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJ56SFYkI3zDER8nkCUzKEspk',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '7.9 km',
                duration: '13 mins',
                duration_seconds: 780,
              },
              walking: {
                distance: '3.7 km',
                duration: '53 mins',
                duration_seconds: 3194,
              },
              transit: {
                distance: '4.2 km',
                duration: '48 mins',
                duration_seconds: 2863,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-14',
              weather_code: 53,
              weather_category: 'drizzle',
              weather_description: 'Moderate drizzle',
              temperature_max: 32.2,
              temperature_min: 24.5,
              temperature_avg: 28.4,
              precipitation_sum: 1.1,
              is_bad_weather: true,
              suggestion:
                'Moderate drizzle. Consider replacing outdoor activities with indoor alternatives.',
              updated_at: '2026-06-13T21:16:50.624334',
              original_date: '2026-07-14',
              reference_date: '2025-07-14',
            },
            weather_action_available: true,
          },
        ],
      },
      {
        day: 2,
        date: '2026-07-15',
        title: 'Cultural and Museum Day',
        summary:
          "Dive into Kuala Lumpur's rich cultural heritage with visits to several museums and a historic temple.",
        activities: [
          {
            time: '09:00',
            title: 'National Textile Museum',
            location_name: 'National Textiles Museum',
            latitude: 3.1467465,
            longitude: 101.6940414,
            category: 'culture',
            description:
              "Start your day at the National Textile Museum, where you can learn about Malaysia's vibrant textile traditions.",
            place_id: 'ChIJ6_aE4M1JzDERegcsYEwivM4',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJ6_aE4M1JzDERegcsYEwivM4',
            nearby_restaurants: [
              {
                name: 'Hock Kee Heritage 福气安康 (Medan Pasar)',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJzaH3hAtJzDERGmZYFQeBwbI',
              },
              {
                name: 'Oriental Kopi • Dataran Merdeka',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJbUHYybBJzDER_zuug2DK2XQ',
              },
              {
                name: 'Warong Old China',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJt1wsCGBJzDERWu4dXyIpILA',
              },
            ],
            travel_from_previous: null,
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-15',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 33.6,
              temperature_min: 24.9,
              temperature_avg: 29.2,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:16:53.515089',
              original_date: '2026-07-15',
              reference_date: '2025-07-15',
            },
            weather_action_available: false,
          },
          {
            time: '10:30',
            title: 'Telekom Museum',
            location_name: 'Muzium Telekom',
            latitude: 3.1488889,
            longitude: 101.6994444,
            category: 'culture',
            description:
              'Visit the Telekom Museum to discover the evolution of telecommunications in Malaysia.',
            place_id: 'ChIJJSAtCNNJzDERETbGF9iz7CI',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJJSAtCNNJzDERETbGF9iz7CI',
            nearby_restaurants: [
              {
                name: 'Midoo Rasa-Salamira',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJF7pOi5ZJzDERa2dbIQnfopI',
              },
              {
                name: 'Mollagaa Restaurant',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJNdOY4uFJzDERwYLGPCzDGq0',
              },
              {
                name: 'High Street Art Cafe',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJuxRHG51JzDERfs14_bThbxk',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '0.8 km',
                duration: '3 mins',
                duration_seconds: 208,
              },
              walking: {
                distance: '0.8 km',
                duration: '11 mins',
                duration_seconds: 686,
              },
              transit: {
                distance: '0.8 km',
                duration: '11 mins',
                duration_seconds: 686,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-15',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 33.6,
              temperature_min: 24.9,
              temperature_avg: 29.2,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:17:00.134843',
              original_date: '2026-07-15',
              reference_date: '2025-07-15',
            },
            weather_action_available: false,
          },
          {
            time: '12:00',
            title: 'Sri Maha Mariamman Temple',
            location_name: 'Sri Maha Mariamman Temple',
            latitude: 3.1433851,
            longitude: 101.6964976,
            category: 'religious',
            description:
              "Explore the Sri Maha Mariamman Temple, one of the oldest Hindu temples in Kuala Lumpur, known for its vibrant architecture and cultural significance.",
            place_id: 'ChIJUXIQqzJIzDERDbwltFc9Pm8',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJUXIQqzJIzDERDbwltFc9Pm8',
            nearby_restaurants: [
              {
                name: 'UpperDeck KL',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJO46b3KRJzDER5gWHHPiswpk',
              },
              {
                name: 'Upper House',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJ0WwEroNJzDER0JRvEBLdivU',
              },
              {
                name: 'Deeriang Restaurant',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJhxLOKoRJzDERZdtgcqw-SSk',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '1.5 km',
                duration: '6 mins',
                duration_seconds: 352,
              },
              walking: {
                distance: '0.8 km',
                duration: '12 mins',
                duration_seconds: 715,
              },
              transit: {
                distance: '0.8 km',
                duration: '12 mins',
                duration_seconds: 715,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-15',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 33.6,
              temperature_min: 24.9,
              temperature_avg: 29.2,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:17:02.743956',
              original_date: '2026-07-15',
              reference_date: '2025-07-15',
            },
            weather_action_available: false,
          },
          {
            time: '14:00',
            title: 'Petronas Arts Gallery',
            location_name: 'GALERI PETRONAS',
            latitude: 3.158154,
            longitude: 101.7120899,
            category: 'culture',
            description:
              'Spend your afternoon at the Petronas Arts Gallery, showcasing contemporary Malaysian art in a modern setting.',
            place_id: 'ChIJH5xmLdE3zDERMjKKtdc41cQ',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJH5xmLdE3zDERMjKKtdc41cQ',
            nearby_restaurants: [
              {
                name: 'Cili Kampung - Suria KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJJ1dGR2g3zDERUHSDro7EB1g',
              },
              {
                name: 'The Oriental Park KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJu5u2gJc3zDER9EUtkNOnt-U',
              },
              {
                name: 'Fork It! - Suria KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJe5ja27I3zDER97onw2XCIsw',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '7.2 km',
                duration: '12 mins',
                duration_seconds: 740,
              },
              walking: {
                distance: '2.9 km',
                duration: '41 mins',
                duration_seconds: 2476,
              },
              transit: {
                distance: '4.3 km',
                duration: '31 mins',
                duration_seconds: 1875,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-15',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 33.6,
              temperature_min: 24.9,
              temperature_avg: 29.2,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:17:08.573637',
              original_date: '2026-07-15',
              reference_date: '2025-07-15',
            },
            weather_action_available: false,
          },
        ],
      },
      {
        day: 3,
        date: '2026-07-16',
        title: 'Entertainment and Urban Experience',
        summary:
          'Enjoy a relaxed day with a mix of entertainment and urban exploration, ending with a timely departure to the airport.',
        activities: [
          {
            time: '09:00',
            title: 'Museum of Illusions',
            location_name: 'Museum Of Illusions Kuala Lumpur',
            latitude: 3.1471339,
            longitude: 101.7121372,
            category: 'culture',
            description:
              'Begin your final day with fun and interactive exhibits at the Museum of Illusions Kuala Lumpur.',
            place_id: 'ChIJAQAw-is2zDER-IZQA10XVP8',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJAQAw-is2zDER-IZQA10XVP8',
            nearby_restaurants: [
              {
                name: 'Ferria KL',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJwUmGenw3zDER170__VHoLKo',
              },
              {
                name: 'Abang Adek Bukit Bintang',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJMX_0aAA3zDERZ1rN9eu3tSc',
              },
              {
                name: "Arthur's Storehouse Pavilion Kuala Lumpur",
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJpasAxWc3zDER-8yagPA83Cg',
              },
            ],
            travel_from_previous: null,
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-16',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 35.8,
              temperature_min: 25.5,
              temperature_avg: 30.6,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:17:10.793620',
              original_date: '2026-07-16',
              reference_date: '2025-07-16',
            },
            weather_action_available: false,
          },
          {
            time: '10:30',
            title: 'Urban Museum',
            location_name: 'UR-MU @ Bukit Bintang',
            latitude: 3.1476079,
            longitude: 101.7094947,
            category: 'culture',
            description:
              "Explore the Urban Museum, which offers a unique perspective on Kuala Lumpur's urban development and art.",
            place_id: 'ChIJ8zPgFPk3zDERsyZ2pJTrrP8',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJ8zPgFPk3zDERsyZ2pJTrrP8',
            nearby_restaurants: [
              {
                name: 'IVY Rooftop Restaurant Bar &amp; Lounge',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJ8U2Z1Ls3zDERH9-HNnzH_GA',
              },
              {
                name: 'PUBLICANS 良品公館',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJe57RAyA3zDERuPjW9sO0B98',
              },
              {
                name: "Reuben's KL",
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJpUvhDts3zDERGKZh_e3IJyk',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '1.2 km',
                duration: '8 mins',
                duration_seconds: 465,
              },
              walking: {
                distance: '0.5 km',
                duration: '7 mins',
                duration_seconds: 398,
              },
              transit: {
                distance: '0.5 km',
                duration: '7 mins',
                duration_seconds: 398,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-16',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 35.8,
              temperature_min: 25.5,
              temperature_avg: 30.6,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion: 'This activity is weather-safe.',
              updated_at: '2026-06-13T21:17:17.764125',
              original_date: '2026-07-16',
              reference_date: '2025-07-16',
            },
            weather_action_available: false,
          },
          {
            time: '12:00',
            title: 'Superpark Malaysia',
            location_name: 'SuperPark Malaysia',
            latitude: 3.1591675,
            longitude: 101.7129914,
            category: 'entertainment',
            description:
              'Spend your afternoon at Superpark Malaysia, a family-friendly entertainment venue with various attractions.',
            place_id: 'ChIJVS4Wdas3zDERTQiiUgNQnlI',
            google_maps_url:
              'https://www.google.com/maps/place/?q=place_id:ChIJVS4Wdas3zDERTQiiUgNQnlI',
            nearby_restaurants: [
              {
                name: 'Cili Kampung - Suria KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJJ1dGR2g3zDERUHSDro7EB1g',
              },
              {
                name: 'The Oriental Park KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJu5u2gJc3zDER9EUtkNOnt-U',
              },
              {
                name: 'Fork It! - Suria KLCC',
                link: 'https://www.google.com/maps/place/?q=place_id:ChIJe5ja27I3zDER97onw2XCIsw',
              },
            ],
            travel_from_previous: {
              driving: {
                distance: '2.1 km',
                duration: '9 mins',
                duration_seconds: 535,
              },
              walking: {
                distance: '2.0 km',
                duration: '28 mins',
                duration_seconds: 1671,
              },
              transit: {
                distance: '2.0 km',
                duration: '28 mins',
                duration_seconds: 1671,
              },
            },
            weather: {
              available: true,
              source: 'historical',
              date: '2025-07-16',
              weather_code: 3,
              weather_category: 'partly_cloudy',
              weather_description: 'Overcast',
              temperature_max: 35.8,
              temperature_min: 25.5,
              temperature_avg: 30.6,
              precipitation_sum: 0,
              is_bad_weather: false,
              suggestion:
                'Overcast. Weather looks suitable for this activity.',
              updated_at: '2026-06-13T21:17:20.214291',
              original_date: '2026-07-16',
              reference_date: '2025-07-16',
            },
            weather_action_available: false,
          },
          {
            time: '19:30',
            title: 'Depart to Airport',
            location_name: '',
            latitude: null,
            longitude: null,
            category: '',
            description: 'Head to the airport for your departure flight.',
            nearby_restaurants: [],
            travel_from_previous: null,
            weather: {
              available: false,
              is_bad_weather: false,
              note: 'Missing activity coordinates.',
            },
            weather_action_available: false,
          },
        ],
      },
    ],
  },
  itinerary_version: 1,
  chat_history: [],
  created_at: '2026-06-13T12:17:20.279090+00:00',
  updated_at: '2026-06-13T12:17:20.279090+00:00',
}

/**
 * Stream SSE helper — returns a Response whose body is a ReadableStream
 * that emits event strings at intervals.
 * @param events - array of SSE-formatted strings.
 * @param delayMs - delay between events.
 */
function sseResponse(events: string[], delayMs = 600): Response {
  const stream = new ReadableStream({
    start(controller) {
      let i = 0
      const iv = setInterval(() => {
        if (i >= events.length) {
          controller.enqueue(
            new TextEncoder().encode('event: done\ndata: {}\n\n'),
          )
          controller.close()
          clearInterval(iv)
          return
        }
        controller.enqueue(new TextEncoder().encode(`${events[i]}\n\n`))
        i += 1
      }, delayMs)
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream;charset=UTF-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}

/**
 * Main mock fetch patch. Intercepts /api/* routes and returns mock responses
 * that mirror the real backend contract.
 */
function patchFetch() {
  // Avoid double-patching
  // @ts-ignore
  if ((window as any).__MOCK_API_INSTALLED__) return
  // @ts-ignore
  ;(window as any).__MOCK_API_INSTALLED__ = true

  const originalFetch = window.fetch.bind(window)

  window.fetch = async (input: RequestInfo, init?: RequestInit) => {
    const method =
      (init && init.method) || (input instanceof Request ? input.method : 'GET')
    const url = (typeof input === 'string' ? input : input.url) || ''
    const u = new URL(url, window.location.origin)
    const path = u.pathname

    // Only intercept /api/* requests
    if (!path.startsWith('/api/')) {
      return originalFetch(input, init)
    }

    // Simulate network latency for all API calls
    await sleep(300 + Math.random() * 300)

    try {
      // GET /api/trips  -> list of trip summaries
      if (path === '/api/trips' && method === 'GET') {
        return new Response(JSON.stringify(tripSummaries), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      // POST /api/trips  (create trip; returns new ID)
      if (path === '/api/trips' && method === 'POST') {
        const body = init?.body ? JSON.parse(String(init.body)) : {}
        const prefs: TripPreferences = body
        const id = slugify(
          prefs.cities?.[0] || prefs.country || 'trip',
          Date.now().toString().slice(-4),
        )

        const summary: TripSummary = {
          id,
          title: `${prefs.cities?.[0] || prefs.country || 'Trip'}`,
          primaryCity: prefs.cities?.[0] || prefs.country || 'destination',
          country: prefs.country || 'Unknown',
          startDate: prefs.startDate || 'TBD',
          endDate: 'TBD',
          dayCount: prefs.days || 2,
          coverImageUrl: '',
          status: 'generating',
        }
        tripSummaries.unshift(summary)

        // Flip to ready after a short delay to simulate generation.
        ;(async () => {
          await sleep(1200 + (prefs.days || 2) * 200)
          tripSummaries.forEach((t) => {
            if (t.id === id) t.status = 'ready'
          })
        })()

        return new Response(JSON.stringify({ id }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      // GET /api/trips/:id -> returns generated itinerary response
      const tripIdMatch = path.match(/^\/api\/trips\/([^/]+)\/?$/)
      if (tripIdMatch && method === 'GET') {
        // In this mock, we always return the same Kuala Lumpur example regardless of ID.
        return new Response(JSON.stringify(MOCK_TRIP_RESPONSE), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      // POST /api/trips/:id/chat -> simple echo-style assistant reply
      const chatMatch = path.match(/^\/api\/trips\/([^/]+)\/chat\/?$/)
      if (chatMatch && method === 'POST') {
        const id = chatMatch[1]
        const reqBody = init?.body ? JSON.parse(String(init.body)) : {}
        const message: string = reqBody.message || reqBody.text || ''
        const assistantReply = {
          id: `mock-assistant-${Date.now()}`,
          role: 'assistant',
          content: `Mock reply for trip ${id}: I received your message: "${String(
            message,
          ).slice(
            0,
            200,
          )}". You can ask me to adjust your Kuala Lumpur itinerary, add attractions, or refine restaurants.`,
          createdAt: new Date().toISOString(),
        }
        await sleep(500 + Math.random() * 500)
        return new Response(JSON.stringify(assistantReply), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      // GET /api/trips/:id/itinerary/stream (SSE simulation, streaming days)
      const sseMatch = path.match(
        /^\/api\/trips\/([^/]+)\/itinerary\/stream\/?$/,
      )
      if (sseMatch && method === 'GET') {
        const days = MOCK_TRIP_RESPONSE.itinerary?.days || []
        const events = days.map(
          (d: any) => `data: ${JSON.stringify({ type: 'day', day: d })}`,
        )
        return sseResponse(events, 700)
      }

      // Fallback: unknown API path -> 404
      return new Response(JSON.stringify({ error: 'Mock API: Not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    } catch (err) {
      return new Response(JSON.stringify({ error: 'Mock API: internal' }), {
        status: 500,
      })
    }
  }
}

/**
 * Initialize mock API if in development.
 * Importing this file will patch fetch.
 */
export function initMockApi() {
  // Check environment — only auto-install in non-production
  // Vite exposes import.meta.env.MODE; fall back to NODE_ENV
  // @ts-ignore
  const mode =
    typeof import.meta !== 'undefined' && import.meta.env
      ? import.meta.env.MODE
      : process.env.NODE_ENV
  if (mode === 'production') return
  patchFetch()
}

// Auto-initialize (safe: init checks mode)
//initMockApi()
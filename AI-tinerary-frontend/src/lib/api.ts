/**
 * frontend/src/lib/api.ts
 * @file api.ts
 * @description Consolidated API service for all backend communication
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

// Helper to get auth headers
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token");
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

// Helper for authenticated fetch
async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {},
): Promise<any> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    // Token expired or invalid
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    window.location.href = "/login";
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${response.statusText}`);
  }

  return response.json();
}

// Authentication API
export const auth = {
  signup: async (email: string, password: string, name: string) => {
    const response = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Signup failed");
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user_id", data.user_id);
    return data;
  },

  login: async (email: string, password: string) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Login failed");
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user_id", data.user_id);
    return data;
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
  },
};

// Trips API
export const trips = {
  list: () => authenticatedFetch("/trips"),

  get: (tripId: string) => authenticatedFetch(`/trips/${tripId}`),

  create: async (tripData: {
    country: string;
    cities: string[];
    start_date: string;
    end_date: string;
    travel_style: string;
    interests: string[];
    budget: string;
    must_include: string[];
    arrival_flight_number?: string;
    departure_flight_number?: string;
  }) => {
    return authenticatedFetch("/trips", {
      method: "POST",
      body: JSON.stringify(tripData),
    });
  },

  delete: (tripId: string) =>
    authenticatedFetch(`/trips/${tripId}`, {
      method: "DELETE",
    }),

  chat: (tripId: string, message: string) =>
    authenticatedFetch(`/trips/${tripId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  weatherReplace: (tripId: string, day: number, activity_index: number) =>
    authenticatedFetch(`/trips/${tripId}/weather-replace`, {
      method: "POST",
      body: JSON.stringify({ day, activity_index }),
    }),

  undo: (tripId: string) =>
    authenticatedFetch(`/trips/${tripId}/undo`, {
      method: "POST",
    }),
};

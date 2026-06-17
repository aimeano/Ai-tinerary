/**
 * frontend/src/lib/assistant.ts
 * @file assistant.ts
 * @description Updated to perform real HTTP requests to the
 *              local Python FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token");
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

/**
 * sendAssistantRequest
 * Forwards structured payloads to the Python backend's API endpoint.
 * Returns a standardized shape containing the assistant's response
 * and optional modified itinerary day data.
 *
 * @param payload - Structured payload describing the requested assistant action.
 * @returns Promise resolving to the backend assistant response.
 */

/**
 * frontend/src/lib/assistant.ts
 */
export async function sendAssistantRequest(payload: any): Promise<{
  assistantMessage: string;
  updatedDay?: any;
}> {
  try {
    const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
    const token = localStorage.getItem("access_token");

    const response = await fetch(`${API_BASE}/trips/${payload.tripId}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        message: payload.message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          `Server returned an error status: ${response.status}`,
      );
    }

    const data = await response.json();

    // ✅ Build updatedDay with the itinerary flag
    let updatedDay = undefined;
    if (data.itinerary_updated && data.itinerary) {
      // Extract the specific day that was updated
      // Assuming payload contains dayNumber or we need to identify which day changed
      const dayNumber = payload.dayNumber;

      updatedDay = {
        day: dayNumber,
        activities: data.itinerary?.days?.[dayNumber - 1]?.activities || [],
        title: data.itinerary?.days?.[dayNumber - 1]?.title,
        date: data.itinerary?.days?.[dayNumber - 1]?.date,
        itinerary: true, // ← KEY FIX: Add this flag so ChatPanel dispatches the event
      };
    }

    return {
      assistantMessage: data.message || "Response received.",
      updatedDay,
    };
  } catch (error) {
    console.error(
      "Failed to communicate with the travel assistant backend:",
      error,
    );
    throw error;
  }
}

/**
 * sendWeatherReplaceRequest
 * Sends a request to replace activities for bad weather conditions
 *
 * @param tripId - The trip ID
 * @param day - Day number (1-indexed)
 * @param activity_index - Index of the activity to replace
 * @returns Promise resolving to updated itinerary
 */
export async function sendWeatherReplaceRequest(
  tripId: string,
  day: number,
  activity_index: number,
): Promise<{ assistantMessage: string; updatedItinerary: any }> {
  try {
    const response = await fetch(
      `${API_BASE}/trips/${tripId}/weather-replace`,
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          day,
          activity_index,
        }),
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          `Server returned an error status: ${response.status}`,
      );
    }

    const data = await response.json();

    return {
      assistantMessage: data.message,
      updatedItinerary: data.itinerary,
    };
  } catch (error) {
    console.error("Failed to replace weather activity:", error);
    throw error;
  }
}

/**
 * undoItinerary
 * Reverts the itinerary to the previous version
 *
 * @param tripId - The trip ID
 * @returns Promise resolving to restored itinerary
 */
export async function undoItinerary(tripId: string): Promise<any> {
  try {
    const response = await fetch(`${API_BASE}/trips/${tripId}/undo`, {
      method: "POST",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          `Server returned an error status: ${response.status}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to undo itinerary:", error);
    throw error;
  }
}

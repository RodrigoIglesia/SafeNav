// src/api.js
/*
 * API module for interacting with the SafeNav Core backend.
 * Provides the API call to the /routes/ endpoint.
 */
//TODO: Add endpoint to pass city to the backend, so it can use city-specific data for routing and safety analysis. The backend must change a config file, and only retrieve data of that config file.
//TODO: The request must be sent when loading the paga (refresh city) or in change
//TODO: This interface has to be added in the design and scenarios (scenario_0 modification)
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";



/**
 * Function to send a route request to the SafeNav Core API.
 *
 * @param {Object} routeRequest - Object with origin, destination, and preferences.
 * @returns {Promise<Object>} Route response from the backend.
 */
export async function requestRoute(routeRequest) {
  const response = await fetch(`${API_BASE_URL}/routes/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(routeRequest),
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}
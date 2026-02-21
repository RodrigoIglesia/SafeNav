// src/api.js
/*
 * API module for interacting with the SafeNav Core backend.
 * Provides the API call to the /routes/ endpoint.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";



/**
 * Sends a route request to the SafeNav Core API.
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

/**
 * Sends a map request to the SafeNav Core API.
 *
 * @param {Object} mapRequest - Object describing the area and zoom level.
 * @returns {Promise<Object>} MapDataResponse from the backend.
 */
export async function requestMap(mapRequest) {
  const response = await fetch(`${API_BASE_URL}/map/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mapRequest),
  });

  if (!response.ok) {
    throw new Error(`Map API Error: ${response.status}`);
  }

  return response.json();
}

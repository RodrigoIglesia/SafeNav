// src/components/FloatingRoutePanel.jsx

import { useState } from "react";
import "./FloatingRoutePanel.css";
import { requestRoute } from "../api.js";
// import { toGeoPoint } from "../utils/geo";

let originTimeout;
let destinationTimeout;

// ==============================
// Geocode
// ==============================
async function geocode(address) {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`
  );

  const results = await response.json();
  if (results.length === 0) return null;

  return [parseFloat(results[0].lat), parseFloat(results[0].lon)];
}

// ==============================
// Search with city bounds
// ==============================
async function searchPlaces(query, bounds) {
  //
  // Nominatim librarie to search places and show suggestions
  //
  if (!query || query.length < 3) return [];

  try {
    let url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(query)}`;

    if (bounds) {
      const [[south, west], [north, east]] = bounds;
      url += `&viewbox=${west},${north},${east},${south}&bounded=1`;
    }

    const response = await fetch(url, {
      headers: { Accept: "application/json" }
    });

    if (!response.ok) return [];

    return await response.json();

  } catch (error) {
    console.error("Search failed:", error);
    return [];
  }
}

// ==============================
// Component
// ==============================
export default function FloatingRoutePanel({
  onRouteChange,
  onMapStyleChange,
  onCityChange,
  activeCityBounds,
  selectedCity,
  cities
}) {

  const [originCoords, setOriginCoords] = useState(null);
  const [destinationCoords, setDestinationCoords] = useState(null);

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);

  const [expanded, setExpanded] = useState(true);

  const styles = [
    { name: "Light", url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" },
    { name: "Std", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" },
    { name: "Dark", url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" },
    { name: "Topo", url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" }
  ];

  // ==============================
  // Submit
  // ==============================
  const handleSubmit = async () => {
    if (!origin || !destination) return;

    try {
      // Obtain Geocode of the selected suggestion
      //TODO: Move to backend
      const finalOrigin =
        originCoords || await geocode(origin);

      const finalDestination =
        destinationCoords || await geocode(destination);

      if (!finalOrigin || !finalDestination) {
        alert("Could not find one of the locations.");
        return;
      }

      const routeRequest = {
        origin: {
          lat: finalOrigin[0],
          lon: finalOrigin[1]
        },
        destination: {
          lat: finalDestination[0],
          lon: finalDestination[1]
        },
        preferences: null
      };

      const routeResponse = await requestRoute(routeRequest);
      console.log("Route response in panel:", routeResponse);
      onRouteChange({
        origin: finalOrigin,
        destination: finalDestination,
        route: routeResponse
      });

    } catch (error) {
      console.error("Route request failed:", error);
      alert("Error requesting route.");
    }
  };

  // ==============================
  // Origin change
  // ==============================
  const handleOriginChange = (value) => {
    setOrigin(value);
    setOriginCoords(null);
    clearTimeout(originTimeout);

    originTimeout = setTimeout(async () => {
      const results = await searchPlaces(value, activeCityBounds);
      setOriginSuggestions(results);
    }, 300);
  };

  // ==============================
  // Destination change
  // ==============================
  const handleDestinationChange = (value) => {
    setDestination(value);
    setDestinationCoords(null);
    clearTimeout(destinationTimeout);

    destinationTimeout = setTimeout(async () => {
      const results = await searchPlaces(value, activeCityBounds);
      setDestinationSuggestions(results);
    }, 300);
  };

  return (
    <div className={`route-panel ${expanded ? "expanded" : "collapsed"}`}>

      <div className="route-panel-header">
        <span>Route Planner</span>
        <button
          className="route-panel-toggle"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "−" : "+"}
        </button>
      </div>

      {expanded && (
        <div className="route-panel-body">

          {/* CITY SELECTOR */}
          <div className="city-selector">
            <select
              value={selectedCity}
              onChange={(e) => onCityChange(e.target.value)}
            >
              {Object.entries(cities).map(([key, city]) => (
                <option key={key} value={key}>
                  {city.label}
                </option>
              ))}
            </select>
          </div>

          {/* ORIGIN */}
          <input
            type="text"
            placeholder="Origin"
            value={origin}
            onChange={(e) => handleOriginChange(e.target.value)}
          />

          {originSuggestions.length > 0 && (
            <div className="suggestions">
              {originSuggestions.map((place) => (
                <div
                  key={place.place_id}
                  className="suggestion-item"
                  onClick={() => {
                    setOrigin(place.display_name);
                    setOriginCoords([parseFloat(place.lat), parseFloat(place.lon)]);
                    setOriginSuggestions([]);
                  }}
                >
                  {place.display_name}
                </div>
              ))}
            </div>
          )}

          {/* DESTINATION */}
          <input
            type="text"
            placeholder="Destination"
            value={destination}
            onChange={(e) => handleDestinationChange(e.target.value)}
          />

          {destinationSuggestions.length > 0 && (
            <div className="suggestions">
              {destinationSuggestions.map((place) => (
                <div
                  key={place.place_id}
                  className="suggestion-item"
                  onClick={() => {
                    setDestination(place.display_name);
                    setDestinationCoords([parseFloat(place.lat), parseFloat(place.lon)]);
                    setDestinationSuggestions([]);
                  }}
                >
                  {place.display_name}
                </div>
              ))}
            </div>
          )}

          <button onClick={handleSubmit}>
            Calculate Route
          </button>

          <div className="map-style-selector">
            <select onChange={(e) => onMapStyleChange(e.target.value)}>
              {styles.map((style) => (
                <option key={style.name} value={style.url}>
                  {style.name}
                </option>
              ))}
            </select>
          </div>

        </div>
      )}
    </div>
  );
}
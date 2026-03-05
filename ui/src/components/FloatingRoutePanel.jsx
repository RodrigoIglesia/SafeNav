// src/components/FloatingRoutePanel.jsx

import { useState } from "react";
import "./FloatingRoutePanel.css";

// Geocode address to coordinates
async function geocode(address) {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`
  );

  const results = await response.json();

  if (results.length === 0) return null;

  return [parseFloat(results[0].lat), parseFloat(results[0].lon)];
}

// Search places for autocomplete
async function searchPlaces(query) {
  if (!query) return [];

  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(query)}`
  );

  return await response.json();
}

export default function FloatingRoutePanel({ onRouteChange, onMapStyleChange }) {

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);

  const [expanded, setExpanded] = useState(true);

  const styles = [
    { name: "Std", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" },
    { name: "Dark", url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" },
    { name: "Light", url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" },
    { name: "Topo", url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" }
  ];

  const handleSubmit = async () => {

    if (!origin || !destination) return;

    const originCoords = await geocode(origin);
    const destinationCoords = await geocode(destination);

    if (!originCoords || !destinationCoords) {
      alert("Could not find one of the locations.");
      return;
    }

    onRouteChange({
      origin: originCoords,
      destination: destinationCoords,
    });
  };

  const handleOriginChange = async (value) => {
    setOrigin(value);

    const results = await searchPlaces(value);
    setOriginSuggestions(results);
  };

  const handleDestinationChange = async (value) => {
    setDestination(value);

    const results = await searchPlaces(value);
    setDestinationSuggestions(results);
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
// src/components/FloatingRoutePanel.jsx

import { useState } from "react";
import "./FloatingRoutePanel.css";

export default function FloatingRoutePanel({ onRouteChange, onMapStyleChange }) {

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [expanded, setExpanded] = useState(true);
  const styles = [
    { name: "Std", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" },
    { name: "Dark", url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" },
    { name: "Light", url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" },
    { name: "Topo", url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" }
  ];

  const handleSubmit = () => {
    if (!origin || !destination) return;

    onRouteChange({
      origin,
      destination,
    });
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

          <input
            type="text"
            placeholder="Origin"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
          />

          <input
            type="text"
            placeholder="Destination"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
          />

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
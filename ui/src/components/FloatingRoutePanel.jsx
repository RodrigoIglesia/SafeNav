// src/components/FloatingRoutePanel.jsx

import { useState } from "react";
import "./FloatingRoutePanel.css";

export default function FloatingRoutePanel({ onRouteChange }) {

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [expanded, setExpanded] = useState(true);

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

        </div>
      )}

    </div>
  );
}
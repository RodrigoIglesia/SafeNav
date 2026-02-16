// src/App.jsx
import { useState } from "react";
import { requestRoute, requestMap } from "./api";
// import "leaflet/dist/leaflet.css";

function App() {
  const [loading, setLoading] = useState(false);
  const [routeResult, setRouteResult] = useState(null);
  const [mapResult, setMapResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRequestRoute = async () => {
    setLoading(true);
    setError(null);
    setRouteResult(null);
    setMapResult(null);

    try {
      const routeRequest = {
        origin: { lat: 40.4168, lon: -3.7038 },
        destination: { lat: 40.4379, lon: -3.6793 },
        preferences: {
          minimize_sun: true,
          avoid_hazard_zones: false,
          prioritize_speed: false,
          comfort_weight: 0.7,
        },
      };

      const response = await requestRoute(routeRequest);
      setRouteResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestMap = async () => {
  setLoading(true);
  setError(null);
  setRouteResult(null);
  setMapResult(null);

  try {
    const mapRequest = {
      area: {
        coordinates: [
          { lat: 40.4, lon: -3.72 },
          { lat: 40.4, lon: -3.67 },
          { lat: 40.45, lon: -3.67 },
          { lat: 40.45, lon: -3.72 }
        ]
      },
      zoom_level: 14,
      include_tiles: true,
      include_metadata: true
    };

    const response = await requestMap(mapRequest);
    setMapResult(response);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};


  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>🌞 SafeNav UI</h1>
      <p>Test the integration between the frontend and the SafeNav Core API.</p>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <button
          onClick={handleRequestRoute}
          disabled={loading}
          style={{
            padding: "0.6rem 1.2rem",
            fontSize: "1rem",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          {loading ? "Requesting..." : "Request Safe Route"}
        </button>

        <button
          onClick={handleRequestMap}
          disabled={loading}
          style={{
            padding: "0.6rem 1.2rem",
            fontSize: "1rem",
            backgroundColor: "#28a745",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          {loading ? "Requesting..." : "Request Map"}
        </button>
      </div>

      {error && (
        <p style={{ color: "red", marginTop: "1rem" }}>
          ❌ Error: {error}
        </p>
      )}

      {routeResult && (
        <>
          <h3>Route Response:</h3>
          <pre
            style={{
              marginTop: "0.5rem",
              background: "#f4f4f4",
              padding: "1rem",
              borderRadius: "8px",
              textAlign: "left",
              fontSize: "0.9rem",
            }}
          >
            {JSON.stringify(routeResult, null, 2)}
          </pre>
        </>
      )}

      {mapResult && (
        <>
          <h3>Map Response:</h3>
          <pre
            style={{
              marginTop: "0.5rem",
              background: "#f4f4f4",
              padding: "1rem",
              borderRadius: "8px",
              textAlign: "left",
              fontSize: "0.9rem",
            }}
          >
            {JSON.stringify(mapResult, null, 2)}
          </pre>
        </>
      )}
    </div>
  );
}

export default App;

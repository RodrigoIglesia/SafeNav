// src/App.jsx
import { useState } from "react";
import { requestRoute } from "./api";

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRequestRoute = async () => {
    setLoading(true);
    setError(null);
    try {
      const routeRequest = {
        origin: { lat: 40.4168, lon: -3.7038 }, // Madrid center
        destination: { lat: 40.4379, lon: -3.6793 }, // Northeast Madrid
        preferences: {
          minimize_sun: true,
          avoid_hazard_zones: false,
          prioritize_speed: false,
          comfort_weight: 0.7,
        },
      };

      const response = await requestRoute(routeRequest);
      setResult(response);
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

      {error && (
        <p style={{ color: "red", marginTop: "1rem" }}>❌ Error: {error}</p>
      )}

      {result && (
        <pre
          style={{
            marginTop: "1rem",
            background: "#f4f4f4",
            padding: "1rem",
            borderRadius: "8px",
            textAlign: "left",
            fontSize: "0.9rem",
          }}
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;

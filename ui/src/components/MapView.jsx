// src/components/MapView.jsx

import { useEffect, useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import { requestMap } from "../api";
import TileLayerRenderer from "./TileLayerRenderer";
import LoadingScreen from "./LoadingScreen";
import "leaflet/dist/leaflet.css";

export default function MapView() {
  const [mapData, setMapData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDefaultMap = async () => {
      try {
        const response = await requestMap({
          area: {
            coordinates: [
              { lat: 40.40, lon: -3.72 },
              { lat: 40.40, lon: -3.67 },
              { lat: 40.45, lon: -3.67 },
              { lat: 40.45, lon: -3.72 }
            ]
          },
          zoom_level: 14,
          include_tiles: true,
          include_metadata: true,
        });

        setMapData(response.map);
      } catch (err) {
        console.error("Map loading error:", err);
        setError(err.message);
      }
    };

    loadDefaultMap();
  }, []);

  if (error) {
    return (
      <div style={styles.centered}>
        <p style={{ color: "red" }}>❌ {error}</p>
      </div>
    );
  }

  if (!mapData) {
    return <LoadingScreen message="Loading SafeNav map..." />;
  }

  const center = calculateCenter(mapData.tiles);

  return (
    <MapContainer
      center={center}
      zoom={mapData.metadata.zoom_level}
      style={{ height: "100vh", width: "100%" }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <TileLayerRenderer tiles={mapData.tiles} />
    </MapContainer>
  );
}

// ==========================================================
// Helpers
// ==========================================================

function calculateCenter(tiles) {
  if (!tiles || tiles.length === 0) {
    return [40.4168, -3.7038]; // fallback
  }

  const coords = tiles[0].bounds.coordinates;

  const lats = coords.map((c) => c.lat);
  const lons = coords.map((c) => c.lon);

  return [
    (Math.min(...lats) + Math.max(...lats)) / 2,
    (Math.min(...lons) + Math.max(...lons)) / 2,
  ];
}

const styles = {
  centered: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    fontSize: "1.1rem",
  },
};
// src/components/MapView.jsx

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import { requestMap } from "../api";
import "leaflet/dist/leaflet.css";

export default function MapView() {
  const [mapData, setMapData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadMap = async () => {
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
        setMapData(response.map);
      } catch (err) {
        setError(err.message);
      }
    };

    loadMap();
  }, []);

  const convertPolygon = (bounds) => {
    return bounds.coordinates[0].map(coord => [
      coord[1], // lat
      coord[0]  // lon
    ]);
  };

  if (error) {
    return <p style={{ color: "red" }}>❌ {error}</p>;
  }

  if (!mapData) {
    return <p>Loading map...</p>;
  }

  return (
    <MapContainer
      center={[40.425, -3.695]}
      zoom={mapData.metadata.zoom_level}
      style={{ height: "100vh", width: "100%" }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {mapData.tiles.map(tile => (
        <Polygon
          key={tile.id}
          positions={convertPolygon(tile.bounds)}
          pathOptions={{ color: "blue", weight: 1 }}
        />
      ))}
    </MapContainer>
  );
}

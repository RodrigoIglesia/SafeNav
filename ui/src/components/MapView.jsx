// src/components/MapView.jsx

import { useState, useRef, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  ZoomControl,
  Marker,
  useMap
} from "react-leaflet";
import L from "leaflet";
import FloatingRoutePanel from "./FloatingRoutePanel";
import "leaflet/dist/leaflet.css";

// Fix default marker icons (Leaflet + Vite/React issue)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png"
});

const DEFAULT_CENTER = [40.4168, -3.7038];
const DEFAULT_ZOOM = 13;

// Component to fit map bounds to route
function FitBounds({ origin, destination }) {
  const map = useMap();

  useEffect(() => {
    if (origin && destination) {
      const bounds = [origin, destination];
      map.fitBounds(bounds, { padding: [80, 80] });
    }
  }, [origin, destination, map]);

  return null;
}

// Component that automatically adjusts the map view
function FitCityBounds({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [40, 40] });
      map.setMaxBounds(bounds);
    }
  }, [bounds, map]);

  return null;
}

export default function MapView() {
  const [tileUrl, setTileUrl] = useState(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
  );

  const [route, setRoute] = useState({
    origin: null,
    destination: null
  });

  const errorTimeoutRef = useRef(null);
  const successTimeoutRef = useRef(null);
  const [osmReachable, setOsmReachable] = useState(true);

  const [cityBounds, setCityBounds] = useState(null);

  const handleTileLoad = () => {
    if (errorTimeoutRef.current) clearTimeout(errorTimeoutRef.current);
    successTimeoutRef.current = setTimeout(() => setOsmReachable(true), 200);
  };

  const handleTileError = () => {
    if (successTimeoutRef.current) clearTimeout(successTimeoutRef.current);
    errorTimeoutRef.current = setTimeout(() => setOsmReachable(false), 1500);
  };

  const handleRouteChange = ({ origin, destination }) => {
    console.log("Route requested:", origin, destination);

    setRoute({
      origin,
      destination
    });
  };

  const handleCityChange = (cityConfig) => {
    const b = cityConfig.bounds;

    setCityBounds([
      [b.south, b.west],
      [b.north, b.east]
    ]);
  };

  return (
    <div style={{ position: "relative" }}>
      {!osmReachable && (
        <div className="loading-screen">
          Connecting to OpenStreetMap...
        </div>
      )}

      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        style={{ height: "100vh", width: "100%" }}
      >
        <TileLayer
          url={tileUrl}
          attribution="&copy; OpenStreetMap contributors"
          eventHandlers={{
            tileload: handleTileLoad,
            tileerror: handleTileError
          }}
        />

        <FitCityBounds bounds={cityBounds} />

        <ZoomControl position="topright" />

        {/* Adjust map view */}
        <FitBounds
          origin={route.origin}
          destination={route.destination}
        />

        {/* Origin marker */}
        {route.origin && (
          <Marker position={route.origin} />
        )}

        {/* Destination marker */}
        {route.destination && (
          <Marker position={route.destination} />
        )}

      </MapContainer>

      <FloatingRoutePanel
        onRouteChange={handleRouteChange}
        onMapStyleChange={setTileUrl}
        onCityChange={handleCityChange}
      />
    </div>
  );
}
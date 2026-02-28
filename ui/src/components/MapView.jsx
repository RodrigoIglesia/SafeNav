// src/components/MapView.jsx

//TODO: Download local tiles to test offline
import { useState, useRef } from "react";
import { MapContainer, TileLayer, ZoomControl } from "react-leaflet";
import FloatingRoutePanel from "./FloatingRoutePanel";
import MapStyleSelector from "./MapStyleSelector";
import "leaflet/dist/leaflet.css";

export default function MapView() {
  const center = [40.4168, -3.7038];
  const zoom = 13;

  const [tileUrl, setTileUrl] = useState(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
  );

  const errorTimeoutRef = useRef(null);
  const successTimeoutRef = useRef(null);
  const [osmReachable, setOsmReachable] = useState(true);

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
  };

  return (
    <div style={{ position: "relative" }}>
      {!osmReachable && (
        <div className="loading-screen">Connecting to OpenStreetMap...</div>
      )}

      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100vh", width: "100%" }}
        zoomControl={false}
      >
        <TileLayer
          url={tileUrl}
          attribution="&copy; OpenStreetMap contributors"
          eventHandlers={{
            tileload: handleTileLoad,
            tileerror: handleTileError
          }}
        />
        <ZoomControl position="topright" />
      </MapContainer>

      <FloatingRoutePanel onRouteChange={handleRouteChange} />

      <MapStyleSelector onChange={(url) => setTileUrl(url)} />
    </div>
  );
}
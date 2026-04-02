// src/components/MapView.jsx

// TODO: Add waiting popup for graph download an route estimation

import { useState, useRef, useEffect } from "react";
import { MapContainer, TileLayer, ZoomControl, Marker, useMap, Polyline } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import FloatingRoutePanel from "./FloatingRoutePanel";
import citiesConfig from "../config/cities.json";
import { toLatLng } from "../utils/geo";


const DEFAULT_ZOOM = 13;

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


// Fit route bounds
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

// Fit city bounds
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

export function mapRoutesToPolylines(routeResponse) {
  if (!routeResponse?.routes?.items) return [];

  return routeResponse.routes.items.map((route) => {
    const latlngs = route.geometry.coordinates.map((point) => [
      point.lat,
      point.lon // Leaflet uses lng but accepts this as second value
    ]);

    return {
      id: route.id,
      latlngs,
      eta: route.eta,
      distance: route.distance
    };
  });
}

export default function MapView() {

  // ===============================
  // Read default city from config
  // ===============================
  const defaultCityKey = citiesConfig.default;
  const defaultCity = citiesConfig.cities[defaultCityKey];

  const initialBounds = [
    [defaultCity.bounds.south, defaultCity.bounds.west],
    [defaultCity.bounds.north, defaultCity.bounds.east]
  ];

  const initialCenter = [
    (defaultCity.bounds.south + defaultCity.bounds.north) / 2,
    (defaultCity.bounds.west + defaultCity.bounds.east) / 2
  ];

  // ===============================
  // State
  // ===============================
  const [tileUrl, setTileUrl] = useState(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
  );

  const [route, setRoute] = useState({
    origin: null,
    destination: null,
    data: null // Store backend response
  });

  const [osmReachable, setOsmReachable] = useState(true);

  const [cityBounds, setCityBounds] = useState(initialBounds);
  const [selectedCity, setSelectedCity] = useState(defaultCityKey);

  const errorTimeoutRef = useRef(null);
  const successTimeoutRef = useRef(null);

  // ===============================
  // Tile status handlers
  // ===============================
  const handleTileLoad = () => {
    if (errorTimeoutRef.current) clearTimeout(errorTimeoutRef.current);
    successTimeoutRef.current = setTimeout(() => setOsmReachable(true), 200);
  };

  const handleTileError = () => {
    if (successTimeoutRef.current) clearTimeout(successTimeoutRef.current);
    errorTimeoutRef.current = setTimeout(() => setOsmReachable(false), 1500);
  };

  // ===============================
  // Route handler
  // ===============================
  const handleRouteChange = ({ origin, destination, route }) => {
    console.log("Route received in MapView:", { origin, destination, route });
    setRoute({ 
      origin: origin,
      destination: destination,
      data: route
    });
  };

  // ===============================
  // City change handler
  // ===============================
  const handleCityChange = (cityKey) => {
    const city = citiesConfig.cities[cityKey];

    setSelectedCity(cityKey);

    const newBounds = [
      [city.bounds.south, city.bounds.west],
      [city.bounds.north, city.bounds.east]
    ];

    setCityBounds(newBounds);

    // Reset route when city changes
    setRoute({ origin: null, destination: null });
  };

  // Generate polylines from the response route
  const polylines = mapRoutesToPolylines(route.data);

  return (
    <div style={{ position: "relative" }}>

      {!osmReachable && (
        <div className="loading-screen">
          Connecting to OpenStreetMap...
        </div>
      )}

      <MapContainer
        center={initialCenter}
        zoom={DEFAULT_ZOOM}
        zoomControl={false}
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

        <FitBounds
          origin={route.origin}
          destination={route.destination}
        />

        <FloatingRoutePanel
          onRouteChange={handleRouteChange}
          onMapStyleChange={setTileUrl}
          onCityChange={handleCityChange}
          activeCityBounds={cityBounds}
          selectedCity={selectedCity}
          cities={citiesConfig.cities}
        />

        {/* Markers using toLatLng */}
        {route.origin && <Marker position={toLatLng(route.origin)} />}
        {route.destination && <Marker position={toLatLng(route.destination)} />}

        {/* Plot Route Candidates Paths */}
        {polylines.map((r, index) => (
          <Polyline
            key={r.id}
            positions={r.latlngs}
            pathOptions={{
              color: index === 0 ? "blue" : "gray",
              weight: index === 0 ? 5 : 3,
              opacity: index === 0 ? 0.9 : 0.6
            }}
          />
        ))}
      </MapContainer>

    </div>
  );
}
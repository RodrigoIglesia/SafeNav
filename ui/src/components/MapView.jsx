// src/components/MapView.jsx

// TODO: Add waiting popup for graph download and route estimation.

import { useState, useRef, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  ZoomControl,
  Marker,
  useMap
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import { mapStyles } from "../config/mapStyles";
import FloatingRoutePanel from "./FloatingRoutePanel";
import RoutesLayer from "./map/RoutesLayer";
import ContextLayer from "./map/ContextLayer";

import citiesConfig from "../config/cities.json";
import { toLatLng } from "../utils/geo";


const DEFAULT_ZOOM = 13;


// ===============================
// Map behavior components
// ===============================

/**
 * Fit the map to the selected route origin and destination.
 */
function FitBounds({ origin, destination }) {
  const map = useMap();

  useEffect(() => {
    if (origin && destination) {
      const bounds = [
        toLatLng(origin),
        toLatLng(destination)
      ];

      map.fitBounds(bounds, {
        padding: [80, 80]
      });
    }
  }, [origin, destination, map]);

  return null;
}


/**
 * Fit the map to the initial city bounds.
 */
function FitCityBounds({ bounds }) {
  const map = useMap();
  const initialized = useRef(false);

  useEffect(() => {
    if (bounds && !initialized.current) {
      map.fitBounds(bounds, {
        padding: [40, 40]
      });

      initialized.current = true;
    }
  }, [bounds, map]);

  return null;
}


export default function MapView() {

  // ===============================
  // Default city configuration
  // ===============================

  const defaultCityKey = citiesConfig.default;
  const defaultCity = citiesConfig.cities[defaultCityKey];

  const initialBounds = [
    [
      defaultCity.bounds.south,
      defaultCity.bounds.west
    ],
    [
      defaultCity.bounds.north,
      defaultCity.bounds.east
    ]
  ];

  const initialCenter = [
    (defaultCity.bounds.south + defaultCity.bounds.north) / 2,
    (defaultCity.bounds.west + defaultCity.bounds.east) / 2
  ];


  // ===============================
  // State
  // ===============================

  const [tileUrl, setTileUrl] = useState(
    mapStyles[0].url
  );

  const [route, setRoute] = useState({
    origin: null,
    destination: null,
    data: null
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
    if (errorTimeoutRef.current) {
      clearTimeout(errorTimeoutRef.current);
    }

    successTimeoutRef.current = setTimeout(
      () => setOsmReachable(true),
      200
    );
  };


  const handleTileError = () => {
    if (successTimeoutRef.current) {
      clearTimeout(successTimeoutRef.current);
    }

    errorTimeoutRef.current = setTimeout(
      () => setOsmReachable(false),
      1500
    );
  };


  // ===============================
  // Route handler
  // ===============================

  const handleRouteChange = ({
    origin,
    destination,
    route
  }) => {
    console.log(
      "Route received in MapView:",
      {
        origin,
        destination,
        route
      }
    );

    setRoute({
      origin,
      destination,
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
      [
        city.bounds.south,
        city.bounds.west
      ],
      [
        city.bounds.north,
        city.bounds.east
      ]
    ];

    setCityBounds(newBounds);

    // Reset route when city changes.
    setRoute({
      origin: null,
      destination: null,
      data: null
    });
  };


  // ===============================
  // Render
  // ===============================

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
        style={{
          height: "100vh",
          width: "100%"
        }}
      >

        {/* ===========================
            Base map
        ============================ */}

        <TileLayer
          key={tileUrl}
          url={tileUrl}
          attribution="&copy; OpenStreetMap contributors"
          eventHandlers={{
            tileload: handleTileLoad,
            tileerror: handleTileError
          }}
        />


        {/* ===========================
            Map behavior
        ============================ */}

        <FitCityBounds
          bounds={cityBounds}
        />

        <FitBounds
          origin={route.origin}
          destination={route.destination}
        />

        <ZoomControl position="topright" />


        {/* ===========================
            UI controls
        ============================ */}

        <FloatingRoutePanel
          onRouteChange={handleRouteChange}
          onMapStyleChange={setTileUrl}
          onCityChange={handleCityChange}
          activeCityBounds={cityBounds}
          selectedCity={selectedCity}
          cities={citiesConfig.cities}
        />


        {/* ===========================
            Route endpoints
        ============================ */}

        {route.origin && (
          <Marker
            position={toLatLng(route.origin)}
          />
        )}

        {route.destination && (
          <Marker
            position={toLatLng(route.destination)}
          />
        )}


        {/* ===========================
            SafeNav map layers
        ============================ */}

        <RoutesLayer
          routes={route.data?.routes}
        />

        <ContextLayer
          routes={route.data?.routes}
          contextDescription={route.data?.context}
          debug={true}
        />

      </MapContainer>

    </div>
  );
}
// src/components/map/RoutesLayer.jsx

/**
 * RoutesLayer
 * ------------------------------------
 * Map layer responsible for visualizing route candidates.
 *
 * Responsibilities:
 * - Transform SafeNav route geometries into Leaflet coordinates.
 * - Render route candidate polylines.
 * - Apply route visualization styles.
 *
 * This component intentionally does not handle contextual data.
 * Context visualization belongs to ContextLayer.
 */

import { useState } from "react";
import { Polyline } from "react-leaflet";
import "./RoutesLayer.css";


/**
 * Converts SafeNav RouteCandidates into data suitable
 * for rendering with Leaflet.
 */
function mapRoutesToPolylines(routes) {
  if (!routes?.items) {
    return [];
  }

  return routes.items.map((route) => ({
    id: route.id,

    latlngs: route.geometry.coordinates.map((point) => [
      point.lat,
      point.lon
    ]),

    eta: route.eta,
    distance: route.distance
  }));
}

/**
 * Individual route visualization.
 */
function RoutePolyline({ route, isPrimary }) {
  const [hovered, setHovered] = useState(false);

  const color = isPrimary ? "#2563eb" : "#6b7280";

  return (
    <>
      {/* Glow layer */}
      {(isPrimary || hovered) && (
        <Polyline
          positions={route.latlngs}
          interactive={false}
          pathOptions={{
            color,
            weight: hovered ? 16 : 11,
            opacity: hovered ? 0.35 : 0.18,
            lineCap: "round",
            lineJoin: "round"
          }}
          className="route-glow"
        />
      )}

      {/* Visible route */}
      <Polyline
        positions={route.latlngs}
        interactive={false}
        pathOptions={{
          color,
          weight: hovered
            ? 8
            : isPrimary
              ? 5
              : 3,
          opacity: hovered
            ? 1
            : isPrimary
              ? 0.95
              : 0.65,
          lineCap: "round",
          lineJoin: "round"
        }}
        className={[
          "route-polyline",
          isPrimary
            ? "route-polyline-primary"
            : "route-polyline-alternative",
          hovered
            ? "route-polyline-hovered"
            : ""
        ].join(" ")}
      />

      {/* Invisible mouse interaction layer */}
      <Polyline
        positions={route.latlngs}
        pathOptions={{
          color: "transparent",
          weight: 20,
          opacity: 0
        }}
        eventHandlers={{
          mouseover: () => {
            console.log("Route hover:", route.id);
            setHovered(true);
          },
          mouseout: () => {
            setHovered(false);
          }
        }}
      />
    </>
  );
}


/*
 * RoutesLayer visualization
 */
export default function RoutesLayer({ routes }) {
  const polylines = mapRoutesToPolylines(routes);

  if (polylines.length === 0) {
    return null;
  }

  return (
    <>
      {polylines.map((route, index) => (
        <RoutePolyline
          key={route.id}
          route={route}
          isPrimary={index === 0}
        />
      ))}
    </>
  );
}
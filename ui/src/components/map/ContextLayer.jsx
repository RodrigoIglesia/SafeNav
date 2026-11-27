// src/components/map/ContextLayer.jsx

import { useState } from "react";
import L from "leaflet";
import {
  Marker,
  Pane,
  Polygon,
  Polyline,
  Popup,
  Tooltip,
  useMap,
  useMapEvents
} from "react-leaflet";

import { CONTEXT_LAYERS } from "../../config/contextStyles";
import { getStickerIcon } from "./contextIcons";
import { pointPosition, areaPositions } from "./contextFeatures";

import "./ContextLayer.css";


/**
 * ContextLayer
 * ------------------------------------
 * Map layer responsible for visualizing contextual information
 * associated with route candidates.
 *
 * - Point features (water points, benches, police) are drawn as stickers.
 * - Area features (parks, shade) are drawn as polygons with a sticker
 *   at their center.
 * - Each layer can be shown/hidden through `visibleLayers`.
 * - Layers with `minZoom` are hidden when zoomed out to avoid clutter.
 * - In debug mode, clicking a route shows its raw RouteContext.
 *
 * Panes:
 * - context-areas    (z 350): below routes (overlay pane, z 400).
 * - context-stickers (z 550): above routes, below origin/destination markers (z 600).
 */
export default function ContextLayer({
  routes,
  contextDescription,
  features,
  visibleLayers,
  debug = true
}) {
  const zoom = useZoom();

  const activeLayers = CONTEXT_LAYERS.filter(
    (layer) => visibleLayers?.[layer.key] && zoom >= layer.minZoom
  );

  return (
    <>
      {/* Area geometries (below routes) */}
      <Pane name="context-areas" style={{ zIndex: 350 }}>
        {activeLayers
          .filter((layer) => layer.kind === "area")
          .map((layer) =>
            (features?.[layer.key] ?? []).map(({ id, feature }) => (
              <AreaShape key={id} layer={layer} feature={feature} />
            ))
          )}
      </Pane>

      {/* Stickers (above routes) */}
      <Pane name="context-stickers" style={{ zIndex: 550 }}>
        {activeLayers.map((layer) =>
          (features?.[layer.key] ?? []).map(({ id, feature }) => (
            <FeatureSticker key={id} layer={layer} feature={feature} />
          ))
        )}
      </Pane>

      {/* Debug: raw RouteContext popup on route click */}
      {debug && (
        <RouteContextDebug
          routes={routes}
          contextDescription={contextDescription}
        />
      )}
    </>
  );
}


// ===============================
// Hooks
// ===============================

function useZoom() {
  const map = useMap();
  const [zoom, setZoom] = useState(() => map.getZoom());

  useMapEvents({
    zoomend: () => setZoom(map.getZoom())
  });

  return zoom;
}


// ===============================
// Feature rendering
// ===============================

function stickerPosition(layer, feature) {
  if (layer.kind === "point") {
    return pointPosition(feature);
  }

  const positions = areaPositions(feature);

  if (positions) {
    const center = L.latLngBounds(positions).getCenter();
    return [center.lat, center.lng];
  }

  // Area feature without polygon but with a location
  return pointPosition(feature);
}


function FeatureSticker({ layer, feature }) {
  const position = stickerPosition(layer, feature);

  if (!position) {
    return null;
  }

  const details = layer.describe?.(feature);

  return (
    <Marker
      position={position}
      icon={getStickerIcon(layer.key)}
      keyboard={false}
      riseOnHover={true}
    >
      <Tooltip
        direction="top"
        className="context-sticker-tooltip"
      >
        <div className="context-sticker-tooltip-title">
          {layer.sticker} {layer.label}
        </div>

        {details && (
          <div className="context-sticker-tooltip-details">
            {details}
          </div>
        )}
      </Tooltip>
    </Marker>
  );
}


function AreaShape({ layer, feature }) {
  const positions = areaPositions(feature);

  if (!positions) {
    return null;
  }

  return (
    <Polygon
      positions={positions}
      interactive={false}
      pathOptions={{
        color: layer.color,
        weight: 1.5,
        opacity: 0.8,
        fillColor: layer.fillColor ?? layer.color,
        fillOpacity: layer.fillOpacity ?? 0.15,
        dashArray: layer.dashArray
      }}
    />
  );
}


// ===============================
// Debug popup
// ===============================

function RouteContextDebug({ routes, contextDescription }) {
  if (!routes?.items || !contextDescription?.items) {
    return null;
  }

  // Build route_id -> RouteContext lookup.
  const contextByRouteId = new Map(
    contextDescription.items.map((context) => [
      context.route_id,
      context
    ])
  );

  return (
    <>
      {routes.items.map((route) => {
        const routeContext = contextByRouteId.get(route.id);

        if (!routeContext) {
          return null;
        }

        const positions = route.geometry.coordinates.map((point) => [
          point.lat,
          point.lon
        ]);

        return (
          <Polyline
            key={`context-${route.id}`}
            positions={positions}
            pathOptions={{
              color: "transparent",
              opacity: 0,
              weight: 15
            }}
          >
            <Popup
              className="context-popup"
              closeButton={true}
              autoClose={true}
              closeOnClick={true}
              maxWidth={500}
            >
              <div className="context-popup-content">

                <div className="context-popup-header">
                  Route Context
                </div>

                <pre className="context-popup-json">
                  {JSON.stringify(routeContext, null, 2)}
                </pre>

              </div>
            </Popup>
          </Polyline>
        );
      })}
    </>
  );
}
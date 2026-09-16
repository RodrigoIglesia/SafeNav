// src/components/map/ContextLayer.jsx

import { Polyline, Popup } from "react-leaflet";

import "./ContextLayer.css";


/**
 * ContextLayer
 * ------------------------------------
 * Optional map layer responsible for visualizing contextual
 * information associated with route candidates.
 *
 * Current implementation:
 * - Creates an invisible interaction layer over each route.
 * - Displays the corresponding RouteContext when the route is clicked.
 * - Keeps the popup open until the user clicks elsewhere.
 *
 * Future:
 * - Water point markers.
 * - Bench markers.
 * - Police office markers.
 * - Park polygons.
 * - Shadow zones.
 * - Weather visualization.
 */
export default function ContextLayer({
  routes,
  contextDescription,
  debug = true
}) {
  if (!debug) {
    return null;
  }

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
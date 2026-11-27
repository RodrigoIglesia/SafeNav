// src/components/ContextFilterPanel.jsx

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { useMap, useMapEvents } from "react-leaflet";

import { CONTEXT_LAYERS } from "../config/contextStyles";
import "./ContextFilterPanel.css";


/**
 * ContextFilterPanel
 * ------------------------------------
 * Floating panel to choose which urban context layers are shown.
 * Shows, for each layer, its sticker, label, and number of features
 * found along the current route candidates.
 */
export default function ContextFilterPanel({
  features,
  visibleLayers,
  onVisibleLayersChange
}) {
  const [expanded, setExpanded] = useState(true);
  const panelRef = useRef(null);

  const map = useMap();
  const [zoom, setZoom] = useState(() => map.getZoom());

  useMapEvents({
    zoomend: () => setZoom(map.getZoom())
  });

  useEffect(() => {
    if (panelRef.current) {
      L.DomEvent.disableClickPropagation(panelRef.current);
      L.DomEvent.disableScrollPropagation(panelRef.current);
    }
  }, []);

  const allVisible = CONTEXT_LAYERS.every((layer) => visibleLayers[layer.key]);

  const toggleLayer = (key) => {
    onVisibleLayersChange({
      ...visibleLayers,
      [key]: !visibleLayers[key]
    });
  };

  const setAll = (value) => {
    onVisibleLayersChange(
      Object.fromEntries(CONTEXT_LAYERS.map((layer) => [layer.key, value]))
    );
  };

  const hasFeatures = CONTEXT_LAYERS.some(
    (layer) => (features?.[layer.key]?.length ?? 0) > 0
  );

  return (
    <div
      ref={panelRef}
      className={`context-panel ${expanded ? "expanded" : "collapsed"}`}
    >
      <div className="context-panel-header">
        <span>Map Context</span>
        <button
          className="context-panel-toggle"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "−" : "+"}
        </button>
      </div>

      {expanded && (
        <div className="context-panel-body">

          {CONTEXT_LAYERS.map((layer) => {
            const count = features?.[layer.key]?.length ?? 0;
            const checked = Boolean(visibleLayers[layer.key]);
            const hiddenByZoom = checked && zoom < layer.minZoom && count > 0;

            return (
              <label
                key={layer.key}
                className={[
                  "context-panel-row",
                  checked ? "" : "is-off",
                  count === 0 ? "is-empty" : ""
                ].join(" ")}
              >
                <span
                  className="context-panel-sticker"
                  style={{ "--sticker-color": layer.color }}
                >
                  {layer.sticker}
                </span>

                <span className="context-panel-label">
                  {layer.label}
                  {hiddenByZoom && (
                    <span className="context-panel-hint">Zoom in to see</span>
                  )}
                </span>

                <span className="context-panel-count">{count}</span>

                <input
                  type="checkbox"
                  className="context-panel-switch"
                  checked={checked}
                  onChange={() => toggleLayer(layer.key)}
                />
              </label>
            );
          })}

          {!hasFeatures && (
            <div className="context-panel-empty">
              Calculate a route to see its context.
            </div>
          )}

          <button
            className="context-panel-all"
            onClick={() => setAll(!allVisible)}
          >
            {allVisible ? "Hide all" : "Show all"}
          </button>
        </div>
      )}
    </div>
  );
}
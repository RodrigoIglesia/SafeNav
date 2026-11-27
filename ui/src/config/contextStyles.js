// src/config/contextStyles.js

/**
 * Visual configuration of the urban context layers.
 *
 * - key:         field name inside RouteContext.urban
 * - kind:        "point" (uses `location`) or "area" (uses `geometry.coordinates`)
 * - sticker:     emoji shown inside the sticker
 * - color:       sticker border / area outline color
 * - fillColor:   area fill color (areas only)
 * - minZoom:     layer is hidden below this zoom level (avoids clutter)
 * - visible:     default visibility in the filter panel
 * - describe():  short detail line shown in the sticker tooltip
 */
export const CONTEXT_LAYERS = [
  {
    key: "water_points",
    label: "Water points",
    kind: "point",
    sticker: "💧",
    color: "#0ea5e9",
    minZoom: 0,
    visible: true,
    describe: (feature) =>
      feature.potable === false ? "Not potable" : "Drinking water"
  },
  {
    key: "benches",
    label: "Benches",
    kind: "point",
    sticker: "🪑",
    color: "#d97706",
    minZoom: 15,
    visible: true,
    describe: (feature) =>
      feature.covered === true
        ? "Covered"
        : feature.covered === false
          ? "Not covered"
          : null
  },
  {
    key: "police_offices",
    label: "Police",
    kind: "point",
    sticker: "🚓",
    color: "#7c3aed",
    minZoom: 0,
    visible: true,
    describe: (feature) => {
      if (feature.is_24h) return "Open 24/7";
      if (feature.open_now === true) return "Open now";
      if (feature.open_now === false) return "Closed now";
      return null;
    }
  },
  {
    key: "parks",
    label: "Parks",
    kind: "area",
    sticker: "🌳",
    color: "#16a34a",
    fillColor: "#22c55e",
    fillOpacity: 0.15,
    minZoom: 0,
    visible: true,
    describe: (feature) =>
      feature.area_m2 ? `${Math.round(feature.area_m2).toLocaleString()} m²` : null
  },
  {
    key: "shadow_zones",
    label: "Shade",
    kind: "area",
    sticker: "⛱️",
    color: "#475569",
    fillColor: "#64748b",
    fillOpacity: 0.12,
    dashArray: "4 4",
    minZoom: 0,
    visible: true,
    describe: () => null
  }
];

export const DEFAULT_VISIBLE_LAYERS = Object.fromEntries(
  CONTEXT_LAYERS.map((layer) => [layer.key, layer.visible])
);
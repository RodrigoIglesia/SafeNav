// src/utils/geo.js


// ==============================
// Type guards
// ==============================
export const isLatLng = (p) =>
  Array.isArray(p) &&
  p.length === 2 &&
  typeof p[0] === "number" &&
  typeof p[1] === "number";

// ==============================
// API → UI
// ==============================
export const toLatLng = (point) => {
  if (!point) return null;

  if (isLatLng(point)) return point;

  if (point.lat !== undefined && point.lon !== undefined) {
    return [point.lat, point.lon];
  }

  console.error("Invalid GeoPoint format:", point);
  return null;
};

// src/components/TileLayerRenderer.jsx

import { Polygon } from "react-leaflet";

/**
 * Renders tile boundaries as Leaflet polygons.
 *
 * @param {Array} tiles - List of Tile objects from MapData.
 */
export default function TileLayerRenderer({ tiles }) {
  if (!tiles || tiles.length === 0) return null;

  return (
    <>
      {tiles.map((tile) => (
        <Polygon
          key={tile.id}
          positions={convertPolygon(tile.bounds)}
          pathOptions={{
            color: "#007bff",
            weight: 1,
          }}
        />
      ))}
    </>
  );
}

/**
 * Converts GeoJSON Polygon coordinates
 * from [lon, lat] to Leaflet format [lat, lon].
 */
function convertPolygon(bounds) {
  if (!bounds?.coordinates?.length) return [];

  return bounds.coordinates[0].map((coord) => [
    coord[1], // latitude
    coord[0], // longitude
  ]);
}
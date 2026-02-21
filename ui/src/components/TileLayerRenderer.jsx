import { Polygon } from "react-leaflet";

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

function convertPolygon(bounds) {
  if (!bounds?.coordinates?.length) return [];

  return bounds.coordinates.map((coord) => [
    coord.lat,
    coord.lon,
  ]);
}
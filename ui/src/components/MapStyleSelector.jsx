// src/components/MapStyleSelector.jsx
import "./MapStyleSelector.css";

export default function MapStyleSelector({ onChange }) {
  const styles = [
    { name: "Standard", url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" },
    { name: "Dark", url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" },
    { name: "Light", url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" },
    { name: "Topo", url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" }
  ];

  return (
    <div className="map-style-selector">
      <span>Map Style:</span>
      {styles.map((style) => (
        <button
          key={style.name}
          onClick={() => onChange(style.url)}
        >
          {style.name}
        </button>
      ))}
    </div>
  );
}
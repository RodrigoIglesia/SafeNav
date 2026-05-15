// src/components/MapStyleSelector.jsx
//TODO: Add images (miniatures) in map styles to show in the selector
import "./MapStyleSelector.css";
import { mapStyles } from "../config/mapStyles";

export default function MapStyleSelector({ onMapStyleChange }) {
  return (
    <div className="map-style-selector">
      <select onChange={(e) => onMapStyleChange(e.target.value)}>
        {mapStyles.map((style) => (
          <option key={style.name} value={style.url}>
            {style.name}
          </option>
        ))}
      </select>
    </div>
  );
}
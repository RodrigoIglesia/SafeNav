const CARTO_KEY = import.meta.env.VITE_CARTO_API_KEY;

console.log("CARTO_KEY loaded:", Boolean(CARTO_KEY));
console.log("CARTO_KEY prefix:", CARTO_KEY?.substring(0, 4));

export const mapStyles = [
  {
    name: "Light",
    url: `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`
  },
  {
    name: "Standard",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
  },
  {
    name: "Dark",
    url: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`
  },
  {
    name: "Topo",
    url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
  }
];  
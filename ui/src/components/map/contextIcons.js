// src/components/map/contextIcons.js

import L from "leaflet";
import { CONTEXT_LAYERS } from "../../config/contextStyles";

const STICKER_SIZE = 30;

const iconCache = new Map();

/**
 * Returns a cached Leaflet divIcon rendering the sticker of a context layer.
 * Icons are created once per layer and reused by every marker.
 */
export function getStickerIcon(layerKey) {
  if (iconCache.has(layerKey)) {
    return iconCache.get(layerKey);
  }

  const layer = CONTEXT_LAYERS.find((item) => item.key === layerKey);

  const icon = L.divIcon({
    className: "context-sticker-wrapper",
    html: `
      <div class="context-sticker" style="--sticker-color: ${layer.color}">
        <span class="context-sticker-emoji">${layer.sticker}</span>
      </div>
    `,
    iconSize: [STICKER_SIZE, STICKER_SIZE],
    iconAnchor: [STICKER_SIZE / 2, STICKER_SIZE / 2],
    tooltipAnchor: [0, -STICKER_SIZE / 2]
  });

  iconCache.set(layerKey, icon);

  return icon;
}
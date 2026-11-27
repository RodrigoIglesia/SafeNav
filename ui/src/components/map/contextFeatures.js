// src/components/map/contextFeatures.js

import { CONTEXT_LAYERS } from "../../config/contextStyles";

/**
 * Collects the urban features of all route contexts, without duplicates.
 *
 * The same feature (e.g. a park) usually appears in several RouteContexts.
 * Features are merged by id and keep the set of routes they belong to.
 *
 * Returns: { [layerKey]: [{ id, feature, routeIds: Set<string> }] }
 */
export function collectContextFeatures(contextDescription) {
  const byLayer = Object.fromEntries(
    CONTEXT_LAYERS.map((layer) => [layer.key, new Map()])
  );

  for (const routeContext of contextDescription?.items ?? []) {
    const urban = routeContext?.urban;

    if (!urban) {
      continue;
    }

    for (const layer of CONTEXT_LAYERS) {
      const features = urban[layer.key] ?? [];

      features.forEach((feature, index) => {
        if (!feature) {
          return;
        }

        const id = featureId(layer.key, feature, index);
        const entries = byLayer[layer.key];

        if (!entries.has(id)) {
          entries.set(id, { id, feature, routeIds: new Set() });
        }

        entries.get(id).routeIds.add(routeContext.route_id);
      });
    }
  }

  return Object.fromEntries(
    Object.entries(byLayer).map(([key, entries]) => [key, [...entries.values()]])
  );
}

function featureId(layerKey, feature, index) {
  if (feature.id !== undefined && feature.id !== null) {
    return `${layerKey}-${feature.id}`;
  }

  const location = feature.location;

  if (location) {
    return `${layerKey}-${location.lat},${location.lon}`;
  }

  return `${layerKey}-${index}`;
}

function isValidPoint(point) {
  return (
    point &&
    Number.isFinite(point.lat) &&
    Number.isFinite(point.lon)
  );
}

/**
 * [lat, lon] for point features, or null if the location is unusable.
 */
export function pointPosition(feature) {
  return isValidPoint(feature?.location)
    ? [feature.location.lat, feature.location.lon]
    : null;
}

/**
 * [[lat, lon], ...] for area features, or null if the geometry is unusable.
 */
export function areaPositions(feature) {
  const coordinates = feature?.geometry?.coordinates ?? [];

  const positions = coordinates
    .filter(isValidPoint)
    .map((point) => [point.lat, point.lon]);

  return positions.length >= 3 ? positions : null;
}
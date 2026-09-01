import { useEffect, useMemo, useRef } from 'react';
import {
  Color,
  ColorGeometryInstanceAttribute,
  GeometryInstance,
  PerInstanceColorAppearance,
  Primitive,
  Rectangle,
  RectangleGeometry,
} from 'cesium';
import { getTemperatureRange } from '../../utils/temperatureColorScale';

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
const roundTo = (value, digits = 6) => Number(value.toFixed(digits));

function buildLookup(data) {
  const valueMap = new Map();
  const latValues = [...new Set(data.map((entry) => roundTo(Number(entry.latitude))))].filter(Number.isFinite).sort((a, b) => a - b);
  const lonValues = [...new Set(data.map((entry) => roundTo(Number(entry.longitude))))].filter(Number.isFinite).sort((a, b) => a - b);
  data.forEach((entry) => valueMap.set(`${roundTo(Number(entry.latitude))}:${roundTo(Number(entry.longitude))}`, Number(entry.value)));
  return { latValues, lonValues, valueMap };
}

function interpolate(targetLat, targetLon, lookup) {
  if (!lookup.latValues.length || !lookup.lonValues.length) return Number.NaN;
  const boundedLat = clamp(targetLat, lookup.latValues[0], lookup.latValues.at(-1));
  const boundedLon = clamp(targetLon, lookup.lonValues[0], lookup.lonValues.at(-1));
  let lowerLatIndex = 0;
  let lowerLonIndex = 0;
  for (let index = 0; index < lookup.latValues.length - 1; index += 1) {
    if (lookup.latValues[index] <= boundedLat && boundedLat <= lookup.latValues[index + 1]) lowerLatIndex = index;
  }
  for (let index = 0; index < lookup.lonValues.length - 1; index += 1) {
    if (lookup.lonValues[index] <= boundedLon && boundedLon <= lookup.lonValues[index + 1]) lowerLonIndex = index;
  }
  const upperLatIndex = Math.min(lowerLatIndex + 1, lookup.latValues.length - 1);
  const upperLonIndex = Math.min(lowerLonIndex + 1, lookup.lonValues.length - 1);
  const lowerLat = lookup.latValues[lowerLatIndex];
  const upperLat = lookup.latValues[upperLatIndex];
  const lowerLon = lookup.lonValues[lowerLonIndex];
  const upperLon = lookup.lonValues[upperLonIndex];
  const values = [
    lookup.valueMap.get(`${lowerLat}:${lowerLon}`), lookup.valueMap.get(`${lowerLat}:${upperLon}`),
    lookup.valueMap.get(`${upperLat}:${lowerLon}`), lookup.valueMap.get(`${upperLat}:${upperLon}`),
  ];
  if (!values.every(Number.isFinite)) return Number.NaN;
  const latRatio = (boundedLat - lowerLat) / (upperLat - lowerLat || 1);
  const lonRatio = (boundedLon - lowerLon) / (upperLon - lowerLon || 1);
  return values[0] * (1 - latRatio) * (1 - lonRatio) + values[1] * (1 - latRatio) * lonRatio + values[2] * latRatio * (1 - lonRatio) + values[3] * latRatio * lonRatio;
}

export default function ScalarFieldLayer({ viewer, data = [], colorScale, selectedTimestamp, selectedDepth = 0 }) {
  const primitiveRef = useRef(null);
  const cells = useMemo(() => {
    if (!data.length) return [];
    const values = data.map((entry) => Number(entry.value));
    const { min, max } = getTemperatureRange(values);
    const lookup = buildLookup(data);
    const minLat = lookup.latValues[0];
    const maxLat = lookup.latValues.at(-1);
    const minLon = lookup.lonValues[0];
    const maxLon = lookup.lonValues.at(-1);
    const latStep = (maxLat - minLat) / Math.max(lookup.latValues.length * 2, 1);
    const lonStep = (maxLon - minLon) / Math.max(lookup.lonValues.length * 2, 1);
    const nextCells = [];
    for (let lat = minLat; lat <= maxLat + 0.001; lat += latStep || 1.25) {
      for (let lon = minLon; lon <= maxLon + 0.001; lon += lonStep || 1.25) {
        const value = interpolate(lat, lon, lookup);
        if (!Number.isFinite(value)) continue;
        const halfLat = (latStep || 1.25) * 0.6;
        const halfLon = (lonStep || 1.25) * 0.6;
        const minLatCell = clamp(lat - halfLat, minLat, maxLat);
        const maxLatCell = clamp(lat + halfLat, minLat, maxLat);
        const minLonCell = clamp(lon - halfLon, minLon, maxLon);
        const maxLonCell = clamp(lon + halfLon, minLon, maxLon);
        if (minLatCell >= maxLatCell || minLonCell >= maxLonCell) continue;
        const color = colorScale(value, min, max);
        nextCells.push({ minLat: minLatCell, maxLat: maxLatCell, minLon: minLonCell, maxLon: maxLonCell, color: color.replace('rgb(', 'rgba(').replace(')', ', 0.76)') });
      }
    }
    return nextCells;
  }, [colorScale, data]);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return undefined;
    if (primitiveRef.current) viewer.scene.primitives.remove(primitiveRef.current);
    if (!cells.length) return undefined;
    const geometryInstances = cells.map((cell) => new GeometryInstance({
      geometry: new RectangleGeometry({ rectangle: Rectangle.fromDegrees(cell.minLon, cell.minLat, cell.maxLon, cell.maxLat), vertexFormat: PerInstanceColorAppearance.VERTEX_FORMAT }),
      attributes: { color: ColorGeometryInstanceAttribute.fromColor(Color.fromCssColorString(cell.color)) },
    }));
    const primitive = new Primitive({
      geometryInstances,
      appearance: new PerInstanceColorAppearance({ closed: true, translucent: true, flat: true }),
      asynchronous: false,
    });
    viewer.scene.primitives.add(primitive);
    primitiveRef.current = primitive;
    return () => {
      if (primitiveRef.current) {
        viewer.scene.primitives.remove(primitiveRef.current);
        primitiveRef.current = null;
      }
    };
  }, [cells, selectedDepth, selectedTimestamp, viewer]);

  return null;
}

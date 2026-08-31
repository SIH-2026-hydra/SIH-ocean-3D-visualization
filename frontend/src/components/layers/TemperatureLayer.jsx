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
import { getTemperatureColor, getTemperatureRange } from '../../utils/temperatureColorScale';

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
const roundTo = (value, digits = 6) => Number(value.toFixed(digits));

function buildTemperatureLookup(data) {
  const valueMap = new Map();
  const latValues = [...new Set(data.map((entry) => roundTo(Number(entry.latitude))))]
    .filter(Number.isFinite)
    .sort((a, b) => a - b);
  const lonValues = [...new Set(data.map((entry) => roundTo(Number(entry.longitude))))]
    .filter(Number.isFinite)
    .sort((a, b) => a - b);

  data.forEach((entry) => {
    const latitude = roundTo(Number(entry.latitude));
    const longitude = roundTo(Number(entry.longitude));
    valueMap.set(`${latitude}:${longitude}`, Number(entry.value));
  });

  return { latValues, lonValues, valueMap };
}

function interpolateTemperature(targetLat, targetLon, { latValues, lonValues, valueMap }) {
  if (!latValues.length || !lonValues.length) return Number.NaN;

  const minLat = latValues[0];
  const maxLat = latValues[latValues.length - 1];
  const minLon = lonValues[0];
  const maxLon = lonValues[lonValues.length - 1];

  const boundedLat = clamp(targetLat, minLat, maxLat);
  const boundedLon = clamp(targetLon, minLon, maxLon);

  let lowerLatIndex = 0;
  let upperLatIndex = latValues.length - 1;

  for (let index = 0; index < latValues.length; index += 1) {
    if (latValues[index] <= boundedLat) {
      lowerLatIndex = index;
    }
    if (latValues[index] >= boundedLat) {
      upperLatIndex = index;
      break;
    }
  }

  let lowerLonIndex = 0;
  let upperLonIndex = lonValues.length - 1;

  for (let index = 0; index < lonValues.length; index += 1) {
    if (lonValues[index] <= boundedLon) {
      lowerLonIndex = index;
    }
    if (lonValues[index] >= boundedLon) {
      upperLonIndex = index;
      break;
    }
  }

  const lowerLat = latValues[lowerLatIndex];
  const upperLat = latValues[upperLatIndex];
  const lowerLon = lonValues[lowerLonIndex];
  const upperLon = lonValues[upperLonIndex];

  const q11 = valueMap.get(`${roundTo(lowerLat)}:${roundTo(lowerLon)}`);
  const q12 = valueMap.get(`${roundTo(lowerLat)}:${roundTo(upperLon)}`);
  const q21 = valueMap.get(`${roundTo(upperLat)}:${roundTo(lowerLon)}`);
  const q22 = valueMap.get(`${roundTo(upperLat)}:${roundTo(upperLon)}`);

  if (!Number.isFinite(q11) || !Number.isFinite(q12) || !Number.isFinite(q21) || !Number.isFinite(q22)) {
    return Number.NaN;
  }

  const latSpan = upperLat - lowerLat || 1;
  const lonSpan = upperLon - lowerLon || 1;
  const latRatio = (boundedLat - lowerLat) / latSpan;
  const lonRatio = (boundedLon - lowerLon) / lonSpan;

  const interpolated =
    q11 * (1 - latRatio) * (1 - lonRatio) +
    q12 * (1 - latRatio) * lonRatio +
    q21 * latRatio * (1 - lonRatio) +
    q22 * latRatio * lonRatio;

  return Number(interpolated);
}

export default function TemperatureLayer({ viewer, data = [], selectedTimestamp, selectedDepth = 0 }) {
  const primitiveRef = useRef(null);

  const surfaceCells = useMemo(() => {
    if (!Array.isArray(data) || !data.length) return [];

    const values = data.map((entry) => Number(entry.value));
    const { min, max } = getTemperatureRange(values);
    const lowerBound = Number.isFinite(min) ? min : 0;
    const upperBound = Number.isFinite(max) ? max : 0;

    const { latValues, lonValues, valueMap } = buildTemperatureLookup(data);
    const minLat = latValues[0];
    const maxLat = latValues[latValues.length - 1];
    const minLon = lonValues[0];
    const maxLon = lonValues[lonValues.length - 1];
    const latStep = latValues.length > 1 ? (maxLat - minLat) / Math.max(latValues.length * 2, 1) : 1.25;
    const lonStep = lonValues.length > 1 ? (maxLon - minLon) / Math.max(lonValues.length * 2, 1) : 1.25;

    const cells = [];

    for (let lat = minLat; lat <= maxLat + 0.001; lat += latStep) {
      for (let lon = minLon; lon <= maxLon + 0.001; lon += lonStep) {
        const value = interpolateTemperature(lat, lon, { latValues, lonValues, valueMap });
        if (!Number.isFinite(value)) continue;

        const halfLat = latStep * 0.6;
        const halfLon = lonStep * 0.6;
        const minLatCell = clamp(lat - halfLat, minLat, maxLat);
        const maxLatCell = clamp(lat + halfLat, minLat, maxLat);
        const minLonCell = clamp(lon - halfLon, minLon, maxLon);
        const maxLonCell = clamp(lon + halfLon, minLon, maxLon);

        if (minLatCell >= maxLatCell || minLonCell >= maxLonCell) continue;

        const color = getTemperatureColor(value, lowerBound, upperBound);
        const alpha = 0.82;
        const rgba = color.startsWith('rgb(')
          ? color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`)
          : color;

        cells.push({
          minLat: minLatCell,
          maxLat: maxLatCell,
          minLon: minLonCell,
          maxLon: maxLonCell,
          color: rgba,
        });
      }
    }

    return cells;
  }, [data]);

  useEffect(() => {
    if (!viewer || !viewer.scene || viewer.isDestroyed()) return undefined;
    if (!surfaceCells.length) {
      if (primitiveRef.current) {
        viewer.scene.primitives.remove(primitiveRef.current);
        primitiveRef.current = null;
      }
      return undefined;
    }

    const rectangles = surfaceCells.map((cell) => {
      const rectangle = Rectangle.fromDegrees(cell.minLon, cell.minLat, cell.maxLon, cell.maxLat);
      const color = Color.fromCssColorString(cell.color);

      return new GeometryInstance({
        geometry: new RectangleGeometry({
          rectangle,
          vertexFormat: PerInstanceColorAppearance.VERTEX_FORMAT,
        }),
        attributes: {
          color: ColorGeometryInstanceAttribute.fromColor(color),
        },
      });
    });

    if (primitiveRef.current) {
      viewer.scene.primitives.remove(primitiveRef.current);
    }

    const primitive = new Primitive({
      geometryInstances: rectangles,
      appearance: new PerInstanceColorAppearance({
        closed: true,
        translucent: true,
        flat: true,
      }),
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
  }, [surfaceCells, viewer, selectedTimestamp, selectedDepth]);

  return null;
}

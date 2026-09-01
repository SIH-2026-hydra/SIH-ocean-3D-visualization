import { useEffect, useRef } from 'react';
import { Cartesian3, Color, Material, PolylineCollection } from 'cesium';

const SAMPLE_LIMIT = 64;
const ARROW_SCALE = 180000;

export default function CurrentVectorLayer({ viewer, data = [], selectedTimestamp, selectedDepth = 0 }) {
  const collectionRef = useRef(null);
  const viewerRefWhenAdded = useRef(null);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || !viewer.scene || !viewer.scene.primitives) {
      return undefined;
    }

    // Safely remove previous collection only if it's from the same viewer instance
    const previousCollection = collectionRef.current;
    const previousViewer = viewerRefWhenAdded.current;

    if (previousCollection && previousViewer === viewer) {
      try {
        // Check the collection is safe to remove
        if (previousCollection.isDestroyed && previousCollection.isDestroyed()) {
          // Already destroyed, just clear refs
          collectionRef.current = null;
          viewerRefWhenAdded.current = null;
        } else if (viewer.scene && viewer.scene.primitives && !previousCollection.isDestroyed()) {
          // Safely remove from primitives
          viewer.scene.primitives.remove(previousCollection);
          collectionRef.current = null;
          viewerRefWhenAdded.current = null;
        }
      } catch {
        // Silently handle removal errors—just clear refs
        collectionRef.current = null;
        viewerRefWhenAdded.current = null;
      }
    }

    const samples = data
      .filter((entry) => Number.isFinite(Number(entry.latitude))
        && Number.isFinite(Number(entry.longitude))
        && Number.isFinite(Number(entry.current_u))
        && Number.isFinite(Number(entry.current_v)))
      .filter((entry, index) => index % Math.max(1, Math.ceil(data.length / SAMPLE_LIMIT)) === 0);

    if (!samples.length) {
      return undefined;
    }

    // Create shared material to avoid repeated allocations
    const material = Material.fromType('Color', { color: Color.fromCssColorString('#8ee8f5') });
    const polylines = new PolylineCollection();

    samples.forEach((entry) => {
      const latitude = Number(entry.latitude);
      const longitude = Number(entry.longitude);
      const east = Number(entry.current_u);
      const north = Number(entry.current_v);
      const speed = Math.hypot(east, north);
      if (!speed) return;

      const length = ARROW_SCALE * Math.min(1.8, Math.max(0.55, speed * 4));
      const direction = Math.atan2(east, north);
      const endLatitude = latitude + (Math.cos(direction) * length) / 111000;
      const endLongitude = longitude + (Math.sin(direction) * length) / (111000 * Math.max(Math.cos(latitude * Math.PI / 180), 0.2));
      const wingLength = length * 0.28;
      const wingAngle = Math.PI / 6;
      const leftDirection = direction + Math.PI - wingAngle;
      const rightDirection = direction + Math.PI + wingAngle;
      const end = Cartesian3.fromDegrees(endLongitude, endLatitude, 360000);
      const start = Cartesian3.fromDegrees(longitude, latitude, 360000);
      const leftWing = Cartesian3.fromDegrees(
        endLongitude + (Math.sin(leftDirection) * wingLength) / 111000,
        endLatitude + (Math.cos(leftDirection) * wingLength) / 111000,
        360000,
      );
      const rightWing = Cartesian3.fromDegrees(
        endLongitude + (Math.sin(rightDirection) * wingLength) / 111000,
        endLatitude + (Math.cos(rightDirection) * wingLength) / 111000,
        360000,
      );

      polylines.add({ positions: [start, end], width: 2, material });
      polylines.add({ positions: [leftWing, end, rightWing], width: 2, material });
    });

    try {
      viewer.scene.primitives.add(polylines);
      collectionRef.current = polylines;
      viewerRefWhenAdded.current = viewer;
      viewer.scene.requestRender();
    } catch (e) {
      console.warn('Error adding polyline collection:', e);
      collectionRef.current = null;
      viewerRefWhenAdded.current = null;
    }

    // Cleanup: this closure only removes the collection created in this effect run
    return () => {
      // Reference the collection and viewer from this effect's scope
      const collectionToRemove = collectionRef.current;
      const viewerAtCleanup = viewerRefWhenAdded.current;

      if (collectionToRemove && viewerAtCleanup && !viewerAtCleanup.isDestroyed() && viewerAtCleanup.scene && viewerAtCleanup.scene.primitives) {
        try {
          if (!collectionToRemove.isDestroyed()) {
            viewerAtCleanup.scene.primitives.remove(collectionToRemove);
          }
        } catch {
          // Silently ignore cleanup errors—collection may have been destroyed by viewer reset
        }
      }

      // Always clear refs to prevent stale references
      collectionRef.current = null;
      viewerRefWhenAdded.current = null;
    };
  }, [data, selectedDepth, selectedTimestamp, viewer]);

  return null;
}

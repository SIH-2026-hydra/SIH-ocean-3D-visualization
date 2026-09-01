import { useEffect, useRef } from 'react';
import { Cartesian3, CustomDataSource, Entity, ScreenSpaceEventHandler, ScreenSpaceEventType, VerticalOrigin } from 'cesium';

const COLORS = { argo: '#e8bd65', buoy: '#8fe0ff', mooring: '#be9aff' };

export default function ObservationLayer({ viewer, observations = [], visible, onSelect }) {
  const dataSourceRef = useRef(null);
  const handlerRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  // Manage data source lifecycle: create once, update as needed
  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) {
      return undefined;
    }

    // Create data source if it doesn't exist
    if (!dataSourceRef.current) {
      dataSourceRef.current = new CustomDataSource('observation-platforms');
      viewer.dataSources.add(dataSourceRef.current);
    }

    return () => {
      // On unmount or viewer destruction, clean up the data source
      if (dataSourceRef.current && !viewer.isDestroyed()) {
        viewer.dataSources.remove(dataSourceRef.current);
      }
      dataSourceRef.current = null;
    };
  }, [viewer]);

  // Update entities when observations or visibility changes
  useEffect(() => {
    if (!dataSourceRef.current || !viewer || viewer.isDestroyed()) {
      return undefined;
    }

    // Clear existing entities
    dataSourceRef.current.entities.removeAll();

    // If not visible, keep data source but don't add entities
    if (!visible) {
      return undefined;
    }

    // Add observation entities
    const platforms = new Map();
    observations.forEach((observation) => {
      if (!platforms.has(observation.platform_id)) {
        platforms.set(observation.platform_id, observation);
      }
    });

    platforms.forEach((observation) => {
      const color = COLORS[observation.platform_type] || '#dffcff';
      const entity = new Entity({
        position: Cartesian3.fromDegrees(observation.longitude, observation.latitude, 300000),
        billboard: {
          image: `data:image/svg+xml;utf8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30"><path d="M15 2 28 15 15 28 2 15Z" fill="${color}" stroke="#07141c" stroke-width="2"/><circle cx="15" cy="15" r="4" fill="#07141c"/></svg>`)}`,
          width: 18,
          height: 18,
          verticalOrigin: VerticalOrigin.CENTER,
        },
      });
      entity.properties = { observation };
      dataSourceRef.current.entities.add(entity);
    });

    if (viewer.scene) {
      viewer.scene.requestRender();
    }

    return undefined;
  }, [observations, visible, viewer]);

  // Manage click handler lifecycle
  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || !dataSourceRef.current) {
      return undefined;
    }

    const scene = viewer.scene;
    if (!scene) {
      return undefined;
    }

    const handler = new ScreenSpaceEventHandler(scene.canvas);
    handlerRef.current = handler;

    handler.setInputAction((movement) => {
      const picked = scene.pick(movement.position);
      const observation = picked?.id?.properties?.observation;
      if (observation) {
        onSelectRef.current?.(observation);
      }
    }, ScreenSpaceEventType.LEFT_CLICK);

    return () => {
      if (handlerRef.current === handler) {
        handler.destroy();
        handlerRef.current = null;
      }
    };
  }, [viewer]);

  return null;
}

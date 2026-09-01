import { useEffect, useRef } from 'react';
import { Cartesian3, CustomDataSource, Entity, ScreenSpaceEventHandler, ScreenSpaceEventType, VerticalOrigin } from 'cesium';

const COLORS = { argo: '#e8bd65', buoy: '#8fe0ff', mooring: '#be9aff' };

export default function ObservationLayer({ viewer, observations = [], visible, onSelect }) {
  const dataSourceRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || !visible) return undefined;
    const dataSource = new CustomDataSource('observation-platforms');
    dataSourceRef.current = dataSource;
    viewer.dataSources.add(dataSource);
    const platforms = new Map();
    observations.forEach((observation) => {
      if (!platforms.has(observation.platform_id)) platforms.set(observation.platform_id, observation);
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
      dataSource.entities.add(entity);
    });
    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement) => {
      const picked = viewer.scene.pick(movement.position);
      const observation = picked?.id?.properties?.observation;
      if (observation) onSelectRef.current?.(observation);
    }, ScreenSpaceEventType.LEFT_CLICK);
    viewer.scene.requestRender();
    return () => {
      handler.destroy();
      if (!viewer.isDestroyed() && !dataSource.isDestroyed()) viewer.dataSources.remove(dataSource, true);
      if (dataSourceRef.current === dataSource) dataSourceRef.current = null;
      viewer.scene.requestRender();
    };
  }, [observations, viewer, visible]);

  return null;
}

import { useEffect, useMemo, useRef } from 'react';
import {
  Cartesian3,
  Color,
  CustomDataSource,
  DistanceDisplayCondition,
  Entity,
  VerticalOrigin,
} from 'cesium';

export default function SelectedLocationMarker({ viewer, location, active }) {
  const dataSourceRef = useRef(null);
  const entityRef = useRef(null);

  const position = useMemo(() => {
    if (!location || !Number.isFinite(location.latitude) || !Number.isFinite(location.longitude)) return null;
    return Cartesian3.fromDegrees(location.longitude, location.latitude, 350000);
  }, [location]);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || !active || !position) return undefined;

    if (!dataSourceRef.current) {
      dataSourceRef.current = new CustomDataSource('selected-location-marker');
      viewer.dataSources.add(dataSourceRef.current);
    }

    const entity = new Entity({
      position: null,
      point: {
        pixelSize: 10,
        color: Color.fromCssColorString('#6cecff'),
        outlineColor: Color.fromCssColorString('#dffcff'),
        outlineWidth: 2,
        heightReference: undefined,
        translucencyByDistance: new DistanceDisplayCondition(0, 30000000),
      },
      billboard: {
        image: 'data:image/svg+xml;utf8,' + encodeURIComponent(`
          <svg xmlns="http://www.w3.org/2000/svg" width="42" height="42" viewBox="0 0 42 42">
            <defs>
              <radialGradient id="g" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#dffcff" stop-opacity="1"/>
                <stop offset="30%" stop-color="#82ebff" stop-opacity="1"/>
                <stop offset="100%" stop-color="#0bd2ff" stop-opacity="0.1"/>
              </radialGradient>
            </defs>
            <circle cx="21" cy="21" r="14" fill="url(#g)"/>
            <circle cx="21" cy="21" r="7" fill="#dffcff"/>
            <circle cx="21" cy="21" r="17" fill="none" stroke="#6cecff" stroke-width="2.5" opacity="0.9"/>
          </svg>
        `),
        width: 24,
        height: 24,
        verticalOrigin: VerticalOrigin.BOTTOM,
        pixelOffset: { x: 0, y: 0 },
      },
    });

    dataSourceRef.current.entities.add(entity);
    entityRef.current = entity;

    return () => {
      if (dataSourceRef.current) {
        dataSourceRef.current.entities.remove(entity);
      }
      if (entityRef.current === entity) entityRef.current = null;
    };
  }, [active, viewer]);

  useEffect(() => {
    if (!entityRef.current || !position || !viewer || viewer.isDestroyed()) return undefined;

    entityRef.current.position = position;
    viewer.scene.requestRender();
    return undefined;
  }, [position, viewer]);

  useEffect(() => {
    return () => {
      if (dataSourceRef.current && !dataSourceRef.current.isDestroyed()) {
        viewer?.dataSources?.remove(dataSourceRef.current, true);
        dataSourceRef.current = null;
        entityRef.current = null;
      }
    };
  }, [viewer]);

  return null;
}

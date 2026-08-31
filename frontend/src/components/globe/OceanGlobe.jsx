import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import {
  Cartesian3,
  Color,
  EllipsoidTerrainProvider,
  Ion,
  Math as CesiumMath,
  OpenStreetMapImageryProvider,
  Viewer,
  ImageryLayer,
} from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';

const HOME = Object.freeze({ longitude: 78, latitude: -7, height: 8_400_000 });

const OceanGlobe = forwardRef(function OceanGlobe({ onReady }, ref) {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const [ready, setReady] = useState(false);

  const flyHome = (duration = 1.7) => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;
    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(HOME.longitude, HOME.latitude, HOME.height),
      orientation: { heading: 0, pitch: CesiumMath.toRadians(-88), roll: 0 },
      duration,
    });
  };

  useImperativeHandle(ref, () => ({
    getViewer: () => viewerRef.current,
    home: () => flyHome(),
    zoomIn: () => {
      const viewer = viewerRef.current;
      if (!viewer || viewer.isDestroyed()) return;
      viewer.camera.zoomIn(Math.max(viewer.camera.positionCartographic.height * 0.28, 120_000));
    },
    zoomOut: () => {
      const viewer = viewerRef.current;
      if (!viewer || viewer.isDestroyed()) return;
      viewer.camera.zoomOut(Math.max(viewer.camera.positionCartographic.height * 0.32, 120_000));
    },
  }));

  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return undefined;

    const token = import.meta.env.VITE_CESIUM_ION_TOKEN?.trim();
    if (token) Ion.defaultAccessToken = token;

    let viewer;
    try {
      const baseLayer = new ImageryLayer(new OpenStreetMapImageryProvider({
        url: 'https://tile.openstreetmap.org/',
      }));

      viewer = new Viewer(containerRef.current, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        baseLayer,
        terrainProvider: new EllipsoidTerrainProvider(),
        requestRenderMode: true,
        maximumRenderTimeChange: Infinity,
      });

      viewerRef.current = viewer;
      viewer.scene.backgroundColor = Color.fromCssColorString('#02070b');
      viewer.scene.globe.baseColor = Color.fromCssColorString('#061923');
      viewer.scene.globe.showGroundAtmosphere = true;
      viewer.scene.skyAtmosphere.show = true;
      viewer.scene.fog.enabled = true;
      viewer.scene.screenSpaceCameraController.enableCollisionDetection = true;
      viewer.scene.screenSpaceCameraController.minimumZoomDistance = 80_000;
      viewer.scene.screenSpaceCameraController.maximumZoomDistance = 45_000_000;
      viewer.scene.globe.enableLighting = false;
      viewer.camera.setView({
        destination: Cartesian3.fromDegrees(HOME.longitude, HOME.latitude, HOME.height),
        orientation: { heading: 0, pitch: CesiumMath.toRadians(-88), roll: 0 },
      });
      setReady(true);
      if (typeof onReady === 'function') {
        onReady(viewer);
      }
    } catch (error) {
      console.error('Unable to initialize Cesium globe:', error);
    }

    return () => {
      setReady(false);
      if (viewer && !viewer.isDestroyed()) viewer.destroy();
      if (viewerRef.current === viewer) viewerRef.current = null;
    };
  }, [onReady]);

  return (
    <div className="globe-stage" aria-label="Interactive global 3D Earth">
      <div ref={containerRef} className="cesium-host" />
      <div className="globe-vignette" aria-hidden="true" />
      <div className={`globe-loader ${ready ? 'globe-loader--hidden' : ''}`} aria-live="polite">
        <span className="loader-orbit" />
        <span>Initializing global environment</span>
      </div>
    </div>
  );
});

export default OceanGlobe;

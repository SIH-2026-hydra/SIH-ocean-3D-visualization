import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Math as CesiumMath,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
} from 'cesium';
import TemperatureLayer from '../layers/TemperatureLayer';
import ScalarFieldLayer from '../layers/ScalarFieldLayer';
import CurrentVectorLayer from '../layers/CurrentVectorLayer';
import ObservationLayer from '../layers/ObservationLayer';
import TemperatureLegend from '../legends/TemperatureLegend';
import GlobeControls from '../globe/GlobeControls';
import OceanGlobe from '../globe/OceanGlobe';
import SelectedLocationMarker from '../globe/SelectedLocationMarker';
import OceanInspector from '../inspector/OceanInspector';
import DepthControl from '../controls/DepthControl';
import TimeControl from '../controls/TimeControl';
import ParameterControl from '../controls/ParameterControl';
import ObservationToggle from '../controls/ObservationToggle';
import { getOceanData, getOceanMetadata, getOceanPoint } from '../../services/api';
import { getBathymetryPoint } from '../../services/bathymetryApi';
import { getNearestObservation, getObservations } from '../../services/observationsApi';
import { getTemperatureRange } from '../../utils/temperatureColorScale';
import { getSalinityColor } from '../../utils/salinityColorScale';
const DEFAULT_TEMPERATURE_TIME = '2026-08-24T00:00:00Z';
const DEMO_BOUNDS = {
  minLat: 5,
  maxLat: 30,
  minLon: 45,
  maxLon: 95,
};
const DEFAULT_DEPTHS = [0, 50, 100, 200, 500];

function OceanMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span className="brand-orbit brand-orbit--one" />
      <span className="brand-orbit brand-orbit--two" />
      <span className="brand-core" />
    </div>
  );
}

export default function AppShell() {
  const globeRef = useRef(null);
  const [viewer, setViewer] = useState(null);
  const [temperatureData, setTemperatureData] = useState([]);
  const [temperatureMetadata, setTemperatureMetadata] = useState({});
  const [availableDepths, setAvailableDepths] = useState(DEFAULT_DEPTHS);
  const [availableTimestamps, setAvailableTimestamps] = useState([DEFAULT_TEMPERATURE_TIME]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedTime, setSelectedTime] = useState(DEFAULT_TEMPERATURE_TIME);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [pointData, setPointData] = useState(null);
  const [pointLoading, setPointLoading] = useState(false);
  const [pointError, setPointError] = useState('');
  const [bathymetry, setBathymetry] = useState(null);
  const [bathymetryUnavailable, setBathymetryUnavailable] = useState(false);
  const [showObservations, setShowObservations] = useState(true);
  const [observationMarkers, setObservationMarkers] = useState([]);
  const [selectedObservation, setSelectedObservation] = useState(null);
  const [selectedDepth, setSelectedDepth] = useState(0);
  const [selectedParameter, setSelectedParameter] = useState('temperature');
  const temperatureRequestRef = useRef(null);
  const pointRequestRef = useRef(null);
  const bathymetryRequestRef = useRef(null);
  const observationRequestRef = useRef(null);
  const observationSelectionRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMetadata() {
      try {
        const metadataResponse = await getOceanMetadata();
        const discovery = metadataResponse?.discovery;
        const timestamps = discovery?.timestamps || [DEFAULT_TEMPERATURE_TIME];
        const normalizedTimestamps = timestamps.filter((timestamp) => typeof timestamp === 'string').sort();
        const earliest = normalizedTimestamps[0] || DEFAULT_TEMPERATURE_TIME;
        const depths = (discovery?.depths || DEFAULT_DEPTHS)
          .map(Number)
          .filter(Number.isFinite)
          .sort((first, second) => first - second);

        if (!cancelled) {
          setSelectedTime(earliest);
          setAvailableTimestamps(normalizedTimestamps.length ? normalizedTimestamps : [DEFAULT_TEMPERATURE_TIME]);
          if (depths.length) {
            setAvailableDepths(depths);
            setSelectedDepth((currentDepth) => (depths.includes(currentDepth) ? currentDepth : depths[0]));
          }
        }
      } catch (loadError) {
        console.warn('Unable to fetch ocean metadata:', loadError);
      }
    }

    loadMetadata();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return undefined;

    let cancelled = false;
    temperatureRequestRef.current?.abort();
    const controller = new AbortController();
    temperatureRequestRef.current = controller;

    async function loadTemperature() {
      setLoading(true);
      setError('');
      setTemperatureData([]);
      setTemperatureMetadata({});

      try {
        const result = await getOceanData({
          parameter: selectedParameter,
          depth: selectedDepth,
          time: selectedTime,
          signal: controller.signal,
          minLat: DEMO_BOUNDS.minLat,
          maxLat: DEMO_BOUNDS.maxLat,
          minLon: DEMO_BOUNDS.minLon,
          maxLon: DEMO_BOUNDS.maxLon,
        });

        if (!cancelled) {
          const nextData = Array.isArray(result?.data) ? result.data : [];
          setTemperatureData(nextData);
          setTemperatureMetadata(result?.metadata || {});
          if (!nextData.length) setError(`${selectedParameter} data unavailable for this depth and time.`);
        }
      } catch (fetchError) {
        if (!cancelled && fetchError.name !== 'AbortError') {
          setTemperatureData([]);
          setTemperatureMetadata({});
          setError(fetchError.message || `${selectedParameter} data failed to load.`);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadTemperature();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [selectedParameter, selectedTime, selectedDepth, viewer]);

  const legendRange = useMemo(() => {
    const values = temperatureData.map((item) => Number(selectedParameter === 'current' ? item.speed : item.value)).filter(Number.isFinite);
    return values.length ? getTemperatureRange(values) : { min: 0, max: 0 };
  }, [selectedParameter, temperatureData]);

  const handleGlobeSelection = async (screenPosition) => {
    const currentViewer = viewer || globeRef.current?.getViewer?.();
    if (!currentViewer || currentViewer.isDestroyed()) return;

    const scene = currentViewer.scene;
    const globe = scene.globe;
    const cartesian = scene.camera.pickEllipsoid(screenPosition, globe.ellipsoid);
    if (!cartesian) {
      setPointError('Ocean data unavailable for this location');
      return;
    }

    const cartographic = globe.ellipsoid.cartesianToCartographic(cartesian);
    const latitude = CesiumMath.toDegrees(cartographic.latitude);
    const longitude = CesiumMath.toDegrees(cartographic.longitude);

    const nextLocation = { latitude, longitude };
    observationSelectionRef.current = null;
    setSelectedObservation(null);
    setSelectedLocation(nextLocation);
  };

  const loadPoint = async (location) => {
    const clickedObservation = observationSelectionRef.current;
    observationSelectionRef.current = null;
    pointRequestRef.current?.abort();
    const controller = new AbortController();
    pointRequestRef.current = controller;
    setPointError('');
    setPointLoading(true);
    setPointData(null);
    setSelectedObservation(clickedObservation || null);

    try {
      const result = await getOceanPoint({
        lat: location.latitude,
        lon: location.longitude,
        depth: selectedDepth,
        time: selectedTime,
        signal: controller.signal,
      });
      if (!controller.signal.aborted) setPointData(result);
      const nearest = await getNearestObservation({ lat: location.latitude, lon: location.longitude, depth: selectedDepth, time: selectedTime, signal: controller.signal });
      if (!controller.signal.aborted && !clickedObservation) setSelectedObservation(nearest.observation);
    } catch (fetchError) {
      if (fetchError.name !== 'AbortError' && !controller.signal.aborted) {
        setPointError(fetchError.message || 'Ocean data unavailable for this location');
      }
    } finally {
      if (!controller.signal.aborted) setPointLoading(false);
    }
  };

  useEffect(() => {
    if (selectedLocation) loadPoint(selectedLocation);
  }, [selectedDepth, selectedLocation, selectedTime]);

  useEffect(() => {
    if (!selectedLocation) return undefined;

    bathymetryRequestRef.current?.abort();
    const controller = new AbortController();
    bathymetryRequestRef.current = controller;
    setBathymetry(null);
    setBathymetryUnavailable(false);

    getBathymetryPoint(selectedLocation.latitude, selectedLocation.longitude, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setBathymetry(result);
          setBathymetryUnavailable(result === null);
        }
      })
      .catch((fetchError) => {
        if (fetchError.name !== 'AbortError') {
          setBathymetryUnavailable(true);
          console.warn('Bathymetry unavailable:', fetchError);
        }
      });

    return () => controller.abort();
  }, [selectedLocation]);

  useEffect(() => {
    if (!showObservations) {
      setObservationMarkers([]);
      return undefined;
    }
    observationRequestRef.current?.abort();
    const controller = new AbortController();
    observationRequestRef.current = controller;
    getObservations({ time: selectedTime, min_lat: DEMO_BOUNDS.minLat, max_lat: DEMO_BOUNDS.maxLat, min_lon: DEMO_BOUNDS.minLon, max_lon: DEMO_BOUNDS.maxLon, signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setObservationMarkers(result.data || []); })
      .catch((fetchError) => { if (fetchError.name !== 'AbortError') console.warn('Observations unavailable:', fetchError); });
    return () => controller.abort();
  }, [selectedTime, showObservations]);

  const handleObservationSelect = useCallback((observation) => {
    observationSelectionRef.current = observation;
    setSelectedLocation({ latitude: observation.latitude, longitude: observation.longitude });
    setSelectedObservation(observation);
  }, []);

  useEffect(() => {
    const currentViewer = viewer || globeRef.current?.getViewer?.();
    if (!currentViewer || currentViewer.isDestroyed()) return undefined;

    const handler = new ScreenSpaceEventHandler(currentViewer.scene.canvas);
    let isDragging = false;
    let dragStart = null;

    handler.setInputAction((movement) => {
      dragStart = { x: movement.position.x, y: movement.position.y };
      isDragging = false;
    }, ScreenSpaceEventType.LEFT_DOWN);

    handler.setInputAction((movement) => {
      if (!dragStart) return;
      const dx = movement.endPosition.x - dragStart.x;
      const dy = movement.endPosition.y - dragStart.y;
      isDragging = Math.hypot(dx, dy) > 8;
    }, ScreenSpaceEventType.MOUSE_MOVE);

    handler.setInputAction(() => {
      isDragging = false;
      dragStart = null;
    }, ScreenSpaceEventType.LEFT_UP);

    handler.setInputAction((click) => {
      if (isDragging) return;
      handleGlobeSelection(click.position);
    }, ScreenSpaceEventType.LEFT_CLICK);

    return () => handler.destroy();
  }, [viewer, selectedTime, selectedDepth]);

  return (
    <main className="app-shell">
      <OceanGlobe ref={globeRef} onReady={setViewer} />
      {viewer && selectedParameter === 'temperature' && (
        <TemperatureLayer
          viewer={viewer}
          data={temperatureData}
          metadata={temperatureMetadata}
          selectedTimestamp={selectedTime}
          selectedDepth={selectedDepth}
        />
      )}
      {viewer && selectedParameter === 'salinity' && (
        <ScalarFieldLayer viewer={viewer} data={temperatureData} colorScale={getSalinityColor} parameter="salinity" selectedTimestamp={selectedTime} selectedDepth={selectedDepth} />
      )}
      {viewer && selectedParameter === 'current' && (
        <CurrentVectorLayer viewer={viewer} data={temperatureData} selectedTimestamp={selectedTime} selectedDepth={selectedDepth} />
      )}
      {viewer && <ObservationLayer viewer={viewer} observations={observationMarkers} visible={showObservations} onSelect={handleObservationSelect} />}
      {viewer && (
        <SelectedLocationMarker
          viewer={viewer}
          location={selectedLocation}
          active={Boolean(selectedLocation) && !pointError}
        />
      )}

      <header className="topbar glass-panel">
        <div className="brand-lockup">
          <OceanMark />
          <div className="brand-copy">
            <strong>Ocean Intelligence Explorer</strong>
            <span>Global Ocean Intelligence Platform</span>
          </div>
        </div>
        <div className="topbar-meta">
          <div className="prototype-badge"><span className="status-pulse" />Prototype Environment</div>
          <div className="phase-chip"><span>Phase 08B</span><b>In-Situ Observations</b></div>
        </div>
      </header>

      <section className="view-context glass-panel" aria-label="Current view">
        <div className="context-symbol" aria-hidden="true">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2"/><path d="M3.8 12h16.4M12 3.8c2.2 2.3 3.3 5 3.3 8.2S14.2 17.9 12 20.2M12 3.8C9.8 6.1 8.7 8.8 8.7 12s1.1 5.9 3.3 8.2"/></svg>
        </div>
        <div><span>Default View</span><strong>Indian Ocean</strong></div>
        <i aria-hidden="true" />
      </section>

      <DepthControl
        depths={availableDepths}
        selectedDepth={selectedDepth}
        onChange={setSelectedDepth}
        loading={loading || pointLoading}
      />

      <ParameterControl selectedParameter={selectedParameter} onChange={setSelectedParameter} />
      <ObservationToggle checked={showObservations} onChange={setShowObservations} />

      <TimeControl
        timestamps={availableTimestamps}
        selectedTime={selectedTime}
        onChange={setSelectedTime}
        loading={loading || pointLoading}
      />

      <GlobeControls
        onHome={() => globeRef.current?.home()}
        onZoomIn={() => globeRef.current?.zoomIn()}
        onZoomOut={() => globeRef.current?.zoomOut()}
      />

      {loading && (
        <div className="temperature-status temperature-status--loading glass-panel">
          Loading temperature field…
        </div>
      )}

      {error && (
        <div className="temperature-status temperature-status--error glass-panel" role="alert">
          {error}
        </div>
      )}

      {viewer && (
        <OceanInspector
          selectedLocation={selectedLocation}
          pointData={pointData}
          bathymetry={bathymetry}
          bathymetryUnavailable={bathymetryUnavailable}
          observation={selectedObservation}
          loading={pointLoading}
          error={pointError}
          onClose={() => {
            setSelectedLocation(null);
            setPointData(null);
            setBathymetry(null);
            setBathymetryUnavailable(false);
            setPointError('');
          }}
        />
      )}

      <TemperatureLegend
        min={legendRange.min}
        max={legendRange.max}
        selectedDepth={selectedDepth}
        timestamp={selectedTime}
        provenance={temperatureMetadata.sourceType || 'model'}
        parameter={selectedParameter}
        unit={selectedParameter === 'temperature' ? '°C' : selectedParameter === 'salinity' ? 'PSU' : 'm/s'}
      />

      <footer className="mission-strip">
        <div><span className="mission-dot" />GLOBAL EXPLORATION</div>
        <span className="mission-separator" />
        <div>PHASE 8B · IN-SITU OBSERVATIONS</div>
        <span className="mission-spacer" />
        <div className="interaction-hint"><span>DRAG</span> rotate <span>SCROLL</span> zoom</div>
      </footer>
    </main>
  );
}

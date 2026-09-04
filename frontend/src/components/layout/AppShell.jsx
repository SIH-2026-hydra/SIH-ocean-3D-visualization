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
import DatasetInfoPanel from './DatasetInfoPanel';
import { getCapabilityDiscovery, getCoverageDiscovery, getDatasetCatalog, getOceanData, getOceanMetadata, getOceanPoint, getVariableDiscovery } from '../../services/api';
import { getBathymetryPoint } from '../../services/bathymetryApi';
import { getNearestObservation, getObservations } from '../../services/observationsApi';
import { getPointPrediction } from '../../services/predictionsApi';
import { getTemperatureColor, getTemperatureRange } from '../../utils/temperatureColorScale';
import { getSalinityColor } from '../../utils/salinityColorScale';
import { createPointQuery, normalizeLocation } from '../../utils/location';
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
  const [availableDepths, setAvailableDepths] = useState([]);
  const [availableTimestamps, setAvailableTimestamps] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [variables, setVariables] = useState([]);
  const [coverage, setCoverage] = useState([]);
  const [capabilities, setCapabilities] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [pointData, setPointData] = useState(null);
  const [pointLoading, setPointLoading] = useState(false);
  const [pointError, setPointError] = useState('');
  const [bathymetry, setBathymetry] = useState(null);
  const [bathymetryUnavailable, setBathymetryUnavailable] = useState(false);
  const [showObservations, setShowObservations] = useState(true);
  const [observationMarkers, setObservationMarkers] = useState([]);
  const [selectedObservation, setSelectedObservation] = useState(null);
  const [selectedDepth, setSelectedDepth] = useState(null);
  const [selectedParameter, setSelectedParameter] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [predictionUnavailableReason, setPredictionUnavailableReason] = useState(null);
  const temperatureRequestRef = useRef(null);
  const pointRequestRef = useRef(null);
  const bathymetryRequestRef = useRef(null);
  const observationRequestRef = useRef(null);
  const predictionRequestRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMetadata() {
      try {
        const [metadataResponse, catalogResponse, variableResponse, coverageResponse, capabilityResponse] = await Promise.all([
          getOceanMetadata(), getDatasetCatalog(), getVariableDiscovery(), getCoverageDiscovery(), getCapabilityDiscovery(),
        ]);
        const discovery = metadataResponse?.discovery || {};
        const nextDatasets = catalogResponse?.datasets || [];
        const nextVariables = variableResponse?.variables || [];
        const nextCoverage = coverageResponse?.coverage || [];
        const nextCapabilities = capabilityResponse?.capabilities || {};
        const activeDataset = nextDatasets[0];
        const timestamps = discovery?.timestamps?.length ? discovery.timestamps : [activeDataset?.temporal_coverage?.start, activeDataset?.temporal_coverage?.end].filter(Boolean);
        const normalizedTimestamps = timestamps.filter((timestamp) => typeof timestamp === 'string').sort();
        const earliest = normalizedTimestamps[0] || '';
        const depths = (activeDataset?.available_depth_levels || discovery?.depths || [])
          .map(Number)
          .filter(Number.isFinite)
          .sort((first, second) => first - second);

        if (!cancelled) {
          setSelectedTime(earliest);
          setAvailableTimestamps(normalizedTimestamps);
          if (depths.length) {
            setAvailableDepths(depths);
            setSelectedDepth((currentDepth) => (depths.includes(currentDepth) ? currentDepth : depths[0]));
          }
          setDatasets(nextDatasets);
          setVariables(nextVariables);
          setCoverage(nextCoverage);
          setCapabilities(nextCapabilities);
          setSelectedParameter((current) => nextVariables.some((item) => item.variable_name === current) ? current : (nextVariables.find((item) => !item.is_derived)?.variable_name || nextVariables[0]?.variable_name || ''));
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

  const activeDataset = datasets[0] || null;
  const activeCoverage = coverage.find((item) => item.dataset_id === activeDataset?.dataset_id) || coverage[0] || null;
  const queryBounds = activeCoverage?.spatial_coverage ? {
    minLat: activeCoverage.spatial_coverage.min_latitude,
    maxLat: activeCoverage.spatial_coverage.max_latitude,
    minLon: activeCoverage.spatial_coverage.min_longitude,
    maxLon: activeCoverage.spatial_coverage.max_longitude,
  } : {};
  const selectedVariable = variables.find((item) => item.variable_name === selectedParameter) || {};
  const isOperationalDataset = activeDataset?.provider === 'Copernicus Marine';
  const homeLocation = useMemo(() => {
    const bounds = activeCoverage?.spatial_coverage;
    if (!bounds) return undefined;
    return {
      longitude: (bounds.min_longitude + bounds.max_longitude) / 2,
      latitude: (bounds.min_latitude + bounds.max_latitude) / 2,
      height: 8_400_000,
    };
  }, [activeCoverage]);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || !selectedParameter || selectedDepth === null || !selectedTime) return undefined;

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
          minLat: queryBounds.minLat,
          maxLat: queryBounds.maxLat,
          minLon: queryBounds.minLon,
          maxLon: queryBounds.maxLon,
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
  }, [selectedParameter, selectedTime, selectedDepth, viewer, queryBounds.minLat, queryBounds.maxLat, queryBounds.minLon, queryBounds.maxLon]);

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

    const nextLocation = normalizeLocation({ latitude, longitude });
    if (!nextLocation) return;
    setSelectedObservation(null);
    setSelectedLocation(nextLocation);
  };

  const loadPoint = async (location) => {
    const query = createPointQuery(location, selectedDepth, selectedTime);
    if (!query) return;
    pointRequestRef.current?.abort();
    const controller = new AbortController();
    pointRequestRef.current = controller;
    setPointError('');
    setPointLoading(true);
    setPointData(null);
    setSelectedObservation(null);

    try {
      const result = await getOceanPoint({
        lat: query.latitude,
        lon: query.longitude,
        depth: query.depth,
        time: query.time,
        signal: controller.signal,
      });
      if (!controller.signal.aborted) setPointData(result);
      const nearest = await getNearestObservation({ lat: query.latitude, lon: query.longitude, depth: query.depth, time: query.time, signal: controller.signal });
      if (!controller.signal.aborted) setSelectedObservation(nearest.observation);
    } catch (fetchError) {
      if (fetchError.name !== 'AbortError' && !controller.signal.aborted) {
        setPointError(fetchError.message || 'Ocean data unavailable for this location');
      }
    } finally {
      if (!controller.signal.aborted) setPointLoading(false);
    }
  };

  useEffect(() => {
    const query = createPointQuery(selectedLocation, selectedDepth, selectedTime);
    if (isOperationalDataset) {
      predictionRequestRef.current?.abort();
      setPrediction(null);
      setPredictionUnavailableReason(null);
      return undefined;
    }
    if (!query) {
      pointRequestRef.current?.abort();
      setPointData(null);
      setSelectedObservation(null);
      setPointLoading(false);
      return undefined;
    }
    loadPoint(query);
    return undefined;
  }, [isOperationalDataset, selectedDepth, selectedLocation, selectedTime]);

  useEffect(() => {
    const query = createPointQuery(selectedLocation, selectedDepth, selectedTime);
    if (!query) {
      predictionRequestRef.current?.abort();
      setPrediction(null);
      setPredictionUnavailableReason(null);
      return undefined;
    }

    predictionRequestRef.current?.abort();
    const controller = new AbortController();
    predictionRequestRef.current = controller;
    setPrediction(null);
    setPredictionUnavailableReason(null);

    getPointPrediction({
      lat: query.latitude,
      lon: query.longitude,
      depth: query.depth,
      time: query.time,
      signal: controller.signal,
    })
      .then((result) => {
        if (!controller.signal.aborted) {
          setPrediction(result.prediction);
          setPredictionUnavailableReason(result.unavailable_reason || null);
        }
      })
      .catch((fetchError) => {
        if (fetchError.name !== 'AbortError') console.warn('ML prediction unavailable:', fetchError);
      });

    return () => controller.abort();
  }, [selectedDepth, selectedLocation, selectedTime]);

  useEffect(() => {
    const location = normalizeLocation(selectedLocation);
    if (!location) {
      bathymetryRequestRef.current?.abort();
      setBathymetry(null);
      setBathymetryUnavailable(false);
      return undefined;
    }

    bathymetryRequestRef.current?.abort();
    const controller = new AbortController();
    bathymetryRequestRef.current = controller;
    setBathymetry(null);
    setBathymetryUnavailable(false);

    getBathymetryPoint(location.latitude, location.longitude, controller.signal)
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
    if (!showObservations || isOperationalDataset) {
      setObservationMarkers([]);
      return undefined;
    }
    observationRequestRef.current?.abort();
    const controller = new AbortController();
    observationRequestRef.current = controller;
    if (!capabilities.query_types?.includes('viewport') || !selectedTime) return undefined;
    getObservations({ time: selectedTime, min_lat: queryBounds.minLat, max_lat: queryBounds.maxLat, min_lon: queryBounds.minLon, max_lon: queryBounds.maxLon, signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setObservationMarkers(result.data || []); })
      .catch((fetchError) => { if (fetchError.name !== 'AbortError') console.warn('Observations unavailable:', fetchError); });
    return () => controller.abort();
  }, [isOperationalDataset, selectedTime, showObservations, capabilities.query_types, queryBounds.minLat, queryBounds.maxLat, queryBounds.minLon, queryBounds.maxLon]);

  const handleObservationSelect = useCallback((observation) => {
    const location = normalizeLocation(observation);
    if (!location) return;
    setSelectedObservation(null);
    setSelectedLocation(location);
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
      <OceanGlobe ref={globeRef} onReady={setViewer} homeLocation={homeLocation} />
      {viewer && selectedParameter === 'temperature' && (
        <TemperatureLayer
          viewer={viewer}
          data={temperatureData}
          metadata={temperatureMetadata}
          selectedTimestamp={selectedTime}
          selectedDepth={selectedDepth}
        />
      )}
      {viewer && selectedParameter !== 'temperature' && selectedParameter !== 'current' && (
        <ScalarFieldLayer viewer={viewer} data={temperatureData} colorScale={selectedParameter === 'salinity' ? getSalinityColor : getTemperatureColor} parameter={selectedParameter} selectedTimestamp={selectedTime} selectedDepth={selectedDepth} />
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
            <strong>OCEANX</strong>
            <span>Indian Ocean Operational Platform</span>
          </div>
        </div>
        <div className="topbar-meta">
          <div className="prototype-badge"><span className="status-pulse" />{isOperationalDataset ? 'Operational data' : 'Development data'}</div>
          <div className="phase-chip"><span>Indian Ocean</span><b>{activeDataset?.provider || 'Connecting'}</b></div>
        </div>
      </header>

      <section className="view-context glass-panel" aria-label="Current view">
        <div className="context-symbol" aria-hidden="true">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2"/><path d="M3.8 12h16.4M12 3.8c2.2 2.3 3.3 5 3.3 8.2S14.2 17.9 12 20.2M12 3.8C9.8 6.1 8.7 8.8 8.7 12s1.1 5.9 3.3 8.2"/></svg>
        </div>
        <div><span>Active model</span><strong>{activeDataset?.model || 'Discovering datasets'}</strong></div>
        <i aria-hidden="true" />
      </section>

      {capabilities.interval_queries?.depth && <DepthControl
          depths={availableDepths}
          selectedDepth={selectedDepth}
          onChange={setSelectedDepth}
          loading={loading || pointLoading}
        />}

      <ParameterControl variables={variables} selectedParameter={selectedParameter} onChange={setSelectedParameter} />
      {!isOperationalDataset && <ObservationToggle checked={showObservations} onChange={setShowObservations} />}

      {capabilities.interval_queries?.time && <TimeControl
          timestamps={availableTimestamps}
          selectedTime={selectedTime}
          onChange={setSelectedTime}
          loading={loading || pointLoading}
        />}

      <GlobeControls
        onHome={() => globeRef.current?.home()}
        onZoomIn={() => globeRef.current?.zoomIn()}
        onZoomOut={() => globeRef.current?.zoomOut()}
      />

      <DatasetInfoPanel dataset={activeDataset} coverage={activeCoverage} metadata={temperatureMetadata} />

      {loading && (
        <div className="temperature-status temperature-status--loading glass-panel">
          Loading {selectedVariable.display_name || selectedParameter} field…
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
          prediction={prediction}
          predictionUnavailableReason={predictionUnavailableReason}
          selectedDepth={selectedDepth}
          selectedTime={selectedTime}
          selectedVariable={selectedVariable}
          operationalMode={isOperationalDataset}
          loading={pointLoading}
          error={pointError}
          onClose={() => {
            setSelectedLocation(null);
            setPointData(null);
            setBathymetry(null);
            setBathymetryUnavailable(false);
            setPrediction(null);
            setPredictionUnavailableReason(null);
            setPointError('');
          }}
        />
      )}

      <TemperatureLegend
        min={legendRange.min}
        max={legendRange.max}
        selectedDepth={selectedDepth}
        timestamp={selectedTime}
        provenance={activeDataset?.provider || temperatureMetadata.sourceType || 'model'}
        parameter={selectedParameter}
        label={selectedVariable.display_name}
        unit={selectedVariable.units || temperatureMetadata.units || ''}
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

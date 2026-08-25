/**
 * Cesium configuration and initialization helpers.
 * Infrastructure-level setup only.
 * Globe instantiation and scene manipulation reserved for frontend implementation.
 */

// Cesium must be installed via npm. The module is imported by components at render time.
// Assets (Workers, Assets, Widgets, ThirdParty) are located in node_modules/cesium
// and resolved by Vite during build.
//
// To use Cesium in a component:
//   import * as Cesium from 'cesium';
//   import 'cesium/Build/Cesium/Widgets/widgets.css';
//   const viewer = new Cesium.Viewer(...);
//
// This file is not instantiating a Viewer or manipulating any scene entities.



import {
  Cartesian3,
  Ion,
  Math as CesiumMath,
} from "cesium";

/**
 * Geographic scope
 * ----------------
 * The platform is global.
 * These coordinates define only the default SIH demonstration view.
 */
export const HOME_VIEW = {
  longitude: 78,
  latitude: 5,
  height: 8_500_000,
  heading: 0,
  pitch: -75,
  roll: 0,
};

export function getHomeCameraDestination() {
  return Cartesian3.fromDegrees(
    HOME_VIEW.longitude,
    HOME_VIEW.latitude,
    HOME_VIEW.height
  );
}

export function getHomeCameraOrientation() {
  return {
    heading: CesiumMath.toRadians(HOME_VIEW.heading),
    pitch: CesiumMath.toRadians(HOME_VIEW.pitch),
    roll: CesiumMath.toRadians(HOME_VIEW.roll),
  };
}

/**
 * Configure Cesium environment-level settings.
 *
 * Never hard-code credentials in source control.
 */
export function configureCesium() {
  const ionToken = import.meta.env.VITE_CESIUM_ION_TOKEN?.trim();

  if (ionToken) {
    Ion.defaultAccessToken = ionToken;
  }
}

/**
 * Shared Viewer defaults for the Phase 1 globe.
 *
 * Scientific visualization layers will be added in later phases.
 */
export const CESIUM_VIEWER_OPTIONS = {
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
  vrButton: false,

  shouldAnimate: true,
};

/**
 * Default duration for smooth camera transitions.
 */
export const CAMERA_FLIGHT_DURATION = 1.8;

/**
 * Relative camera movement used by the custom zoom controls.
 */
export const CAMERA_ZOOM_FACTOR = 0.35;
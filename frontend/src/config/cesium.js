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

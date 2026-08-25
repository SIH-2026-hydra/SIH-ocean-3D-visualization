PROJECT:
SIH26067 — Web-Based Interactive 3D Visualization of
Numerical Ocean Models and In-Situ Observations

PRODUCT:
A global interactive 3D ocean intelligence platform combining
numerical ocean model outputs and in-situ observations.

GEOGRAPHIC SCOPE:
Global architecture.
Indian Ocean = initial/default SIH demonstration viewport only.
Users must eventually be able to explore the entire globe.

PRIMARY EXPERIENCE:
The 3D globe is the product's visual centerpiece.
The interface should feel closer to a scientific combination of
Google Earth + ocean intelligence + weather visualization than a
traditional dashboard.

PROTOTYPE 1 EVENTUAL FEATURES:
- Global 3D globe
- Temperature
- Salinity
- Ocean currents
- Depth exploration
- Time exploration
- Observation stations
- Model data
- Model vs observation comparison
- Scientific legends
- Dataset/source metadata

IMPORTANT:
These are eventual Prototype 1 features.
DO NOT implement them all in the current Stitch generation.

CURRENT PHASE:
Frontend Phase 1 only.

IMPLEMENT NOW:
- Application shell
- Global Cesium globe
- Initial Indian Ocean camera position
- Rotate
- Zoom
- Pan/navigation
- Home/reset to Indian Ocean
- Professional scientific/ocean visual identity
- Desktop-first responsive foundation

DO NOT IMPLEMENT YET:
- Temperature
- Salinity
- Currents
- Observation markers
- Depth slider
- Timeline
- Model comparison
- API data visualization
- ML UI
- Charts

TECHNOLOGY:
React
Vite
CesiumJS
JavaScript/JSX

BACKEND:
FastAPI already exists.
Do not modify or recreate it.

FUTURE DATA FLOW:
Global datasets / global ML
        ↓
FastAPI
        ↓
regional bounding-box query
        ↓
Cesium visualization

VISUAL DIRECTION:
Professional scientific product.
Dark ocean-oriented interface.
High contrast.
Clean typography.
Minimal controls.
Large globe.
Avoid generic admin-dashboard appearance.
Avoid excessive cards.
Avoid decorative clutter.
The globe must dominate the screen.

FRONTEND COMPONENT CONTRACT:
App.jsx
→ application composition

AppShell.jsx
→ main application layout

OceanGlobe.jsx
→ Cesium globe/viewer

GlobeControls.jsx
→ globe navigation/home controls

styles/
→ visual system

IMPORTANT DEVELOPMENT RULE:
Preserve existing Vite/Cesium infrastructure.
Do not restructure working project configuration unnecessarily.
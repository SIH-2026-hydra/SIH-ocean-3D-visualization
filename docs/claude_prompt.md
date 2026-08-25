You are working directly inside an existing repository for **SIH26067 — Ocean Intelligence Explorer**, a web-based interactive 3D ocean intelligence platform integrating numerical ocean model outputs, in-situ observations and eventually globally trained ML outputs.
The backend foundation is already complete, tested and working. The frontend infrastructure has also already been created. Your task is NOT to scaffold another frontend. Your task is to implement the existing Phase 1 React files and turn the existing frontend scaffold into an exceptional, production-quality interactive 3D globe experience.
Before editing anything, inspect the repository and specifically read the existing `frontend/package.json`, `frontend/vite.config.js`, `frontend/.env.example`, `frontend/README.md`, `PROJECT_CONTEXT.md` if present, `frontend/src/main.jsx`, `frontend/src/config/cesium.js`, and all existing files under `frontend/src/components`. Preserve the existing architecture and working configuration wherever possible.
The frontend currently uses **React 18 + Vite 5 + CesiumJS**. Continue using JavaScript/JSX. Do not migrate to TypeScript. Do not replace Cesium with Three.js, React Three Fiber, Mapbox, a static map, image, CSS globe, video or another visualization technology.
This is **Frontend Phase 1 only**. Implement a real global CesiumJS globe, its application shell, its controls and the Phase 1 visual system. Do not implement scientific-data functionality yet.
The geographic architecture is GLOBAL. The application must render the entire Earth and allow unrestricted navigation anywhere on the planet. The **Indian Ocean is only the initial/default SIH demonstration camera position**, not a geographic system boundary. Do not restrict navigation or generic architecture to Indian Ocean coordinates.
Use the existing file responsibilities exactly:
`frontend/src/main.jsx` remains the React entry point. Preserve its existing React/StrictMode bootstrap and add the global `./styles/index.css` import if it is not already present.
`frontend/src/App.jsx` must remain very small and should primarily compose/render `AppShell`.
`frontend/src/components/layout/AppShell.jsx` owns the full-screen application composition and floating interface overlays. It must not contain Cesium Viewer lifecycle implementation.
`frontend/src/components/globe/OceanGlobe.jsx` owns the actual Cesium Viewer, globe container, Viewer lifecycle, initial camera positioning, camera operations exposed to the parent, and cleanup.
`frontend/src/components/globe/GlobeControls.jsx` owns the presentation and invocation of Home/Reset, Zoom In and Zoom Out controls.
`frontend/src/styles/index.css` owns the complete Phase 1 visual system.
`frontend/src/config/cesium.js` is infrastructure configuration. Reuse or improve it only if necessary for a reliable Cesium implementation.
`frontend/src/services/api.js` must remain untouched. Backend integration is deliberately deferred.
Do not collapse the application into one giant `App.jsx`. Maintain clean component boundaries.
The desired component relationship is:
`main.jsx → App.jsx → AppShell.jsx → OceanGlobe.jsx + GlobeControls.jsx`
with `index.css` providing the visual system.
Implement `OceanGlobe.jsx` as a REAL CesiumJS globe. Instantiate `Cesium.Viewer` only after the React container has mounted. Keep the Viewer instance stable using appropriate refs. Do not recreate it on every render. Handle React 18 StrictMode safely. Destroy the Viewer during cleanup so hot reloads/unmounting do not leak WebGL resources or create duplicate viewers.
Import the required Cesium widget CSS correctly.
The initial camera must smoothly establish a compelling view centered approximately over the **Indian Ocean**, with enough altitude and framing to communicate India, Arabian Sea, Bay of Bengal, surrounding Indian Ocean and wider geographic context. After initialization, the user must be free to rotate, pan and zoom globally using standard Cesium interaction.
Create a clean imperative interface between the globe and controls using `forwardRef`/`useImperativeHandle`, callbacks, or an equally clean React approach. Do NOT use global Viewer variables, DOM querying hacks or duplicated Viewer instances.
Expose operations sufficient for:

* reset/home to the Indian Ocean default viewpoint
* zoom in
* zoom out
  Home/Reset should use a smooth Cesium camera flight rather than an abrupt teleport.
  Disable unnecessary built-in Cesium widgets if they conflict visually with our custom interface, while preserving essential globe interaction and all legally required Cesium attribution/credits. Do not hide or circumvent required attribution.
  Do not hard-code or invent a Cesium ion token. Respect `VITE_CESIUM_ION_TOKEN` if the existing environment architecture provides one. The Phase 1 implementation should preferably remain usable without committing any private credential. If the selected Cesium imagery/terrain configuration requires a token and no token is available, provide a sensible token-free fallback rather than breaking the application.
  IMPORTANT: inspect the existing Cesium/Vite asset configuration instead of assuming it works. Actually run the application/build. If Cesium Workers, Assets, Widgets or other runtime resources fail to resolve, make the smallest correct change to the frontend Vite/Cesium infrastructure necessary to support the real Viewer. Do not redesign unrelated configuration.
  Now implement the visual experience. The quality bar is extremely high. This should look like a premium scientific visualization product suitable for a major research organization, oceanographic institution or high-level hackathon presentation—not a student dashboard.
  Create a **cinematic dark glassmorphism ocean-science interface** where the real 3D Earth is the hero. The Cesium viewport should fill essentially the entire browser window and receive at least 90% of the visual attention. Never put the globe inside a card, bordered dashboard panel or tiled map container. It should be the full-screen spatial canvas with interface elements floating above it.
  The visual language should use deep near-black and abyssal-ocean tones with restrained cyan/aqua/ice-blue accents. Build high-quality translucent glass surfaces using carefully controlled transparency, backdrop blur, subtle saturation, thin luminous edge borders, soft multi-layer shadows and restrained internal highlights. Glass should feel physically believable and premium rather than simply being semi-transparent rectangles.
  Avoid the stereotypical AI-generated interface look. Do NOT create numerous rounded cards, excessive gradients, giant glowing headings, neon cyberpunk elements, oversized pills, random metric cards, decorative charts or excessive blue glow. Glassmorphism must be sophisticated and restrained.
  Typography should be exceptionally clean, precise and scientific. Establish a strong hierarchy between product identity, small technical descriptors, status labels and tooltips. Use sensible system/font stacks unless an existing dependency provides something appropriate; do not add a heavy font dependency unnecessarily.
  Create a compact floating top glass bar. It should feel integrated with the globe rather than like a website navbar. Include:
* a refined minimal ocean/globe/scientific symbol that can be implemented using CSS or lightweight inline SVG
* **Ocean Intelligence Explorer**
* a subtle descriptor such as **Global Ocean Intelligence Platform**
* a restrained **Prototype Environment** status indicator
  Do not include fake menu items for features that do not exist yet.
  Create a subtle floating geographic context element displaying something like:
  **Default View · Indian Ocean**
  This communicates camera context only. Do not imply the platform itself is Indian-Ocean-only.
  Create a beautifully minimal floating `GlobeControls` treatment containing:
* Home / Reset View
* Zoom In
* Zoom Out
  Use high-quality iconography via lightweight inline SVG rather than adding a large icon package unless one already exists.
  Every control must have:
* meaningful `aria-label`
* accessible keyboard focus
* tooltip
* hover state
* active/pressed feedback where appropriate
* polished 150–300ms transitions
  The controls should visually recede when idle and become slightly more prominent during interaction.
  Consider a subtle bottom-edge Phase 1 treatment containing only truthful contextual information such as:
  **Prototype Environment**
  **Phase 1 · Global Globe Foundation**
  Do not add fake scientific readings.
  The interface must NEVER claim:
* LIVE
* REAL-TIME
* current observations
* active buoy count
* temperature values
* salinity values
* model accuracy
* ML predictions
  because none of those data systems are connected in this phase.
  The base globe should be visually rich, elegant and suitable for future scientific overlays. Oceans should be distinguishable and visually important, but do not distort geography or apply excessive effects that would later interfere with temperature fields, observation markers or current vectors. Preserve recognizable land/ocean geography.
  Use Cesium atmosphere/scene settings conservatively if they improve depth and visual quality. The globe should feel dimensional and cinematic without becoming science-fiction themed. Avoid childish stars, exaggerated bloom and game-like effects.
  Ensure the application looks excellent at **1920×1080**, because this will be an important presentation resolution, while remaining properly usable on normal laptop displays such as 1366×768 and 1440×900. This is desktop-first. Use responsive CSS to prevent controls/header elements from colliding at smaller widths. Mobile optimization is not a Phase 1 priority, but the page must not catastrophically break.
  The application should have no ordinary page scrolling on desktop. Use a true viewport-filling layout.
  Leave visual space for future overlays without implementing them. Later phases will introduce left-side scientific controls, a bottom timeline and a right information panel. The Phase 1 shell should therefore avoid architectural decisions that would make those overlays impossible, but do NOT render empty placeholder panels for them now.
  Do not create a landing page, splash screen, marketing hero, feature section, onboarding sequence, sidebar dashboard or multiple pages. Opening the application should immediately put the user inside the actual global 3D exploration environment.
  Do not use stock photography, external decorative images or fake map screenshots. The real Cesium globe is the central visual.
  Do not connect FastAPI during this task. `src/services/api.js` must remain reserved.
  Do NOT implement:
  temperature visualization,
  salinity visualization,
  ocean currents,
  current particles,
  observation stations,
  Argo floats,
  buoys,
  model fields,
  bathymetry,
  depth slider,
  timeline,
  parameter selector,
  dataset selector,
  scientific legend,
  information panel,
  profile chart,
  model-vs-observation comparison,
  ML controls,
  search,
  authentication,
  analytics,
  landing pages,
  or any Phase 2+ functionality.
  Do not create fake placeholders for these features.
  Keep dependencies minimal. Prefer React, Cesium and high-quality CSS. Do not add Tailwind, Material UI, Bootstrap, Redux, Zustand, Three.js, React Three Fiber, Mapbox, chart libraries or large UI frameworks just to accomplish Phase 1. If an additional dependency is genuinely unavoidable, explain why before adding it. Prefer implementing the required UI without new dependencies.
  Once implementation is complete, do not stop at code generation. Validate it.
  From `frontend`, run the appropriate existing commands:
  `npm install` if dependencies are not already installed,
  `npm run lint`,
  `npm run build`.
  Fix errors rather than merely reporting them.
  Run the Vite development server long enough to verify that the application starts without runtime compilation errors. If your environment permits browser inspection, verify that the real Cesium globe initializes rather than showing a blank container.
  Do not modify the backend. Do not touch backend tests, backend data, backend requirements or backend architecture.
  Do not change the existing API service.
  Do not regenerate the project scaffold.
  Do not overwrite project documentation unnecessarily.
  If you encounter a problem with existing Vite/Cesium infrastructure that prevents the globe from working, make the smallest frontend infrastructure fix necessary and preserve the rest.
  The Phase 1 implementation is complete only when:
* the existing React application renders successfully
* a real Cesium globe fills the application viewport
* the entire Earth remains globally navigable
* the initial camera presents the Indian Ocean
* rotation works
* pan/navigation works
* zoom works
* Home/Reset smoothly returns to the Indian Ocean viewpoint
* Zoom In/Out controls operate on the real Cesium camera
* the React Viewer lifecycle is safe
* the application has an exceptional professional dark glassmorphism visual identity
* the globe remains visually dominant
* the UI is accessible and responsive for desktop/laptop
* no fake scientific data appears
* no Phase 2 functionality has been implemented
* `npm run lint` passes
* `npm run build` passes
* the backend remains untouched
  After these conditions are satisfied, STOP. Do not proceed to temperature, API integration or any other future phase.
  The final experience should make someone opening the application immediately think: **this is a sophisticated global scientific platform for exploring the ocean in 3D.** It should feel visually memorable and presentation-ready while remaining restrained, credible and extensible enough to become the foundation for the complete ocean intelligence platform.

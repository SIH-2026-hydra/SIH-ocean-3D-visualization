# Frontend Infrastructure

## Prerequisites

- Windows 10/11
- Node.js 18.0.0 or later
- npm 9.0.0 or later
- Git
- VS Code recommended

Verify installation:

```powershell
node --version
npm --version
```

## Setup

From the project root:

```powershell
cd frontend
npm install
```

This installs all dependencies locally into `node_modules/`. These files are not committed to Git; each developer must run `npm install` after cloning.

## Environment Configuration

Copy `.env.example` to `.env` and update as needed:

```powershell
copy .env.example .env
```

Example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_CESIUM_ION_TOKEN=
```

The `.env` file is **not** tracked by Git. Each developer provides their own Cesium ion token if needed. The API base URL defaults to the Phase 1 backend local address.

## Development

Start the Vite development server:

```powershell
npm run dev
```

The app will run on http://127.0.0.1:5173 and hot-reload on file changes.

## Linting

Check for linting issues:

```powershell
npm run lint
```

Fix automatically:

```powershell
npm run lint:fix
```

## Build for Production

Create an optimized production build:

```powershell
npm run build
```

Output is generated in `dist/`.

## Preview Production Build

```powershell
npm run preview
```

## Project Structure

```
frontend/
├── public/                  # Static assets
├── src/
│   ├── components/
│   │   ├── globe/          # Cesium globe components (reserved for frontend AI)
│   │   │   ├── OceanGlobe.jsx
│   │   │   └── GlobeControls.jsx
│   │   └── layout/         # Application layout (reserved for frontend AI)
│   │       └── AppShell.jsx
│   ├── config/
│   │   └── cesium.js       # Cesium configuration infrastructure
│   ├── services/
│   │   └── api.js          # FastAPI integration (reserved for frontend AI)
│   ├── styles/
│   │   └── index.css       # Global styles (reserved for frontend AI)
│   ├── App.jsx             # App root (reserved for frontend AI)
│   └── main.jsx            # React entry point
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── eslint.config.js        # ESLint configuration
├── index.html              # HTML entry point
├── package.json            # npm manifest
├── package-lock.json       # Dependency lock (committed to Git)
├── vite.config.js          # Vite configuration
└── README.md               # This file
```

## Stack

- **React 18**: UI framework
- **Vite 5**: Modern build tool and dev server
- **CesiumJS 1.120**: 3D geospatial visualization engine
- **ESLint 9**: Linting with React and React Hooks plugins

## Cesium Asset Handling

CesiumJS requires runtime assets (Workers, Assets, Widgets, ThirdParty) to be available during development and production.

**Installation:**
```powershell
npm install cesium
```

**Import and usage in components:**
```javascript
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';

// Create viewer, add entities, etc.
const viewer = new Cesium.Viewer('cesiumContainer');
```

Vite resolves Cesium assets from `node_modules/cesium` automatically. No manual asset copying is required. The build system handles asset bundling correctly.

## Global Geographic Architecture

This is a **global** ocean visualization platform, not an Indian-Ocean-only application.

**Key design decisions:**

- The frontend renders the entire Earth
- Global navigation (rotate, zoom, pan) is always available
- The Indian Ocean is the **default demonstration viewport** for Prototype 1
- Users can navigate to any geographic region
- Future ML pipelines may operate on global ocean datasets
- Future data requests will use bounding-box filtering (`min_lat`, `max_lat`, `min_lon`, `max_lon`) to fetch only the visible region

**Future Phase 1 globe requirements (for next frontend AI):**
- Render full Earth
- Initial camera position over Indian Ocean demonstration region
- Allow rotation, zooming, and panning
- Provide Home/Reset action to return camera to default Indian Ocean view
- No geographic restrictions on navigation

This architecture ensures the platform can grow to global scope without redesigning the frontend foundation.

## Dependency Policy

- **Commit:** `package.json`, `package-lock.json`, `.env.example`
- **Ignore:** `node_modules/`, `.env`, `dist/`, `.vscode/`, platform cache files
- **All dependencies:** Installed locally via npm, not globally
- **Lock file:** `package-lock.json` ensures identical dependency versions across all six Windows development systems

When dependencies change, always commit the updated `package-lock.json`.

## VS Code Integration

Select the frontend's local Node.js environment:

```
Ctrl + Shift + P
→ Terminal: Select Default Profile
→ PowerShell
→ Reopen in integrated terminal
```

VS Code will then use the local `node_modules/.bin/` binaries for linting and other tools.

## Notes

- **React implementation is intentionally deferred.** The `App.jsx`, `components/`, and `styles/` files contain only placeholders. A separate frontend AI tool will implement the actual React components and Cesium globe.

- **Build verification is deferred.** With reserved React entry files, `npm run build` will not produce a fully working application. Full verification happens after the frontend AI implements the globe.

- **Cesium Viewer is not instantiated in infrastructure setup.** `src/config/cesium.js` contains only documentation. The actual Cesium Viewer creation and scene manipulation is handled by the frontend implementation task.

## Troubleshooting

**npm install hangs or fails:**
- Verify Node.js and npm versions meet minimum requirements
- Clear npm cache: `npm cache clean --force`
- Delete `package-lock.json` and `node_modules/`, then retry

**Port 5173 already in use:**
- Check for other Vite instances: `netstat -ano | findstr :5173`
- Modify `vite.config.js` to use a different port

**ESLint errors in reserved files:**
- Those are expected. The linting config allows unused variables in reserved component files.
- Actual linting enforces best practices once the frontend AI writes real code.

## Next Steps

The frontend infrastructure is now complete. The next task is for a dedicated frontend AI to:

1. Implement `src/App.jsx` with the main application structure
2. Implement Cesium globe initialization in `src/components/globe/OceanGlobe.jsx`
3. Implement globe controls (rotation, zoom, pan, Home/Reset) in `src/components/globe/GlobeControls.jsx`
4. Implement layout structure in `src/components/layout/AppShell.jsx`
5. Add global styles in `src/styles/index.css`
6. Implement API integration in `src/services/api.js`
7. Build and verify the Phase 1 globe with initial Indian Ocean camera position and global navigation

Only then will backend API integration, ocean data visualization, and subsequent features follow.

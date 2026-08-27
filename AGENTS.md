# NicRush SIH Frontend Development Rules

## Scope

This workspace is for the React frontend of the NicRush SIH project.

The backend is COMPLETE and READ-ONLY.

## Absolute backend restriction

NEVER modify anything inside:

- backend/**
- backend/main.py
- backend/database.py
- backend/core/**
- backend/receiver/**
- backend/simulator/**

NEVER modify:

- Python files
- FastAPI routes
- FastAPI application logic
- SQLite database schema
- DCHI backend calculations
- telemetry processing
- backend standardization logic
- backend problem detection logic
- backend API contracts

The frontend must adapt to the existing backend.

The backend must NOT be changed to accommodate frontend code.

## Allowed frontend scope

Implementation may modify:

- frontend-react/**
- frontend-react/package.json
- frontend-react/package-lock.json
- Vite configuration
- TypeScript configuration
- Tailwind configuration
- shadcn configuration
- frontend-related documentation

Do not modify the existing legacy frontend unless explicitly instructed.

## API rules

The React application must consume the existing FastAPI API.

NEVER invent endpoints.

NEVER invent response fields.

NEVER rename backend fields inside the API layer without an explicit reason.

NEVER duplicate DCHI calculations in React.

The backend remains the single source of truth for:

- sensor standardization
- water-depth calculation
- blockage scoring
- DCHI
- status
- primary problem
- problem ranking
- priority ranking
- historical telemetry

## Architecture rules

Keep HTTP/API communication centralized in:

frontend-react/src/lib/

Keep API TypeScript interfaces in:

frontend-react/src/types/

Keep repeated server-state logic in:

frontend-react/src/hooks/

Keep reusable UI components in:

frontend-react/src/components/

Do not scatter raw fetch() calls throughout arbitrary components.

## Safety before editing

Before making any changes:

1. Inspect the relevant existing frontend code.
2. Inspect the relevant backend API implementation READ-ONLY.
3. Identify the exact endpoint and response fields being used.
4. List all files that will be modified.
5. Confirm that no backend file will be modified.

## Git safety

Before committing:

- Run git status.
- Confirm backend/** has no modifications.
- Do not commit backend changes.
- Do not commit local SQLite databases.
- Do not commit secrets or .env.local.

## Coding style

Prefer:

- TypeScript
- small reusable React components
- typed API responses
- clear naming
- accessible UI
- responsive layouts
- minimal dependencies

Avoid unnecessary state-management libraries.

Do not introduce Redux, Zustand, Next.js, or another backend unless explicitly requested.

## Product direction

NicRush is a municipal stormwater drainage digital twin.

The frontend should prioritize:

1. Network health
2. Priority queue
3. Node selection
4. DCHI
5. Sensor condition
6. Problem identification
7. Historical trends
8. Representative GIS network
9. Priority alerts

The dashboard should feel like a professional municipal operations interface rather than a generic IoT dashboard.

## Critical instruction

If a frontend problem appears to require a backend change:

STOP.

Explain the conflict and ask before modifying backend/**.

# AI Real Estate Advisor — Frontend

React + TypeScript (Vite) UI for the AI Real Estate Advisor backend. Replaces the retired Streamlit app.

## Setup

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if the API isn't on localhost:8000
npm run dev
```

The dev server runs at `http://localhost:5173` by default and talks to the FastAPI backend (`http://localhost:8000` unless overridden) over `fetch`.

## Build

```bash
npm run build      # type-checks (tsc -b) and outputs frontend/dist/
npm run preview    # serve the production build locally
```

## Structure

- `src/api/client.ts` — typed fetch client + shared constants (cities/localities)
- `src/tabs/` — Valuation, Market Insights, Financing, History, Documents tabs
- `src/components/Sidebar.tsx` — currency toggle, city snapshot, unit converter
- `src/index.css` — global theme (light/dark via `prefers-color-scheme`), no emoji/pictogram icons anywhere

## Notes

- Charts use `recharts`.
- Session history is persisted to `localStorage` (no backend persistence).
- The Documents tab exercises the RAG endpoints (`/documents`, `/documents/upload`, `/documents/chat`).

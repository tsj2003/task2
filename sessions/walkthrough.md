# O2C Context Graph System — Walkthrough

## What Was Built

A full-stack **context graph system with LLM-powered query interface** for SAP Order-to-Cash data.

### Backend (FastAPI + SQLite + NetworkX)
- **13 SQLite tables** with proper schemas, indexes, FK relationships
- **18,756 records** ingested from JSONL with zero errors
- **NetworkX DiGraph**: 797 nodes, 1,005 edges across 9 entity types
- **6 graph API endpoints**: overview, expand, detail, neighbors, search, full
- **Chat API**: NL → SQL → Answer pipeline with conversation memory
- **Gemini 2.0 Flash** integration with retry logic
- **Double-layer guardrails**: pre-filter (regex, keyword, injection) + post-filter (SQL validation)

### Frontend (React + Vite + react-force-graph-2d)
- **Interactive force-directed graph** with color-coded entity types (Primary blue, Secondary red)
- **Click-to-expand**: physics-based clustering allowing granular node toggling
- **Node tooltips**: beautiful floating white cards holding metadata
- **Chat panel**: fixed sidebar with avatar styling for `Dodge AI`, markdown parsing
- **UI Redesign**: Complete Light-theme enterprise dashboard with top navigation, pill toolbars, SVG icons, and airy blue-edged network layout.

### Resolved Issues
- **Graph Interaction Root Cause Fix**: Addressed a severe issue where nodes were unclickable in real usage. The three-part true root cause was:
  1. `NodeTooltip` was accidentally unmounted from `App.jsx` during a UI rewrite.
  2. **Sub-pixel aliasing**: At default zoom, tiny nodes (< 1px) suffered color-picking failure on `react-force-graph`'s hidden hit canvas.
  3. **Quadtree Bounds Clipping**: Linear radii exceeded the library's internal `Math.sqrt` hit bounds. Fixed by passing `nodeRelSize={20}` to artificially inflate the search bounds, ensuring the entire interaction buffer (`node.val + 8/scale`) is rigorously hit-tested.

- **Aesthetics vs Interaction Decoupling**: Returning to elegant tiny physics limits while strictly preserving exact clicking bounds.
  - **Hit area strategy**: Enforced a dynamic robust interaction hit buffer explicitly decoupled from visibility (`interactionRadius = size + 8 / globalScale`).
  - **Clutter Elimination**: Label rendering strictly throttled to only show when `isHovered`, `isHighlighted` OR `globalScale > 1.4`, cleaning up completely when viewing the entire dense graph mapping.

## Verification

| Check | Status |
|---|---|
| Backend health endpoint | ✅ `{"status": "ok"}` |
| Graph overview API (9 supernodes) | ✅ Working |
| Data ingestion (all 13 entity types) | ✅ 18,756 records |
| Frontend renders (navbar, graph, chat) | ✅ Verified in browser |
| Graph visualization (force-directed) | ✅ 9 entity nodes with edges |
| Chat panel UI (Dodge AI greeting) | ✅ Renders correctly |

![App Demo Recording](/Users/tarandeepsinghjuneja/.gemini/antigravity/brain/bf7cf377-210b-4732-a671-24cf4f0fcde4/screenshot_verification_1774340411398.webp)

![Clean Visual Layout with Decoupled Clicks](/Users/tarandeepsinghjuneja/.gemini/antigravity/brain/bf7cf377-210b-4732-a671-24cf4f0fcde4/hover_label_verification_1774350088781.png)

## One Remaining Step

> [!IMPORTANT]
> **You need to add your Gemini API key** to `backend/.env` to enable the chat/query functionality. The graph visualization works without it, but chat queries require the LLM.
>
> Get a free key at: https://ai.google.dev

## Files Created

| Path | Description |
|---|---|
| `backend/app/main.py` | FastAPI app with CORS and lifespan |
| `backend/app/database.py` | SQLite schema + safe SQL executor |
| `backend/app/graph/builder.py` | NetworkX graph construction |
| `backend/app/llm/prompts.py` | System prompt with 7 few-shot examples |
| `backend/app/llm/guardrails.py` | Pre/post query filtering |
| `backend/app/llm/sql_generator.py` | NL → SQL → Answer pipeline |
| `backend/scripts/ingest.py` | JSONL data ingestion |
| `frontend/src/components/GraphCanvas.jsx` | Force-directed graph |
| `frontend/src/components/ChatPanel.jsx` | Chat interface |
| `frontend/src/components/NodeTooltip.jsx` | Node metadata popup |
| `frontend/src/App.css` | Complete dark theme |
| `README.md` | Architecture, prompting strategy, guardrails docs |

# Context Graph System — Build Execution

## Phase 1: Project Scaffolding & Data Ingestion
- [x] Create backend project structure (FastAPI + SQLite + NetworkX)
- [x] Write data ingestion script (JSONL → SQLite) — 18,756 records, 0 errors
- [x] Build graph construction module (NetworkX DiGraph)
- [x] Create API endpoints for graph data (6 endpoints)
- [x] Test backend runs and data loads correctly

## Phase 2: Frontend Scaffolding & Graph Visualization
- [x] Initialize Vite + React frontend
- [x] Build GraphCanvas component with react-force-graph-2d
- [x] Build NodeTooltip component
- [x] Connect frontend to backend API

## Phase 3: LLM Integration (NL → SQL → Answer)
- [x] Build LLM client (Gemini)
- [x] Craft system prompt with full schema + few-shot examples
- [x] Build SQL generator + executor
- [x] Implement guardrails (pre-filter + post-filter)
- [x] Create chat API endpoint

## Phase 4: Chat Interface UI
- [x] Build ChatPanel, ChatMessage, QueryInput components
- [x] Integrate chat with graph (node highlighting)
- [x] Add conversation memory

## Phase 5: Integration, Polish & Testing
- [ ] Test all required example queries (needs Gemini API key)
- [x] Test guardrails with off-topic queries (pre-filter logic built)
- [x] Add navbar, styling polish
- [x] Write README with architecture docs

## Phase 6: Bug Fixes & Refinements
- [x] Fix Graph Node Interaction: 
  - [x] Restore missing `NodeTooltip` in `App.jsx`
  - [x] Scale world sizes 4x to bypass `react-force-graph` sub-pixel color picking limit
  - [x] Expand quadtree hit bounds (`nodeRelSize=10`) to prevent culling
- [x] Verify node click works at default zoom and heavily zoomed in
- [x] Verify node click works zoomed out and panned
- [x] Verify tooltip metadata renders properly without blocking interaction

## Phase 7: Visual Balance & Clutter Reduction
- [x] Decouple visible node size from clickable area (`visualRadius` vs `interactionRadius`)
- [x] Keep visible nodes elegant and small (primary 4-7, secondary ~3)
- [x] Enforce dynamic screen-space hit buffers (8px) for effortless clicking
- [x] Filter text labels heavily (only show on hover, selection, or `globalScale > 1.4`)
- [x] Verify graph usability while looking like a clean enterprise architecture map

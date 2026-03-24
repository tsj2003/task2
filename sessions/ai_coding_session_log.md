# AI Coding Session Log — O2C Context Graph System
**Tool Used:** Google Gemini (Antigravity Agent) via VS Code Extension
**Date:** March 24, 2025
**Session Duration:** ~12 hours (06:00 AM – 6:30 PM IST)
**Developer:** Tarandeep Singh Juneja

---

## Session Overview
Built a full-stack SAP Order-to-Cash Context Graph system with LLM-powered NL→SQL query interface, interactive graph visualization, and enterprise guardrails. Iterated through dataset analysis, architecture design, backend implementation, frontend UI redesign, critical bug fixes, and cloud deployment.

---

## Phase 1: Dataset Analysis & Architecture Planning

### Prompt 1: Initial dataset exploration
**User:** Analyze the provided JSONL dataset files and determine entity types, relationships, and data volume.

**AI Actions:**
- Scanned 13 JSONL files in `data/raw/` directory
- Identified entity types: BusinessPartners, SalesOrderHeaders, SalesOrderItems, OutboundDeliveryHeaders, BillingDocuments, JournalEntries, Payments, Plants, ProductDescriptions, CustomerCompanyAssignments, CustomerSalesAreaAssignments, ProductPlants, ProductStorageLocations
- Counted 18,756 total records across all files
- Mapped FK relationships: `soldToParty` links Orders↔Customers↔Billing, `referenceDocument` links Billing↔Journal, `clearingAccountingDocument` links Journal↔Payments
- Identified key limitation: No VBFA (document flow) table — Order→Delivery→Billing must be traced through customer matching

**Files Created:**
- `dataset_analysis.md` — Full entity breakdown with record counts and relationship mapping

---

### Prompt 2: Design the system architecture
**User:** Design the full architecture. Use FastAPI backend, React frontend, SQLite for storage, NetworkX for graph.

**AI Actions:**
- Designed modular backend: `app/main.py`, `app/database.py`, `app/graph/builder.py`, `app/llm/` module
- Designed frontend: React + Vite with `react-force-graph-2d` for visualization
- Chose SQLite over Neo4j for zero-infra portability + LLM SQL compatibility
- Chose NetworkX for in-memory graph traversal serving the visualization API

**Decision Rationale (Database):**
SQLite enables the LLM to generate standard SQL queries directly executable against the data store. A graph DB like Neo4j would require Cypher query generation, adding complexity and hallucination risk. NetworkX handles the graph traversal needs (neighbor expansion, search) without external infrastructure.

---

## Phase 2: Backend Implementation

### Prompt 3: Create the database schema
**AI Actions:**
- Created `app/database.py` with 13 normalized tables
- Added composite primary keys for junction tables (e.g., `journal_entries` uses `companyCode + fiscalYear + accountingDocument + accountingDocumentItem`)
- Created 13 indexes for fast JOIN performance
- Implemented `execute_readonly_sql()` with SQL injection protection
- Implemented `get_schema_description()` that generates a human-readable schema for LLM context injection

**Key SQL Safety Code:**
```python
def execute_readonly_sql(sql: str) -> list[dict]:
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        raise ValueError("Only SELECT/WITH queries are allowed")
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "REPLACE", "TRUNCATE"]
    for word in forbidden:
        if word in sql_upper.split():
            raise ValueError(f"Forbidden SQL keyword: {word}")
```

### Prompt 4: Build the data ingestion pipeline
**AI Actions:**
- Created `scripts/ingest.py` to parse nested JSONL structures
- Implemented recursive flattening for nested JSON objects (e.g., `to_SalesOrderItem` arrays inside order headers)
- Added upsert logic via `INSERT OR REPLACE` for idempotent re-runs
- Successfully ingested 18,756 records across 13 tables

**Command:** `python scripts/ingest.py data/raw`

### Prompt 5: Build the graph construction engine
**AI Actions:**
- Created `app/graph/builder.py` using NetworkX DiGraph
- Extracts 9 entity types from SQLite as graph nodes
- Creates edges based on FK relationships with labeled edge types: `SOLD_TO`, `HAS_ITEM`, `CONTAINS_MATERIAL`, `PRODUCED_AT`, `BILLED_TO`, `GENERATES_JOURNAL`, `POSTED_FOR`, `CLEARED_BY`, `PAID_BY`
- Final graph: 797 nodes, 1005 edges
- Exposed via REST API: `/api/graph/overview`, `/api/graph/full`, `/api/graph/node/{id}`, `/api/graph/expand/{type}`

### Prompt 6: Build the LLM query pipeline
**AI Actions:**
- Created `app/llm/client.py` — Gemini API client with exponential backoff retry (3 attempts)
- Created `app/llm/prompts.py` — System prompt with:
  - Dynamically injected database schema
  - 10 documented relationship paths
  - 7 few-shot examples (aggregation, flow tracing, anomaly detection, guardrail rejections)
  - Structured JSON output format enforcement
- Created `app/llm/sql_generator.py` — Full NL→SQL→Answer pipeline:
  1. Pre-filter (guardrails check)
  2. LLM call (Gemini 2.5 Flash)
  3. Parse JSON response
  4. Post-filter (SQL validation)
  5. Execute SQL against SQLite
  6. Format natural language answer with data
- Created `app/llm/guardrails.py` — Dual-layer safety:
  - Pre-filter: 7 off-topic regex patterns, 4 SQL injection patterns, 28 dataset keywords
  - Post-filter: Forbidden keyword set, table name validation, response structure validation

### Prompt 7: Build the API routers
**AI Actions:**
- Created `app/routers/graph.py` — REST endpoints for graph data
- Created `app/routers/chat.py` — Chat endpoint with conversation memory (stores last 10 messages per session)
- Created `app/main.py` — FastAPI app with CORS, lifespan events (DB init + graph build on startup)

---

## Phase 3: Frontend Implementation

### Prompt 8: Scaffold the React frontend
**AI Actions:**
- Set up Vite + React project
- Created `src/services/api.js` with 7 API functions (fetchGraphFull, sendChatMessage, etc.)
- Created `src/components/GraphCanvas.jsx` — Force-directed graph using `react-force-graph-2d`
- Created `src/components/ChatPanel.jsx` — Chat interface with markdown rendering
- Created `src/components/NodeTooltip.jsx` — Click-to-inspect metadata popup

### Prompt 9: Redesign UI to match enterprise reference screenshots
**User:** Rebuild the frontend UI to match provided reference screenshots — light theme, enterprise dashboard, 75/25 split layout.

**AI Actions:**
- Rewrote `App.css` with complete light theme (`#f7f7f5` background)
- Implemented 75/25 layout split (graph canvas / chat panel)
- Added slim top navbar with breadcrumb navigation
- Added floating dark toolbar with 7 icon buttons (Ask AI, Chat, Monitor, Crop, Zoom, Download, More)
- Styled chat panel with avatar system, markdown rendering, SQL query expander
- Added typing indicator animation

---

## Phase 4: Critical Bug Fixes

### Prompt 10: Fix graph node click interaction bug
**User:** Nodes render but cannot be clicked. Visible node is much larger than clickable area.

**AI Actions (Iteration 1):**
- Diagnosed root cause: `nodeCanvasObject` custom rendering without matching `nodePointerAreaPaint`
- Added `nodePointerAreaPaint` callback — INSUFFICIENT FIX

**AI Actions (Iteration 2):**
- Diagnosed deeper root cause: World-coordinate node radii were too small (2-5px), causing sub-pixel aliasing on the hidden hit-detection canvas
- Also found `NodeTooltip` was unmounted and `onNodeClick` handler was missing from App.jsx
- Fixed by:
  1. Restoring NodeTooltip component mounting with state management
  2. Adding `onNodeClick` handler prop
  3. Scaling up `ENTITY_SIZES` by 4x to prevent quadtree culling
  4. Setting `nodeRelSize={10}` to expand the internal bounding boxes

**AI Actions (Iteration 3 — Final):**
- Decoupled visual rendering from hit detection completely
- Visual node radii: 3-7px (small, clean)
- Invisible hit buffer: `size + (8 / globalScale)` — guarantees 8 screen-space pixels of clickable area at ALL zoom levels
- Set `nodeRelSize={20}` to prevent quadtree from culling any node before the pointer test fires
- Added dynamic label decluttering: labels only appear on hover, selection, or when `globalScale > 1.4`

**Verification:** Tested at zoom levels 0.1x through 10x — nodes clickable at every level

### Prompt 11: Wire toolbar buttons
**User:** Toolbar buttons in the header are not functional.

**AI Actions:**
- Added `forwardRef` and `useImperativeHandle` to GraphCanvas component
- Exposed `fitToScreen()` and `zoomIn()` methods
- Wired all 7 toolbar buttons:
  - Ask AI / Chat → Focus chat input
  - Monitor → Toggle fullscreen mode
  - Crop → Auto-fit graph to viewport
  - Zoom → Step-zoom 1.5x
  - Download / More → Feature placeholder alerts

---

## Phase 5: LLM Model Fix

### Prompt 12: Fix Gemini API 429 quota error
**User:** Chat returns "I'm having trouble connecting to the AI service"

**AI Actions:**
- Diagnosed via direct Python test: API key valid but `gemini-2.0-flash` model has hard `limit: 0` quota for user's free tier
- Listed available models via `genai.list_models()`
- Found `gemini-2.5-flash` fully authorized
- Updated `app/llm/client.py`: Changed model from `gemini-2.0-flash` to `gemini-2.5-flash`
- Verified end-to-end: NL question → SQL generation → SQLite execution → formatted answer

**Verified Query Result:**
```
Q: "Which products are associated with the highest number of billing documents?"
A: LIPBALM 4G LIGHTNING VIT E (79), FACEWASH 100ML DETAN-PACK 2 (78), Machismo Hair cream wax 100GM (78)...
SQL: SELECT pd.product, pd.productDescription, COUNT(DISTINCT bd.billingDocument) AS billing_document_count FROM sales_order_items AS soi JOIN sales_order_headers AS soh ON soi.salesOrder = soh.salesOrder JOIN billing_documents AS bd ON soh.soldToParty = bd.soldToParty JOIN product_descriptions AS pd ON soi.material = pd.product AND pd.language = 'EN' GROUP BY pd.product, pd.productDescription ORDER BY billing_document_count DESC LIMIT 10;
```

---

## Phase 6: Final Audit & Submission

### Prompt 13: Comprehensive submission audit
**AI Actions:**
- Verified all 5 functional requirements against the rubric
- Checked for misleading hardcoding: NONE found
- Verified guardrails reject off-topic prompts and SQL injection
- Verified graph relationships are data-driven from SQLite FKs
- Verified LLM answers are grounded in actual SQL query results
- Created `submission_audit.md` with full pass/fail checklist

### Prompt 14: Clean, package, and push to GitHub
**AI Actions:**
- Created `/sessions` directory with development artifacts
- Initialized git repository
- Force-included `backend/data/o2c.db` (bypassing .gitignore) for cloud deployment
- Pushed to `https://github.com/tsj2003/task2.git`
- Added cloud deployment instructions to README.md

### Prompt 15: Deploy to cloud
**AI Actions:**
- Backend deployed to Render.com (Python 3.11.9 — fixed Python 3.14 pydantic-core compilation failure)
- Frontend deployed to Vercel (Vite auto-detected)
- Fixed CORS by advising `ALLOWED_ORIGINS=*` environment variable on Render
- Live backend URL: `https://task2-df8h.onrender.com`

---

## Technical Decisions Log

| Decision | Choice | Rationale |
|---|---|---|
| Database | SQLite | Zero-infra, portable, enables LLM-generated SQL directly |
| Graph Engine | NetworkX | In-memory, fast traversal, no external DB needed |
| LLM | Gemini 2.5 Flash | Free tier, fast, good SQL generation capability |
| Visualization | react-force-graph-2d | Canvas-based, handles 800+ nodes smoothly |
| Query Safety | Dual-layer guardrails | Pre-filter (regex) + Post-filter (SQL validation) |
| Hit Detection | Decoupled rendering | Visual radius ≠ click radius, screen-space buffer |

---

## Files Modified/Created (Complete List)

### Backend (Python)
- `backend/app/__init__.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/graph/__init__.py`
- `backend/app/graph/builder.py`
- `backend/app/llm/__init__.py`
- `backend/app/llm/client.py`
- `backend/app/llm/guardrails.py`
- `backend/app/llm/prompts.py`
- `backend/app/llm/sql_generator.py`
- `backend/app/routers/__init__.py`
- `backend/app/routers/chat.py`
- `backend/app/routers/graph.py`
- `backend/scripts/ingest.py`
- `backend/requirements.txt`
- `backend/.env.example`

### Frontend (React/JavaScript)
- `frontend/src/App.jsx`
- `frontend/src/App.css`
- `frontend/src/main.jsx`
- `frontend/src/components/GraphCanvas.jsx`
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/components/NodeTooltip.jsx`
- `frontend/src/services/api.js`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/vite.config.js`

### Root
- `README.md`
- `.gitignore`
- `sessions/` (this log + audit artifacts)

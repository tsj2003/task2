"""Graph data API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from app.graph.builder import (
    get_graph_overview,
    get_nodes_by_type,
    get_node_detail,
    get_node_neighbors,
    search_nodes,
    get_graph,
)

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/overview")
def graph_overview():
    """Return supernode summary of the graph."""
    return get_graph_overview()


@router.get("/expand/{entity_type}")
def expand_entity_type(
    entity_type: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Return individual nodes of a given entity type."""
    nodes = get_nodes_by_type(entity_type, limit=limit, offset=offset)
    if not nodes:
        raise HTTPException(status_code=404, detail=f"No nodes found for type: {entity_type}")
    return {"nodes": nodes, "entity_type": entity_type, "count": len(nodes)}


@router.get("/node/{node_id:path}")
def node_detail(node_id: str):
    """Return full details for a single node."""
    detail = get_node_detail(node_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return detail


@router.get("/node/{node_id:path}/neighbors")
def node_neighbors(node_id: str, depth: int = Query(default=1, ge=1, le=3)):
    """Return the neighborhood of a node."""
    result = get_node_neighbors(node_id, depth=depth)
    if not result["nodes"]:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return result


@router.get("/search")
def graph_search(q: str = Query(..., min_length=1)):
    """Search nodes by ID or attribute values."""
    results = search_nodes(q)
    return {"results": results, "query": q, "count": len(results)}


@router.get("/full")
def full_graph():
    """Return the full graph data (nodes + edges) for visualization."""
    G = get_graph()
    nodes = []
    for node, data in G.nodes(data=True):
        node_data = dict(data)
        node_data["id"] = node
        node_data["connections"] = G.degree(node)
        nodes.append(node_data)

    edges = []
    for u, v, edata in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "relationship": edata.get("relationship", "RELATED"),
        })

    return {"nodes": nodes, "edges": edges}

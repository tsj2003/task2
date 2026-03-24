"""Build a NetworkX DiGraph from the SQLite O2C data."""
import logging
import networkx as nx
from app.database import get_connection

logger = logging.getLogger(__name__)

_graph: nx.DiGraph | None = None


def build_graph() -> nx.DiGraph:
    """Construct the full O2C graph from database tables."""
    global _graph
    conn = get_connection()
    G = nx.DiGraph()

    # 1. Business Partners (Customers)
    for row in conn.execute("SELECT * FROM business_partners").fetchall():
        G.add_node(
            f"Customer:{row['businessPartner']}",
            entity_type="Customer",
            id=row["businessPartner"],
            name=row["businessPartnerFullName"] or row["businessPartnerName"] or "",
            blocked=bool(row["businessPartnerIsBlocked"]),
            category=row["businessPartnerCategory"] or "",
        )

    # 2. Sales Order Headers
    for row in conn.execute("SELECT * FROM sales_order_headers").fetchall():
        node_id = f"SalesOrder:{row['salesOrder']}"
        G.add_node(
            node_id,
            entity_type="SalesOrder",
            id=row["salesOrder"],
            totalNetAmount=row["totalNetAmount"],
            currency=row["transactionCurrency"] or "INR",
            deliveryStatus=row["overallDeliveryStatus"] or "",
            creationDate=row["creationDate"] or "",
            soldToParty=row["soldToParty"] or "",
        )
        # Edge: SalesOrder → Customer
        if row["soldToParty"]:
            cust_node = f"Customer:{row['soldToParty']}"
            if cust_node in G:
                G.add_edge(node_id, cust_node, relationship="SOLD_TO")

    # 3. Sales Order Items
    for row in conn.execute("SELECT * FROM sales_order_items").fetchall():
        item_id = f"SalesOrderItem:{row['salesOrder']}-{row['salesOrderItem']}"
        G.add_node(
            item_id,
            entity_type="SalesOrderItem",
            id=f"{row['salesOrder']}-{row['salesOrderItem']}",
            salesOrder=row["salesOrder"],
            material=row["material"] or "",
            quantity=row["requestedQuantity"],
            netAmount=row["netAmount"],
            plant=row["productionPlant"] or "",
        )
        # Edge: SalesOrder → SalesOrderItem
        order_node = f"SalesOrder:{row['salesOrder']}"
        if order_node in G:
            G.add_edge(order_node, item_id, relationship="HAS_ITEM")

        # Edge: SalesOrderItem → Product
        if row["material"]:
            prod_node = f"Product:{row['material']}"
            if prod_node not in G:
                # Try to get product description
                desc_row = conn.execute(
                    "SELECT productDescription FROM product_descriptions WHERE product = ? AND language = 'EN'",
                    (row["material"],),
                ).fetchone()
                G.add_node(
                    prod_node,
                    entity_type="Product",
                    id=row["material"],
                    description=desc_row["productDescription"] if desc_row else "",
                )
            G.add_edge(item_id, prod_node, relationship="CONTAINS_MATERIAL")

        # Edge: SalesOrderItem → Plant
        if row["productionPlant"]:
            plant_node = f"Plant:{row['productionPlant']}"
            if plant_node in G:
                G.add_edge(item_id, plant_node, relationship="PRODUCED_AT")

    # 4. Outbound Delivery Headers
    for row in conn.execute("SELECT * FROM outbound_delivery_headers").fetchall():
        node_id = f"Delivery:{row['deliveryDocument']}"
        G.add_node(
            node_id,
            entity_type="Delivery",
            id=row["deliveryDocument"],
            goodsMovementStatus=row["overallGoodsMovementStatus"] or "",
            pickingStatus=row["overallPickingStatus"] or "",
            shippingPoint=row["shippingPoint"] or "",
            creationDate=row["creationDate"] or "",
        )
        # Edge: Delivery → Plant (via shippingPoint)
        if row["shippingPoint"]:
            plant_node = f"Plant:{row['shippingPoint']}"
            if plant_node in G:
                G.add_edge(node_id, plant_node, relationship="SHIPS_FROM")

    # 5. Billing Documents
    for row in conn.execute("SELECT * FROM billing_documents").fetchall():
        node_id = f"BillingDocument:{row['billingDocument']}"
        G.add_node(
            node_id,
            entity_type="BillingDocument",
            id=row["billingDocument"],
            totalNetAmount=row["totalNetAmount"],
            currency=row["transactionCurrency"] or "INR",
            isCancelled=bool(row["billingDocumentIsCancelled"]),
            billingDate=row["billingDocumentDate"] or "",
            accountingDocument=row["accountingDocument"] or "",
            soldToParty=row["soldToParty"] or "",
        )
        # Edge: BillingDocument → Customer
        if row["soldToParty"]:
            cust_node = f"Customer:{row['soldToParty']}"
            if cust_node in G:
                G.add_edge(node_id, cust_node, relationship="BILLED_TO")

    # 6. Journal Entries
    for row in conn.execute("SELECT * FROM journal_entries").fetchall():
        je_key = f"{row['accountingDocument']}-{row['accountingDocumentItem']}"
        node_id = f"JournalEntry:{je_key}"
        G.add_node(
            node_id,
            entity_type="JournalEntry",
            id=je_key,
            accountingDocument=row["accountingDocument"],
            glAccount=row["glAccount"] or "",
            amount=row["amountInTransactionCurrency"],
            currency=row["transactionCurrency"] or "INR",
            postingDate=row["postingDate"] or "",
            referenceDocument=row["referenceDocument"] or "",
            customer=row["customer"] or "",
            clearingDocument=row["clearingAccountingDocument"] or "",
        )
        # Edge: JournalEntry → BillingDocument (via referenceDocument)
        if row["referenceDocument"]:
            bill_node = f"BillingDocument:{row['referenceDocument']}"
            if bill_node in G:
                G.add_edge(node_id, bill_node, relationship="REFERENCES_BILLING")
                G.add_edge(bill_node, node_id, relationship="GENERATES_JOURNAL")

        # Edge: JournalEntry → Customer
        if row["customer"]:
            cust_node = f"Customer:{row['customer']}"
            if cust_node in G:
                G.add_edge(node_id, cust_node, relationship="POSTED_FOR")

    # 7. Payments
    for row in conn.execute("SELECT * FROM payments").fetchall():
        pay_key = f"{row['accountingDocument']}-{row['accountingDocumentItem']}"
        node_id = f"Payment:{pay_key}"
        G.add_node(
            node_id,
            entity_type="Payment",
            id=pay_key,
            accountingDocument=row["accountingDocument"],
            amount=row["amountInTransactionCurrency"],
            currency=row["transactionCurrency"] or "INR",
            postingDate=row["postingDate"] or "",
            customer=row["customer"] or "",
            clearingDocument=row["clearingAccountingDocument"] or "",
        )
        # Edge: Payment → Customer
        if row["customer"]:
            cust_node = f"Customer:{row['customer']}"
            if cust_node in G:
                G.add_edge(node_id, cust_node, relationship="PAID_BY")

        # Edge: Payment ↔ JournalEntry (via clearingAccountingDocument)
        if row["clearingAccountingDocument"]:
            # Find journal entries with matching clearing document
            for je_node in list(G.nodes):
                if je_node.startswith("JournalEntry:") and G.nodes[je_node].get("clearingDocument") == row["clearingAccountingDocument"]:
                    G.add_edge(je_node, node_id, relationship="CLEARED_BY")
                    break

    # 8. Plants
    for row in conn.execute("SELECT * FROM plants").fetchall():
        node_id = f"Plant:{row['plant']}"
        G.add_node(
            node_id,
            entity_type="Plant",
            id=row["plant"],
            name=row["plantName"] or "",
            salesOrganization=row["salesOrganization"] or "",
        )

    _graph = G
    logger.info("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def get_graph() -> nx.DiGraph:
    """Return the cached graph, building if necessary."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def get_graph_overview() -> dict:
    """Return a high-level summary: supernodes by entity type with edge counts."""
    G = get_graph()
    entity_types = {}
    for node, data in G.nodes(data=True):
        etype = data.get("entity_type", "Unknown")
        if etype not in entity_types:
            entity_types[etype] = {"count": 0, "nodes": []}
        entity_types[etype]["count"] += 1

    # Count edges between entity types
    edge_summary = {}
    for u, v, edata in G.edges(data=True):
        u_type = G.nodes[u].get("entity_type", "Unknown")
        v_type = G.nodes[v].get("entity_type", "Unknown")
        rel = edata.get("relationship", "RELATED")
        key = (u_type, v_type, rel)
        edge_summary[key] = edge_summary.get(key, 0) + 1

    supernodes = []
    for etype, info in entity_types.items():
        supernodes.append({
            "id": f"supernode:{etype}",
            "entity_type": etype,
            "count": info["count"],
            "label": f"{etype} ({info['count']})",
        })

    superedges = []
    for (src_type, tgt_type, rel), count in edge_summary.items():
        superedges.append({
            "source": f"supernode:{src_type}",
            "target": f"supernode:{tgt_type}",
            "relationship": rel,
            "count": count,
            "label": f"{rel} ({count})",
        })

    return {"nodes": supernodes, "edges": superedges}


def get_nodes_by_type(entity_type: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return individual nodes of a given entity type."""
    G = get_graph()
    nodes = []
    for node, data in G.nodes(data=True):
        if data.get("entity_type") == entity_type:
            nodes.append({"id": node, **data})
    return nodes[offset: offset + limit]


def get_node_detail(node_id: str) -> dict | None:
    """Return full details for a single node."""
    G = get_graph()
    if node_id not in G:
        return None
    data = dict(G.nodes[node_id])
    data["id"] = node_id
    data["connections"] = G.degree(node_id)
    return data


def get_node_neighbors(node_id: str, depth: int = 1) -> dict:
    """Return the neighborhood of a node up to given depth."""
    G = get_graph()
    if node_id not in G:
        return {"nodes": [], "edges": []}

    visited = {node_id}
    frontier = {node_id}
    all_nodes = []
    all_edges = []

    for _ in range(depth):
        next_frontier = set()
        for n in frontier:
            for neighbor in list(G.predecessors(n)) + list(G.successors(n)):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier

    for n in visited:
        node_data = dict(G.nodes[n])
        node_data["id"] = n
        node_data["connections"] = G.degree(n)
        all_nodes.append(node_data)

    for u, v, edata in G.edges(data=True):
        if u in visited and v in visited:
            all_edges.append({
                "source": u,
                "target": v,
                "relationship": edata.get("relationship", "RELATED"),
            })

    return {"nodes": all_nodes, "edges": all_edges}


def search_nodes(query: str, limit: int = 20) -> list[dict]:
    """Search nodes by ID or attribute values."""
    G = get_graph()
    query_lower = query.lower()
    results = []

    for node, data in G.nodes(data=True):
        score = 0
        if query_lower in node.lower():
            score = 10
        else:
            for val in data.values():
                if isinstance(val, str) and query_lower in val.lower():
                    score = 5
                    break
        if score > 0:
            results.append({"id": node, "score": score, **data})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

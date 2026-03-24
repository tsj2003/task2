"""Guardrails: pre-filter and post-filter for query safety."""
import re
import logging

logger = logging.getLogger(__name__)

# Keywords that suggest off-topic queries
OFF_TOPIC_PATTERNS = [
    r"\b(write|compose|create)\s+(a|me|an?)?\s*(poem|story|essay|song|joke|haiku)\b",
    r"\b(tell|say)\s+(me)?\s*(a|an?)?\s*(joke|story|riddle)\b",
    r"\bwhat\s+is\s+the\s+(meaning|capital|population|president|weather)\b",
    r"\b(who|what)\s+is\s+(the\s+)?(president|prime\s+minister|ceo)\b",
    r"\b(translate|convert)\s+.*\s+(to|into)\s+(french|spanish|hindi|german)\b",
    r"\bhow\s+to\s+(cook|make|build|fix)\b",
    r"\b(play|sing|dance|draw)\b",
    r"\b(hello|hi|hey)\s+(how\s+are\s+you|there)\b",
]

# Dataset-related keywords that suggest a valid query
DATASET_KEYWORDS = [
    "order", "sales", "delivery", "billing", "invoice", "payment", "journal",
    "customer", "product", "material", "plant", "amount", "document", "entry",
    "flow", "trace", "cancelled", "status", "total", "net", "currency",
    "shipped", "billed", "delivered", "receivable", "accounting", "gl",
    "profit", "cost", "company", "fiscal", "posting", "clearing",
    "broken", "incomplete", "anomaly", "highest", "lowest", "count", "average",
    "sum", "group", "list", "show", "find", "get", "which", "how many",
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)",
    r"(--|#|/\*)",
    r"UNION\s+SELECT",
    r"OR\s+1\s*=\s*1",
    r"'\s*OR\s*'",
]

# Forbidden SQL keywords for post-filter
FORBIDDEN_SQL = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "EXEC", "EXECUTE"}


def is_relevant_query(query: str) -> tuple[bool, str]:
    """
    Pre-filter: Check if a query is relevant to the O2C dataset.
    Returns (is_relevant, rejection_reason).
    """
    query_lower = query.lower().strip()

    if not query_lower or len(query_lower) < 2:
        return False, "Please enter a question about the Order-to-Cash dataset."

    if len(query_lower) > 5000:
        return False, "Your query is too long. Please keep it under 5000 characters."

    # Check for off-topic patterns
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, query_lower):
            return False, "This system is designed to answer questions related to the SAP Order-to-Cash dataset only. I can help you explore sales orders, deliveries, billing documents, payments, and more."

    # Check for SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Your query contains potentially unsafe patterns. Please rephrase your question in natural language."

    # Check if query has any dataset-related keywords
    has_dataset_keyword = any(kw in query_lower for kw in DATASET_KEYWORDS)

    # If query is very short and has no keywords, it might be gibberish
    if len(query_lower) < 10 and not has_dataset_keyword:
        # Allow it through to LLM - it has its own guardrails
        return True, ""

    return True, ""


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Post-filter: Validate generated SQL is safe to execute.
    Returns (is_safe, error_message).
    """
    if not sql:
        return True, ""

    sql_upper = sql.upper().strip()

    # Must start with SELECT or WITH
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return False, "Generated query is not a SELECT statement."

    # Check for forbidden keywords
    words = set(re.findall(r'\b[A-Z]+\b', sql_upper))
    forbidden_found = words & FORBIDDEN_SQL
    if forbidden_found:
        return False, f"Generated query contains forbidden operations: {', '.join(forbidden_found)}"

    # Valid table names in our schema
    valid_tables = {
        "business_partners", "customer_company_assignments",
        "customer_sales_area_assignments", "sales_order_headers",
        "sales_order_items", "outbound_delivery_headers",
        "billing_documents", "journal_entries", "payments",
        "plants", "product_descriptions", "product_plants",
        "product_storage_locations",
    }

    # Extract table names from FROM/JOIN clauses (basic check)
    from_pattern = re.findall(r'(?:FROM|JOIN)\s+(\w+)', sql, re.IGNORECASE)
    for table in from_pattern:
        if table.lower() not in valid_tables:
            logger.warning("SQL references unknown table: %s", table)
            # Don't block - could be a subquery alias

    return True, ""


def validate_response(response: dict) -> dict:
    """Post-filter: Validate and sanitize the LLM response."""
    if not isinstance(response, dict):
        return {
            "reasoning": "Invalid response format",
            "sql_query": None,
            "answer": "I encountered an error processing your question. Please try rephrasing.",
            "referenced_entities": [],
            "confidence": 0.0,
        }

    # Ensure required fields
    response.setdefault("reasoning", "")
    response.setdefault("sql_query", None)
    response.setdefault("answer", "I couldn't generate a response. Please try again.")
    response.setdefault("referenced_entities", [])
    response.setdefault("confidence", 0.5)

    # Validate SQL if present
    if response["sql_query"]:
        is_safe, error = validate_sql(response["sql_query"])
        if not is_safe:
            response["sql_query"] = None
            response["answer"] = f"I generated an unsafe query and blocked it for safety. Error: {error}"
            response["confidence"] = 0.0

    # Add caveat for low confidence
    if response["confidence"] < 0.3 and response["sql_query"]:
        response["answer"] += "\n\n⚠️ Note: I'm not very confident in this answer. The results may be incomplete or inaccurate."

    return response

"""NL → SQL → Answer pipeline: processes user queries end-to-end."""
import logging
from app.llm.client import generate, parse_json_response
from app.llm.prompts import get_system_prompt
from app.llm.guardrails import is_relevant_query, validate_response
from app.database import execute_readonly_sql

logger = logging.getLogger(__name__)


def process_query(user_question: str, conversation_history: list[dict] | None = None) -> dict:
    """
    Full pipeline: user question → pre-filter → LLM → SQL execution → answer.
    
    Returns dict with: answer, sql_query, query_results, referenced_entities, confidence
    """
    # 1. Pre-filter
    is_relevant, rejection = is_relevant_query(user_question)
    if not is_relevant:
        return {
            "answer": rejection,
            "sql_query": None,
            "query_results": None,
            "referenced_entities": [],
            "confidence": 1.0,
        }

    # 2. Build context with conversation history
    system_prompt = get_system_prompt()
    if conversation_history:
        history_text = "\n\nCONVERSATION HISTORY (last 5 exchanges):\n"
        for msg in conversation_history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"{role.upper()}: {content}\n"
        system_prompt += history_text

    # 3. Call LLM
    try:
        raw_response = generate(system_prompt, user_question)
        response = parse_json_response(raw_response)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return {
            "answer": "I'm having trouble connecting to the AI service. Please try again in a moment.",
            "sql_query": None,
            "query_results": None,
            "referenced_entities": [],
            "confidence": 0.0,
        }

    # 4. Post-filter / validate
    response = validate_response(response)

    # 5. Execute SQL if present
    query_results = None
    if response.get("sql_query"):
        try:
            query_results = execute_readonly_sql(response["sql_query"])
            # Format results into the answer
            if query_results:
                result_text = "\n\n**Results:**\n"
                for i, row in enumerate(query_results[:20], 1):
                    row_text = " | ".join(f"**{k}**: {v}" for k, v in row.items() if v is not None)
                    result_text += f"{i}. {row_text}\n"
                if len(query_results) > 20:
                    result_text += f"\n_...and {len(query_results) - 20} more results_"
                response["answer"] = response.get("answer", "") + result_text
            else:
                response["answer"] += "\n\nNo matching records found in the dataset."
        except Exception as e:
            logger.error("SQL execution failed: %s | Query: %s", e, response["sql_query"])
            response["answer"] = f"I generated a query but it encountered an error: {str(e)}. Let me try to answer differently — please rephrase your question."
            response["confidence"] = max(0, response.get("confidence", 0) - 0.3)

    return {
        "answer": response.get("answer", ""),
        "sql_query": response.get("sql_query"),
        "query_results": query_results,
        "referenced_entities": response.get("referenced_entities", []),
        "confidence": response.get("confidence", 0.5),
    }

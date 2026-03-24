"""Google Gemini LLM client with retry logic."""
import json
import logging
import time
import google.generativeai as genai
from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

_model = None


def get_model():
    """Initialize and return the Gemini model."""
    global _model
    if _model is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Please add it to your .env file.")
        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Gemini model initialized with gemini-2.5-flash")
    return _model


def generate(system_prompt: str, user_message: str, temperature: float = 0.1, max_retries: int = 3) -> str:
    """Generate a response from Gemini with retry logic."""
    model = get_model()
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [
                    {"role": "user", "parts": [{"text": system_prompt + "\n\nUser Query: " + user_message}]},
                ],
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=4096,
                ),
            )
            return response.text
        except Exception as e:
            logger.warning("Gemini API attempt %d failed: %s", attempt + 1, e)
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.info("Retrying in %ds...", wait)
                time.sleep(wait)
            else:
                raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {e}")


def parse_json_response(text: str) -> dict:
    """Extract and parse JSON from LLM response text."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "reasoning": "Failed to parse LLM response",
            "sql_query": None,
            "answer": text,
            "referenced_entities": [],
            "confidence": 0.3,
        }

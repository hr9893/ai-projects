import json
from groq import Groq
from backend.app.config import GROQ_MODEL

_client = None

DRUG_KEYWORDS = {
    "drug", "drugs", "medicine", "medication", "dosage", "dose",
    "prescription", "antibiotic", "tablet", "injection", "side effect",
    "side effects", "contraindication", "contraindications", "pharmacy",
    "pharmacology", "drug interaction", "interactions",
}

def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq()
    return _client


ROUTER_PROMPT = """You are a query router for a hospital assistant system.
Classify the user's question into exactly one category:

- "sql": Questions asking for specific records, counts, totals, statuses, or
  lookups from structured data — e.g. claims, insurance amounts, equipment
  tickets, dates, patient counts, "how many", "list all", "what is the status of".

- "rag": Questions asking about policies, procedures, general knowledge,
  explanations, or "how does X work" — e.g. leave policy, substitution policy,
  equipment maintenance guidelines, clinical protocols.

- "both": Questions that need BOTH — e.g. "how many claims are pending AND
  what's our claims escalation policy".

Respond with ONLY a JSON object, no other text:
{{"route": "sql" | "rag" | "both", "reasoning": "<one short sentence>"}}

User question: {question}
"""


def classify_query(question: str) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": ROUTER_PROMPT.format(question=question)}],
        temperature=0,
        response_format={"type": "json_object"},  # forces valid JSON if your Groq model supports it
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
        route = parsed.get("route", "rag")
        if route not in ("sql", "rag", "both"):
            route = "rag"
        return {"route": route, "reasoning": parsed.get("reasoning", "")}
    except (json.JSONDecodeError, AttributeError):
        ## Fail safe: default to RAG rather than crashing the request
        return {"route": "rag", "reasoning": "fallback — classification failed to parse"}


# --- add to router.py ---

def is_drug_related(question: str) -> bool:
    q = question.lower()
    return any(keyword in q for keyword in DRUG_KEYWORDS)
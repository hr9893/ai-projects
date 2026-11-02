import logging

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient, TypeSafeError

logger = logging.getLogger(__name__)


ROUTE_QUESTION = Choice(
    instructions="Choose the best route for answering the user's question.",
    criteria={
        "sql": (
            "Requires specific database records, counts, totals, statuses, "
            "dates, or structured data lookups."
        ),
        "rag": (
            "Requires information from policies, procedures, clinical guidelines, "
            "documents, or general knowledge."
        ),
        "both": (
            "Requires both structured database data and document-based "
            "information to answer completely."
        ),
    },
)

DRUG_QUESTION = Noul(
    instructions="Is the user's question related to drugs or medications?",
    criteria=NoulCriteria(
        true=(
            "Asks about medicines, dosage, prescriptions, drug interactions, "
            "side effects, contraindications, or pharmacology."
        ),
        false=(
            "Does not ask about drugs, medicines, or medication-related information."
        ),
    ),
)

DRUG_KEYWORDS = {
    "drug", "drugs", "medicine", "medicines", "medication", "medications",
    "dosage", "dose", "prescription", "antibiotic", "tablet", "injection",
    "side effect", "side effects", "contraindication", "contraindications",
    "pharmacy", "pharmacology", "drug interaction", "drug interactions",
    "interactions",
}


def classify_query(question: str) -> dict:
    """Route the query and classify whether it is drug-related."""

    try:
        with TypeSafeClient() as client:
            response = client.system_one(
                state={"question": question},
                questions={
                    "route": ROUTE_QUESTION,
                    "drug_related": DRUG_QUESTION,
                },
            )

        route = response.choices["route"].choice
        drug_score = response.nouls["drug_related"].noul

        return {
            "route": route,
            "reasoning": f"Jev selected '{route}'.",
            "confidence": response.choices["route"].confidence,
            "drug_related": drug_score >= 0.5,
            "drug_related_score": drug_score,
        }

    except TypeSafeError as error:
        logger.warning("Jev routing failed: %s", error)

        question_lower = question.lower()
        drug_related = any(
            keyword in question_lower for keyword in DRUG_KEYWORDS
        )

        return {
            "route": "rag",
            "reasoning": "Jev failed; defaulting to RAG.",
            "confidence": 0.0,
            "drug_related": drug_related,
            "drug_related_score": None,
        }
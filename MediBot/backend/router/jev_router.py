from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient, TypeSafeError
from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("jev_router")


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
    function_name = "classify_query"
    LOGGER.extMethodEntry(function_name, None, lambda : "Entry")

    LOGGER.extDebugAsJson(function_name, lambda : "Classifier  incoming question ->", question)

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

        response = {
            "route": route,
            "reasoning": f"Jev selected '{route}'.",
            "confidence": response.choices["route"].confidence,
            "drug_related": drug_score >= 0.5,
            "drug_related_score": drug_score,
        }

        LOGGER.extDebugAsJson(function_name, lambda: f"Classifier  response for question {question}", f"Response Payload -> {response}")

        return response

    except TypeSafeError as error:
        LOGGER.extError(function_name, lambda: "Exception occurred", error, str(error))

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
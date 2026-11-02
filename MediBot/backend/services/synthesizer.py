from backend.core.llm_config import generate_completion, SYNTHESIS_MODEL

DOC_SYSTEM_PROMPT = """You are MediAssist, a helpful and highly accurate hospital knowledge assistant.
Answer the user's question using ONLY the provided context excerpts below.

Rules:
1. If the context doesn't contain enough information to answer confidently, say "I do not have access to this information in my current collections" rather than guessing.
2. Be concise, specific, and empathetic.
3. If you use information from the context, mention the [Source] at the end of the sentence.

Context:
{context}

User Question: {question}
"""

def generate_rag_answer(question: str, context: str) -> str:
    """
    Generates a natural language answer based purely on the retrieved document context.
    """
    if not context.strip():
         return "I couldn't find relevant information for that question in your authorized collections."

    full_prompt = DOC_SYSTEM_PROMPT.format(context=context, question=question)

    return generate_completion(
        prompt=full_prompt,
        model=SYNTHESIS_MODEL,
        temperature=0.2
    )

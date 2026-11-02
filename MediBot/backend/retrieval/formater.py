from langchain_core.documents import Document

def format_doc_answer(docs: list[Document]) -> str:
    """Formats the LangChain documents into a single string for the LLM prompt."""
    if not docs:
        return ""

    # Combine the chunks, including the file name in the output so the LLM can cite it
    context = "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )
    return context

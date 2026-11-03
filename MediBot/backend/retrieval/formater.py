from langchain_core.documents import Document
from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("formatter_service")

def format_doc_answer(docs: list[Document]) -> str:
    """Formats the LangChain documents into a single string for the LLM prompt."""
    function_name = "format_doc_answer"
    LOGGER.extMethodEntry(function_name, f"Incoming Documents -> {docs}")

    if not docs:
        return ""

    context = "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )
    LOGGER.extMethodEntry(function_name, f"Outgoing Documents -> {context}")
    return context

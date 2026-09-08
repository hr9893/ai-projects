import os
from groq import Groq
from langchain_groq import ChatGroq

from backend.app.config import GROQ_MODEL


class LLMClient:
    """
    Single point of LLM access for the whole app. Wraps both:
      - the raw Groq client, for simple one-shot completions (doc_rag, router)
      - the LangChain ChatGroq wrapper, for chains that expect a LangChain LLM
        (create_sql_query_chain in sql_rag.py needs this specific interface)

    Use LLMClient.get_instance() everywhere instead of instantiating
    Groq()/ChatGroq() directly — this guarantees the API key check and
    model config happen exactly once, in exactly one place.
    """

    _instance = None

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to a .env file at your "
                "project root, or set it as an environment variable, "
                "before starting the app."
            )
        self._raw_client = Groq(api_key=api_key)
        self._chat_model = ChatGroq(model=GROQ_MODEL, api_key=api_key, temperature=0)

    @classmethod
    def get_instance(cls) -> "LLMClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def complete(self, prompt: str, temperature: float = 0.2) -> str:
        """One-shot text completion — used by doc_rag.py and router.py."""
        response = self._raw_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    @property
    def chat_model(self) -> ChatGroq:
        """LangChain-compatible LLM instance — used by sql_rag.py's create_sql_query_chain."""
        return self._chat_model
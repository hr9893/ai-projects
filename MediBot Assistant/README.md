# MediBot Backend

Advanced RAG backend for MediAssist Health Network with RBAC-enforced
retrieval, Hybrid Search (dense + BM25), cross-encoder reranking, and SQL RAG.

## Setup

1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Anthropic API key + Qdrant URL
4. Start Qdrant locally (or use Qdrant Cloud free tier):
   `docker run -p 6333:6333 qdrant/qdrant`
5. Place source PDFs/Markdown into `data/raw_docs/<collection>/`
6. Run ingestion once: `python scripts/run_ingestion.py`
7. Start the API: `uvicorn app.main:app --reload`

## Demo credentials

| Username        | Password            | Role               |
|-----------------|----------------------|--------------------|
| dr.mehta        | doctor               | doctor             |
| nurse.priya     | nurse                | nurse              |
| billing.ravi    | billing_executive    | billing_executive  |
| tech.anand      | technician           | technician         |
| admin.sys       | admin                | admin              |

## Architecture

login -> RBAC filter (server-verified role) -> query router (analytical vs
document) -> Hybrid RAG (dense+sparse+RBAC filter -> rerank -> LLM) OR
SQL RAG (NL->SQL->execute->NL answer) -> response with sources + retrieval_type

## Adversarial prompt tests

See `tests/test_rbac.py` for the automated checks. For the README
submission, log in as `nurse.priya` and ask for billing/equipment content;
capture screenshots showing the RBAC refusal message.

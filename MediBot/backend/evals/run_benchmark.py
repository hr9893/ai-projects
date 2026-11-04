import json
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.retrieval.document_retriever import retrieve_documents
from backend.db.vector_db import get_vector_store

from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("run_eval_benchmark")


def main():
    function_name = "main"
    LOGGER.extMethodEntry(function_name, lambda : "Entry")

    parser = argparse.ArgumentParser(description="Run retrieval evaluation benchmark against Medi Buddy.")
    parser.add_argument("--eval-set", type=str, required=True, help="Path to retrieval_eval_set.jsonl")
    parser.add_argument("--output", type=str, required=True, help="Path to save results JSONL")
    parser.add_argument("--qdrant-path", type=str, default="./qdrant_db", help="Path to local Qdrant storage")
    parser.add_argument("--role", type=str, default="admin", help="RBAC role to use (default: admin)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of documents to retrieve per query")

    args = parser.parse_args()

    vector_store = get_vector_store()

    eval_set_path = Path(args.eval_set)
    output_path = Path(args.output)

    with open(eval_set_path, "r", encoding="utf-8") as f_in, \
            open(output_path, "w", encoding="utf-8") as f_out:

        for line in f_in:
            if not line.strip():
                continue
            item = json.loads(line)
            query_id = item["query_id"]
            query_text = item["query"]

            docs = retrieve_documents(
                query=query_text,
                role=args.role,
                top_k=args.top_k
            )

            results = []
            for doc in docs:
                file_name = doc.metadata.get("file_name", doc.metadata.get("source", "unknown"))
                page = doc.metadata.get("page", 1)

                res_obj = {"source": file_name}
                try:
                    res_obj["page"] = int(page)
                except (ValueError, TypeError):
                    res_obj["page"] = 1

                results.append(res_obj)

            output_obj = {
                "query_id": query_id,
                "results": results,
                "abstained": False
            }

            f_out.write(json.dumps(output_obj) + "\n")

    LOGGER.extDebugAsJson(function_name, lambda: f"Evaluation results saved to {output_path}")
    LOGGER.extMethodExit(function_name, lambda: "Exit")

if __name__ == "__main__":
    main()
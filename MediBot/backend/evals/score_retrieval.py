"""Score page-normalized ranked retrieval output against the supplied qrels."""
import argparse, json, math
from collections import defaultdict

def parse_doc_id(item):
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        raise ValueError(f"Each result must be a doc_id string or object, got: {item!r}")
    if item.get("doc_id"):
        return str(item["doc_id"])
    source = item.get("source") or item.get("filename")
    page = item.get("page")
    if source is not None and page is not None:
        return f"{source}::p{int(page):02d}"
    raise ValueError(f"Result needs doc_id or source/filename plus page: {item!r}")

def read_qrels(path):
    qrels = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) != 4:
                raise ValueError(f"Expected 4 tab-separated qrels columns: {line!r}")
            qid, _, doc_id, rel = cols
            qrels[qid][doc_id] = int(rel)
    return qrels

def dcg(grades, k):
    return sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(grades[:k]))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True, help="Retriever output JSONL, one object per query")
    ap.add_argument("--qrels", required=True, help="Path to qrels.tsv")
    ap.add_argument("--eval-set", required=True, help="Path to retrieval_eval_set.jsonl")
    ap.add_argument("--known-distractors", required=True, help="Path to known_distractors.tsv")
    ap.add_argument("--k", nargs="+", type=int, default=[1, 3, 5, 10])
    ap.add_argument("--per-query", help="Optional path to write per-query JSONL metrics")
    args = ap.parse_args()

    qrels = read_qrels(args.qrels)
    with open(args.eval_set, encoding="utf-8") as f:
        eval_rows = [json.loads(line) for line in f if line.strip()]
    eval_by_id = {r["query_id"]: r for r in eval_rows}
    distractors = defaultdict(set)
    with open(args.known_distractors, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            qid, _, doc_id, _ = line.rstrip("\n").split("\t")
            distractors[qid].add(doc_id)

    ranked, abstained = {}, {}
    with open(args.results, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            qid = row["query_id"]
            if qid in ranked:
                raise ValueError(f"Duplicate query_id in results: {qid}")
            seen, ids = set(), []
            for item in row.get("results", []):
                did = parse_doc_id(item)
                if did not in seen:
                    ids.append(did)
                    seen.add(did)
            ranked[qid] = ids
            abstained[qid] = bool(row.get("abstained", False))

    ks = sorted(set(args.k))
    per_query = []
    for qid, spec in eval_by_id.items():
        ids = ranked.get(qid, [])
        grades = qrels.get(qid, {})
        out = {"query_id": qid, "answerable": spec["answerable"], "returned": len(ids), "abstained": abstained.get(qid, False)}
        for k in ks:
            top = ids[:k]
            rels = [grades.get(d, 0) for d in top]
            relevant_total = sum(1 for g in grades.values() if g > 0)
            hit_ranks = [i + 1 for i, g in enumerate(rels) if g > 0]
            recall = len(hit_ranks) / relevant_total if relevant_total else None
            mrr = 1 / hit_ranks[0] if hit_ranks else 0.0
            ideal_dcg = dcg(sorted((g for g in grades.values() if g > 0), reverse=True), k)
            ndcg = dcg(rels, k) / ideal_dcg if ideal_dcg else None
            out[f"recall@{k}"] = recall
            out[f"mrr@{k}"] = mrr
            out[f"ndcg@{k}"] = ndcg
            out[f"precision@{k}"] = sum(1 for g in rels if g > 0) / k
            out[f"known_distractor_hit@{k}"] = any(d in distractors[qid] for d in top)
        out["abstention_correct"] = (not spec["answerable"]) and abstained.get(qid, False)
        per_query.append(out)

    summary = {"queries_in_eval_set": len(eval_by_id), "queries_with_results": len(ranked), "k": ks, "metrics": {}}
    groups = [("answerable", [r for r in per_query if r["answerable"]]), ("unanswerable", [r for r in per_query if not r["answerable"]])]
    for group_name, group in groups:
        summary["metrics"][group_name] = {"query_count": len(group)}
        for k in ks:
            for name in ["recall", "mrr", "ndcg", "precision", "known_distractor_hit"]:
                field = f"{name}@{k}"
                vals = [r[field] for r in group if r[field] is not None]
                summary["metrics"][group_name][field] = round(sum(vals) / len(vals), 4) if vals else None
        summary["metrics"][group_name]["abstention_rate"] = round(sum(1 for r in group if r["abstained"]) / len(group), 4) if group else None
    unanswerable = summary["metrics"]["unanswerable"]["query_count"]
    summary["metrics"]["unanswerable"]["correct_abstention_rate"] = (round(sum(1 for r in per_query if not r["answerable"] and r["abstention_correct"]) / unanswerable, 4) if unanswerable else None)
    print(json.dumps(summary, indent=2))
    if args.per_query:
        with open(args.per_query, "w", encoding="utf-8") as f:
            for row in per_query:
                f.write(json.dumps(row) + "\n")

if __name__ == "__main__":
    main()

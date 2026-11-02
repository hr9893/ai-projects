import os
from dotenv import load_dotenv
load_dotenv()

# Add this line explicitly for the debug script:
os.environ["TYPESAFE_API_KEY"] = "apikey_2193744b9749ab68482bb832989ae4ca24ae_736fe372a484f1ed4842cccf0cfe5684b11eeb36835b1c1b8a06e142898e1a0c"

# We import the exact same functions your chat_service uses
from retrieval.document_retriever import retrieve_documents
from db.vector_db import get_vector_store

def debug_chunk_retrieval():
    # 1. Ask a question you KNOW the answer to in your PDFs
    query = "What are the Urine Analysis Interpretation?"
    role = "doctor"
    collection = "clinical"

    print(f"\n========================================================")
    print(f"DEBUGGING QDRANT RETRIEVAL")
    print(f"Query: '{query}'")
    print(f"Role: {role} | UI Collection: {collection}")
    print(f"========================================================\n")

    # 2. Check the raw Qdrant connection first (Bypassing RBAC and Jev)
    print("--- 1. Testing Raw Qdrant Connection (No Filters) ---")
    try:
        store = get_vector_store()
        raw_candidates = store.similarity_search(query=query, k=5)
        print(f"Raw Qdrant returned {len(raw_candidates)} chunks.")
        for i, doc in enumerate(raw_candidates):
            print(f"\nChunk {i+1} Metadata: {doc.metadata}")
            print(f"Chunk {i+1} Text: {doc.page_content[:150]}...")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to connect to or query Qdrant: {e}")
        return

    # If raw_candidates is 0, your Qdrant database is empty or pointing to the wrong folder!
    if not raw_candidates:
        print("\n❌ STOP: Your Qdrant database returned 0 chunks even without filters.")
        print("Check that your QDRANT_PATH points to the correct folder containing your data.")
        return

    # 3. Test with the Full Pipeline (RBAC + UI Filter + Jev)
    print("\n\n--- 2. Testing Full Pipeline (RBAC + Jev Reranking) ---")
    try:
        final_docs = retrieve_documents(
            query=query,
            role=role,
            active_collection=collection,
            top_k=5,
            candidate_k=20
        )
        print(f"\nPipeline finished. Jev allowed {len(final_docs)} chunks through.")

        for i, doc in enumerate(final_docs):
            score = doc.metadata.get('jev_relevance_score', 'N/A')
            print(f"\n[Jev Score: {score}] Chunk {i+1}: {doc.page_content[:150]}...")

    except Exception as e:
        print(f"ERROR in full pipeline: {e}")

if __name__ == "__main__":
    debug_chunk_retrieval()
import hashlib
from pathlib import Path
import uuid
import os

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker import HierarchicalChunker
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import (
    FastEmbedSparse,
    QdrantVectorStore,
    RetrievalMode,
)
from backend.config.configs import (QDRANT_COLLECTION, EMBED_MODEL, SPARSE_MODEL,MEDIASSIST_DB_PATH)
from backend.core.rbac import access_roles_for_collection

def format_chunk_text(chunk) -> str:
    """Add heading breadcrumbs before the chunk content."""
    headings = getattr(chunk.meta, "headings", [])
    content = chunk.text.strip()
    breadcrumbs = " > ".join(headings) if headings else ""
    return f"{breadcrumbs}\n\n{content}" if breadcrumbs else content

def extract_page_number(chunk) -> int:
    """Safely dig into Docling's provenance tree to find the original PDF page number."""
    try:
        if hasattr(chunk.meta, "doc_items"):
            for item in chunk.meta.doc_items:
                if hasattr(item, "prov") and item.prov:
                    for prov in item.prov:
                        if hasattr(prov, "page_no") and prov.page_no is not None:
                            return int(prov.page_no)
    except Exception:
        pass
    return 1  # Default to page 1 if Docling can't find it

def load_and_chunk_file(file_path: Path, converter: DocumentConverter, chunker: HierarchicalChunker) -> list[Document]:
    """
    Convert one PDF with Docling, hierarchically chunk it,
    and return LangChain Documents with exact Chunk IDs and Page numbers.
    """
    result = converter.convert(file_path)
    docling_document = result.document

    documents: list[Document] = []

    # Create a stable, unique ID for this document based on its filename
    document_id = hashlib.md5(file_path.name.encode()).hexdigest()

    for i, chunk in enumerate(chunker.chunk(docling_document)):
        # Create a stable ID for this exact chunk (e.g. "a1b2c3d4_chunk_5")
        raw_string = f"{file_path.name}_chunk_{i}"
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_string))

        # Grab the PDF page number!
        page_num = extract_page_number(chunk)

        documents.append(
            Document(
                page_content=format_chunk_text(chunk),
                metadata={
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "collection": file_path.parent.name,
                    "source": file_path.parent.name,
                    "access_role": access_roles_for_collection(file_path.parent.name),
                    "headings": getattr(chunk.meta, "headings", []),
                    "page": page_num,             # <--- Required for Evals!
                    "document_id": document_id,   # <--- For your tracking
                    "chunk_id": chunk_id          # <--- For Qdrant Upserts
                },
            )
        )

    return documents

def load_all_documents(document_path: Path) -> list[Document]:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    chunker = HierarchicalChunker()

    file_paths = [
        path
        for path in sorted(document_path.rglob("*"))
        if path.is_file() and path.suffix.lower() == ".pdf"
    ]

    documents: list[Document] = []
    print(f"Found {len(file_paths)} files", flush=True)

    for file_path in file_paths:
        try:
            print(f"Processing: {file_path.name}", flush=True)

            file_documents = load_and_chunk_file(
                file_path=file_path,
                converter=converter,
                chunker=chunker,
            )

            documents.extend(file_documents)
            print(f"Created {len(file_documents)} LangChain Documents", flush=True)

        except Exception as error:
            print(f"Failed to process {file_path}: {error}", flush=True)

    print(f"Total LangChain Documents created: {len(documents)}", flush=True)
    return documents

def create_embeddings_and_store(documents: list[Document], qdrant_path: Path) -> QdrantVectorStore:
    dense_embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    sparse_embedding = FastEmbedSparse(model_name=SPARSE_MODEL)

    # Extract the chunk_ids so Qdrant knows to UPSERT (update) instead of duplicating
    chunk_ids = [doc.metadata["chunk_id"] for doc in documents]

    vector_stores = QdrantVectorStore.from_documents(
        documents=documents,
        embedding=dense_embedding,
        sparse_embedding=sparse_embedding,
        path=str(qdrant_path),
        collection_name=QDRANT_COLLECTION,
        retrieval_mode=RetrievalMode.HYBRID,
        ids=chunk_ids   # <--- THIS IS THE MAGIC THAT ENABLES UPDATES
    )

    print(f"Stored/Updated {len(documents)} documents in Qdrant (HNSW Indexed)", flush=True)

    return vector_stores

if __name__ == "__main__":

    # 1. Define where your PDFs are stored (update this path if it's different!)
    # For example: document_directory = Path("backend/data/documents")
    document_directory = Path("backend/data")  # <-- Change this to your PDF folder

    # 2. Define where Qdrant should save its database
    qdrant_db_path = Path("backend/qdrant_db")

    print("Starting Ingestion Pipeline...", flush=True)

    # Check if the document folder exists
    if not document_directory.exists():
        print(f"Error: Could not find document folder at {document_directory}", flush=True)
        print("Please create this folder and put your PDFs inside, or update the path in injest.py.", flush=True)
    else:
        # 3. Load and chunk the documents
        all_docs = load_all_documents(document_directory)

        if len(all_docs) > 0:
            # 4. Save them into Qdrant
            create_embeddings_and_store(all_docs, qdrant_db_path)
            print("Ingestion Complete!", flush=True)
        else:
            print("No PDFs found to ingest!", flush=True)
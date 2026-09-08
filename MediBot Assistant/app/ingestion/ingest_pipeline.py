from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.transforms.chunker import HierarchicalChunker
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode

SUPPORTED_EXTENSIONS = {".pdf"}

dense_embedding = HuggingFaceEmbeddings(model= "sentence-transformers/all-MiniLM-L6-v2")
sparse_embedding = FastEmbedSparse(model= "Qdrant/bm25")

def run_full_ingestion(document_path: Path) -> list[Document]:
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    chunker = HierarchicalChunker()

    file_paths = [
        fp for fp in sorted(document_path.rglob("*"))
        if fp.is_file() and fp.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    documents: list[Document] = []
    print(f"Found {len(file_paths)} files", flush=True)

    for file_path in file_paths:
        try:
            source_category = file_path.parent.name
            print(f"Processing: {file_path.name} | Source: {source_category}", flush=True)

            result = converter.convert(file_path)
            docling_doc = result.document

            document_chunk_count = 0
            for chunk in chunker.chunk(docling_doc):
                headings = getattr(chunk.meta, "headings", [])

                # Wrap directly in a LangChain Document object
                doc = Document(
                    page_content=format_chunk_text(chunk),
                    metadata={
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "source": source_category,
                        "headings": headings,
                    }
                )
                documents.append(doc)
                document_chunk_count += 1

            print(f"-> Created {document_chunk_count} LangChain documents for {file_path.name}", flush=True)

        except Exception as e:
            print(f"Failed to process {file_path}: {e}", flush=True)

    print(f"Total LangChain documents created: {len(documents)}", flush=True)
    if documents:
        QdrantVectorStore.from_documents(
            documents=documents,
            embedding=dense_embedding,
            sparse_embedding=sparse_embedding,
            path="./qdrant_db",
            collection_name="medibot_hybrid",
            retrieval_mode=RetrievalMode.HYBRID,
        )
        print("Embeddings successfully persisted!", flush=True)

    return documents

def format_chunk_text(chunk) -> str:
    """Formats the chunk text with breadcrumb headings for context."""
    headings = getattr(chunk.meta, "headings", [])
    content = chunk.text.strip()
    breadcrumbs = " > ".join(headings) if headings else ""

    if breadcrumbs:
        return f"{breadcrumbs}\n\n{content}"
    return content


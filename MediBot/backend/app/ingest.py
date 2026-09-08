from pathlib import Path

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
from qdrant_client import QdrantClient
from backend.app.rcba import access_roles_for_collection
from backend.app.search import (get_existing_vector_store, retrieve_document)

COLLECTION_NAME = "medibot_hybrid"

DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"


def format_chunk_text(chunk) -> str:
    """Add heading breadcrumbs before the chunk content."""
    headings = getattr(chunk.meta, "headings", [])
    content = chunk.text.strip()

    breadcrumbs = " > ".join(headings) if headings else ""

    return f"{breadcrumbs}\n\n{content}" if breadcrumbs else content

def load_and_chunk_file(file_path: Path, converter: DocumentConverter,chunker: HierarchicalChunker,
) -> list[Document]:
    """
    Convert one PDF with Docling, hierarchically chunk it,
    and return LangChain Documents.
    """

    result = converter.convert(file_path)
    docling_document = result.document

    documents: list[Document] = []

    for chunk in chunker.chunk(docling_document):
        documents.append(
            Document(
                page_content=format_chunk_text(chunk),
                metadata={
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "collection": file_path.parent.name,
                    "source" : file_path.parent.name,
                    "access_role": access_roles_for_collection(file_path.parent.name),
                    "headings": getattr(chunk.meta, "headings", []),
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

            print(
                f"Created {len(file_documents)} LangChain Documents",
                flush=True,
            )

        except Exception as error:
            print(f"Failed to process {file_path}: {error}", flush=True)

    print(f"Total LangChain Documents created: {len(documents)}",flush=True,)

    return documents


def create_embeddings_and_store(documents: list[Document], qdrant_path: Path, ) -> QdrantVectorStore:

    dense_embedding  = HuggingFaceEmbeddings(model_name= DENSE_MODEL )
    sparse_embedding  = FastEmbedSparse(model_name= SPARSE_MODEL)

    vector_stores = QdrantVectorStore.from_documents(documents=documents,
                                                    embedding=dense_embedding,
                                                    sparse_embedding=sparse_embedding,
                                                    path=str(qdrant_path),
                                                    collection_name=COLLECTION_NAME,
                                                    retrieval_mode=RetrievalMode.HYBRID,
                                                    )
    print(f"Stored {len(documents)} documents in Qdrant",flush=True,)

    return vector_stores

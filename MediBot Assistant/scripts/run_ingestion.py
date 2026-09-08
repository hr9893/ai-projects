from pathlib import Path
from app.ingestion.ingest_pipeline import run_full_ingestion

if __name__ == "__main__":
    ##run_full_ingestion(Path("./data"))
    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data"

    chunks = run_full_ingestion(data_path)

    print(f"Path found: {data_path}")
    print("path Found")
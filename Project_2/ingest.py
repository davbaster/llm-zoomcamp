import sys
import time
from pathlib import Path

import pandas as pd
from sqlitesearch import TextSearchIndex


KEYWORD_FIELDS = [
    "chunk_id",
    "volume",
    "chapter",
    "section",
    "subsection",
    "source_file",
    "source_url",
]

TEXT_FIELDS = ["text"]

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" 
print(f"Data directory: {DATA_DIR}")


def load_data():
    df = pd.read_json(DATA_DIR / "processed" / "chunks.jsonl", orient="records", lines=True)
    df = df.fillna("Not Available")

    return df.to_dict(orient="records")

def create_index(db_path):
    return TextSearchIndex(
        text_fields=TEXT_FIELDS,
        keyword_fields=KEYWORD_FIELDS,
        id_field="chunk_id",
        db_path=str(db_path),
    )

def build_index_keyword(documents, rebuild=True):

    db_path = DATA_DIR / "dc-vol-1-v2.db"

    with create_index(db_path) as index:
        if rebuild:
            # Use this when rebuilding from the complete chunks.jsonl file.
            index.clear()
            index.fit(documents)
        else:
            # Upserts documents by chunk_id.
            for doc in documents:
                index.add(doc)

        print(f"Indexed {index.count()} documents.")

    print(f"Index saved to {db_path}")
    return index


if __name__ == "__main__":
    
    documents = load_data()
    build_index_keyword(documents, rebuild=True)

    index = TextSearchIndex(
        text_fields=["text"],
        keyword_fields=["chunk_id", "chapter","section", "subsection", "source_file"  ],
        db_path=str(DATA_DIR / "dc-vol-1.db")
    )

    query = "I want to know what electricity is"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = index.search(query, num_results=2)
    print(answer)
    index.close()
    print("database closed")

import sys
import time
from pathlib import Path

import pandas as pd
from sqlitesearch import TextSearchIndex


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" 
print(f"Data directory: {DATA_DIR}")


def load_data():
    df = pd.read_json(DATA_DIR / "processed" / "chunks.jsonl", orient="records", lines=True)
    df = df.fillna("Not Available")

    return df.to_dict(orient="records")

def build_index_keyword(documents):

    index = TextSearchIndex(
        text_fields=["text"], #volume can be a keyword field, but all documents currently have the same value (Volume I - DC), so it will not help much with filtering yet.
        keyword_fields=["chunk_id", "chapter","section", "subsection", "source_file"  ],
        db_path=str(DATA_DIR / "dc-vol-1.db")
    )

    for doc in documents:
        index.add(doc)
        print(f"""Added: {doc["chunk_id"][:60]}...""")
        time.sleep(0.5)

    index.close()
    print("Done. Index saved to dc-vol-1.db")

if __name__ == "__main__":
    
    documents = load_data()
    index = build_index_keyword(documents)

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

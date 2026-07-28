import sys
import time

import pandas as pd
from sqlitesearch import TextSearchIndex

def load_data():
    df = pd.read_csv("c:/DATA/Cursos/llm-zoomcamp/Project-1/top_anime_dataset.csv")
    df = df.fillna("Not Available")

    return df.to_dict(orient="records")

def build_index_keyword(documents):

    index = TextSearchIndex(
        text_fields=["title", "title_english", "studios", "genres", "synopsis", "source"],
        keyword_fields=["mal_id"],
        db_path="./data/anime.db"
    )

    for doc in documents:
        index.add(doc)
        print(f"""Added: {doc["title_english"][:60]}...""")
        time.sleep(0.5)

    index.close()
    print("Done. Index saved to anime.db")

if __name__ == "__main__":
    documents = load_data()
    index = build_index_keyword(documents)

    index = TextSearchIndex(
        text_fields=["title", "title_english", "studios", "genres", "synopsis", "source"],
        keyword_fields=["mal_id"],
        db_path="./data/anime.db"
    )

    query = "I want to watch animes from Production I.G. Can you recommend one?"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = index.search(query, num_results=2)
    print(answer)
    index.close()
    print("database closed")
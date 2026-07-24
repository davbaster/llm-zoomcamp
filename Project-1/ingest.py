import sys

import pandas as pd
from minsearch import Index

def load_data():
    df = pd.read_csv("c:/DATA/Cursos/llm-zoomcamp/Project-1/top_anime_dataset.csv")
    df = df.fillna("Not Available")

    return df.to_dict(orient="records")

def build_index_keyword(documents):
    index = Index(
        text_fields=["title", "title_english", "studios", "genres", "synopsis", "source"],
        keyword_fields=["mal_id"]
    )
    index.fit(documents)
    return index

if __name__ == "__main__":
    documents = load_data()
    index = build_index_keyword(documents)

    query = "I want to watch animes from Production I.G. Can you recommend one?"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = index.search(query)
    print(answer)
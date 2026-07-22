import numpy as np
import pandas as pd
from minsearch import Index

def load_data():
    df = pd.read_csv("./top_anime_dataset.csv")
    df.head()

    return df.to_dict(orient="records")

def build_index(documents):
    index = Index(
        text_fields=["question", "section", "answer"],
        keyword_fields=["course"]
    )
    index.fit(documents)
    return index
import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from minsearch import Index
from openai import OpenAI
from tqdm import tqdm

from db_init import get_embedding_dimensions
from db_save import upsert_anime_records


DATASET_PATH = Path(__file__).with_name("top_anime_dataset.csv")
SEARCH_FIELDS = (
    "title",
    "title_english",
    "studios",
    "genres",
    "source",
    "synopsis",
)
INTEGER_FIELDS = (
    "mal_id",
    "episodes",
    "scored_by",
    "rank",
    "popularity",
    "members",
    "favorites",
    "year",
)
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def load_dataframe():
    return pd.read_csv(DATASET_PATH)


def load_data():
    """Load documents for the existing in-memory keyword search."""
    dataframe = load_dataframe().copy()
    dataframe[list(SEARCH_FIELDS)] = dataframe[list(SEARCH_FIELDS)].fillna(
        "Not Available"
    )
    return dataframe.to_dict(orient="records")


def build_index_keyword(documents):
    index = Index(
        text_fields=list(SEARCH_FIELDS),
        keyword_fields=["mal_id"],
    )
    index.fit(documents)
    return index


def _normalise_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def prepare_anime_records(limit=None):
    """Return database-ready records, preserving missing values as NULL."""
    dataframe = load_dataframe()
    if limit is not None:
        dataframe = dataframe.head(limit)

    records = []
    for raw_record in dataframe.to_dict(orient="records"):
        record = {
            column: _normalise_value(value) for column, value in raw_record.items()
        }
        for field in INTEGER_FIELDS:
            if record[field] is not None:
                record[field] = int(record[field])
        records.append(record)
    return records


def build_embedding_text(record):
    """Build the embedding input from only the fields used for search."""
    labels = {
        "title": "Title",
        "title_english": "English title",
        "studios": "Studios",
        "genres": "Genres",
        "source": "Source",
        "synopsis": "Synopsis",
    }
    return "\n".join(
        f"{labels[field]}: {record.get(field) or 'Not Available'}"
        for field in SEARCH_FIELDS
    )


def _batches(items, batch_size):
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def generate_embeddings(
    records,
    model=DEFAULT_EMBEDDING_MODEL,
    batch_size=100,
    client=None,
):
    """Add an OpenAI embedding to each record in-place and return the records."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")

    load_dotenv()
    client = client or OpenAI()
    embedding_dimensions = get_embedding_dimensions()

    for batch in tqdm(list(_batches(records, batch_size)), desc="Generating embeddings"):
        inputs = [build_embedding_text(record) for record in batch]
        request = {"model": model, "input": inputs}
        if model.startswith("text-embedding-3-"):
            request["dimensions"] = embedding_dimensions

        response = client.embeddings.create(**request)
        embeddings = [item.embedding for item in response.data]

        if len(embeddings) != len(batch):
            raise RuntimeError("The embedding API returned an unexpected number of vectors.")

        for record, embedding in zip(batch, embeddings, strict=True):
            if len(embedding) != embedding_dimensions:
                raise ValueError(
                    "Embedding dimensions do not match EMBEDDING_DIMENSIONS "
                    f"({embedding_dimensions})."
                )
            record["embedding"] = embedding

    return records


def ingest_to_postgres(
    limit=None,
    embedding_model=None,
    embedding_batch_size=100,
    database_batch_size=500,
):
    """Generate embeddings for the CSV data and upsert the records into PostgreSQL."""
    records = prepare_anime_records(limit=limit)
    generate_embeddings(
        records,
        model=embedding_model or os.getenv(
            "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        ),
        batch_size=embedding_batch_size,
    )
    return upsert_anime_records(records, batch_size=database_batch_size)


def main():
    parser = argparse.ArgumentParser(description="Anime dataset ingestion utilities")
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Generate embeddings and upsert the dataset into PostgreSQL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Only process the first N dataset records.",
    )
    parser.add_argument(
        "--embedding-model",
        help="OpenAI embedding model to use.",
    )
    parser.add_argument(
        "--query",
        default="I want to watch animes from Production I.G. Can you recommend one?",
        help="Query used with the in-memory keyword-search demo.",
    )
    args = parser.parse_args()

    if args.postgres:
        count = ingest_to_postgres(
            limit=args.limit,
            embedding_model=args.embedding_model,
        )
        print(f"Upserted {count} anime records into PostgreSQL.")
        return

    documents = load_data()
    index = build_index_keyword(documents)
    print(index.search(args.query))


if __name__ == "__main__":
    main()

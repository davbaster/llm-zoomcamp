import math
from datetime import datetime

from db_init import DB_TIMEZONE, get_db_connection


ANIME_COLUMNS = (
    "mal_id",
    "title",
    "title_english",
    "type",
    "source",
    "episodes",
    "status",
    "airing",
    "rating",
    "score",
    "scored_by",
    "rank",
    "popularity",
    "members",
    "favorites",
    "synopsis",
    "year",
    "genres",
    "studios",
    "url",
)


def _vector_literal(embedding):
    """Return an embedding in pgvector's text representation."""
    if embedding is None:
        return None

    values = [float(value) for value in embedding]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("Embedding values must be finite numbers.")

    return "[" + ",".join(format(value, ".9g") for value in values) + "]"


def upsert_anime_records(records, batch_size=500):
    """Insert or update anime records and their embeddings in PostgreSQL."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")

    rows = []
    for record in records:
        if record.get("mal_id") is None:
            raise ValueError("Each anime record must include a mal_id.")
        rows.append(
            tuple(record.get(column) for column in ANIME_COLUMNS)
            + (_vector_literal(record.get("embedding")),)
        )

    if not rows:
        return 0

    update_columns = tuple(column for column in ANIME_COLUMNS if column != "mal_id")
    assignments = ",\n                    ".join(
        f"{column} = EXCLUDED.{column}" for column in update_columns
    )

    query = f"""
        INSERT INTO anime (
            {", ".join(ANIME_COLUMNS)}, embedding
        ) VALUES (
            {", ".join(["%s"] * len(ANIME_COLUMNS))}, %s::vector
        )
        ON CONFLICT (mal_id) DO UPDATE SET
            {assignments},
            embedding = EXCLUDED.embedding,
            updated_at = NOW()
    """

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for start in range(0, len(rows), batch_size):
                cur.executemany(query, rows[start : start + batch_size])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return len(rows)


def save_conversation(record, question, course):
    timestamp = datetime.now(DB_TIMEZONE)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (
                    question, answer, course, model, instructions, prompt,
                    prompt_tokens, completion_tokens, total_tokens,
                    response_time, cost, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    question,
                    record.answer,
                    course,
                    record.model,
                    record.instructions,
                    record.prompt,
                    record.prompt_tokens,
                    record.completion_tokens,
                    record.total_tokens,
                    record.response_time,
                    record.cost,
                    timestamp,
                ),
            )
            conversation_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    return conversation_id

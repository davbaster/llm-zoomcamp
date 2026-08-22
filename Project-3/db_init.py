import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv
from psycopg import sql


DB_TIMEZONE = datetime.now().astimezone().tzinfo
DEFAULT_EMBEDDING_DIMENSIONS = 1536

load_dotenv()


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        dbname=os.getenv("POSTGRES_DB", "anime_assistant"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )


def get_embedding_dimensions():
    dimensions = int(
        os.getenv("EMBEDDING_DIMENSIONS", str(DEFAULT_EMBEDDING_DIMENSIONS))
    )
    if dimensions <= 0:
        raise ValueError("EMBEDDING_DIMENSIONS must be a positive integer.")
    return dimensions


def init_db(drop=False):
    """Create the catalog, retrieval, monitoring, and feedback schema.

    Set drop=True only for a local development reset. This deletes all
    application data before recreating the tables.
    """
    embedding_dimensions = get_embedding_dimensions()
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            if drop:
                cur.execute("DROP TABLE IF EXISTS conversation_retrievals")
                cur.execute("DROP TABLE IF EXISTS feedback")
                cur.execute("DROP TABLE IF EXISTS conversations")
                cur.execute("DROP TABLE IF EXISTS anime")

            cur.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS anime (
                        mal_id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        title_english TEXT,
                        type TEXT,
                        source TEXT,
                        episodes INTEGER,
                        status TEXT,
                        airing BOOLEAN,
                        rating TEXT,
                        score FLOAT,
                        scored_by INTEGER,
                        rank INTEGER,
                        popularity INTEGER,
                        members INTEGER,
                        favorites INTEGER,
                        synopsis TEXT,
                        year SMALLINT,
                        genres TEXT,
                        studios TEXT,
                        url TEXT,
                        embedding vector({embedding_dimensions}),
                        search_vector TSVECTOR GENERATED ALWAYS AS (
                            setweight(
                                to_tsvector('simple', COALESCE(title, '')),
                                'A'
                            ) ||
                            setweight(
                                to_tsvector('simple', COALESCE(title_english, '')),
                                'A'
                            ) ||
                            setweight(
                                to_tsvector('simple', COALESCE(genres, '')),
                                'B'
                            ) ||
                            setweight(
                                to_tsvector('simple', COALESCE(studios, '')),
                                'B'
                            ) ||
                            setweight(
                                to_tsvector('simple', COALESCE(source, '')),
                                'C'
                            ) ||
                            setweight(
                                to_tsvector('english', COALESCE(synopsis, '')),
                                'C'
                            )
                        ) STORED,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                    )
                    """
                ).format(embedding_dimensions=sql.SQL(str(embedding_dimensions)))
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGSERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    mal_id INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    response_time DOUBLE PRECISION NOT NULL,
                    cost DOUBLE PRECISION NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id INTEGER NOT NULL REFERENCES conversations(id)
                        ON DELETE CASCADE,
                    source TEXT NOT NULL CHECK (source IN ('user', 'judge')),
                    relevance TEXT,
                    explanation TEXT,
                    score SMALLINT CHECK (score IN (-1, 1)),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_retrievals (
                    conversation_id BIGSERIAL NOT NULL REFERENCES conversations(id)
                        ON DELETE CASCADE,
                    mal_id INTEGER NOT NULL REFERENCES anime(mal_id),
                    retrieval_method TEXT NOT NULL CHECK (
                        retrieval_method IN ('keyword', 'vector', 'hybrid')
                    ),
                    rank SMALLINT NOT NULL CHECK (rank > 0),
                    score DOUBLE PRECISION,
                    PRIMARY KEY (conversation_id, mal_id, retrieval_method),
                    UNIQUE (conversation_id, retrieval_method, rank)
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_anime_search_vector
                ON anime USING GIN (search_vector)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_anime_embedding_hnsw
                ON anime USING hnsw (embedding vector_cosine_ops)
                WHERE embedding IS NOT NULL
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
                ON conversations (timestamp DESC)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feedback_conversation_id
                ON feedback (conversation_id)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feedback_timestamp
                ON feedback (timestamp DESC)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_retrievals_lookup
                ON conversation_retrievals (conversation_id, retrieval_method, rank)
                """
            )
        conn.commit()
    finally:
        conn.close()


def init_feedback():
    """Backward-compatible initializer for existing callers."""
    init_db(drop=False)


if __name__ == "__main__":
    init_db()
    print("Database initialized")

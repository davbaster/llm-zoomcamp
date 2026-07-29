import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv
from psycopg import sql


DB_TIMEZONE = datetime.now().astimezone().tzinfo
#DEFAULT_EMBEDDING_DIMENSIONS = 1536

load_dotenv()


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        dbname=os.getenv("POSTGRES_DB", "anime_assistant"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )


def init_db(drop=False):
    """Create the catalog, retrieval, monitoring, and feedback schema.

    Set drop=True only for a local development reset. This deletes all
    application data before recreating the tables.
    """

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            if drop:

                cur.execute("DROP TABLE IF EXISTS feedback")
                cur.execute("DROP TABLE IF EXISTS conversations")


            cur.execute(

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
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                    )
                """)


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
            """)

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
            
        """)
        conn.commit()
    finally:
        conn.close()



if __name__ == "__main__":
    init_db()
    print("Database initialized")

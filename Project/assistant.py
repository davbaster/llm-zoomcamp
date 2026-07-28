import sys

from sqlitesearch import TextSearchIndex
from dotenv import load_dotenv
from openai import OpenAI

from ingest import load_data, build_index_keyword
from rag_helper import RAGBase



def create_assistant():
    load_dotenv()

    index = TextSearchIndex(
        text_fields=["title", "title_english", "studios", "genres", "synopsis", "source"],
        keyword_fields=["mal_id"],
        db_path="./data/anime.db"
    )

    return RAGBase(
        index=index,
        llm_client=OpenAI()
    )

#need to close the db index when the assistant is no longer needed to free up resources
def close_assistant(assistant):
    if hasattr(assistant, "index") and assistant.index is not None:
        assistant.index.close()


if __name__ == "__main__":
    assistant = create_assistant()

    query = "I want to watch animes from madhouse studios. Can you recommend one?"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = assistant.rag(query)
    print(answer)
    close_assistant(assistant)

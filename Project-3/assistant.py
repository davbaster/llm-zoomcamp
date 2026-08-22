import sys

from dotenv import load_dotenv
from openai import OpenAI

from ingest import load_data, build_index_keyword
from rag_helper import RAGBase



def create_assistant():
    load_dotenv()

    documents = load_data()
    index = build_index_keyword(documents)

    return RAGBase(
        index=index,
        llm_client=OpenAI()
    )

if __name__ == "__main__":
    assistant = create_assistant()

    query = "I want to watch animes from madhouse studios. Can you recommend one?"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = assistant.rag(query)
    print(answer)

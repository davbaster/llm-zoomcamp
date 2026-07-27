# Anime Recommendation Assistant

An anime recommendation assistant that uses a user's natural-language request to find relevant titles in an anime dataset and generate concise recommendations with an LLM.

The current prototype combines keyword search with retrieval-augmented generation (RAG):

1. Anime records are loaded from a CSV file.
2. A `minsearch` index retrieves the most relevant records.
3. The retrieved records are added to a prompt.
4. An OpenAI model generates recommendations using only the retrieved context.

The application provides a Streamlit interface backed by a Flask API. Vector search, hybrid search, persistent indexes in PostgreSQL, automated evaluation, user feedback monitoring, and containerized deployment are part of the planned project roadmap.

## Dataset

This project uses the [Top Anime CSV dataset on Kaggle](https://www.kaggle.com/datasets/muhammadaqeelkabir/top-anime-csv), downloaded locally as [`top_anime_dataset.csv`](top_anime_dataset.csv).

The records include fields such as:

- title and English title
- synopsis
- genres
- studios
- source
- MyAnimeList ID (`mal_id`)

The dataset is used for recommendations and should be reviewed for missing values, duplicates, and data-quality limitations before production use.

## Project files

- [`api.py`](api.py): Flask API that serves recommendations.
- [`app.py`](app.py): Streamlit frontend that calls the Flask API.
- [`assistant.py`](assistant.py): Creates the recommendation assistant and loads the search index.
- [`ingest.py`](ingest.py): Loads the CSV and builds the keyword index.
- [`rag_helper.py`](rag_helper.py): Retrieval, prompt construction, and LLM response generation.
- [`Generating ground truth.ipynb`](Generating%20ground%20truth.ipynb): Generates evaluation questions and ground-truth recommendations.
- [`Search evaluation.ipynb`](Search%20evaluation.ipynb): Evaluates search quality against the generated ground truth.
- [`top_anime_dataset.csv`](top_anime_dataset.csv): Local copy of the anime dataset.

## Requirements

- Python 3.14 or a compatible Python version supported by the project configuration.
- [uv](https://docs.astral.sh/uv/).
- An OpenAI API key.

## Installation

From the `Project-1` directory, install the project dependencies with:

```bash
uv sync
```

Create a `.env` file in this directory and add your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
```

Add a `.gitignore` file and add .env file to avoid sending the key to your repository.
Do not commit the `.env` file or expose the API key in source control.

## PostgreSQL schema

The database schema requires PostgreSQL with the `pgvector` extension available. Add these settings to `.env` when running PostgreSQL locally:

```env
POSTGRES_HOST=localhost
POSTGRES_DB=anime_assistant
POSTGRES_USER=user
POSTGRES_PASSWORD=password
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

`EMBEDDING_DIMENSIONS` must match the embedding model used during ingestion. The default, `1536`, matches OpenAI's `text-embedding-3-small` model.

Create the tables and indexes with:

```bash
uv run python db_init.py
```

The initializer creates the anime catalog, full-text and vector indexes, conversations, feedback, and retrieval-tracking tables. The `init_db(drop=True)` function is intended only for local development because it deletes all application data.

After initializing the database, generate embeddings and load the anime dataset with:

```bash
uv run python ingest.py --postgres
```

This calls the OpenAI Embeddings API and can incur API costs. To perform a small smoke-test ingestion first, use `uv run python ingest.py --postgres --limit 10`.

## Run the application

The application consists of a Flask API and a Streamlit frontend. Run them in two terminals, both from the `Project-1` directory.

### Start the Flask API

```bash
uv run flask --app api run --host 127.0.0.1 --port 5000
```

The API provides:

- `GET /health`: health check.
- `POST /recommend`: generates recommendations from a JSON request such as:

```json
{"query": "I want to watch an anime from Madhouse with fantasy and adventure elements."}
```

### Start the Streamlit frontend

```bash
uv run streamlit run app.py
```

Streamlit will display a local URL. Open it in a browser, enter a request such as:

```text
I want to watch an anime from Madhouse with fantasy and adventure elements.
```

The Streamlit application sends the request to `http://127.0.0.1:5000/recommend` and displays the generated answer and retrieved anime records. To use another API address, set `ANIME_API_URL` in the environment before starting Streamlit. The thumbs-up and thumbs-down controls are currently visual placeholders; persistent feedback storage and monitoring are planned.

## Run the Jupyter notebooks

Start Jupyter from the `Project-1` directory:

```bash
uv run jupyter notebook
```

Then open the notebooks in the Jupyter browser interface:

### Generate ground truth

Open [`Generating ground truth.ipynb`](Generating_ground_truth.ipynb) and run the cells to create the ground-truth data used to evaluate the system.

### Evaluate search

Open [`Search evaluation.ipynb`](Search_evaluation.ipynb) and run the cells to measure the quality of the retrieved recommendations using the generated ground truth.

If the notebooks are opened from another working directory, update any relative data paths or start Jupyter from `Project-1` so that `top_anime_dataset.csv` and the ground-truth CSV files can be found.

## Evaluation and future roadmap

The project is intended to evolve into a production-style RAG system with the following components:

- Generate and maintain a reliable ground-truth evaluation set.
- Add vector search over anime descriptions and compare it with the current keyword search.
- Implement hybrid search combining lexical and vector retrieval.
- Store anime records, embeddings, indexes, evaluation results, and feedback in PostgreSQL, using a vector extension where appropriate.
- Add an LLM-as-a-Judge evaluator for RAG response quality, including criteria such as relevance, faithfulness, and answer usefulness.
- Store user thumbs-up and thumbs-down feedback together with the request, retrieved records, and generated answer.
- Add Grafana dashboards to monitor response quality, evaluation scores, feedback trends, latency, and errors.
- Package the application and PostgreSQL in containers and use Docker Compose for local deployment.

These components are documented as the target architecture; they are not all available in the current prototype.

## Current limitations

- Retrieval currently uses `minsearch` keyword search; embeddings and hybrid retrieval are not implemented yet.
- The index is built in memory when the application starts.
- The Flask API and Streamlit frontend must currently be started as separate processes.
- Feedback is not persisted.
- PostgreSQL, Grafana, Docker, and Docker Compose configuration still need to be added.

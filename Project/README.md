# Anime Recommendation Assistant

## Problem and RAG flow

This project solves the problem of finding anime recommendations from a large catalogue using natural-language descriptions. Users can describe the story, genre, setting, characters, or tone they want, and the assistant returns recommendations grounded in the catalogue instead of relying only on the LLM's general knowledge.

The application follows a retrieval-augmented generation (RAG) flow:

1. A user submits a question through Streamlit.
2. The Flask API searches the local anime knowledge base for relevant titles.
3. The retrieved titles are added to the LLM prompt as context.
4. The LLM writes the recommendation using that context.
5. The API saves the conversation, evaluates the answer with a judge, and accepts user feedback.
6. Grafana queries the stored monitoring data from PostgreSQL.

## Dataset

The recommendation agent uses `data/top_anime_dataset.csv`, a catalogue of anime titles and metadata used by the local keyword-search index. The dataset contains one row per title and the following columns. The source dataset is available on [Kaggle](https://www.kaggle.com/datasets/muhammadaqeelkabir/top-anime-csv).

| Column | Description |
| --- | --- |
| `mal_id` | Unique MyAnimeList identifier. |
| `title` | Original title of the anime. |
| `title_english` | English title, when available. |
| `type` | Format, such as TV, movie, OVA, or special. |
| `source` | Original source material, such as manga, novel, or original. |
| `episodes` | Number of episodes. |
| `status` | Release status, such as Finished Airing or Currently Airing. |
| `airing` | Whether the anime is currently airing. |
| `rating` | Audience or age rating. |
| `score` | Average user score. |
| `scored_by` | Number of users who submitted a score. |
| `rank` | Ranking based on the user score. |
| `popularity` | Popularity ranking. |
| `members` | Number of users who have added the title to their list. |
| `favorites` | Number of users who marked the title as a favorite. |
| `synopsis` | Plot summary or description. |
| `year` | Release year, when available. |
| `genres` | Genres associated with the title. |
| `studios` | Animation or production studios. |
| `url` | Link to the title's MyAnimeList page. |

## Ingestion pipeline

The ingestion process is implemented in [`ingest.py`](ingest.py). It prepares the catalogue before the recommendation agent is used:

1. `load_data()` reads `data/top_anime_dataset.csv` with pandas and replaces missing values.
2. The rows are converted into dictionaries so they can be indexed as documents.
3. `build_index_keyword()` creates a SQLite-backed `TextSearchIndex` at `data/anime.db`.
4. The index stores searchable fields such as title, English title, synopsis, genres, studios, and source, while `mal_id` is used as the keyword identifier.
5. The persisted index is loaded by `assistant.py` when the API or Streamlit application starts.

This is an offline preparation step: Docker Compose uses the existing `data/anime.db` at runtime and does not rebuild the index on every startup. If the catalogue changes, run the ingestion process again to regenerate the local index.

From the `Project` directory, the ingestion script can be run with:

```bash
python ingest.py
```

## Evaluation and parameter tuning

To measure the quality of retrieval, I created a gold-truth dataset in [`data/ground_truth-mal-2.csv`](data/ground_truth-mal-2.csv). It contains generated recommendation questions and the `mal_id` of the catalogue document that should be retrieved for each question. The dataset contains five questions for each of the 500 catalogue records used in the experiment, for a total of 2,500 evaluation questions.

I used [`Generating_ground_truth.ipynb`](Generating_ground_truth.ipynb) to generate the questions, test different prompts and generation settings, and prepare the evaluation data. This project uses "fine-tuning" to mean application-level prompt and parameter tuning; the model weights themselves were not retrained.

## Evaluation criteria

The following rubric is used to evaluate the project. The evidence column describes the current implementation and makes it easier to review.

| Criterion | 0 points | 1 point | 2 points | Current evidence |
| --- | --- | --- | --- | --- |
| Problem description | The problem is not described. | The problem is described briefly or unclearly. | The problem is well described and the project solution is clear. | The problem and solution are described above. |
| Retrieval flow | No knowledge base or LLM is used. | No knowledge base is used and the LLM is queried directly. | Both a knowledge base and an LLM are used. | SQLite keyword retrieval provides context to the LLM. |
| Retrieval evaluation | No retrieval evaluation is provided. | Only one retrieval approach is evaluated. | Multiple retrieval approaches are evaluated and the best is used. | Gold-truth data is prepared; retrieval metrics and comparison of multiple approaches are still to be documented. |
| LLM evaluation | No final-output evaluation is provided. | Only one approach or prompt is evaluated. | Multiple approaches are evaluated and the best is used. | A judge evaluates relevance and stores verdicts; multiple-prompt comparison is not yet documented. |
| Interface | No way to interact with the application. | CLI, script, or notebook only. | UI, web application, or API is provided. | Streamlit UI and Flask API are available. |
| Ingestion pipeline | No ingestion. | Semi-automated ingestion with a notebook or Python script. | Automated ingestion with a tool such as Kestra, dlt, Airflow, or Prefect. | `ingest.py` provides Python-script ingestion into SQLite. |
| Monitoring | No monitoring. | User feedback or a monitoring dashboard exists. | User feedback and a dashboard with at least five charts exist. | PostgreSQL stores feedback and Grafana provides the monitoring dashboard. |
| Containerization | No containerization. | Dockerfile for the main app or Compose for dependencies only. | Everything runs in Docker Compose. | PostgreSQL, API, Streamlit, Grafana, and dashboard provisioning are defined in Compose. |
| Reproducibility | Instructions, data, or access are missing. | Instructions are incomplete, or versions/data are not fully reproducible. | Instructions and data are clear, easy to run, and all dependency versions are specified. | Dataset and setup instructions are included; dependency ranges should be pinned for a fully reproducible score. |
| Hybrid search | Not implemented. | — | 1 bonus point for combining and evaluating text and vector search. | Not implemented; the current system uses keyword search. |
| Document re-ranking | Not implemented. | — | 1 bonus point for document re-ranking. | Not implemented. |
| User query rewriting | Not implemented. | — | 1 bonus point for query rewriting. | Not implemented. |
| Cloud deployment | Not deployed. | — | 2 bonus points for cloud deployment. | Not implemented. |
| Other bonus | No additional bonus. | — | Up to 3 extra points for clearly documented additional work. | No additional bonus claimed. |

The Docker Compose setup starts:

- PostgreSQL for conversations and feedback
- A Flask API for the recommendation agent
- Streamlit for the user interface
- Grafana for monitoring conversations, feedback, cost, tokens, models, and response time

![Project architecture](images/architecture.png)

## Project Architecture

The project separates recommendation, observability, and presentation so each part has one clear responsibility:

- **SQLite + keyword search for the catalogue.** The anime dataset is stored locally in `data/anime.db` and queried through `TextSearchIndex`. This keeps retrieval lightweight and easy to run for a small, read-mostly catalogue.
- **Flask API for the RAG agent.** The API owns the recommendation workflow: retrieve relevant titles, call the LLM, evaluate the answer, and record the result. Keeping this logic behind an API means the interface can stay simple and other clients can use the agent later.
- **Streamlit for the user experience.** Streamlit only collects questions, displays recommendations, and submits thumbs-up or thumbs-down feedback to the API.
- **PostgreSQL for operational data.** Conversations, token usage, response time, cost, judge verdicts, and user feedback are stored in PostgreSQL. This data is relational, changes over time, and is well suited to SQL analysis.
- **Grafana for monitoring.** Grafana reads PostgreSQL directly to show request quality, cost, latency, token usage, and feedback without adding monitoring logic to the application request path.
- **Docker Compose for local integration.** Compose gives each service a stable internal name such as `api` and `postgres`, while named volumes retain PostgreSQL and Grafana data between restarts.

The current retrieval layer is keyword-based. A future version can add vector search alongside it for hybrid retrieval when semantic matching becomes necessary.

## Requirements

- Docker Desktop with Docker Compose, or docker engine.
- An OpenAI API key

## 1. Configure the environment

Open a terminal in this directory:

```bash
cd Project
```

Copy the example environment file:

macOS/Linux:

```bash
cp .EXAMPLE_env .env
```

Windows PowerShell:

```powershell
Copy-Item .EXAMPLE_env .env
```

Open `.env` and replace `KeyHere` with your OpenAI API key.

Do not commit `.env` or share your API key.

## 2. Start the project

Build the application image and start all services:

```bash
docker compose up --build
```

The first startup may take a few minutes while Docker downloads images and installs Python dependencies.


## 3. Open the application

When the containers are running, open:

- Streamlit assistant: [http://localhost:8501](http://localhost:8501)
- Grafana: [http://localhost:3000](http://localhost:3000)

The default Grafana credentials are:

```text
Username: admin
Password: admin
```

If you changed the Grafana values in `.env`, use those values instead.



## 4. Ask a question

1. Open Streamlit at `http://localhost:8501`.
2. Enter an anime request, for example:

   ```text
   can you recommend anything about reviving in another world?
   ```

3. Click **Ask**.
4. Review the answer and recommendations.

![Streamlit assistant](images/streamlit-assistant.png)

The API response includes the generated answer, a conversation ID, and a list of catalogue recommendations:

```json
{
  "query": "Can you recommend a fantasy anime with a clever main character?",
  "answer": "...generated recommendation...",
  "conversation_id": "...",
  "recommendations": [
    {"title": "...", "genres": "...", "synopsis": "..."}
  ]
}
```


5. Select **+1** or **-1** to submit feedback.

![Giving Feedback in the app](images/streamlit-assistant-feedback.png)

Each request is saved in PostgreSQL. The agent also evaluates the answer and stores a judge relevance result.

## 5. View Grafana monitoring

Open Grafana at `http://localhost:3000` and open the **Anime assistant** dashboard.

The dashboard is provisioned automatically and includes:

- Recent conversations
- User thumbs-up and thumbs-down feedback
- Judge relevance percentage
- LLM cost over time
- Prompt, completion, and total token usage
- Requests by model
- Response time

![Grafana dashboard](images/grafana-dashboard.png)

## Useful commands

Stop the services but keep the database and Grafana data:

```bash
docker compose down
```

Start the existing services again:

```bash
docker compose up
```

View service status:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs -f api
```

View all logs:

```bash
docker compose logs -f
```

## Reset local data

To remove the PostgreSQL and Grafana volumes and start from an empty installation:

```bash
docker compose down -v
docker compose up --build
```

This deletes local conversations, feedback, and Grafana configuration. Use it only when you want a clean reset.

## Troubleshooting

### The API cannot start

Check the API logs:

```bash
docker compose logs api
```

Make sure `.env` contains a valid `OPENAI_API_KEY` and the PostgreSQL settings are present.

### Streamlit says it cannot connect to the API

Check that the API is running and healthy:

```bash
docker compose ps
docker compose logs -f api
```

### Grafana is empty

Wait for the `grafana-init` service to finish, then refresh Grafana. You can inspect its logs with:

```bash
docker compose logs grafana-init
```

The dashboard will show more useful data after users ask questions and submit feedback.

## Conclusion

The current evaluation shows that approximately 50% of the generated answers meet our quality expectations. This gives us a useful baseline and also shows that there is room for improvement. In a future version, we hope to add vector search and combine it with the current keyword search through a hybrid retrieval approach. Better retrieval should provide more relevant context to the LLM and improve the quality of the final recommendations.

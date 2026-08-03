# Anime Recommendation Assistant

This project is an anime recommendation assistant powered by a retrieval-augmented generation (RAG) agent.

The Docker Compose setup starts:

- PostgreSQL for conversations and feedback
- A Flask API for the recommendation agent
- Streamlit for the user interface
- Grafana for monitoring conversations, feedback, cost, tokens, models, and response time



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

![Docker Compose startup](images/docker-compose-startup.png)

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


5. Select **+1** or **-1** to submit feedback.

![Giving Feedback in the app](images/streamlit-assistant-feedback.png)

Each request is saved in PostgreSQL. The agent also evaluates the answer and stores a judge relevance result.

## 5. View Grafana monitoring

Open Grafana at `http://localhost:3000` and open the **Fitness assistant** dashboard.

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

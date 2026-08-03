# Grafana Dashboard System

## Direction and feel

Operational RAG monitoring: calm, technical, and evidence-led. The dashboard should help a developer answer three questions quickly: what was requested, how good the answer was, and what it cost to produce.

## Information hierarchy

1. Recent conversations are the primary investigation surface.
2. User feedback and judge relevance summarize answer quality.
3. Cost, token usage, model mix, and response time explain system behavior.

## Data conventions

- Use the `conversations` table for request, model, token, cost, latency, and timestamp data.
- Use the `feedback` table for user scores (`source = 'user'`, `score`) and judge verdicts (`source = 'judge'`, `relevance`).
- Join feedback to conversations using `conversation_id` and filter each feedback source explicitly.
- Apply Grafana's dashboard time range to every time-based query with `$__timeFrom()` and `$__timeTo()`.
- Use `cost`, not `openai_cost`; `model`, not `model_used`; and `score`, not `feedback`.

## Panel patterns

- Recent conversations: table with conversation ID, question, answer, model, response time, cost, judge relevance, and user score.
- User feedback: pie chart with labeled `Thumbs up` and `Thumbs down` rows.
- Judge quality: gauge showing the percentage of `RELEVANT` judge verdicts.
- Cost and latency: time series with a `time` column and the measured value.
- Token usage: time series for prompt, completion, and total tokens.
- Model mix: bar chart grouped by `model` and ordered by request count.

## Display conventions

- Cost uses `currencyUSD`.
- Response time is displayed in seconds (`s`).
- Relevance is displayed as a percentage.
- Keep the dashboard UID stable so provisioning updates the existing dashboard instead of creating duplicates.
- Keep datasource UID replacement in the provisioning script; dashboard JSON may contain an exported placeholder UID.

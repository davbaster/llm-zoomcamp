# Analysis Plan: agent_traces

## Connection
pipeline: agent_traces
dataset: agent_traces_data
destination: duckdb

## Profile Summary
| table | rows | key columns | notes |
|-------|------|-------------|-------|
| logs | 20000 | index (unique 0-19999), session_id, type, timestamp, log (raw json) | temporal: timestamp; type: user/assistant; log.usage.{input,output}_tokens on assistant rows; log.cwd = project path |

## Questions
1. [x] How does daily log activity trend over the period? → Chart 1
2. [x] What's the split between user and assistant messages? → Chart 2
3. [x] Which projects generate the most agent activity? → Chart 3
4. [x] Which Claude models are used? → Chart 4
5. [x] How does token usage (input/output) trend day over day? → Chart 5
6. [x] What time of day is the agent most active? → Chart 6
7. [x] Which sessions have the most messages? → Chart 7

## Data Gaps
(none)

## Chart 1: Daily Activity Trend
question: How does daily log activity trend over the period?
type: line
x: timestamp (daily)
y: count(*)
source: logs

```sql
SELECT
    date_trunc('day', timestamp) AS day,
    count(*) AS events
FROM logs
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_line(point=True).encode(
    x="day:T",
    y="events:Q",
    tooltip=["day:T", "events:Q"]
).properties(title="Daily Activity Trend")
```

## Chart 2: User vs Assistant Messages
question: What's the split between user and assistant messages?
type: bar
x: type
y: count(*)
source: logs

```sql
SELECT type, count(*) AS n
FROM logs
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("n:Q", title="messages"),
    y=alt.Y("type:N", sort="-x"),
    tooltip=["type:N", "n:Q"]
).properties(title="User vs Assistant Messages")
```

## Chart 3: Activity by Project
question: Which projects generate the most agent activity?
type: bar
x: cwd
y: count(*)
source: logs

```sql
SELECT
    json_extract_string(log, '$.cwd') AS project,
    count(*) AS n
FROM logs
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("n:Q", title="events"),
    y=alt.Y("project:N", sort="-x"),
    tooltip=["project:N", "n:Q"]
).properties(title="Activity by Project")
```

## Chart 4: Model Usage
question: Which Claude models are used?
type: bar
x: model
y: count(*)
source: logs (type = assistant)

```sql
SELECT
    json_extract_string(log, '$.message.model') AS model,
    count(*) AS n
FROM logs
WHERE type = 'assistant'
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("n:Q", title="assistant messages"),
    y=alt.Y("model:N", sort="-x"),
    tooltip=["model:N", "n:Q"]
).properties(title="Model Usage")
```

## Chart 5: Token Usage Per Day
question: How does token usage (input/output) trend day over day?
type: line
x: timestamp (daily)
y: sum(tokens)
source: logs (type = assistant)

```sql
SELECT
    date_trunc('day', timestamp) AS day,
    sum(CAST(json_extract(log, '$.usage.input_tokens') AS BIGINT)) AS input_tokens,
    sum(CAST(json_extract(log, '$.usage.output_tokens') AS BIGINT)) AS output_tokens
FROM logs
WHERE type = 'assistant'
GROUP BY 1
ORDER BY 1
```

```altair
_df_long = df.melt(id_vars=["day"], value_vars=["input_tokens", "output_tokens"], var_name="token_type", value_name="tokens")
alt.Chart(_df_long).mark_line(point=True).encode(
    x="day:T",
    y="tokens:Q",
    color="token_type:N",
    tooltip=["day:T", "token_type:N", "tokens:Q"]
).properties(title="Token Usage Per Day")
```

## Chart 6: Activity by Hour of Day
question: What time of day is the agent most active?
type: bar
x: hour
y: count(*)
source: logs

```sql
SELECT
    extract(hour FROM timestamp) AS hour,
    count(*) AS n
FROM logs
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("hour:O", title="hour of day (UTC)"),
    y=alt.Y("n:Q", title="events"),
    tooltip=["hour:O", "n:Q"]
).properties(title="Activity by Hour of Day")
```

## Chart 7: Busiest Sessions
question: Which sessions have the most messages?
type: bar
x: session_id
y: count(*)
source: logs

```sql
SELECT session_id, count(*) AS n
FROM logs
GROUP BY 1
ORDER BY 2 DESC
LIMIT 15
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("n:Q", title="messages"),
    y=alt.Y("session_id:N", sort="-x"),
    tooltip=["session_id:N", "n:Q"]
).properties(title="Busiest Sessions (top 15)")
```

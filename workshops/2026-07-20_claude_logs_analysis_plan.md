# Analysis Plan: claude_logs

## Connection
pipeline: claude_logs
dataset: claude_logs_data
destination: duckdb

## Profile Summary
| table | rows | key columns | notes |
|-------|------|-------------|-------|
| session_events | 2640 | project, session_id, event_type, event (raw json) | temporal: event.timestamp (ISO string); event_type: assistant/user/queue-operation/mode/ai-title/last-prompt/system/attachment/file-history-snapshot |
| prompt_history | 99 | session_id, project, timestamp (epoch ms), entry (raw json) | temporal: timestamp |

## Questions
1. [x] How has my daily Claude Code activity changed over time? → Chart 1
2. [x] What kinds of events make up my sessions (user vs assistant vs system)? → Chart 2
3. [x] Which projects am I spending the most time in? → Chart 3
4. [x] Which Claude Code versions have I been using? → Chart 4
5. [x] How many prompts do I submit per day? → Chart 5
6. [x] Which Claude models am I using most? → Chart 6
7. [x] What time of day am I most active? → Chart 7

## Data Gaps
(none)

## Chart 1: Daily Activity Trend
question: How has my daily Claude Code activity changed over time?
type: line
x: event.timestamp (daily)
y: count(*)
source: session_events

```sql
SELECT
    date_trunc('day', CAST(json_extract_string(event, '$.timestamp') AS TIMESTAMP)) AS day,
    count(*) AS events
FROM session_events
WHERE json_extract_string(event, '$.timestamp') IS NOT NULL
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

## Chart 2: Event Type Breakdown
question: What kinds of events make up my sessions (user vs assistant vs system)?
type: bar
x: event_type
y: count(*)
source: session_events

```sql
SELECT event_type, count(*) AS n
FROM session_events
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("n:Q", title="events"),
    y=alt.Y("event_type:N", sort="-x"),
    tooltip=["event_type:N", "n:Q"]
).properties(title="Event Type Breakdown")
```

## Chart 3: Activity by Project
question: Which projects am I spending the most time in?
type: bar
x: project
y: count(*)
source: session_events

```sql
SELECT project, count(*) AS n
FROM session_events
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

## Chart 4: Claude Code Version Usage
question: Which Claude Code versions have I been using?
type: bar
x: version
y: count(*)
source: session_events

```sql
SELECT
    coalesce(json_extract_string(event, '$.version'), 'unknown') AS version,
    count(*) AS n
FROM session_events
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("n:Q", title="events"),
    y=alt.Y("version:N", sort="-x"),
    tooltip=["version:N", "n:Q"]
).properties(title="Claude Code Version Usage")
```

## Chart 5: Prompts Submitted Per Day
question: How many prompts do I submit per day?
type: line
x: timestamp (daily)
y: count(*)
source: prompt_history

```sql
SELECT
    date_trunc('day', to_timestamp(timestamp / 1000)) AS day,
    count(*) AS prompts
FROM prompt_history
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_line(point=True, color="orange").encode(
    x="day:T",
    y="prompts:Q",
    tooltip=["day:T", "prompts:Q"]
).properties(title="Prompts Submitted Per Day")
```

## Chart 6: Model Usage
question: Which Claude models am I using most?
type: bar
x: model
y: count(*)
source: session_events (event_type = assistant)

```sql
SELECT
    json_extract_string(event, '$.message.model') AS model,
    count(*) AS n
FROM session_events
WHERE event_type = 'assistant'
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

## Chart 7: Activity by Hour of Day
question: What time of day am I most active?
type: bar
x: hour
y: count(*)
source: session_events

```sql
SELECT
    extract(hour FROM CAST(json_extract_string(event, '$.timestamp') AS TIMESTAMP)) AS hour,
    count(*) AS n
FROM session_events
WHERE json_extract_string(event, '$.timestamp') IS NOT NULL
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

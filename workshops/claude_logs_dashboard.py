import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import dlt

    return alt, dlt, mo


@app.cell
def _(dlt):
    pipeline = dlt.attach("claude_logs")
    dataset = pipeline.dataset()
    return (dataset,)


@app.cell
def _(mo):
    mo.md("""
    # Claude Code Usage Report
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Activity Over Time
    """)
    return


@app.cell
def _(dataset):
    df_chart1 = dataset("""
        SELECT
            date_trunc('day', CAST(json_extract_string(event, '$.timestamp') AS TIMESTAMP)) AS day,
            count(*) AS events
        FROM session_events
        WHERE json_extract_string(event, '$.timestamp') IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart1,)


@app.cell
def _(alt, df_chart1):
    _chart = alt.Chart(df_chart1).mark_line(point=True).encode(
        x="day:T",
        y="events:Q",
        tooltip=["day:T", "events:Q"]
    ).properties(title="Daily Activity Trend")
    _chart
    return


@app.cell
def _(dataset):
    df_chart5 = dataset("""
        SELECT
            date_trunc('day', to_timestamp(timestamp / 1000)) AS day,
            count(*) AS prompts
        FROM prompt_history
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart5,)


@app.cell
def _(alt, df_chart5):
    _chart = alt.Chart(df_chart5).mark_line(point=True, color="orange").encode(
        x="day:T",
        y="prompts:Q",
        tooltip=["day:T", "prompts:Q"]
    ).properties(title="Prompts Submitted Per Day")
    _chart
    return


@app.cell
def _(dataset):
    df_chart7 = dataset("""
        SELECT
            extract(hour FROM CAST(json_extract_string(event, '$.timestamp') AS TIMESTAMP)) AS hour,
            count(*) AS n
        FROM session_events
        WHERE json_extract_string(event, '$.timestamp') IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart7,)


@app.cell
def _(alt, df_chart7):
    _chart = alt.Chart(df_chart7).mark_bar().encode(
        x=alt.X("hour:O", title="hour of day (UTC)"),
        y=alt.Y("n:Q", title="events"),
        tooltip=["hour:O", "n:Q"]
    ).properties(title="Activity by Hour of Day")
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Session Composition
    """)
    return


@app.cell
def _(dataset):
    df_chart2 = dataset("""
        SELECT event_type, count(*) AS n
        FROM session_events
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart2,)


@app.cell
def _(alt, df_chart2):
    _chart = alt.Chart(df_chart2).mark_bar().encode(
        x=alt.X("n:Q", title="events"),
        y=alt.Y("event_type:N", sort="-x"),
        tooltip=["event_type:N", "n:Q"]
    ).properties(title="Event Type Breakdown")
    _chart
    return


@app.cell
def _(dataset):
    df_chart6 = dataset("""
        SELECT
            json_extract_string(event, '$.message.model') AS model,
            count(*) AS n
        FROM session_events
        WHERE event_type = 'assistant'
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart6,)


@app.cell
def _(alt, df_chart6):
    _chart = alt.Chart(df_chart6).mark_bar().encode(
        x=alt.X("n:Q", title="assistant messages"),
        y=alt.Y("model:N", sort="-x"),
        tooltip=["model:N", "n:Q"]
    ).properties(title="Model Usage")
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Where I'm Working
    """)
    return


@app.cell
def _(dataset):
    df_chart3 = dataset("""
        SELECT project, count(*) AS n
        FROM session_events
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart3,)


@app.cell
def _(alt, df_chart3):
    _chart = alt.Chart(df_chart3).mark_bar().encode(
        x=alt.X("n:Q", title="events"),
        y=alt.Y("project:N", sort="-x"),
        tooltip=["project:N", "n:Q"]
    ).properties(title="Activity by Project")
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Tooling
    """)
    return


@app.cell
def _(dataset):
    df_chart4 = dataset("""
        SELECT
            coalesce(json_extract_string(event, '$.version'), 'unknown') AS version,
            count(*) AS n
        FROM session_events
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart4,)


@app.cell
def _(alt, df_chart4):
    _chart = alt.Chart(df_chart4).mark_bar().encode(
        x=alt.X("n:Q", title="events"),
        y=alt.Y("version:N", sort="-x"),
        tooltip=["version:N", "n:Q"]
    ).properties(title="Claude Code Version Usage")
    _chart
    return


if __name__ == "__main__":
    app.run()

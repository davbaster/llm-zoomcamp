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
    pipeline = dlt.attach("agent_traces", destination="playground", dataset_name="agent_logs")
    dataset = pipeline.dataset()
    return (dataset,)


@app.cell
def _(mo):
    mo.md("""
    # Agent Traces Usage Report
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
            date_trunc('day', timestamp) AS day,
            count(*) AS events
        FROM logs
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
            date_trunc('day', timestamp) AS day,
            sum(CAST(json_extract(log, '$.usage.input_tokens') AS BIGINT)) AS input_tokens,
            sum(CAST(json_extract(log, '$.usage.output_tokens') AS BIGINT)) AS output_tokens
        FROM logs
        WHERE type = 'assistant'
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart5,)


@app.cell
def _(alt, df_chart5):
    _df_long = df_chart5.melt(
        id_vars=["day"],
        value_vars=["input_tokens", "output_tokens"],
        var_name="token_type",
        value_name="tokens",
    )
    _chart = alt.Chart(_df_long).mark_line(point=True).encode(
        x="day:T",
        y="tokens:Q",
        color="token_type:N",
        tooltip=["day:T", "token_type:N", "tokens:Q"]
    ).properties(title="Token Usage Per Day")
    _chart
    return


@app.cell
def _(dataset):
    df_chart6 = dataset("""
        SELECT
            extract(hour FROM timestamp) AS hour,
            count(*) AS n
        FROM logs
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart6,)


@app.cell
def _(alt, df_chart6):
    _chart = alt.Chart(df_chart6).mark_bar().encode(
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
        SELECT type, count(*) AS n
        FROM logs
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart2,)


@app.cell
def _(alt, df_chart2):
    _chart = alt.Chart(df_chart2).mark_bar().encode(
        x=alt.X("n:Q", title="messages"),
        y=alt.Y("type:N", sort="-x"),
        tooltip=["type:N", "n:Q"]
    ).properties(title="User vs Assistant Messages")
    _chart
    return


@app.cell
def _(dataset):
    df_chart4 = dataset("""
        SELECT
            json_extract_string(log, '$.message.model') AS model,
            count(*) AS n
        FROM logs
        WHERE type = 'assistant'
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart4,)


@app.cell
def _(alt, df_chart4):
    _chart = alt.Chart(df_chart4).mark_bar().encode(
        x=alt.X("n:Q", title="assistant messages"),
        y=alt.Y("model:N", sort="-x"),
        tooltip=["model:N", "n:Q"]
    ).properties(title="Model Usage")
    _chart
    return


@app.cell
def _(dataset):
    df_chart7 = dataset("""
        SELECT session_id, count(*) AS n
        FROM logs
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 15
    """).df()
    return (df_chart7,)


@app.cell
def _(alt, df_chart7):
    _chart = alt.Chart(df_chart7).mark_bar().encode(
        x=alt.X("n:Q", title="messages"),
        y=alt.Y("session_id:N", sort="-x"),
        tooltip=["session_id:N", "n:Q"]
    ).properties(title="Busiest Sessions (top 15)")
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
        SELECT
            json_extract_string(log, '$.cwd') AS project,
            count(*) AS n
        FROM logs
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


if __name__ == "__main__":
    app.run()

from flask import Flask, jsonify, request

from assistant import create_assistant


app = Flask(__name__)
assistant = create_assistant()


def _json_safe_records(records):
    """Convert values returned by pandas/minsearch into JSON-safe values."""
    safe_records = []
    for record in records:
        safe_record = {}
        for key, value in record.items():
            if hasattr(value, "item"):
                value = value.item()
            safe_record[key] = value
        safe_records.append(safe_record)
    return safe_records


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/recommend")
def recommend():
    payload = request.get_json(silent=True) or {}
    query = payload.get("query")

    if not isinstance(query, str) or not query.strip():
        return jsonify({"error": "The request must include a non-empty 'query' string."}), 400

    try:
        answer, recommendations = assistant.rag(query.strip())
    except Exception:
        app.logger.exception("Recommendation request failed")
        return jsonify({"error": "Unable to generate recommendations."}), 500

    return jsonify(
        {
            "query": query.strip(),
            "answer": answer,
            "recommendations": _json_safe_records(recommendations),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

import uuid
from flask import Flask, jsonify, request
from assistant import create_assistant
import db_save
from judge import evaluate_relevance

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

        #saving before calling judge to avoid destroying last call data
        record = assistant.get_last_call()
        conversation_id = str(uuid.uuid4())
        print("uuid generated: " + conversation_id)
        db_save.save_conversation(conversation_id, record, query.strip())

        relevance, explanation = evaluate_relevance(query.strip(), answer)

        db_save.save_judge_feedback(
            conversation_id=conversation_id,
            relevance=relevance,
            explanation=explanation
        )

    except Exception:
        app.logger.exception("Recommendation request failed")
        return jsonify({"error": "Unable to generate recommendations."}), 500

    return jsonify(
        {
            "query": query.strip(),
            "answer": answer,
            "conversation_id": conversation_id,
            "recommendations": _json_safe_records(recommendations),
        }
    )


#conversation_id is used to identify the conversation in the db
# , and feedback is 1 for relevant and -1 for non-relevant
#conversation_id is used two times in the feedback table, 
# first to save the feedback provided by the judge, and 
# second to save the feedback provided by the user 
# Therefore, conversation_id cannot be unique in the feedback table,
#  and it should be used to identify the conversation in the db
@app.route("/feedback", methods=["POST"])
def handle_feedback():
    data = request.get_json(silent=True) or {}
    conversation_id = data.get("conversation_id")
    feedback = data.get("feedback")

    if not conversation_id or type(feedback) is not int or feedback not in [1, -1]:
        return jsonify({"error": "Invalid input"}), 400


    db_save.save_user_feedback(
        conversation_id=conversation_id,
        score=feedback,
        explanation="user feedback"#TODO: Add explanation field to the feedback form and pass it here
    )

    return jsonify({"message": f"Feedback received: {feedback}"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

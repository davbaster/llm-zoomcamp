import os

import requests
import streamlit as st
from assistant import create_assistant

#from judge import evaluate_relevance
#from db_feedback import save_feedback

API_URL = os.getenv("ANIME_API_URL", "http://127.0.0.1:5000")

answer, recommendation = None, None
assistant = create_assistant()

st.title("Anime Recommendation Assistant")

user_input = st.text_input("Enter your question:")

if st.button("Ask"):
    if not user_input.strip():
        st.warning("Please enter a question.")

    else:
        with st.spinner("Processing..."):
            try:
                
                #answer, recommendation  = assistant.rag(user_input)

                response = requests.post(

                    f"{API_URL}/recommend",
                    json={"query": user_input.strip()},
                    timeout=120,
                )
                response.raise_for_status()
                st.session_state.recommendation_response = response.json()
                st.session_state.conversation_id = st.session_state.recommendation_response.get("conversation_id")

                #record = assistant.last_call
                #st.write(f"Response time: {record.response_time:.2f}s")
                #st.write(f"Prompt tokens: {record.prompt_tokens}")
                #st.write(f"Completion tokens: {record.completion_tokens}")
                #st.write(f"Cost: ${record.cost:.4f}")

                #conversation_id = save_conversation(record, user_input, "llm-zoomcamp")
                #st.session_state.conversation_id = conversation_id

                #relevance, explanation = evaluate_relevance(user_input, answer)
                #save_feedback(conversation_id, "judge",
                #                relevance=relevance, explanation=explanation)
                #st.write(f"Relevance: {relevance}")
                #st.write(f"Explanation: {explanation}")

            except requests.RequestException as error:
                st.error(
                    "Could not connect to the recommendation API. Please ensure the API is running and accessible."
                    f"Error code: {error}")
                st.caption(str(error))

            except ValueError:
                st.error("Invalid response from the API. Please check the API logs for more details.")

response_data = st.session_state.get("recommendation_response")

if response_data:
    st.success("Completed!")
    st.subheader("Answer:")
    st.write(response_data["answer"])
    st.write("Other titles that you might like:")
    st.dataframe(response_data["recommendations"])    

    col1, col2 = st.columns(2)
    with col1:
        if st.button("+1"):
            try:
                response = requests.post(

                    f"{API_URL}/feedback",
                    json={"conversation_id": response_data["conversation_id"], "feedback": 1},
                    timeout=120,
                )
                #TODO: response feedback should receive a 200ok.
                #no answer should be received.
                response.raise_for_status()
                if response.status_code == 200:
                    st.success("Feedback submitted successfully.")
                else:
                    st.error(f"Unexpected response from the API: {response.status_code}")

            except requests.RequestException as error:
                st.error(
                    "Could not connect to the feedback API. Please ensure the API is running and accessible."
                    f"Error code: {error}")
                st.caption(str(error))
            

    with col2:
        if st.button("-1"):
            try:
                response = requests.post(

                    f"{API_URL}/feedback",
                    json={"conversation_id": response_data["conversation_id"], "feedback": -1},
                    timeout=120,
                )
                #TODO: response feedback should receive a 200ok.
                #no answer should be received.
                response.raise_for_status()
                if response.status_code == 200:
                    st.success("Feedback submitted successfully.")
                else:
                    st.error(f"Unexpected response from the API: {response.status_code}")

            except requests.RequestException as error:
                st.error(
                    "Could not connect to the feedback API. Please ensure the API is running and accessible."
                    f"Error code: {error}")
                st.caption(str(error))
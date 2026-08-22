import os

import requests
import streamlit as st


API_URL = os.getenv("ANIME_API_URL", "http://127.0.0.1:5000")


st.title("Anime Recommendation Assistant")

user_input = st.text_input("Enter your question:")

if st.button("Ask"):
    if not user_input.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Processing..."):
            try:
                response = requests.post(
                    f"{API_URL.rstrip('/')}/recommend",
                    json={"query": user_input.strip()},
                    timeout=120,
                )
                response.raise_for_status()
                st.session_state.recommendation_response = response.json()
            except requests.RequestException as error:
                st.error(
                    "Could not reach the recommendation API. "
                    "Make sure the Flask API is running."
                )
                st.caption(str(error))
            except ValueError:
                st.error("The recommendation API returned an invalid response.")


response_data = st.session_state.get("recommendation_response")

if response_data:
    st.success("Completed!")
    st.write("Answer:")
    st.write(response_data["answer"])
    st.write("Other titles that you might like:")
    st.dataframe(response_data["recommendations"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("+1"):
            st.write("Thanks!")

    with col2:
        if st.button("-1"):
            st.write("Thanks for the feedback!")

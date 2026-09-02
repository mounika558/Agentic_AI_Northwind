import streamlit as st
import asyncio

from agent import ask_agent


st.set_page_config(
    page_title="NorthWind Manufacturing Assistant",
    page_icon="🏭"
)

st.title("🏭 NorthWind Manufacturing Assistant")

st.write(
    "Ask questions about materials, customers, sales orders, "
    "tickets, and invoices."
)


question = st.chat_input("Ask something...")


if question:

    # Display user question
    with st.chat_message("user"):
        st.write(question)

    # Run agent
    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:
                answer = asyncio.run(
                    ask_agent(question)
                )

                st.write(answer)

            except Exception as e:

                st.error(
                    f"Error while processing request: {str(e)}"
                )
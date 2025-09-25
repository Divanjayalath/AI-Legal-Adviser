# app.py

import streamlit as st
import os
import dotenv

# Import our agent creator from the src/agents/ folder
from src.agents.master_agent import create_master_agent

def main():
    """
    Main function to run the Streamlit application for the AI Legal Agent.
    """
    # --- Page Configuration ---
    st.set_page_config(page_title="AI Legal Adviser - Sri Lanka", page_icon="⚖️")
    st.title("⚖️ AI Legal Adviser Agent")
    st.write("Ask legal questions or ask to find a lawyer by specialty and location.")

    # --- Load Environment Variables ---
    dotenv.load_dotenv()

    # --- Initialize the Agent ---
    # This function creates our Master Agent with its tools.
    # It's cached so it only runs once.
    @st.cache_resource
    def get_agent():
        """Initializes and returns the master agent executor."""
        return create_master_agent()

    # --- Chat Interface ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Load the agent, with error handling
    try:
        agent_executor = get_agent()
    except Exception as e:
        st.error(f"Failed to create the AI agent: {e}")
        st.info("Please check your .env credentials and ensure all libraries are installed.")
        st.stop()

    # Get user input from the chat box
    if prompt := st.chat_input("Ask about your rights or find a lawyer..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get the AI's response
        with st.chat_message("assistant"):
            with st.spinner("The agent is thinking..."):
                try:
                    # Send the user's question to the agent
                    response = agent_executor.invoke({"input": prompt})
                    
                    # The agent's final answer is in the "output" key
                    answer = response["output"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error("An error occurred. See details below.")
                    st.exception(e) # Display the full technical error in the app

# --- Run the App ---
if __name__ == '__main__':
    main()
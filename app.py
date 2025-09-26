# app.py

import streamlit as st
import os
import dotenv

# Import our agent and parser creation functions
from src.agents.master_agent import create_master_agent
from src.agents.query_understanding_agent import get_query_parser_chain, ParsedQuery

def main():
    """
    Main function to run the final Streamlit application with the integrated Query Understanding Agent.
    """
    # --- Page Configuration ---
    st.set_page_config(page_title="AI Legal Adviser - Sri Lanka", page_icon="⚖️")
    st.title("⚖️ AI Legal Adviser Agent")
    st.write("Ask complex legal questions or ask to find a lawyer by specialty and location.")

    # --- Load Environment Variables ---
    dotenv.load_dotenv()

    # --- Initialize both the agent and the parser ---
    # This is cached so it only runs once, making the app faster.
    @st.cache_resource
    def get_agent_and_parser():
        agent_executor = create_master_agent()
        parser_chain = get_query_parser_chain()
        return agent_executor, parser_chain

    # --- Chat Interface ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    try:
        agent_executor, parser_chain = get_agent_and_parser()
    except Exception as e:
        st.error(f"Failed to create the AI agent or parser: {e}")
        st.info("Please verify your .env credentials and ensure all libraries are installed.")
        st.stop()

    if prompt := st.chat_input("Ask about your rights or find a lawyer..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Agent is analyzing and planning..."):
                try:
                    # --- NEW WORKFLOW STEP 1: PARSE THE QUERY ---
                    st.write("Understanding your query...")
                    parsed_query: ParsedQuery = parser_chain.invoke({"query": prompt})
                    
                    st.write(f"Intent identified: **{parsed_query.intent}**")
                    
                    # --- NEW WORKFLOW STEP 2: RUN THE MASTER AGENT WITH STRUCTURED INPUT ---
                    st.write("Executing the plan...")
                    
                    # Create a clear, structured input for the master agent
                    agent_input = f"Based on the user's query, the primary intent is '{parsed_query.intent}'. "
                    if parsed_query.entities:
                        agent_input += f"The key details are {parsed_query.entities}. "
                    agent_input += f"Please address the following core task: {parsed_query.cleaned_query}"

                    # Send the structured input to the agent
                    response = agent_executor.invoke({"input": agent_input})
                    
                    answer = response["output"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error("An error occurred. See details below.")
                    st.exception(e)

if __name__ == '__main__':
    main()
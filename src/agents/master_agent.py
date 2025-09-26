# src/agents/master_agent.py

import os
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_huggingface.chat_models import ChatHuggingFace
from langchain_huggingface import HuggingFaceEndpoint

# Import the tools we created
from src.tools.retrieval_tool import search_legal_documents
from src.tools.lawyer_finder_tool import find_lawyer

def create_master_agent():
    """
    Creates and returns the master agent executor with a more robust prompt.
    """
    #  Define the tools the agent can use 
    tools = [search_legal_documents, find_lawyer]

    # Get a pre-built prompt template from LangChain Hub
    # This prompt is specifically designed for agents that use tools
    prompt = hub.pull("hwchase17/react")

    # Create the base LLM first, then wrap it with ChatHuggingFace
    base_llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        temperature=0.3,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
    )
    
    # Now wrap it with ChatHuggingFace (this is the required pattern)
    llm = ChatHuggingFace(llm=base_llm)

    #  Create the agent
    agent = create_react_agent(llm, tools, prompt)

    # Create the Agent Executor with better error handling
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True,  # This helps with occasional formatting mistakes
        max_iterations=10,  # Increase iterations to allow proper completion
        return_intermediate_steps=False  # Don't return intermediate steps to reduce confusion
    )

    return agent_executor
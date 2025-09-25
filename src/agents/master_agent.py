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
    # 1. Define the tools
    tools = [search_legal_documents, find_lawyer]

    # 2. Get a pre-built prompt template from LangChain Hub
    # This prompt is specifically designed for agents that use tools
    prompt = hub.pull("hwchase17/react")

    # 3. Create the base LLM first, then wrap it with ChatHuggingFace
    base_llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        temperature=0.3,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
    )
    
    # Now wrap it with ChatHuggingFace (this is the required pattern)
    llm = ChatHuggingFace(llm=base_llm)

    # 4. Create the agent
    agent = create_react_agent(llm, tools, prompt)

    # 5. Create the Agent Executor with better error handling
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True,  # This helps with occasional formatting mistakes
        max_iterations=3,  # Limit iterations to prevent infinite loops
        early_stopping_method="force"  # Use valid early stopping method
    )

    return agent_executor
# src/agents/master_agent.py

import os
from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Import the tools we created
from src.tools.retrieval_tool import search_legal_documents
from src.tools.lawyer_finder_tool import find_lawyer

def create_master_agent():
    """
    Creates and returns the master agent executor with a more robust prompt.
    """
    #  Define the tools the agent can use 
    tools = [search_legal_documents, find_lawyer]

    # Create a custom prompt template for legal assistance
    from langchain.prompts import PromptTemplate
    
    template = """You are a helpful AI legal assistant for Sri Lankan law. Use the available tools to help users with legal questions and find lawyers.

Available tools:
{tools}

Tool names: {tool_names}

When answering legal questions:
1. Use search_legal_documents to find relevant legal information
2. Provide clear, structured answers based on the legal documents
3. If asked about finding lawyers, use find_lawyer tool
4. Always conclude with "Final Answer:" followed by your complete response

Format your responses as:
Thought: I need to [what you plan to do]
Action: [tool name]
Action Input: [input to the tool]
Observation: [tool result]
Thought: [analysis of the result]
Final Answer: [complete structured answer to the user]

Question: {input}
{agent_scratchpad}"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )

    # Create Groq LLM - free and fast alternative
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    #  Create the agent
    agent = create_react_agent(llm, tools, prompt)

    # Create the Agent Executor with better error handling
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
        handle_parsing_errors=True,  # This helps with occasional formatting mistakes
        max_iterations=5,  # Reduced iterations to prevent infinite loops
        max_execution_time=30,  # 30 second timeout
        return_intermediate_steps=False,  # Don't return intermediate steps to reduce confusion
        early_stopping_method="generate"  # Stop early if we get a good answer
    )

    return agent_executor
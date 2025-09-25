# app.py

import streamlit as st # Creates the web interface
import os # Helps read environment variables
import dotenv
import chromadb
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA # The "smart search + answer" system
from langchain.prompts import PromptTemplate # Templates for AI questions
from langchain_core.language_models.llms import LLM # Base class for AI models
from huggingface_hub import InferenceClient # Connects to Hugging Face AI
from typing import Any, List, Optional # Type hints for better code

# ---------DEFINE A CUSTOM, STABLE HUGGING FACE LLM CLASS --------
class CustomHuggingFaceLLM(LLM):
    """
    A custom LangChain LLM class that connects to the Hugging Face Inference API.
    This provides a stable interface, bypassing the rapidly changing official wrappers.
    """
    client: Optional[InferenceClient] = None       # The connection to HuggingFace
    repo_id: str = "mistralai/Mistral-7B-Instruct-v0.2" #Use Mistral AI 
    temperature: float = 0.5 #How creative the  AI should be 
    

    # connect to the hugging face using API key 
    def __init__(self, api_token: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.client = InferenceClient(token=api_token)
    
    class Config:
        arbitrary_types_allowed = True # Allows custom objects like InferenceClient

    @property
    def _llm_type(self) -> str:
        return "custom_huggingface"


    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str: #
        """
        Makes a call to the Hugging Face Inference API using the chat_completion method.
        """
        try:
            # Format the prompt for a chat model
            messages = [{"role": "user", "content": prompt}]
            
            # Send the question to Mistral AI on Hugging Face
            response = self.client.chat_completion(
                messages,
                model=self.repo_id,
                max_tokens=512, #(about 300-400 words)
                temperature=self.temperature,
            )
            return response.choices[0].message.content or "" # Get the AI's answer
        
        # If something goes wrong, show an error
        except Exception as e:
            # Add more detailed error logging
            st.error(f"Hugging Face API call failed: {e}")
            return f"Error: Could not get a response from the model. Details: {e}"
        



# ---------- MAIN APPLICATION LOGIC ----------
def main():

    #create a web page 
    st.set_page_config(page_title="AI Legal Adviser - Sri Lanka", page_icon="⚖️")
    st.title("⚖️ AI Legal Adviser for Sri Lanka")
    st.write("Ask questions about Sri Lankan law.")

#Read the .env filr with API keys , and check that all rerquired keys and if have an error  stop the app with an error message 
    try:
        dotenv.load_dotenv()  # Read the .env file with your secret keys
        required_keys = ["HUGGINGFACEHUB_API_TOKEN", "CHROMA_TENANT", "CHROMA_DATABASE", "CHROMA_API_KEY"]
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            st.error(f"Missing required environment variables: {', '.join(missing_keys)}")
            st.stop() # Stop the app if any keys are missing
    except Exception as e:
        st.error(f"Error loading environment variables: {e}")
        st.stop()

    #The smart RAG system 
    @st.cache_resource
    def get_rag_chain():
        # Connect to your ChromaDB database in the cloud
        client = chromadb.CloudClient(
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE"),
            api_key=os.getenv("CHROMA_API_KEY")
        )
        # Set up the document search system
        vector_store = Chroma(client=client, collection_name='sri_lanka_legal')
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # Create your custom AI model
        llm = CustomHuggingFaceLLM(api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"))

        prompt_template = """
        You are a helpful legal assistant for Sri Lankan law. Use the following context to answer the question.
        If you don't know the answer from the context, say that you don't know.
        **Disclaimer: This is AI-generated information and not a substitute for professional legal advice.**
        CONTEXT: {context}
        QUESTION: {question}
        ANSWER:
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        return chain
    
    #Chat interface 
    #Creates an empty chat history if one doesn't exist
    #Shows all previous messages (yours and the AI's)

    if "messages" not in st.session_state: #create empty chat history 
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]): # Show if it's from user or assistant
            st.markdown(message["content"])  # Display the message


    #Connects to your AI + database system, or shows an error if it fails
    try:
        rag_chain = get_rag_chain()
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        st.stop()

#The Chat Input and Processing (
    if prompt := st.chat_input("Ask about employee termination, etc."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt) # Show the user's question

        with st.chat_message("assistant"):
            with st.spinner("Searching..."):  # Show loading spinner
                try:
                    # THE MAGIC HAPPENS HERE:
                    response = rag_chain.invoke({"query": prompt})

                    # Show the AI's answer
                    st.markdown(response["result"])

                    # Show which documents were used
                    with st.expander("Show Sources"):
                        for doc in response["source_documents"]:
                            st.write(f"**Source:** {os.path.basename(doc.metadata.get('source', 'N/A'))}, Page: {doc.metadata.get('page', 'N/A')}")
                            st.write(f"> {doc.page_content[:250]}...") # Show first 250 characters

                            # Save the answer to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response["result"]})
                except Exception as e:
                    st.error("An error occurred. See details below.")
                    st.exception(e)  # Show detailed error

#App Launcher
if __name__ == '__main__':
    main()  # Start the app when  run this file
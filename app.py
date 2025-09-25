# app.py

import streamlit as st
import os
import sys
import dotenv
import chromadb
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from huggingface_hub import InferenceClient
from typing import Any, List, Mapping, Optional

# --- 1. DEFINE A CUSTOM, STABLE HUGGING FACE LLM CLASS ---
class CustomHuggingFaceLLM(LLM):
    """
    A custom LangChain LLM class that connects to the Hugging Face Inference API.
    This provides a stable interface, bypassing the rapidly changing official wrappers.
    """
    client: Optional[InferenceClient] = None
    repo_id: str = "mistralai/Mistral-7B-Instruct-v0.2"
    temperature: float = 0.5
    
    def __init__(self, api_token: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.client = InferenceClient(token=api_token)
    
    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "custom_huggingface"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        Makes a call to the Hugging Face Inference API using the chat_completion method.
        """
        try:
            # Format the prompt for a chat model
            messages = [{"role": "user", "content": prompt}]
            
            # Use the chat_completion method which we know works
            response = self.client.chat_completion(
                messages,
                model=self.repo_id,
                max_tokens=512,
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            # Add more detailed error logging
            st.error(f"Hugging Face API call failed: {e}")
            return f"Error: Could not get a response from the model. Details: {e}"

# --- 2. MAIN APPLICATION LOGIC ---
def main():
    st.set_page_config(page_title="AI Legal Adviser - Sri Lanka", page_icon="⚖️")
    st.title("⚖️ AI Legal Adviser for Sri Lanka")
    st.write("Ask questions about Sri Lankan law.")

    try:
        dotenv.load_dotenv()
        required_keys = ["HUGGINGFACEHUB_API_TOKEN", "CHROMA_TENANT", "CHROMA_DATABASE", "CHROMA_API_KEY"]
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            st.error(f"Missing required environment variables: {', '.join(missing_keys)}")
            st.stop()
    except Exception as e:
        st.error(f"Error loading environment variables: {e}")
        st.stop()

    @st.cache_resource
    def get_rag_chain():
        client = chromadb.CloudClient(
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE"),
            api_key=os.getenv("CHROMA_API_KEY")
        )
        vector_store = Chroma(client=client, collection_name='sri_lanka_legal')
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # Initialize our new, stable custom LLM
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

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    try:
        rag_chain = get_rag_chain()
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        st.stop()

    if prompt := st.chat_input("Ask about employee termination, etc."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                try:
                    response = rag_chain.invoke({"query": prompt})
                    st.markdown(response["result"])
                    with st.expander("Show Sources"):
                        for doc in response["source_documents"]:
                            st.write(f"**Source:** {os.path.basename(doc.metadata.get('source', 'N/A'))}, Page: {doc.metadata.get('page', 'N/A')}")
                            st.write(f"> {doc.page_content[:250]}...")
                    st.session_state.messages.append({"role": "assistant", "content": response["result"]})
                except Exception as e:
                    st.error("An error occurred. See details below.")
                    st.exception(e)

if __name__ == '__main__':
    main()
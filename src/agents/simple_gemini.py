# src/agents/simple_gemini.py
"""
Simple Gemini LLM wrapper that uses google-generativeai directly
This bypasses the langchain-google-genai issues we've been having
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from typing import Optional, List, Any

# Load environment variables
load_dotenv()

class SimpleGeminiLLM(LLM):
    """Simple Gemini LLM that uses google-generativeai directly"""
    
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.3
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Configure the API
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(self.model_name)
    
    @property
    def _llm_type(self) -> str:
        return "simple_gemini"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the Gemini API directly"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")
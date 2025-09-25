# test_hf_connection.py

import os
import dotenv
from huggingface_hub import InferenceClient

def run_test():
    """
    A simple, direct test of the Hugging Face Inference API connection.
    """
    print("--- Starting Hugging Face Connection Test ---")
    
    # 1. Load credentials
    dotenv.load_dotenv()
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    
    if not hf_token:
        print("❌ ERROR: HUGGINGFACEHUB_API_TOKEN not found in .env file.")
        return
        
    print("✅ Hugging Face token loaded successfully.")

    # 2. Initialize the client
    try:
        client = InferenceClient(token=hf_token)
        print("✅ Inference Client initialized.")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize the client: {e}")
        return

    # 3. Make a test API call
    model_to_test = "mistralai/Mistral-7B-Instruct-v0.2"
    prompt = "What is the capital of Sri Lanka?"
    
    print(f"\nAttempting to generate text with model: {model_to_test}...")
    print(f"Prompt: '{prompt}'")
    
    try:
        response = client.text_generation(prompt, model=model_to_test, max_new_tokens=20)
        print("\n--- ✅ SUCCESS! ---")
        print("Response from Hugging Face:")
        print(response)
        
    except Exception as e:
        print("\n--- ❌ FAILED! ---")
        print("An error occurred during the API call. This is the root cause.")
        print("Detailed Error:")
        print(e)

if __name__ == "__main__":
    run_test()
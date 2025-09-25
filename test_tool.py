# test_tool.py

from src.tools.lawyer_finder_tool import find_lawyer
import dotenv

def run_test():
    """
    A simple script to test the lawyer_finder_tool in isolation.
    """
    # Load environment variables (good practice, though not needed for this specific tool)
    dotenv.load_dotenv()
    
    print("--- 🧪 Starting test for Lawyer Finder Tool ---")
    
    # Define a sample search
    test_specialty = "Employment Law"
    test_location = "Colombo"
    
    print(f"Searching for lawyers with specialty: '{test_specialty}' in location: '{test_location}'")
    
    # Call the tool directly
    tool_input = {"specialty": test_specialty, "location": test_location}
    results = find_lawyer.invoke(tool_input)
    
    print("\n--- RESULTS ---")
    print(results)
    print("--- ✅ Test Finished ---")

# Run the test when the script is executed
if __name__ == "__main__":
    run_test()
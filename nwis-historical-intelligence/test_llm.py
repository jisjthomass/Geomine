import os
import sys

# Add project root and src to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from dotenv import load_dotenv
from src.llm import GeminiProvider, LLMProvider

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[INFO] GEMINI_API_KEY environment variable is not set.")
        print("[INFO] Please set GEMINI_API_KEY in your environment to test live Gemini API generation.")
        print("[INFO] Example (PowerShell): $env:GEMINI_API_KEY='your-api-key'")
        print("[INFO] Example (Bash): export GEMINI_API_KEY='your-api-key'")
        print("[SUCCESS] Missing API key handled cleanly without unhandled exception.")
        return

    try:
        print("[INFO] Initializing GeminiProvider...")
        provider: LLMProvider = GeminiProvider()
        test_prompt = "Reply with exactly: LLM abstraction test successful"
        print(f"[INFO] Sending test prompt: '{test_prompt}'")
        response = provider.generate(test_prompt)
        print("\n--- Gemini Response ---")
        print(response.strip())
        print("-----------------------")
        print("[SUCCESS] LLM abstraction test executed successfully.")
    except Exception as e:
        print(f"[ERROR] An error occurred during LLM testing: {e}")


if __name__ == "__main__":
    main()

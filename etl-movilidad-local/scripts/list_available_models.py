"""
List available Gemini models with your API key
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configure API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("="*70)
print("AVAILABLE GEMINI MODELS")
print("="*70)

try:
    models = genai.list_models()

    print("\nModels that support generateContent:\n")

    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"✓ {model.name}")
            print(f"  Display name: {model.display_name}")
            print(f"  Description: {model.description[:80]}...")
            print()

except Exception as e:
    print(f"Error listing models: {e}")

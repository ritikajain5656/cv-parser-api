import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY is missing in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# List available models
models = genai.list_models()
for m in models:
    print(m.name, "-", getattr(m, "description", "No description"))

import os
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY is missing in .env file")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    pdf = fitz.open(pdf_path)
    for page in pdf:
        text += page.get_text()
    pdf.close()
    return text

# Clean Gemini output to extract JSON
def clean_json(text):
    """
    Try to extract JSON from text returned by Gemini.
    If fails, wrap raw text in a 'raw_text' field.
    """
    try:
        # Try direct JSON parse
        return json.loads(text)
    except json.JSONDecodeError:
        # Remove any leading/trailing non-json characters
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # Fallback: return raw text
        return {"raw_text": text.strip()}

@app.get("/")
def read_root():
    return {"message": "PDF Extractor API (with Gemini) is running!"}

@app.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    try:
        # Save PDF temporarily
        pdf_path = f"temp_{file.filename}"
        with open(pdf_path, "wb") as buffer:
            buffer.write(await file.read())

        # Extract raw text
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text.strip():
            raise HTTPException(status_code=400, detail="PDF is empty or unreadable")

        # Prompt for Gemini
        prompt = f"""
Extract structured information from this PDF text:

{pdf_text}

Return JSON with this schema:
{{
  "name": "",
  "email": "",
  "phone": "",
  "skills": [],
  "experience": [],
  "education": []
}}
"""

        # Call Gemini
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        # Clean JSON safely
        result_json = clean_json(response.text)

        return {"result": result_json}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

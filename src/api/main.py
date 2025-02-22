from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from typing import Dict
from dotenv import load_dotenv
from ..data_processing.pipeline import DataProcessingPipeline
from ..ai_interface.gemini_chat import GeminiTutor
from ..data_processing.logger_config import setup_logger

# Load environment variables
load_dotenv()

app = FastAPI()
logger = setup_logger('api')

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pipeline = DataProcessingPipeline()

# Get API key from environment
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY environment variable is required")

tutor = GeminiTutor(
    gemini_api_key=gemini_api_key,
    pipeline=pipeline
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the file
        pipeline.process_file(file_path)
        
        # Clean up
        os.remove(file_path)
        
        return {"message": "File processed successfully"}
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(query: Dict[str, str]):
    try:
        response = await tutor.chat(query["text"])
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
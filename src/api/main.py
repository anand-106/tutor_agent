import os
import sys
import logging
import json
import traceback
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Document processing
import fitz  # PyMuPDF
import docx

# FastAPI
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

# Import our LangChain orchestrator
from src.ai_interface.langchain_orchestrator import LangChainOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger("api")

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Now use absolute imports instead of relative
from src.data_processing.pipeline import DataProcessingPipeline
from src.data_processing.logger_config import setup_logger
from src.ai_interface.agents import LessonPlanAgent

# Load environment variables
load_dotenv()

# Initialize logger first
logger = setup_logger('api')

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"

# Get API keys
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
]

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    # Add OpenAI key to the beginning of the API keys list
    GEMINI_API_KEYS.insert(0, OPENAI_API_KEY)

# Filter out None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not GEMINI_API_KEYS:
    logger.error("No API keys found in environment variables")
    raise ValueError("At least one API key is required")

def ensure_static_files():
    """Ensure static directory and files exist"""
    try:
        # Create directories
        STATIC_DIR.mkdir(exist_ok=True)
        UPLOAD_DIR.mkdir(exist_ok=True)
        
        # Create styles.css if it doesn't exist
        styles_path = STATIC_DIR / "styles.css"
        if not styles_path.exists():
            with open(styles_path, 'w', encoding='utf-8') as f:
                f.write("""
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 20px;
}

.upload-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chat-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    height: 80vh;
}

#chat-history {
    flex-grow: 1;
    overflow-y: auto;
    margin-bottom: 20px;
    padding: 10px;
    background: #f9f9f9;
    border-radius: 4px;
}

.chat-input {
    display: flex;
    gap: 10px;
}

input[type="text"] {
    flex-grow: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    padding: 10px 20px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background: #0056b3;
}

.message {
    margin: 10px 0;
    padding: 10px;
    border-radius: 4px;
}

.user-message {
    background: #e3f2fd;
    margin-left: 20%;
}

.ai-message {
    background: #f5f5f5;
    margin-right: 20%;
}
""")
            logger.info(f"Created {styles_path}")
        
        # Create script.js if it doesn't exist
        script_path = STATIC_DIR / "script.js"
        if not script_path.exists():
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write("""
// Add base URL configuration
const API_BASE_URL = window.location.origin;

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const chatHistory = document.getElementById('chat-history');
    const queryInput = document.getElementById('query-input');
    const sendButton = document.getElementById('send-button');

    console.log("Page loaded. API Base URL:", API_BASE_URL);
    console.log("Current location:", window.location.href);
    
    // Test API endpoints
    fetch(`${API_BASE_URL}/api/ping`)
        .then(response => response.json())
        .then(data => console.log("Ping test:", data))
        .catch(error => console.error("Ping test failed:", error));

    async function handleResponse(response) {
        try {
            const contentType = response.headers.get("content-type");
            console.log("Response:", {
                url: response.url,
                status: response.status,
                contentType: contentType
            });
            
            if (contentType && contentType.includes("application/json")) {
                const result = await response.json();
                console.log("Response data:", result);
                return result;
            } else {
                const text = await response.text();
                console.error("Unexpected response:", {
                    url: response.url,
                    status: response.status,
                    contentType,
                    text: text.substring(0, 500)
                });
                throw new Error(`Server error (${response.status}): ${text.substring(0, 100)}`);
            }
        } catch (error) {
            console.error("Response handling error:", error);
            throw error;
        }
    }

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const files = fileInput.files;
        if (files.length === 0) {
            uploadStatus.textContent = 'Please select files to upload';
            return;
        }

        uploadStatus.textContent = 'Uploading...';
        
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await handleResponse(response);
                
                if (!response.ok) {
                    throw new Error(result.detail || 'Upload failed');
                }
                
                uploadStatus.textContent = result.message || 'File uploaded successfully!';
                fileInput.value = '';
            } catch (error) {
                console.error("Upload error:", error);
                uploadStatus.textContent = `Error: ${error.message}`;
            }
        }
    });

    async function sendMessage() {
        const query = queryInput.value.trim();
        if (!query) return;

        addMessage(query, 'user');
        queryInput.value = '';

        try {
            const response = await fetch(`${API_BASE_URL}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: query })
            });

            const result = await handleResponse(response);
            
            if (!response.ok) {
                throw new Error(result.detail || 'Failed to get response');
            }

            addMessage(result.response, 'ai');
        } catch (error) {
            console.error("Chat error:", error);
            addMessage(`Error: ${error.message}`, 'ai');
        }
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = text;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    sendButton.addEventListener('click', sendMessage);
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
});
""")
            logger.info(f"Created {script_path}")
        
        logger.info("Static files check complete")
    except Exception as e:
        logger.error(f"Error ensuring static files: {str(e)}")
        raise

# Create FastAPI app
app = FastAPI()

# Call ensure_static_files after logger initialization
ensure_static_files()

# Configure CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

# Mount static files after middleware
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize components
pipeline = DataProcessingPipeline(
    use_pinecone=False,
    api_keys=GEMINI_API_KEYS  # Pass all API keys to pipeline
)

# Initialize the LangChain orchestrator
def get_api_keys():
    try:
        # Load the API keys from the .env file
        logger.info("Loading API keys from .env file")
        load_dotenv()
        
        # Get Gemini API keys
        keys = []
        i = 1
        while True:
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if not key:
                break
            keys.append(key)
            i += 1
        
        if not keys:
            logger.warning("No Gemini API keys found in .env file")
            raise ValueError("No API keys found in .env file. Please check your configuration.")
        
        logger.info(f"Successfully loaded {len(keys)} API keys")
        return keys
    except Exception as e:
        logger.error(f"Error loading API keys: {str(e)}")
        raise ValueError(f"Failed to load API keys: {str(e)}")

# Initialize the orchestrator
try:
    api_keys = get_api_keys()
    orchestrator = LangChainOrchestrator(api_keys)
    logger.info("LangChain orchestrator initialized successfully")
except Exception as e:
    logger.error(f"Error initializing LangChain orchestrator: {str(e)}")
    orchestrator = None
    
# Dictionary to store topics by user_id
topics_cache = {}

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            logger.error(f"index.html not found at {index_path}")
            return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)
        with open(index_path) as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)

@app.post("/api/upload")
async def upload_file(file: UploadFile):
    try:
        # Check if the orchestrator is initialized
        if not orchestrator:
            logger.error("Orchestrator not initialized")
            return ErrorResponse(message="The AI service is not available. Please try again later.")
        
        # Process the uploaded file
        logger.info(f"Received file upload: {file.filename}")
        
        # Save the uploaded file
        file_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File saved to {file_path}")
        
        # Extract text from the file
        text = extract_text_from_file(file_path)
        
        if not text:
            logger.warning(f"No text extracted from {file.filename}")
            return ErrorResponse(message="Could not extract text from the file.")
        
        # Extract topics from the text
        topics = extract_topics_from_text(text, orchestrator.topic_agent)
        
        if not topics:
            logger.warning("No topics extracted from the text")
            return ErrorResponse(message="Could not extract any topics from the file content.")
        
        # Set the topics in the orchestrator
        orchestrator.set_topics(topics)
        
        # Ensure topics is properly formatted for JSON response
        # Make a clean copy with validated types for the response
        sanitized_topics = []
        for topic in topics:
            sanitized_topic = {
                "title": str(topic.get("title", "Unknown Topic")),
                "content": str(topic.get("content", "")),
                "subtopics": []
            }
            
            # Process subtopics
            for subtopic in topic.get("subtopics", []):
                if isinstance(subtopic, dict):
                    sanitized_subtopic = {
                        "title": str(subtopic.get("title", "Unknown Subtopic")),
                        "content": str(subtopic.get("content", "")),
                    }
                    sanitized_topic["subtopics"].append(sanitized_subtopic)
            
            sanitized_topics.append(sanitized_topic)
        
        # Return success response with sanitized topics
        return {
            "message": "File processed successfully",
            "topics": sanitized_topics  # Return the sanitized list directly
        }
        
    except Exception as e:
        logger.error(f"Error processing uploaded file: {str(e)}")
        traceback.print_exc()
        return ErrorResponse(message=f"Error processing file: {str(e)}")

class DiagramRequest(BaseModel):
    text: str
    diagram_type: Optional[str] = "flowchart"  # flowchart, sequence, class, etc.

@app.post("/api/generate-diagram")
async def generate_diagram(request: DiagramRequest):
    try:
        # Extract diagram type and description from request
        diagram_type = request.diagram_type.lower()
        description = request.text

        # Generate Mermaid code based on the description and type
        if diagram_type == "flowchart":
            mermaid_code = f"""graph TD
    {description}"""
        elif diagram_type == "sequence":
            mermaid_code = f"""sequenceDiagram
    {description}"""
        elif diagram_type == "class":
            mermaid_code = f"""classDiagram
    {description}"""
        else:
            mermaid_code = description  # Use raw description if type not recognized

        return JSONResponse(content={"mermaid_code": mermaid_code})
    except Exception as e:
        logger.error(f"Error generating diagram: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate diagram"}
        )

def sanitize_response(response):
    """
    Sanitize the response to ensure no raw JSON or error messages are displayed to the user.
    
    Args:
        response: The response from the tutor agent
        
    Returns:
        Sanitized response that can be safely displayed to the user
    """
    logger.info(f"Sanitizing response type: {type(response)}")
    
    # Skip sanitization for flow responses
    if isinstance(response, dict) and response.get('teaching_mode') == 'dynamic_flow':
        logger.info("Skipping sanitization for dynamic_flow response")
        return response
    
    # If response is a string, check for JSON-like content
    if isinstance(response, str):
        if response.strip().startswith('{') and response.strip().endswith('}'):
            try:
                # Try to parse it as JSON
                parsed = json.loads(response)
                
                # If it's an error message or contains error indicators
                if 'error' in parsed or 'title' in parsed and ('error' in parsed.get('additional_notes', '').lower() or 'too short' in parsed.get('summary', '').lower()):
                    logger.warning("Detected error JSON in response, replacing with friendly message")
                    return {
                        "response": "I'm still processing this information. Could you please ask a more specific question or provide more details about what you'd like to learn?",
                        "teaching_mode": "exploratory"
                    }
                
                # If it's a normal JSON object, just return it
                return parsed
            except json.JSONDecodeError:
                # Not valid JSON, continue with normal processing
                pass
    
    # If it's a dictionary, check for JSON-like content in response field
    if isinstance(response, dict) and 'response' in response:
        # Skip sanitization for flow responses (additional check)
        if response.get('teaching_mode') == 'dynamic_flow':
            logger.info("Skipping response field sanitization for dynamic_flow")
            return response
            
        response_text = response['response']
        if isinstance(response_text, str):
            if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                try:
                    # Check if it's a JSON string that contains an error
                    parsed = json.loads(response_text)
                    if 'error' in parsed or 'title' in parsed and ('error' in parsed.get('additional_notes', '').lower() or 'too short' in parsed.get('summary', '').lower()):
                        logger.warning("Detected error JSON in response.response field, replacing with friendly message")
                        response['response'] = "I'm still processing this information. Could you please ask a more specific question or provide more details about what you'd like to learn?"
                except json.JSONDecodeError:
                    # If it contains JSON-like markers but isn't valid JSON
                    if "{'title':" in response_text or '{"title":' in response_text:
                        logger.warning("Detected JSON-like content in response.response field, replacing with friendly message")
                        response['response'] = "I'm still processing this information. Could you please ask a more specific question or provide more details about what you'd like to learn?"
    
    return response

# Chat request model
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    command_type: Optional[str] = None

# Error response model
class ErrorResponse(BaseModel):
    message: str

@app.post("/api/chat")
async def handle_chat(request: Request, message: ChatRequest):
    try:
        # Get the message content and user ID
        query = message.message
        user_id = message.user_id if message.user_id else "default_user"
        
        # Check if the orchestrator is initialized
        if not orchestrator:
            logger.error("Orchestrator not initialized")
            return ErrorResponse(message="The AI service is not available. Please try again later.")
        
        # Log the incoming message
        logger.info(f"Received chat message from user {user_id}: {query[:50]}...")
        
        # Check if message is empty
        if not query or query.strip() == "":
            logger.warning("Empty message received")
            return ErrorResponse(message="Please provide a message.")
        
        # Process the message using the orchestrator
        try:
            # Special handling for the "start flow" command
            if query.lower().strip() == "start flow":
                logger.info("Detected 'start flow' command")
                response = orchestrator.process(query, user_id=user_id)
            else:
                # Process regular messages
                response = orchestrator.process(query, user_id=user_id)
                
            # Sanitize the response to ensure it's JSON serializable
            response = _sanitize_json(response)
            
            # Check rate limits
            # (implementation stays the same)
            
            # Return the response
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            traceback.print_exc()
            return ErrorResponse(message=f"Error processing message: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        traceback.print_exc()
        return ErrorResponse(message="An unexpected error occurred.")

# Add debug route to check static file serving
@app.get("/debug/paths")
async def debug_paths():
    return {
        "base_dir": str(BASE_DIR),
        "static_dir": str(STATIC_DIR),
        "static_files": [str(f) for f in STATIC_DIR.glob("*") if f.is_file()],
        "upload_dir": str(UPLOAD_DIR)
    }

# Add CORS headers to all responses
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/test")
async def test():
    return JSONResponse(content={"status": "ok"})

@app.get("/debug/files")
async def debug_files():
    try:
        return {
            "base_dir": str(BASE_DIR),
            "static_dir": str(STATIC_DIR),
            "static_exists": STATIC_DIR.exists(),
            "static_files": [str(f.relative_to(STATIC_DIR)) for f in STATIC_DIR.glob("**/*") if f.is_file()],
            "current_dir": str(Path.cwd()),
            "upload_dir": str(UPLOAD_DIR),
            "upload_exists": UPLOAD_DIR.exists(),
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health")
async def health_check():
    try:
        # Get only actual routes, excluding static file mounts
        routes = [
            {"path": route.path, "methods": list(route.methods)} 
            for route in app.routes 
            if hasattr(route, 'methods')  # Skip mounted static files
        ]
        
        # Get static files separately
        static_files = [
            str(f.relative_to(STATIC_DIR)) 
            for f in STATIC_DIR.glob("**/*") 
            if f.is_file()
        ]
        
        return {
            "status": "ok",
            "routes": routes,
            "static_files": static_files,
            "static_dir_exists": STATIC_DIR.exists(),
            "static_dir_path": str(STATIC_DIR)
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e)
            }
        )

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

@app.get("/api/debug/request")
async def debug_request(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "cookies": dict(request.cookies),
    }

@app.get("/api/debug/static")
async def debug_static():
    try:
        files = {
            "index.html": (STATIC_DIR / "index.html").exists(),
            "styles.css": (STATIC_DIR / "styles.css").exists(),
            "script.js": (STATIC_DIR / "script.js").exists(),
            "test.html": (STATIC_DIR / "test.html").exists()
        }
        
        file_contents = {}
        for file_name in files:
            file_path = STATIC_DIR / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_contents[file_name] = f.read()[:100] + "..."  # First 100 chars
                except Exception as e:
                    file_contents[file_name] = f"Error reading file: {str(e)}"
            else:
                file_contents[file_name] = "File does not exist"
        
        return {
            "static_dir": str(STATIC_DIR),
            "files_exist": files,
            "file_previews": file_contents,
            "all_files": [str(f.relative_to(STATIC_DIR)) for f in STATIC_DIR.glob("**/*") if f.is_file()]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/topics")
async def get_all_topics():
    """Get topics structure for all processed files"""
    try:
        topics = pipeline.get_topics()
        
        # Log the topics for debugging
        logger.info(f"Topics cache contains keys: {list(topics.keys())}")
        
        # If topics is empty, return a helpful message
        if not topics:
            return JSONResponse(
                content={"message": "No topics available. Please upload a file first."},
                status_code=200
            )
        
        # If we have a current filename, use it for display
        if hasattr(pipeline, 'current_filename') and pipeline.current_filename:
            # Create a more user-friendly response
            formatted_topics = {}
            for key, value in topics.items():
                if key.startswith("current_document_"):
                    formatted_topics[pipeline.current_filename] = value
                else:
                    formatted_topics[key] = value
            
            return JSONResponse(
                content={"topics": formatted_topics},
                status_code=200
            )
            
        return JSONResponse(
            content={"topics": topics},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/topics/{file_path:path}")
async def get_file_topics(file_path: str):
    """Get topics structure for a specific file"""
    try:
        topics = pipeline.get_topics(file_path)
        return JSONResponse(
            content={"topics": topics},
            status_code=200
        )
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"No topics found for file: {file_path}"}
        )
    except Exception as e:
        logger.error(f"Error retrieving topics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/topics/{file_path:path}/{topic_path:path}")
async def get_topic_by_path(file_path: str, topic_path: str):
    """Get specific topic/subtopic using path"""
    try:
        # Convert topic path string to list (e.g., "chapter1/section2" -> ["chapter1", "section2"])
        path_parts = [p for p in topic_path.split("/") if p]
        
        topic = pipeline.get_topic_by_path(file_path, path_parts)
        return JSONResponse(
            content={"topic": topic},
            status_code=200
        )
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Topic path not found: {topic_path}"}
        )
    except Exception as e:
        logger.error(f"Error retrieving topic: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.post("/api/select-file")
async def select_file(file_data: Dict[str, str]):
    try:
        file_path = file_data.get("file_path")
        if not file_path:
            return JSONResponse(
                status_code=400,
                content={"detail": "No file path provided"}
            )
            
        # Check if we have topics for this file
        if file_path not in pipeline.topics_cache:
            return JSONResponse(
                status_code=404,
                content={"detail": f"File not found: {file_path}"}
            )
            
        # Get the topics and set them in the orchestrator
        topics = pipeline.get_topics(file_path)
        if topics and 'topics' in topics:
            orchestrator.set_topics(topics['topics'])
        
        return JSONResponse(
            content={"message": f"Selected file: {file_path}"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error selecting file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/files")
async def get_files():
    """Get list of all processed files"""
    try:
        files = list(pipeline.topics_cache.keys())
        return JSONResponse(
            content={"files": files},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving files: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/debug/topics-cache")
async def debug_topics_cache():
    """Debug endpoint to check the state of the topics cache"""
    try:
        return {
            "topics_cache_keys": list(pipeline.topics_cache.keys()),
            "topics_cache_size": len(pipeline.topics_cache),
            "shared_state": orchestrator.get_shared_state()
        }
    except Exception as e:
        logger.error(f"Error in debug topics cache: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Add these new models after the existing BaseModel classes
class UserInteractionRequest(BaseModel):
    user_id: str
    interaction_type: str
    topic: Optional[str] = None
    duration_minutes: Optional[int] = None
    score: Optional[int] = None
    questions: Optional[List[Dict]] = None
    cards_reviewed: Optional[int] = None
    correct_recalls: Optional[int] = None
    view_duration_seconds: Optional[int] = None

# Add these new endpoints after the existing endpoints
@app.post("/api/user/track")
async def track_user_interaction(request: UserInteractionRequest):
    """Track user interaction and update knowledge model"""
    try:
        interaction_data = {
            "type": request.interaction_type,
            "topic": request.topic,
        }
        
        # Add optional fields based on interaction type
        if request.interaction_type == "quiz_result" and request.score is not None:
            interaction_data["score"] = request.score
            interaction_data["questions"] = request.questions or []
            
        elif request.interaction_type == "study_session" and request.duration_minutes is not None:
            interaction_data["duration_minutes"] = request.duration_minutes
            
        elif request.interaction_type == "flashcard_review":
            interaction_data["cards_reviewed"] = request.cards_reviewed or 0
            interaction_data["correct_recalls"] = request.correct_recalls or 0
            
        elif request.interaction_type == "topic_view":
            interaction_data["view_duration_seconds"] = request.view_duration_seconds or 0
        
        # Use the orchestrator's track_interaction method
        orchestrator._track_interaction(request.user_id, request.interaction_type, request.topic, interaction_data)
        
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.error(f"Error tracking user interaction: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/user/{user_id}/knowledge")
async def get_user_knowledge_summary(user_id: str):
    """Get a summary of the user's knowledge across all topics"""
    try:
        # Get knowledge data from the shared state
        shared_state = orchestrator.get_shared_state()
        progress = shared_state.get("progress", {}).get(user_id, {})
        
        # Ensure we're not passing null values where strings are expected
        # Create a sanitized version of the progress dictionary
        sanitized_progress = {}
        for topic_key, topic_data in progress.items():
            if topic_key is None:
                continue  # Skip null keys
            
            sanitized_topic = {}
            for k, v in topic_data.items():
                if k is None or v is None:
                    continue  # Skip null keys or values
                sanitized_topic[k] = v
            
            # Only add the topic if it has data
            if sanitized_topic:
                sanitized_progress[topic_key] = sanitized_topic
        
        return JSONResponse(
            content={"knowledge_summary": sanitized_progress},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting user knowledge summary: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/user/{user_id}/topic/{topic}")
async def get_topic_progress(user_id: str, topic: str):
    """Get detailed progress for a specific topic"""
    try:
        # Get topic progress from the shared state
        shared_state = orchestrator.get_shared_state()
        progress = shared_state.get("progress", {}).get(user_id, {}).get(topic, {})
        
        # Sanitize the progress data to remove null values
        sanitized_progress = {}
        for k, v in progress.items():
            if k is None:
                continue  # Skip null keys
                
            # Handle nested dictionaries
            if isinstance(v, dict):
                sanitized_v = {}
                for sub_k, sub_v in v.items():
                    if sub_k is not None and sub_v is not None:
                        sanitized_v[sub_k] = sub_v
                if sanitized_v:
                    sanitized_progress[k] = sanitized_v
            # Handle non-null values
            elif v is not None:
                sanitized_progress[k] = v
        
        return JSONResponse(
            content={"topic_progress": sanitized_progress},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting topic progress: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/api/user/{user_id}/patterns")
async def analyze_learning_patterns(user_id: str):
    """Analyze learning patterns and provide insights"""
    try:
        # For now, return a simplified response
        return JSONResponse(
            content={
                "learning_patterns": {
                    "status": "Data collection in progress",
                    "message": "More data needed for meaningful patterns"
                }
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error analyzing learning patterns: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# Add these new models for lesson plan requests
class LessonPlanRequest(BaseModel):
    user_id: str
    topic: str
    knowledge_level: float = Field(..., ge=0, le=100)
    subtopics: Optional[List[Dict[str, Any]]] = None
    time_available: Optional[int] = 60

class CurriculumRequest(BaseModel):
    user_id: str
    topics: List[Dict[str, Any]]
    total_time_available: Optional[int] = 600

# Add these new endpoints
@app.post("/api/generate-lesson-plan")
async def generate_lesson_plan(request: LessonPlanRequest):
    """Generate a personalized lesson plan for a specific topic"""
    try:
        # Initialize the lesson plan agent
        lesson_plan_agent = LessonPlanAgent(GEMINI_API_KEYS)
        
        # Generate the lesson plan
        lesson_plan = lesson_plan_agent.process(
            user_id=request.user_id,
            topic=request.topic,
            knowledge_level=request.knowledge_level,
            subtopics=request.subtopics,
            time_available=request.time_available
        )
        
        return lesson_plan
    except Exception as e:
        logger.error(f"Error generating lesson plan: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson plan: {str(e)}")

@app.post("/api/generate-curriculum")
async def generate_curriculum(request: CurriculumRequest):
    """Generate a comprehensive curriculum covering multiple topics"""
    try:
        # Initialize the lesson plan agent
        lesson_plan_agent = LessonPlanAgent(GEMINI_API_KEYS)
        
        # Generate the curriculum
        curriculum = lesson_plan_agent.generate_curriculum(
            user_id=request.user_id,
            topics=request.topics,
            total_time_available=request.total_time_available
        )
        
        return curriculum
    except Exception as e:
        logger.error(f"Error generating curriculum: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate curriculum: {str(e)}")

# Helper function to sanitize responses for JSON serialization
def _sanitize_json(obj):
    if isinstance(obj, dict):
        # Create a new dict with only non-null keys and sanitized values
        result = {}
        for k, v in obj.items():
            if k is not None:  # Skip null keys
                sanitized_value = _sanitize_json(v)
                if sanitized_value is not None:  # Skip null values
                    result[k] = sanitized_value
        return result
    elif isinstance(obj, list):
        # Create a new list with sanitized non-null values
        return [_sanitize_json(item) for item in obj if item is not None]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Convert other types to string
        return str(obj)

# Function to extract text from various file types
def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Extract text from various file types (PDF, DOCX, TXT)
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text or None if extraction failed
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # PDF extraction
        if file_ext == '.pdf':
            try:
                text = ""
                with fitz.open(file_path) as pdf:
                    for page in pdf:
                        text += page.get_text()
                return text
            except Exception as e:
                logger.error(f"Error extracting text from PDF: {str(e)}")
                return None
                
        # DOCX extraction
        elif file_ext == '.docx':
            try:
                doc = docx.Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logger.error(f"Error extracting text from DOCX: {str(e)}")
                return None
                
        # TXT files
        elif file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading TXT file: {str(e)}")
                return None
                
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return None
            
    except Exception as e:
        logger.error(f"Error in extract_text_from_file: {str(e)}")
        return None

# Function to extract topics from text
def extract_topics_from_text(text: str, topic_agent) -> List[Dict[str, Any]]:
    """
    Extract topics from text using the topic agent
    
    Args:
        text: Text to extract topics from
        topic_agent: Agent for topic extraction
        
    Returns:
        List of topics with hierarchical structure
    """
    try:
        logger.info("Extracting topics from text")
        
        # Check if text is too long and truncate if necessary
        if len(text) > 50000:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 50000 chars")
            text = text[:50000]
            
        # Process the text with the topic agent
        result = topic_agent.process(text)
        
        # Check if the result contains topics
        if isinstance(result, dict) and "topics" in result:
            topics = result["topics"]
            logger.info(f"Extracted {len(topics)} topics")
            return topics
        else:
            logger.warning("Topic agent did not return expected format")
            # Try to create a basic topic structure
            return [{
                "title": "Document Content",
                "content": text[:1000] + "...",  # Include a preview of the content
                "subtopics": []
            }]
            
    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        traceback.print_exc()
        return [] 
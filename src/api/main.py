from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
import os
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv
from pathlib import Path
import sys
from pydantic import BaseModel, Field

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Now use absolute imports instead of relative
from src.data_processing.pipeline import DataProcessingPipeline
from src.ai_interface.gemini_chat import GeminiTutor
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

# Filter out None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not GEMINI_API_KEYS:
    logger.error("No GEMINI API keys found in environment variables")
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

tutor = GeminiTutor(
    api_keys=GEMINI_API_KEYS,
    pipeline=pipeline
)

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

@app.post("/api/upload")  # Changed route to /api/upload
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        # Check file extension
        allowed_extensions = {'.pdf', '.docx', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        file_path = UPLOAD_DIR / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Use a consistent key for the topics cache
            consistent_key = f"current_document_{file.filename}"
            pipeline.process_file(str(file_path), metadata={"consistent_key": consistent_key})
            
            # Set this as the current file for the tutor
            tutor.set_current_file(consistent_key)
            
            # Store the original filename for reference
            pipeline.current_filename = file.filename
        finally:
            if file_path.exists():
                file_path.unlink()
        
        return JSONResponse(
            content={"message": "File processed successfully"},
            status_code=200
        )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": str(e.detail)}
        )
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

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

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        message = data.get('text')
        if not message:
            raise HTTPException(status_code=400, detail="No message provided")
            
        # Get relevant content from vector store
        results = pipeline.search_content(message, top_k=3)
        
        # Format the context from search results
        context = ""
        if isinstance(results, dict) and 'documents' in results:
            # ChromaDB results
            documents = results['documents']
            if documents and isinstance(documents, list):
                if documents and isinstance(documents[0], list):
                    documents = [doc for sublist in documents for doc in sublist]
                context = "\n\n".join(documents)
        
        # Generate response using context
        response = tutor.chat(message, context=context)
        
        # Check if this is a diagram response
        if "```mermaid" in response:
            try:
                # Extract the explanation and diagram code
                parts = response.split("```mermaid")
                explanation = parts[0].strip()
                mermaid_code = parts[1].split("```")[0].strip()
                
                # Determine diagram type
                diagram_type = "flowchart"  # default
                if mermaid_code.startswith("classDiagram"):
                    diagram_type = "class"
                elif mermaid_code.startswith("sequenceDiagram"):
                    diagram_type = "sequence"
                
                logger.info(f"Generated diagram of type: {diagram_type}")
                logger.info(f"Mermaid code: {mermaid_code}")
                
                return JSONResponse(content={
                    "response": response,
                    "has_diagram": True,
                    "mermaid_code": mermaid_code,
                    "diagram_type": diagram_type,
                    "explanation": explanation
                })
            except Exception as diagram_error:
                logger.error(f"Error processing diagram: {str(diagram_error)}")
                # Fall back to regular response if diagram processing fails
                pass
        
        # Return response with appropriate status
        if "rate limit" in response.lower() or "quota" in response.lower():
            return JSONResponse(
                content={"response": response},
                status_code=429  # Too Many Requests
            )
        return JSONResponse(content={"response": response, "has_diagram": False})
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"response": "An error occurred. Please try again later."}
        )

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
            
        # Set as current file
        tutor.set_current_file(file_path)
        
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
            "current_file": tutor.current_file
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
        
        result = tutor.track_user_interaction(request.user_id, interaction_data)
        return JSONResponse(content=result, status_code=200)
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
        result = tutor.get_user_knowledge_summary(user_id)
        return JSONResponse(content=result, status_code=200)
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
        result = tutor.get_topic_progress(user_id, topic)
        return JSONResponse(content=result, status_code=200)
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
        result = tutor.analyze_learning_patterns(user_id)
        return JSONResponse(content=result, status_code=200)
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
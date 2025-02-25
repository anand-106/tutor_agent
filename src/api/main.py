from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
import os
from typing import Dict
from dotenv import load_dotenv
from pathlib import Path
from ..data_processing.pipeline import DataProcessingPipeline
from ..ai_interface.gemini_chat import GeminiTutor
from ..data_processing.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Initialize logger first
logger = setup_logger('api')

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"

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
pipeline = DataProcessingPipeline(use_pinecone=False)
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY environment variable is required")

tutor = GeminiTutor(
    gemini_api_key=gemini_api_key,
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
            pipeline.process_file(str(file_path))
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

@app.post("/api/chat")  # Changed route to /api/chat
async def chat(query: Dict[str, str]):
    try:
        if not query.get("text"):
            return JSONResponse(
                status_code=400,
                content={"detail": "No query text provided"}
            )
            
        response = tutor.chat(query["text"])
        return JSONResponse(
            content={"response": response},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
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
import uvicorn
from pathlib import Path

if __name__ == "__main__":
    # Ensure we're in the project root directory
    project_root = Path(__file__).resolve().parent
    
    # Change to project root directory
    import os
    os.chdir(project_root)
    
    # Run the server
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True) 
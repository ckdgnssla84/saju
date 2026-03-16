from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from calculator import SajuCalculator
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

calculator = SajuCalculator()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCbTZD1m3RHMo-k-zC493Ug6pVr_OavTmg"
model = None
if GEMINI_API_KEY and "AIza" in GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        pass

class CalculateRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str = "male"

class ChatRequest(BaseModel):
    message: str
    saju_data: dict = None

# --- API ---
@app.post("/api/calculate")
async def calculate_saju(req: CalculateRequest):
    try:
        return calculator.compute(req.year, req.month, req.day, req.hour, req.minute, req.gender)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_fortune_teller(req: ChatRequest):
    if not model or not req.saju_data:
        return {"response": "상담을 위해 먼저 사주를 분석해주세요."}
    try:
        response = model.generate_content(f"Saju: {req.saju_data}. User: {req.message}")
        return {"response": response.text}
    except Exception as e:
        return {"response": f"오류: {str(e)}"}

# --- FRONTEND SERVING (The fix for blank screen) ---
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"

if static_dir.exists():
    # 1. Mount assets folder specifically
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # 2. Serve static files (favicon, etc)
    @app.get("/{file_path:path}")
    async def serve_static(file_path: str):
        # If the requested path exists as a file in static_dir, serve it
        full_path = static_dir / file_path
        if full_path.is_file():
            return FileResponse(full_path)
        
        # If it's an API call we missed, return 404
        if file_path.startswith("api/"):
            return {"error": "Not Found"}
            
        # Otherwise, always serve index.html (for React Router)
        return FileResponse(static_dir / "index.html")

    @app.get("/")
    async def root():
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def no_frontend():
        return {"message": "Backend OK, but Frontend files are missing."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

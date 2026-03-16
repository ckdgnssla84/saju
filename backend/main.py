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

# --- 1. API ---
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
        return {"response": f"AI Error: {str(e)}"}

# --- 2. FRONTEND (The Bulletproof Fix) ---
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"

if static_dir.exists():
    # Serve assets first with highest priority
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Catch-all for other static files and index.html
    @app.get("/{rest_of_path:path}")
    async def serve_frontend(rest_of_path: str):
        # 1. If requesting a specific file like favicon.svg
        file_path = static_dir / rest_of_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # 2. Always fallback to index.html for React Router / Blank page fix
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def no_static():
        return {"message": "Static folder not found at " + str(static_dir)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

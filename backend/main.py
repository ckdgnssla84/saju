from fastapi import FastAPI, HTTPException, Request
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

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

calculator = SajuCalculator()

# Gemini Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCbTZD1m3RHMo-k-zC493Ug6pVr_OavTmg"
model = None
if GEMINI_API_KEY and "AIza" in GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Gemini Error: {e}")

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

# 1. API ROUTES (MUST COME BEFORE STATIC FILES)
@app.post("/api/calculate")
async def calculate_saju(req: CalculateRequest):
    try:
        result = calculator.compute(req.year, req.month, req.day, req.hour, req.minute, req.gender)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_fortune_teller(req: ChatRequest):
    user_msg = req.message
    saju = req.saju_data
    if not saju: return {"response": "사주 데이터가 없습니다."}
    
    context = f"User Saju: {saju}. Ask: {user_msg}. Act as Saju expert."
    if model:
        try:
            response = model.generate_content(context)
            return {"response": response.text}
        except Exception as e:
            return {"response": f"AI Error: {str(e)}"}
    return {"response": "Mock Response"}

# 2. STATIC FILES (MOUNT AT THE VERY END)
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"

if static_dir.exists():
    # Use standard mount for files
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    
    # Catch-all for React index.html
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"): # Prevent API hijacking
             return None 
        index_path = static_dir / "index.html"
        return FileResponse(index_path)
    
    @app.get("/")
    async def serve_root():
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def no_static():
        return {"error": "Frontend static files not found"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

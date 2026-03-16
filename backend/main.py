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

# CORS Setup - Flexible for deployment
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
        print("Gemini API Configured (gemini-1.5-flash)")
    except Exception as e:
        print(f"Gemini Config Error: {e}")
else:
    print("Gemini API Key NOT FOUND. Running in mock mode.")

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

@app.post("/api/calculate")
def calculate_saju(req: CalculateRequest):
    try:
        result = calculator.compute(req.year, req.month, req.day, req.hour, req.minute, req.gender)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_fortune_teller(req: ChatRequest):
    user_msg = req.message
    saju = req.saju_data
    
    if not saju:
        return {"response": "먼저 분석 시작 버튼을 눌러주세요."}

    context = f"""
    User's Saju Chart:
    - Year: {saju['year']['ganji']} ({saju['year']['element']})
    - Month: {saju['month']['ganji']} ({saju['month']['element']})
    - Day: {saju['day']['ganji']} ({saju['day']['element']}) - This is the Day Master (The User).
    - Hour: {saju['hour']['ganji']} ({saju['hour']['element']})
    
    The user asks: "{user_msg}"
    
    Act as a wise, mystical Korean Fortune Teller. 
    Interpret the user's question based on their Day Master ({saju['day']['element']}) and the overall balance of elements.
    Use polite but mystical Korean language.
    """

    if model:
        try:
            response = model.generate_content(context)
            return {"response": response.text}
        except Exception as e:
            return {"response": f"AI 통신 오류 발생: {str(e)}"}
    else:
        day_master = saju.get('day', {}).get('element', 'Unknown')
        return {"response": f"[Mock Mode] 당신은 {day_master}의 기운을 타고났습니다."}

# ---------------------------------------------------------------------
# Static File Hosting (Server Frontend from the same domain)
# ---------------------------------------------------------------------
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Fallback to index.html for any frontend routes (SPA)
        return FileResponse(static_dir / "index.html")
else:
    @app.get("/")
    def read_root():
        return {"message": "Saju API is running (Static folder not found)"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

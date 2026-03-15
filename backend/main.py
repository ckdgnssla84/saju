from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from calculator import SajuCalculator
import os
from dotenv import load_dotenv
import google.generativeai as genai

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

app = FastAPI()

# CORS Setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Changed to False for "*" compatibility
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
        # Find first available model that supports generateContent
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"Available Models: {available_models}")
        
        # Pick best one
        if 'models/gemini-1.5-flash' in available_models:
            target_model = 'models/gemini-1.5-flash'
        elif 'models/gemini-pro' in available_models:
            target_model = 'models/gemini-pro'
        else:
            target_model = available_models[0] if available_models else None
            
        if target_model:
            model = genai.GenerativeModel(target_model)
            print(f"Gemini API Configured! Using model: {target_model}")
    except Exception as e:
        print(f"Gemini Config Error: {e}")
else:
    print("Gemini API Key NOT FOUND. Using mock mode.")

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

@app.get("/")
def read_root():
    return {"message": "Saju API is running"}

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
    
    # Construct Context
    context = ""
    if saju:
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
    else:
        context = f"User asks: {user_msg}. Act as a Korean Fortune Teller."

    if model:
        try:
            response = model.generate_content(context)
            return {"response": response.text}
        except Exception as e:
            print(f"GenAI Error Trace: {e}")
            # Show actual error for debugging
            return {"response": f"AI 통신 오류 발생: {str(e)}"}
    else:
        # Mock Response
        if saju:
            day_master = saju.get('day', {}).get('element', 'Unknown')
            return {"response": f"[Mock Mode] 당신은 {day_master}의 기운을 타고났습니다. '{user_msg}'에 대한 답변은 AI 키를 설정하면 들을 수 있습니다."}
        else:
            return {"response": "[Mock Mode] 사주 정보가 없습니다."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

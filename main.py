"""
API du module IA - assistant réparation/vente de téléphones.

Lancer en local :
    pip install -r requirements.txt
    export LLM_API_KEY=sk-...
    uvicorn main:app --reload

Endpoints :
    POST /chat            -> question texte (FR/AR/EN)
    POST /diagnose-image   -> photo -> panne + estimation de coût
    POST /diagnose-video   -> vidéo -> panne + transcription + réponse
"""
from dotenv import load_dotenv
load_dotenv()  # charge le fichier .env s'il existe, avant tout le reste

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from app.chat_service import ask_chatbot
from app.vision_service import classify_damage
from app.pricing_service import estimate_repair_cost
from app.video_service import analyze_video
from app.voice_service import answer_voice_question

app = FastAPI(title="Assistant Réparation & Vente iPhone - Module IA")


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None


@app.post("/chat")
def chat(req: ChatRequest):
    return ask_chatbot(req.message, req.history)


@app.post("/diagnose-image")
async def diagnose_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    diagnosis = classify_damage(image_bytes)
    pricing = estimate_repair_cost(
        diagnosis.get("damage_type", "aucun_dommage_visible"),
        diagnosis.get("severity", "inconnu"),
        diagnosis.get("device_model_guess", "inconnu"),
        diagnosis.get("is_iphone", True),
    )
    return {"diagnosis": diagnosis, "pricing": pricing}


@app.post("/ask-voice")
async def ask_voice(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    return answer_voice_question(audio_bytes, filename=file.filename or "question.mp3")


@app.post("/diagnose-video")
async def diagnose_video(file: UploadFile = File(...)):
    video_bytes = await file.read()
    result = analyze_video(video_bytes)

    diagnosis = result.get("visual_diagnosis", {})
    pricing = estimate_repair_cost(
        diagnosis.get("damage_type", "aucun_dommage_visible"),
        diagnosis.get("severity", "inconnu"),
        diagnosis.get("device_model_guess", "inconnu"),
        diagnosis.get("is_iphone", True),
    )
    result["pricing"] = pricing
    return result


@app.get("/health")
def health():
    return {"status": "ok"}
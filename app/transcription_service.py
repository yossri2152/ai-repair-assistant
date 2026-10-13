"""
Transcription audio partagée, utilisée par video_service.py (audio extrait
d'une vidéo) et par l'endpoint /ask-voice (question posée à l'oral).

Utilise Groq (gratuit) plutôt qu'OpenAI Whisper — voir video_service.py
pour le détail du choix.
"""
import os
import requests
from fastapi import HTTPException

WHISPER_API_KEY = os.getenv("WHISPER_API_KEY", "")
WHISPER_API_URL = os.getenv("WHISPER_API_URL", "https://api.groq.com/openai/v1/audio/transcriptions")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3")


def transcribe_audio(audio_path: str) -> str:
    if not WHISPER_API_KEY:
        return "[DEMO - WHISPER_API_KEY non configurée, transcription non disponible]"

    try:
        with open(audio_path, "rb") as f:
            response = requests.post(
                WHISPER_API_URL,
                headers={"Authorization": f"Bearer {WHISPER_API_KEY}"},
                files={"file": f},
                data={"model": WHISPER_MODEL},
                timeout=60,
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Impossible de contacter l'API de transcription: {e}")

    if response.status_code != 200:
        try:
            error_detail = response.json()
        except ValueError:
            error_detail = response.text
        raise HTTPException(
            status_code=502,
            detail=f"L'API de transcription a renvoyé une erreur ({response.status_code}): {error_detail}",
        )

    return response.json().get("text", "")
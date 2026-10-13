"""
Permet à un client de poser sa question à l'oral (fichier audio : message
vocal WhatsApp, note vocale enregistrée sur le site, etc.) plutôt qu'à
l'écrit. Réutilise la transcription (Groq) et le chatbot existants —
aucune nouvelle IA à entraîner.
"""
import os
import tempfile

from app.transcription_service import transcribe_audio
from app.chat_service import ask_chatbot


def answer_voice_question(audio_bytes: bytes, filename: str = "question.mp3") -> dict:
    """
    audio_bytes: contenu brut du fichier audio envoyé par le client
    Retourne {"transcript": str, "answer": str, "language": str}
    """
    suffix = os.path.splitext(filename)[1] or ".mp3"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        transcript = transcribe_audio(tmp_path)
    finally:
        os.remove(tmp_path)

    if not transcript.strip() or transcript.startswith("[DEMO"):
        return {
            "transcript": transcript,
            "answer": None,
            "language": None,
        }

    chat_result = ask_chatbot(transcript)

    return {
        "transcript": transcript,
        "answer": chat_result["answer"],
        "language": chat_result["language"],
    }
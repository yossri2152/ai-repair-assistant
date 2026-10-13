"""
Traitement d'une vidéo envoyée par le client (ex: il filme le téléphone
qui ne charge pas, ou décrit le problème à voix haute).

Approche réaliste (pas de modèle vidéo maison) :
 1. Extraire quelques frames clés -> réutiliser vision_service.classify_damage
 2. Extraire l'audio -> le transcrire (Whisper via Groq, gratuit) -> réutiliser chat_service
 3. Combiner les deux résultats

Les deux pipelines (1 et 2) tournent EN PARALLÈLE dans deux threads, car
chacun passe le plus clair de son temps à attendre ffmpeg (sous-processus)
ou une réponse réseau (API) — donc pas besoin de code async, les threads
suffisent et c'est beaucoup plus simple à maintenir.

Nécessite ffmpeg installé sur la machine (voir README pour Windows/Mac/Linux).

Transcription audio : Gemini (utilisé pour le chat/vision) n'expose pas
d'endpoint de transcription compatible OpenAI. On utilise donc Groq, qui
propose Whisper gratuitement (compte séparé, toujours sans carte bancaire).
"""
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import imageio_ffmpeg
from fastapi import HTTPException

from app.vision_service import classify_damage
from app.chat_service import ask_chatbot
from app.transcription_service import transcribe_audio

# Binaire ffmpeg embarqué par imageio-ffmpeg : pas besoin d'installation
# système ni de configurer le PATH (utile sur Windows).
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

NUM_FRAMES = 3  # nombre d'images clés à extraire pour rester léger

SEVERITY_ORDER = {"leger": 1, "moyen": 2, "grave": 3, "inconnu": 0}


def _run_ffmpeg(args: list[str], step_name: str):
    try:
        subprocess.run([FFMPEG_BIN, *args], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Échec ffmpeg ({step_name}): {e.stderr.decode(errors='ignore')[:300]}",
        )


def _extract_frames(video_path: str, out_dir: str) -> list[str]:
    """Extrait NUM_FRAMES images réparties sur la vidéo."""
    pattern = os.path.join(out_dir, "frame_%02d.jpg")
    _run_ffmpeg(
        ["-i", video_path, "-vf", "fps=1/2", "-frames:v", str(NUM_FRAMES), pattern, "-y"],
        "extraction des images",
    )
    return sorted(
        os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("frame_")
    )


def _extract_audio(video_path: str, out_path: str) -> str:
    _run_ffmpeg(
        ["-i", video_path, "-vn", "-acodec", "mp3", out_path, "-y"],
        "extraction audio",
    )
    return out_path


def _process_visual(video_path: str, out_dir: str) -> dict:
    """Pipeline 1 : frames -> diagnostic visuel (on garde le pire des 3)."""
    frame_paths = _extract_frames(video_path, out_dir)
    frame_diagnoses = [
        classify_damage(open(fp, "rb").read()) for fp in frame_paths
    ]
    return max(
        frame_diagnoses,
        key=lambda d: SEVERITY_ORDER.get(d.get("severity", "inconnu"), 0),
        default={},
    )


def _process_audio(video_path: str, out_dir: str) -> dict:
    """Pipeline 2 : audio -> transcription -> réponse du chatbot."""
    audio_path = _extract_audio(video_path, os.path.join(out_dir, "audio.mp3"))
    transcript = transcribe_audio(audio_path)
    chat_result = ask_chatbot(transcript) if transcript.strip() and not transcript.startswith("[DEMO") else None
    return {"transcript": transcript, "chat_result": chat_result}


def analyze_video(video_bytes: bytes) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "input.mp4")
        with open(video_path, "wb") as f:
            f.write(video_bytes)

        # Les deux pipelines lisent le même fichier vidéo en lecture seule
        # et écrivent dans des fichiers distincts (frame_*.jpg vs audio.mp3)
        # -> aucun conflit, on peut les lancer vraiment en parallèle.
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_visual = executor.submit(_process_visual, video_path, tmp)
            future_audio = executor.submit(_process_audio, video_path, tmp)

            # .result() relève toute exception survenue dans le thread
            # (y compris une HTTPException ffmpeg/API) côté thread principal
            visual_result = future_visual.result()
            audio_result = future_audio.result()

    return {
        "visual_diagnosis": visual_result,
        "audio_transcript": audio_result["transcript"],
        "chatbot_reply": audio_result["chat_result"],
    }
"""
Service de chat texte multilingue.
Appelle une API compatible Anthropic/OpenAI/Mistral.
Le RAG (recherche dans le catalogue/tarifs du commerçant) est
volontairement laissé en placeholder — à brancher sur pgvector
ou Pinecone une fois que vous avez un vrai catalogue (voir Étape 2
du plan initial).
"""
import os
import requests
from fastapi import HTTPException
from app.language import detect_language, SYSTEM_PROMPTS

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")


def retrieve_context(question: str) -> str:
    """
    TODO (Étape 2 du plan) : remplacer par une vraie recherche
    vectorielle dans le catalogue / les tarifs du commerçant.
    Pour l'instant, renvoie un contexte statique d'exemple.
    """
    return (
        "Tarifs indicatifs : écran iPhone 60-120 DT, batterie 40-70 DT, "
        "port de charge 30-50 DT. Délai moyen : 24 à 48h. "
        "Horaires : Lun-Sam 9h-18h."
    )


def _sanitize_history(history: list[dict] | None) -> list[dict]:
    """Ignore les entrées mal formées (ex: {} envoyé par erreur depuis /docs)."""
    if not history:
        return []
    return [
        h for h in history
        if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content")
    ]


def ask_chatbot(question: str, history: list[dict] | None = None) -> dict:
    """
    question: message du client
    history: liste de {"role": "user"/"assistant", "content": "..."}
    Retourne {"answer": str, "language": str}
    """
    lang = detect_language(question)
    system_prompt = SYSTEM_PROMPTS[lang]
    context = retrieve_context(question)

    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nContexte boutique:\n{context}"}
    ]
    messages.extend(_sanitize_history(history))
    messages.append({"role": "user", "content": question})

    if not LLM_API_KEY:
        # Mode démo sans clé API, pour tester le squelette
        return {
            "answer": "[DEMO - pas de clé API configurée] " + context,
            "language": lang,
        }

    try:
        response = requests.post(
            LLM_API_URL,
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={"model": LLM_MODEL, "messages": messages, "max_tokens": 500},
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Impossible de contacter l'API LLM: {e}")

    if response.status_code != 200:
        # Renvoie le vrai message d'erreur de l'API (clé invalide, quota, modèle inconnu...)
        try:
            error_detail = response.json()
        except ValueError:
            error_detail = response.text
        raise HTTPException(
            status_code=502,
            detail=f"L'API LLM a renvoyé une erreur ({response.status_code}): {error_detail}",
        )

    data = response.json()
    answer = data["choices"][0]["message"]["content"]

    return {"answer": answer, "language": lang}
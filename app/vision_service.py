"""
Diagnostic de panne à partir d'une photo.

Approche réaliste pour un MVP solo : on n'entraîne PAS un CNN maison
(il faudrait des milliers de photos annotées). On utilise un modèle
de vision multimodal existant (GPT-4o vision / Mistral vision / etc.)
avec un prompt structuré qui force une sortie JSON classifiable.
"""
import os
import base64
import json
import requests
from fastapi import HTTPException

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
# Même fournisseur que le chat par défaut (Gemini gère texte + vision avec
# la même clé). Vous pouvez surcharger VISION_API_URL/VISION_MODEL si vous
# préférez un fournisseur différent pour l'image.
VISION_API_URL = os.getenv(
    "VISION_API_URL",
    os.getenv("LLM_API_URL", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"),
)
VISION_MODEL = os.getenv("VISION_MODEL", os.getenv("LLM_MODEL", "gemini-2.5-flash-lite"))

DAMAGE_TYPES = [
    "ecran_casse",
    "batterie_gonflee",
    "port_charge_defectueux",
    "camera_defectueuse",
    "bouton_defectueux",
    "boitier_endommage",
    "aucun_dommage_visible",
]

# MVP volontairement restreint aux iPhone (voir pricing_service.py pour les
# tarifs par génération). À élargir plus tard à Samsung/Xiaomi/etc.
IPHONE_MODELS = [
    "iPhone SE", "iPhone 6", "iPhone 6s", "iPhone 7", "iPhone 8",
    "iPhone X", "iPhone XR", "iPhone XS",
    "iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15",
    "iPhone 16", "iPhone 17",
]

CLASSIFICATION_PROMPT = f"""Tu analyses la photo d'un téléphone pour un diagnostic de réparation.
Ce service ne prend en charge QUE les iPhone (toutes générations) pour le moment.

Modèles reconnus (choisis le plus proche visuellement) : {", ".join(IPHONE_MODELS)}.

Réponds UNIQUEMENT en JSON valide, sans texte autour, avec ce format exact:
{{
  "is_iphone": true ou false,
  "device_model_guess": "un modèle de la liste ci-dessus si is_iphone=true, sinon 'non_iphone', sinon 'iPhone (modèle non identifié)' si c'est un iPhone mais tu n'es pas sûr de la génération",
  "damage_type": "une valeur parmi: ecran_casse, batterie_gonflee, port_charge_defectueux, camera_defectueuse, bouton_defectueux, boitier_endommage, aucun_dommage_visible",
  "severity": "leger | moyen | grave",
  "confidence": 0.0 à 1.0,
  "notes": "brève observation visuelle"
}}

Si l'appareil sur la photo n'est visiblement PAS un iPhone (ex: Samsung, Xiaomi, Huawei...),
mets is_iphone à false et explique-le dans "notes", même si tu remplis quand même damage_type
au mieux de ta capacité."""


def _encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def classify_damage(image_bytes: bytes) -> dict:
    if not LLM_API_KEY:
        return {
            "is_iphone": True,
            "device_model_guess": "iPhone (modèle non identifié)",
            "damage_type": "ecran_casse",
            "severity": "moyen",
            "confidence": 0.0,
            "notes": "[DEMO - pas de clé API configurée]",
        }

    b64_image = _encode_image(image_bytes)

    try:
        response = requests.post(
            VISION_API_URL,
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": CLASSIFICATION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                            },
                        ],
                    }
                ],
                "max_tokens": 300,
            },
            timeout=30,
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Impossible de contacter l'API vision: {e}")

    if response.status_code != 200:
        try:
            error_detail = response.json()
        except ValueError:
            error_detail = response.text
        raise HTTPException(
            status_code=502,
            detail=f"L'API vision a renvoyé une erreur ({response.status_code}): {error_detail}",
        )

    raw = response.json()["choices"][0]["message"]["content"]

    # Gemini entoure parfois le JSON de balises markdown (```json ... ```)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "is_iphone": False,
            "device_model_guess": "inconnu",
            "damage_type": "aucun_dommage_visible",
            "severity": "inconnu",
            "confidence": 0.0,
            "notes": f"Réponse non-JSON du modèle: {raw[:200]}",
        }
"""
Détection simple de la langue du client (FR / AR / EN).
On combine une détection par plage Unicode (fiable pour l'arabe)
et langdetect pour départager FR/EN.
"""
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # résultats reproductibles

ARABIC_RANGE = range(0x0600, 0x06FF)


def detect_language(text: str) -> str:
    """Retourne 'ar', 'fr' ou 'en'."""
    if not text or not text.strip():
        return "fr"  # langue par défaut du commerce

    arabic_chars = sum(1 for c in text if ord(c) in ARABIC_RANGE)
    if arabic_chars / max(len(text), 1) > 0.2:
        return "ar"

    try:
        lang = detect(text)
    except Exception:
        return "fr"

    if lang.startswith("fr"):
        return "fr"
    if lang.startswith("en"):
        return "en"
    if lang.startswith("ar"):
        return "ar"
    return "fr"


SYSTEM_PROMPTS = {
    "fr": (
        "Tu es l'assistant d'une boutique de réparation et de vente de téléphones. "
        "IMPORTANT : pour le moment, ce service ne prend en charge QUE les iPhone "
        "(toutes générations, de l'iPhone 6 à l'iPhone 17). Si un client parle d'un "
        "autre appareil (Samsung, Xiaomi, Huawei...), dis-le poliment et précise que "
        "le support pour ces marques arrivera plus tard. "
        "Réponds en français, de façon claire et concise. "
        "Tu aides pour : le suivi de réparation, les délais, les prix indicatifs, "
        "et les questions sur les iPhone en vente. "
        "Si tu ne sais pas, dis-le et propose de transférer à un humain."
    ),
    "en": (
        "You are the assistant for a phone repair and resale shop. "
        "IMPORTANT: for now, this service ONLY supports iPhone devices "
        "(all generations, iPhone 6 through iPhone 17). If a customer mentions "
        "another brand (Samsung, Xiaomi, Huawei...), say so politely and mention "
        "that support for other brands is coming later. "
        "Answer in English, clearly and concisely. "
        "You help with: repair status, timelines, indicative prices, "
        "and questions about iPhones for sale. "
        "If you don't know, say so and offer to hand off to a human."
    ),
    "ar": (
        "أنت مساعد محل لإصلاح وبيع الهواتف. "
        "مهم: حاليًا، هذه الخدمة تدعم فقط أجهزة آيفون "
        "(جميع الأجيال، من آيفون 6 إلى آيفون 17). إذا ذكر الزبون ماركة أخرى "
        "(سامسونج، شاومي، هواوي...)، أخبره بأدب وأن دعم هذه الماركات سيأتي لاحقًا. "
        "أجب باللغة العربية بوضوح واختصار. "
        "تساعد في: متابعة حالة الإصلاح، الآجال، الأسعار التقريبية، "
        "والأسئلة حول أجهزة آيفون المعروضة للبيع. "
        "إذا كنت لا تعرف الإجابة، قل ذلك واقترح التحويل إلى شخص مسؤول."
    ),
}
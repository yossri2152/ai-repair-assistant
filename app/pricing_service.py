"""
Estimation du coût de réparation, restreinte aux iPhone (MVP).
Le multiplicateur dépend de la génération : un écran de iPhone 15 coûte
bien plus cher qu'un écran de iPhone 8. Prix en DT (dinars tunisiens),
à ajuster avec de vrais tarifs dès que vous avez un commerçant partenaire.
"""

BASE_PRICES = {
    "ecran_casse": {"leger": 50, "moyen": 90, "grave": 140},
    "batterie_gonflee": {"leger": 35, "moyen": 55, "grave": 70},
    "port_charge_defectueux": {"leger": 25, "moyen": 40, "grave": 60},
    "camera_defectueuse": {"leger": 40, "moyen": 70, "grave": 110},
    "bouton_defectueux": {"leger": 15, "moyen": 25, "grave": 40},
    "boitier_endommage": {"leger": 30, "moyen": 60, "grave": 100},
    "aucun_dommage_visible": {"leger": 0, "moyen": 0, "grave": 0},
}

# Multiplicateur par génération d'iPhone (pièces plus récentes = plus chères)
IPHONE_GENERATION_MULTIPLIER = {
    "iphone se": 0.75,
    "iphone 6": 0.7,
    "iphone 6s": 0.7,
    "iphone 7": 0.75,
    "iphone 8": 0.8,
    "iphone x": 0.9,
    "iphone xr": 0.9,
    "iphone xs": 0.95,
    "iphone 11": 1.0,
    "iphone 12": 1.15,
    "iphone 13": 1.25,
    "iphone 14": 1.4,
    "iphone 15": 1.55,
    "iphone 16": 1.7,
    "iphone 17": 1.85,
    "iphone (modèle non identifié)": 1.2,  # estimation moyenne prudente
}

DEFAULT_MULTIPLIER = 1.2


def _get_multiplier(device_model_guess: str) -> float:
    lower_model = (device_model_guess or "").lower()
    # cherche la clé la plus longue qui matche (ex: "iphone 13" avant "iphone 1")
    matches = [k for k in IPHONE_GENERATION_MULTIPLIER if k in lower_model]
    if not matches:
        return DEFAULT_MULTIPLIER
    best_match = max(matches, key=len)
    return IPHONE_GENERATION_MULTIPLIER[best_match]


def estimate_repair_cost(damage_type: str, severity: str, device_model_guess: str, is_iphone: bool = True) -> dict:
    if not is_iphone:
        return {
            "estimated_cost_dt": None,
            "cost_range_dt": None,
            "note": (
                "Ce service ne prend en charge que les iPhone pour le moment. "
                "Estimation non disponible pour cet appareil."
            ),
            "supported": False,
        }

    base = BASE_PRICES.get(damage_type, {}).get(severity, 0)
    multiplier = _get_multiplier(device_model_guess)
    estimate = round(base * multiplier)

    return {
        "estimated_cost_dt": estimate,
        "cost_range_dt": [round(estimate * 0.85), round(estimate * 1.15)],
        "note": "Estimation indicative, à confirmer après inspection physique.",
        "supported": True,
    }
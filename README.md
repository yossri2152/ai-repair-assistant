# Module IA — Assistant Réparation & Vente de Téléphones

Squelette du module IA pour votre projet freelance. Trois capacités :
chat multilingue (FR/AR/EN), diagnostic de panne par photo, et diagnostic
par vidéo (frames + audio).

## Démarrage rapide

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export LLM_API_KEY=sk-votre-cle          # OpenAI, ou adaptez LLM_API_URL pour Mistral/autre
export LLM_MODEL=gpt-4o-mini
export VISION_MODEL=gpt-4o-mini

uvicorn main:app --reload
```

Sans clé API (`LLM_API_KEY` non définie), l'API répond en mode démo
(réponses statiques) pour que vous puissiez tester la structure sans
dépenser de crédits.

Pour l'endpoint vidéo, `ffmpeg` doit être installé sur la machine :
```bash
sudo apt install ffmpeg
```

## Tester les endpoints

```bash
# Chat
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "شحال ثمن تبديل الشاشة"}'

# Image
curl -X POST localhost:8000/diagnose-image -F "file=@ecran_casse.jpg"

# Vidéo
curl -X POST localhost:8000/diagnose-video -F "file=@probleme.mp4"
```

## Ce qui est du vrai code vs ce qui est un placeholder

| Brique | État |
|---|---|
| Détection de langue FR/AR/EN | Fonctionnel |
| Chat via LLM | Fonctionnel (branchez votre clé API) |
| RAG sur le catalogue/tarifs réels | **Placeholder** — `retrieve_context()` dans `chat_service.py`, à remplacer par une vraie recherche vectorielle (pgvector/Pinecone) une fois que vous avez le catalogue d'un commerçant |
| Classification d'image | Fonctionnel, via modèle de vision existant (pas de CNN maison) |
| Estimation de coût | Fonctionnel mais avec des prix d'exemple — à remplacer par les vrais tarifs |
| Vidéo | Fonctionnel comme pipeline frames+audio, mais **ce n'est pas un vrai modèle vidéo** — c'est la seule approche réaliste à votre échelle |

## Plan de phasage recommandé

1. **Cette semaine** : brancher une vraie clé API, tester `/chat` et
   `/diagnose-image` avec de vraies photos de téléphones cassés.
2. **Semaine suivante** : remplacer `retrieve_context()` par du vrai RAG
   dès que vous avez le catalogue/tarifs d'un commerçant test.
3. **Ensuite seulement** : `/diagnose-video`, une fois que texte + image
   tournent bien — c'est la brique la plus coûteuse en temps et en API.

## Prochaine étape suggérée

Une fois ce module testé, on enchaîne sur le backend "métier"
(publications, rendez-vous, comptes utilisateurs) qui appellera ces
endpoints IA — comme prévu dans le plan initial (Node.js/Spring Boot +
React/Angular + AWS).

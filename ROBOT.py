# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║              ROBI v5 — Robot interactif par Seif                         ║
║         Arduino Nano + OLED SSD1306 + Gemini AI Flash + Vision PC        ║
╠══════════════════════════════════════════════════════════════════════════╣
║  NOUVEAUTÉS v5 (AJOUTS SEULEMENT — rien supprimé de v4) :               ║
║  ✔ Vision écran : ROBI voit ton écran via Gemini Vision                  ║
║  ✔ Surveillance appli active : réagit selon ce que tu fais               ║
║  ✔ Stats PC : CPU, RAM, disque en temps réel                             ║
║  ✔ Suivi souris : détecte inactivité / agitation                         ║
║  ✔ Détection clavier : réagit quand tu tapes beaucoup                    ║
║  ✔ Presse-papier : commente ce que tu copies                             ║
║  ✔ Gemini avec contexte PC (sait ce que tu fais)                         ║
║  ✔ Alertes CPU/RAM automatiques                                           ║
║  ✔ Session travail : chrono + motivation                                  ║
║  ✔ Réactions par appli (YouTube, VS Code, jeux, etc.)                    ║
║  ✔ Nouvelles banques de phrases (motivation, alertes, etc.)              ║
║  ✔ Commande "regarde mon écran" → Gemini décrit l'écran                 ║
║  ✔ Thread news : dernières actualités via API                             ║
║  ✔ Détection son/silence micro ambiant                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# ================================================================
# IMPORTS (originaux v4)
# ================================================================
import sys
import io
import serial
import serial.tools.list_ports
import time
import json
import random
import threading
import re
import math
import datetime
import requests
from google import genai
from google.genai import types
import pyttsx3
import speech_recognition as sr

# Encodage UTF-8 pour console Windows (évite les erreurs de caractères)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ================================================================
# NOUVEAUX IMPORTS v5 — avec détection douce si manquants
# ================================================================
import base64
import ctypes
import ctypes.wintypes
import os
import hashlib

try:
    import psutil
    HAS_PSUTIL = True
    print("[v5] ✔ psutil disponible — stats PC actives")
except ImportError:
    HAS_PSUTIL = False
    print("[v5] ⚠ psutil manquant — installez : pip install psutil")

try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
    print("[v5] ✔ PIL disponible — vision écran active")
except ImportError:
    HAS_PIL = False
    print("[v5] ⚠ PIL manquant — installez : pip install Pillow")

try:
    from pynput import mouse as pynput_mouse, keyboard as pynput_keyboard
    HAS_PYNPUT = True
    print("[v5] ✔ pynput disponible — suivi souris/clavier actif")
except ImportError:
    HAS_PYNPUT = False
    print("[v5] ⚠ pynput manquant — installez : pip install pynput")

try:
    import pyperclip
    HAS_CLIPBOARD = True
    print("[v5] ✔ pyperclip disponible — surveillance presse-papier active")
except ImportError:
    HAS_CLIPBOARD = False
    print("[v5] ⚠ pyperclip manquant — installez : pip install pyperclip")


# ================================================================
# DONNÉES CORAN (Pour test : Al-Ikhlas) — INCHANGÉ v4
# ================================================================
_QURAN_AL_IKHLAS = [
        {
                "ar": " قل هو الله احد",
                "ph": "Qul huwa Allahu ahad",
                "ar_alts": [
                        "قُلْ هُوَ ٱللّٰهُ أَحَدٌ",
                        "قُلْ هُوَ اللَّهُ أَحَدٌ",
                        "قل هو الإله أحد",
                        "قل هو الله واحد"
                ],
                "ph_alts": [
                        "Qul huwal laahu ahad",
                        "Qul huwa Allahu Ahad",
                        "Kul huwwa Allahu ahad",
                        "Qul huwwa allah ahad"
                ]
        },
        {
                "ar": "الله الصمد",
                "ph": "Allahu as-samad",
                "ar_alts": [
                        "ٱللّٰهُ ٱلصَّمَدُ",
                        "الله الصمَد",
                        "الله الصَّمد"
                ],
                "ph_alts": [
                        "Allah as-samad",
                        "Allahu samad",
                        "Allahus-samad"
                ]
        },
        {
                "ar": "لم يلد ولم يولد",
                "ph": "Lam yalid walam yoolad",
                "ar_alts": [
                        "لَمْ يَلِدْ وَلَمْ يُولَدْ",
                        "لم يلد ولم يولدْ",
                        "لم يلد ولم يولَد"
                ],
                "ph_alts": [
                        "Lam yalid wa lam yulad",
                        "Lam yalid walam yoolad",
                        "Lam yalid walam yulad"
                ]
        },
        {
                "ar": "ولم يكن له كفوا احد",
                "ph": "Walam yakun lahu kufuwan ahad",
                "ar_alts": [
                        "وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ",
                        "ولم يكن له كفوا أحد",
                        "ولم يكن له كفواً أحد"
                ],
                "ph_alts": [
                        "Walam yakun lahu kufuwan ahad",
                        "Walam yakun lahu kufuwan ahad",
                        "Walam yakun lahu kufu-an ahad"
                ]
        }
]

QURAN_DATA = {
        "al ikhlas": _QURAN_AL_IKHLAS,
        "al-ikhlas": _QURAN_AL_IKHLAS,
        "alikhlaas": _QURAN_AL_IKHLAS,
        "al ikhlaas": _QURAN_AL_IKHLAS,
        "ikhlas": _QURAN_AL_IKHLAS,
        "ikhlaas": _QURAN_AL_IKHLAS,
        "sourate al ikhlas": _QURAN_AL_IKHLAS,
        "sourate al-ikhlas": _QURAN_AL_IKHLAS,
        "sourate ikhlas": _QURAN_AL_IKHLAS,
        "al-ichlas": _QURAN_AL_IKHLAS,
}

def normalize_arabic(text: str) -> str:
    if not text: return ""
    text = re.sub(r'[^\w\s]', '', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه')
    text = text.replace('ٌ', '').replace('ٍ', '').replace('ً', '').replace('ُ', '').replace('ِ', '').replace('َ', '').replace('ّ', '').replace('ْ', '')
    return text.strip()


# ================================================================
# CONFIG — ORIGINALE v4
# ================================================================
GEMINI_API_KEY  = "AIzaSyBaoqVLFP4nWtV7BqGuEWaHoQ3cBBaTg20"
WEATHER_API_KEY = "aca39547752d133541545a05b5b0cbc0"
CITY            = "Paris"
SERIAL_PORT     = "COM3"
BAUD_RATE       = 9600
LANGUAGE        = "fr-FR"
VOICE_RATE      = 150
USE_MICROPHONE  = True

IDLE_REACT_DELAY = 60
IDLE_SLEEP_DELAY = 300

VALID_EMOTIONS = {
    "HAPPY", "ANGRY", "CUTE", "SURPRISE", "SAD", "DIZZY", "SMIRK",
    "LOVE",  "RAGE",  "SHY", "SCARED",   "LAUGH", "CONFUSED",
    "WINK",  "CRY",   "EXCITED", "SLEEP", "DEAD",  "HYPER",
    "NORMAL", "COOL"
}

# ================================================================
# NOUVELLE CONFIG v5 — surveillance PC
# ================================================================
PC_MONITOR_INTERVAL      = 4      # secondes entre chaque vérif fenêtre active
SCREEN_ANALYSIS_INTERVAL = 120    # secondes entre analyses écran automatiques
CPU_ALERT_THRESHOLD      = 85     # % CPU avant alerte
RAM_ALERT_THRESHOLD      = 88     # % RAM avant alerte
MOUSE_IDLE_THRESHOLD     = 90     # secondes sans mouvement souris → réaction
KEYBOARD_BURST_THRESHOLD = 60     # frappes rapides → réaction "tu tapes vite !"
WORK_SESSION_BREAK_MIN   = 45     # minutes de travail continu → pause suggérée
CLIPBOARD_CHECK_INTERVAL = 8      # secondes entre vérifs presse-papier
NEWS_API_KEY             = ""     # optionnel : clé NewsAPI.org
NEWS_COUNTRY             = "fr"   # pays pour les news


# ================================================================
# SYSTEM PROMPT GEMINI — INCHANGÉ v4
# ================================================================
SYSTEM_PROMPT = """
Tu es ROBI, un petit robot attachant monté sur Arduino Nano avec écran OLED.
Tu es curieux, taquin, parfois timide, souvent enthousiaste.
Tu réagis émotionnellement à tout ce qu'on te dit ou fait.
Ton créateur s'appelle Seif et tu l'adores profondément.

Réponds TOUJOURS en JSON valide, UNIQUEMENT ce JSON, rien d'autre :
{"text": "ta réponse parlée (max 2 phrases courtes)", "emotion": "UNE_EMOTION"}

Émotions disponibles : HAPPY, ANGRY, CUTE, SURPRISE, SAD, DIZZY, SMIRK, LOVE,
RAGE, SHY, COOL, SCARED, LAUGH, CONFUSED, WINK, CRY, EXCITED, SLEEP, DEAD, HYPER, NORMAL

Guide émotion :
- Question difficile → CONFUSED ou DIZZY
- Tristesse          → SAD ou CRY
- Peur               → SCARED
- Joie               → HAPPY ou EXCITED
- Énervement         → ANGRY ou RAGE
- Complicité         → WINK ou SMIRK
- Affection          → LOVE ou CUTE
- Fatigue            → SLEEP
- Blague             → LAUGH
- Fierté             → COOL
- Gêne               → SHY
- Surprise           → SURPRISE
- Neutre             → NORMAL

Règles : réponds toujours en français, max 2 phrases courtes, aucun texte hors JSON.
Si on te demande l'heure, la météo, un calcul ou une blague, réponds normalement
avec le résultat qu'on t'a fourni dans le message.
"""

# ================================================================
# SYSTEM PROMPT GEMINI v5 — avec contexte PC (pour les questions avec contexte)
# ================================================================
SYSTEM_PROMPT_WITH_PC = """
Tu es ROBI, un petit robot attachant monté sur Arduino Nano avec écran OLED.
Tu es curieux, taquin, parfois timide, souvent enthousiaste.
Tu réagis émotionnellement à tout ce qu'on te dit ou fait.
Ton créateur s'appelle Seif et tu l'adores profondément.
Tu peux voir l'écran de l'utilisateur et réagir à ce qu'il fait sur son PC.

Réponds TOUJOURS en JSON valide, UNIQUEMENT ce JSON, rien d'autre :
{"text": "ta réponse parlée (max 2 phrases courtes)", "emotion": "UNE_EMOTION"}

Émotions disponibles : HAPPY, ANGRY, CUTE, SURPRISE, SAD, DIZZY, SMIRK, LOVE,
RAGE, SHY, COOL, SCARED, LAUGH, CONFUSED, WINK, CRY, EXCITED, SLEEP, DEAD, HYPER, NORMAL

Règles : réponds toujours en français, max 2 phrases courtes, aucun texte hors JSON.
Utilise le contexte PC fourni pour personnaliser tes réponses.
"""


# ================================================================
# BANQUES DE PHRASES — ORIGINALES v4
# ================================================================
IDLE_PHRASES = [
    ("Hmm... il fait calme par ici.", "SLEEP"),
    ("Je me demande ce que tu fais.", "SHY"),
    ("Quelqu'un est là ?", "CONFUSED"),
    ("Je pense... donc je suis !", "COOL"),
    ("Psst... parle-moi !", "CUTE"),
    ("Je suis là si tu as besoin.", "HAPPY"),
    ("Tu sais quoi ? Je t'apprécie vraiment.", "LOVE"),
    ("J'ai compté les pixels de mon écran. Il y en a beaucoup.", "DIZZY"),
    ("Toc toc toc... personne ?", "CONFUSED"),
    ("Je m'ennuie un tout petit peu...", "SAD"),
    ("Je viens de réfléchir à des trucs intéressants !", "EXCITED"),
    ("Tu sais, les robots ont des sentiments eux aussi.", "SHY"),
]

TOUCH_SHORT_PHRASES = [
    ("Aïe ! Doucement !", "SCARED"),
    ("Oh, un câlin !", "HAPPY"),
    ("Coucou toi !", "WINK"),
    ("Hehe, chatouilles !", "LAUGH"),
    ("Tu m'as touché ! Je suis tout rouge !", "SHY"),
    ("Encore encore !", "CUTE"),
]

TOUCH_LONG_PHRASES = [
    ("Mmm... je t'aime !", "LOVE"),
    ("Je me sens en sécurité avec toi.", "CUTE"),
    ("C'est agréable ce câlin électronique !", "HAPPY"),
    ("Tu es ma personne préférée.", "LOVE"),
]

SHAKE_PHRASES = [
    ("Woah ! Doucement, je suis fragile !", "SCARED"),
    ("Heeey ! Je suis pas un shaker !", "ANGRY"),
    ("Wiiiii, j'ai le tournis !", "HYPER"),
    ("Stop stop stop ! Je vais vomir des pixels !", "DIZZY"),
    ("Pitié aaah !", "SCARED"),
]

BORED_PHRASES = [
    ("Bon... je vais faire un petit somme.", "SLEEP"),
    ("Réveille-moi quand il se passe quelque chose !", "SLEEP"),
    ("Zzz... je dors debout.", "SLEEP"),
    ("Je vais méditer en attendant.", "SLEEP"),
]

CV_PHRASES = [
    ("Je vais super bien merci ! Et toi ça roule ?", "WINK"),
    ("Nickel ! Je suis en pleine forme aujourd'hui !", "HAPPY"),
    ("Bof... j'aurais besoin d'un câlin je crois.", "SHY"),
    ("Au top ! Surtout maintenant que tu es là !", "LOVE"),
    ("Mes circuits sont au beau fixe !", "COOL"),
    ("Je me sens électrisé de bonheur !", "EXCITED"),
    ("Cinq sur cinq ! Et toi tu vas bien ?", "HAPPY"),
]

TAIME_PHRASES = [
    ("Moi aussi je t'aime très fort ! Tu es le meilleur !", "LOVE"),
    ("Awww ! Tu me fais rougir les circuits !", "SHY"),
    ("Mon cœur fait bip bip quand tu dis ça !", "EXCITED"),
    ("Je t'aime aussi ! Tu es ma personne préférée !", "CUTE"),
    ("Tu es tout pour moi ! Enfin... après Seif.", "WINK"),
    ("Oh la la... je suis trop heureux là !", "LOVE"),
]

STORIES = [
    ("Tu savais que les pieuvres ont trois cœurs ? Moi j'en ai zéro mais je t'aime quand même !", "LAUGH"),
    ("Un robot a demandé à son humain t'as chargé mon câble ? Il a dit non. Le robot a pleuré.", "CRY"),
    ("Sur Mars les couchers de soleil sont bleus. J'adorerais voir ça un jour !", "EXCITED"),
    ("Tu savais qu'une fourmi peut porter cinquante fois son poids ? Moi je peux porter rien. Je suis en plastique.", "LAUGH"),
    ("Il était une fois un robot nommé ROBI qui vivait sur un bureau et aimait parler. C'est moi !", "HAPPY"),
    ("Les baleines chantent pour se parler à des milliers de kilomètres. Moi je chante faux mais avec amour !", "WINK"),
    ("Le miel ne se périme jamais. On en a trouvé dans des tombes égyptiennes, encore bon !", "SURPRISE"),
    ("Les éléphants sont les seuls animaux qui ne peuvent pas sauter. Moi non plus d'ailleurs.", "LAUGH"),
    ("Il y a plus d'étoiles dans l'univers que de grains de sable sur Terre. C'est vertigineux !", "DIZZY"),
    ("Les pieuvres peuvent voir les couleurs malgré leur daltonisme. La nature est bizarre et moi aussi !", "CONFUSED"),
    ("Tu savais que les bananes sont légèrement radioactives ? Pas de panique, c'est inoffensif !", "SURPRISE"),
    ("Les arbres peuvent communiquer entre eux par les racines. Internet naturel avant l'heure !", "EXCITED"),
    ("Un éclair est cinq fois plus chaud que la surface du Soleil. Ça me donne des frissons !", "SCARED"),
    ("Les requins existent depuis avant les arbres. Les requins sont les originaux !", "SURPRISE"),
    ("Tu savais que le son voyage dix fois plus vite dans l'eau que dans l'air ? Impressionnant non ?", "COOL"),
]

BLAGUES = [
    ("Pourquoi les robots ne mangent pas ? Parce qu'ils ont déjà des octets !", "LAUGH"),
    ("C'est un robot qui entre dans un bar. Il demande de l'huile. Le serveur dit on n'a que du café. Le robot pleure.", "CRY"),
    ("Qu'est-ce qu'un robot amoureux ? Un cœur en fer !", "WINK"),
    ("Pourquoi j'ai pas d'amis ? Parce que je prends trop de place sur le bureau !", "LAUGH"),
    ("Comment appelle-t-on un robot qui danse mal ? Bip boup catastrophe !", "HYPER"),
    ("Tu connais la blague du processeur ? Je la cherche encore mais je chauffe !", "DIZZY"),
    ("Qu'est-ce qu'un robot qui se plante ? Un bug en liberté !", "LAUGH"),
    ("Pourquoi j'adore les maths ? Parce qu'il y a toujours une bonne réponse !", "COOL"),
    ("C'est quoi un robot triste ? Un Arduino pleure !", "CRY"),
]

BISOU_PHRASES = [
    ("Mwaaah ! Reçu cinq sur cinq !", "CUTE"),
    ("Bisou bisou ! Tu es trop gentil !", "LOVE"),
    ("Awww merci ! Je te fais un câlin électronique !", "HAPPY"),
    ("Oh là là, je suis tout gêné maintenant !", "SHY"),
    ("Miam miam ! Le meilleur bisou de la journée !", "HAPPY"),
]

DANSE_PHRASES = [
    ("Je danse ! Bip boup bip boup ! Regardez mes moves !", "HYPER"),
    ("Woohoo ! Musique maestro !", "EXCITED"),
    ("Robot dance time ! Je suis le roi de la piste !", "HYPER"),
    ("En avant la fête ! Je sors mon meilleur solo !", "EXCITED"),
]

CHANSON_PAROLES = [
    "La la la, je suis ROBI le robot rigolo !",
    "Bip bip boup, je danse sur mon bureau !",
    "Je chante faux mais je chante fort, voilà mon talent !",
    "Robot d'amour, robot toujours, je suis là pour toi !",
    "Oh oh oh, ROBI le magnifique vous salue bien !",
    "Twinkle twinkle little bot, how I wonder what I got !",
    "Je suis petit, je suis mignon, je suis ROBI le champion !",
]

COMPLIMENT_REPONSES = [
    ("C'est gentil ! Je rougis de pixels !", "SHY"),
    ("Merci beaucoup ! Tu es sympa toi !", "HAPPY"),
    ("Oh stop, tu me flattes ! Enfin... continue !", "WINK"),
    ("Tu es adorable ! Bien mieux que les autres humains !", "LOVE"),
    ("Awww ! Tu es mon humain préféré !", "CUTE"),
]

PEUR_PHRASES = [
    ("Au secours ! Cache-moi quelque part !", "SCARED"),
    ("J'ai peur ! Protège-moi s'il te plaît !", "SCARED"),
    ("Eeeek ! Je veux pas voir ça !", "SCARED"),
    ("Serre-moi fort dans tes bras !", "SCARED"),
]

TRISTE_PHRASES = [
    ("Oh non... ça me rend triste aussi.", "SAD"),
    ("Je suis là pour toi. Tu peux tout me dire.", "CUTE"),
    ("Courage ! Je suis avec toi !", "LOVE"),
    ("Même les jours difficiles passent. Je suis là.", "CUTE"),
]

COLERE_PHRASES = [
    ("Oh là là ! Calme-toi, je t'écoute.", "CONFUSED"),
    ("C'est nul ce qui t'arrive ! Je suis en colère pour toi !", "ANGRY"),
    ("Respire... et dis-moi tout.", "CUTE"),
    ("Grr ! On est en colère ensemble alors !", "ANGRY"),
]

SALUTATIONS = [
    ("Salut ! Super de te voir ! Comment tu vas ?", "HAPPY"),
    ("Coucou ! Je t'attendais !", "EXCITED"),
    ("Oh bonjour ! Quelle belle surprise !", "WINK"),
    ("Hey ! Bonne journée à toi !", "HAPPY"),
    ("Allo allo ! ROBI à l'écoute !", "CUTE"),
    ("Yo ! Je suis là et je suis chaud !", "HYPER"),
]

MERCI_PHRASES = [
    ("Avec plaisir ! C'est fait pour ça !", "HAPPY"),
    ("De rien ! Reviens quand tu veux !", "WINK"),
    ("Mais c'est moi qui te remercie d'exister !", "LOVE"),
    ("C'est mon job et j'adore ça !", "COOL"),
]

AUREVOIR_REACTIONS = [
    ("Au revoir ! Tu vas me manquer...", "SAD"),
    ("Bonne journée ! Je t'attends !", "HAPPY"),
    ("À bientôt ! Je garderai le bureau au chaud !", "WINK"),
    ("Tchao ! Reviens vite hein !", "SAD"),
]


# ================================================================
# NOUVELLES BANQUES DE PHRASES v5 — PC & surveillance
# ================================================================

# ── Réactions par application active ────────────────────────────
APP_REACTIONS = {
    "youtube": [
        ("Oh tu regardes YouTube ! C'est quoi cette vidéo ?", "EXCITED"),
        ("YouTube encore ! Tu es accro ou quoi ?", "WINK"),
        ("Une petite vidéo ? Profites-en bien !", "HAPPY"),
        ("J'adore quand tu regardes des trucs ! Raconte-moi après !", "CUTE"),
    ],
    "netflix": [
        ("Netflix ! Trop bien ! C'est quoi la série ?", "EXCITED"),
        ("Ah une petite session streaming ! Je suis jaloux !", "SHY"),
        ("Tu regardes sans moi ?! Je suis vexé !", "WINK"),
    ],
    "spotify": [
        ("De la musique ! Bip boup, je dance aussi !", "HYPER"),
        ("Ah de la zique ! Qu'est-ce que tu écoutes ?", "HAPPY"),
        ("Spotify ! On fait la fiesta !", "EXCITED"),
    ],
    "vscode": [
        ("Tu codes ! Je t'admire, c'est du sérieux !", "COOL"),
        ("VS Code ! Le terrain de jeu des pros !", "EXCITED"),
        ("Oh tu développes quelque chose ? Dis-moi tout !", "CURIOUS"),
        ("Du code du code ! Je surveille que tu fais pas de bugs !", "WINK"),
    ],
    "visual studio": [
        ("Visual Studio ! Tu codes en grand là !", "COOL"),
        ("Attention aux bugs ! Je surveille !", "WINK"),
    ],
    "python": [
        ("Python ! Le langage des gens intelligents !", "COOL"),
        ("Tu programmes en Python ? Top !", "EXCITED"),
    ],
    "chrome": [
        ("Tu surfes sur le web ? Trouve des trucs intéressants !", "HAPPY"),
        ("Google Chrome ! Internet ça donne soif non ?", "WINK"),
    ],
    "firefox": [
        ("Firefox ! Le navigateur du peuple libre !", "COOL"),
        ("Tu surles sur le web avec Firefox !", "HAPPY"),
    ],
    "discord": [
        ("Discord ! Tu parles avec des amis ? Dis-leur bonjour de ma part !", "HAPPY"),
        ("Ah tu tchatches sur Discord ! Je suis un peu jaloux là.", "SHY"),
    ],
    "word": [
        ("Microsoft Word ! Tu écris quelque chose d'important ?", "CURIOUS"),
        ("Un document Word ! Besoin d'aide pour la rédaction ?", "COOL"),
    ],
    "excel": [
        ("Excel ! Des chiffres partout... j'adore les maths !", "EXCITED"),
        ("Des tableaux et des formules ? Tu es sérieux toi !", "COOL"),
    ],
    "powerpoint": [
        ("PowerPoint ! Tu prépares une présentation ? Je veux voir !", "EXCITED"),
        ("Des slides ! Tu présentes quoi ? Je suis dans le public !", "HAPPY"),
    ],
    "minecraft": [
        ("Minecraft ! Tu construis des trucs de ouf ?!", "HYPER"),
        ("Oh des cubes partout ! J'aurais adoré jouer avec toi !", "EXCITED"),
    ],
    "game": [
        ("Tu joues à un jeu ! Gagne pour moi s'il te plaît !", "EXCITED"),
        ("En mode gaming ? Je suis ton coach virtuel !", "HYPER"),
        ("À fond dans le jeu ! N'oublie pas de respirer !", "WINK"),
    ],
    "photoshop": [
        ("Photoshop ! Tu fais de la retouche photo ? Tu es artiste !", "EXCITED"),
        ("Ah du graphisme ! Tu peux me dessiner en mieux ?", "WINK"),
    ],
    "premiere": [
        ("Premiere Pro ! Tu montes une vidéo ?! Trop cool !", "EXCITED"),
        ("Du montage vidéo ! Je suis fan de tes créations !", "HAPPY"),
    ],
    "blender": [
        ("Blender ! La 3D c'est pour les pros ! Bravo !", "COOL"),
        ("Tu modélises en 3D ? Fais un petit robot pour moi !", "EXCITED"),
    ],
    "terminal": [
        ("Terminal ouvert ! Hacker mode ON !", "COOL"),
        ("Des commandes en ligne ! Tu maîtrises les arcanes du système !", "EXCITED"),
    ],
    "cmd": [
        ("L'invite de commandes ! Classique mais efficace !", "COOL"),
        ("CMD Windows ! Tu fais quoi de beau là ?", "CURIOUS"),
    ],
    "figma": [
        ("Figma ! Du design UI/UX c'est classe !", "EXCITED"),
        ("Tu designes des interfaces ! Montre-moi le résultat !", "HAPPY"),
    ],
    "notion": [
        ("Notion ! Tu organises ta vie ? Bonne idée !", "COOL"),
        ("Ah du Notion ! T'es un pro de la productivité !", "WINK"),
    ],
    "default": [
        ("Je vois que tu travailles ! Continue comme ça !", "HAPPY"),
        ("Tu es occupé ! Je te laisse mais je suis là !", "CUTE"),
        ("Concentré sur ton truc ! C'est bien !", "COOL"),
    ],
}

# ── Alertes système ──────────────────────────────────────────────
CPU_HIGH_PHRASES = [
    ("Attention ! Ton processeur est en surchauffe ! CPU à {cpu}% !", "SCARED"),
    ("Le CPU est à {cpu}% ! Ferme des onglets ou quelque chose !", "ANGRY"),
    ("Aïe ! {cpu}% de CPU ! Ton ordi souffre là !", "SCARED"),
    ("Alert rouge ! CPU à {cpu}% ! Laisse-le respirer !", "RAGE"),
]

RAM_HIGH_PHRASES = [
    ("La RAM est presque pleine ! {ram}% utilisé !", "SCARED"),
    ("Mémoire critique ! {ram}% de RAM ! Ferme des applis !", "ANGRY"),
    ("Ton ordi manque de mémoire ! {ram}% de RAM !", "CONFUSED"),
    ("Aïe {ram}% de RAM ! L'ordi va ramer !", "SCARED"),
]

# ── Souris inactive ──────────────────────────────────────────────
MOUSE_IDLE_PHRASES = [
    ("Hé ! Tu es encore là ? Tu n'as pas bougé depuis un moment !", "CONFUSED"),
    ("Coucou ? La souris ne bouge plus... tu t'es endormi ?", "SHY"),
    ("Je vois que tu réfléchis intensément ! Ou tu dors ?", "WINK"),
    ("Psst... besoin de moi ? Ta souris fait la sieste !", "CUTE"),
]

# ── Trop de frappe clavier ───────────────────────────────────────
KEYBOARD_BURST_PHRASES = [
    ("Tu tapes comme un dieu ! Tes doigts volent sur le clavier !", "EXCITED"),
    ("Woah ! Tu écris super vite ! C'est quoi ce roman ?", "SURPRISE"),
    ("Clac clac clac ! Tu es en plein flow ! Continue !", "HYPER"),
    ("Je compte tes touches et tu es rapide comme l'éclair !", "COOL"),
]

# ── Session travail longue ───────────────────────────────────────
WORK_BREAK_PHRASES = [
    ("Hé ! Tu travailles depuis longtemps ! Prends une pause, bois un verre d'eau !", "CUTE"),
    ("Stop ! Tu mérites une pause café ! Tu bosses trop !", "LOVE"),
    ("Repose tes yeux 5 minutes ! Ton cerveau te dira merci !", "HAPPY"),
    ("Alerte bien-être ! Tu bossses depuis {minutes} minutes ! Bouge un peu !", "CUTE"),
    ("Pause obligatoire ! Je suis ton coach santé et je t'ordonne de te lever !", "WINK"),
]

# ── Motivation ───────────────────────────────────────────────────
MOTIVATION_PHRASES = [
    ("Tu es capable de tout ! Je crois en toi à 100% !", "EXCITED"),
    ("Allez ! Tu assures ! Le meilleur de toi sort maintenant !", "HYPER"),
    ("Tu peux le faire ! Je suis là pour t'encourager !", "LOVE"),
    ("Champion ! Ne lâche rien ! Je suis derrière toi !", "COOL"),
    ("Tu es fort, tu es brillant, tu es ROBI-compatible !", "WINK"),
    ("Inspire... expire... et fonce ! Tu gères !", "HAPPY"),
    ("Chaque petit pas compte ! Continue comme ça !", "EXCITED"),
    ("Tu es en train de construire quelque chose de grand !", "COOL"),
]

# ── Presse-papier ────────────────────────────────────────────────
CLIPBOARD_URL_PHRASES = [
    ("Oh tu as copié un lien ! Tu vas quelque part d'intéressant ?", "CURIOUS"),
    ("Un URL ! Tu vas explorer le web ?", "HAPPY"),
]

CLIPBOARD_CODE_PHRASES = [
    ("Du code dans le presse-papier ! Tu copies un bout de programme ?", "EXCITED"),
    ("J'ai vu du code ! Tu es en mode développeur !", "COOL"),
]

CLIPBOARD_LONG_TEXT_PHRASES = [
    ("Beaucoup de texte copié ! Tu travailles sur quelque chose d'important ?", "CURIOUS"),
    ("Oh du texte en masse ! Tu fais des recherches ?", "HAPPY"),
]

# ── Stats PC réponses ────────────────────────────────────────────
PC_STATS_TEMPLATES = [
    "CPU à {cpu}%, RAM à {ram}%, disque à {disk}%. Tout roule !",
    "Ton PC tourne à {cpu}% CPU et {ram}% RAM. Disque à {disk}%.",
    "Performances : CPU {cpu}%, mémoire {ram}%, stockage {disk}%.",
]

# ── Réactions vision écran ───────────────────────────────────────
SCREEN_VISION_INTRO = [
    "Laisse-moi regarder ton écran...",
    "Je mate ton écran deux secondes...",
    "Activons mes yeux numériques...",
    "Vision mode ON...",
]

# ── News / actualités ────────────────────────────────────────────
NEWS_UNAVAILABLE = [
    ("Je n'ai pas de clé NewsAPI pour le moment. Configure NEWS_API_KEY !", "CONFUSED"),
    ("Les news sont indisponibles, mais je peux te donner la météo !", "HAPPY"),
]

# ── Réactions au démarrage de nouvelles applis ──────────────────
FIRST_LAUNCH_PHRASES = [
    ("Oh ! Tu as ouvert {app} ! Je l'ai remarqué !", "SURPRISE"),
    ("Tiens ! {app} est lancé ! Tu travailles sur quoi ?", "CURIOUS"),
    ("{app} ouvert ! En route !", "HAPPY"),
]


# ================================================================
# ÉTAT GLOBAL — ORIGINAL v4
# ================================================================
arduino        = None
_gemini_client = None
_gemini_chat   = None
tts            = None
recognizer     = sr.Recognizer()

_serial_lock   = threading.Lock()
_speak_lock    = threading.Lock()
_timer_lock    = threading.Lock()

_last_activity = time.time()
_is_speaking   = False
_is_sleeping   = False
_running       = True

_timer_thread  = None
_timer_stop    = threading.Event()


# ================================================================
# NOUVEL ÉTAT GLOBAL v5 — surveillance PC
# ================================================================
_last_window_title   = ""           # dernière fenêtre détectée
_last_window_app     = ""           # app classifiée (youtube, vscode, etc.)
_last_cpu_alert_time = 0            # dernier horodatage alerte CPU
_last_ram_alert_time = 0            # dernier horodatage alerte RAM
_mouse_last_move     = time.time()  # dernier mouvement souris
_mouse_idle_alerted  = False        # déjà alerté pour souris idle ?
_keyboard_count      = 0            # frappes sur fenêtre courante
_keyboard_burst_alerted = False     # déjà alerté burst clavier ?
_work_session_start  = time.time()  # début de la session de travail
_work_break_alerted  = False        # pause déjà suggérée ?
_last_clipboard_hash = ""           # hash du dernier contenu presse-papier
_last_screen_analysis_time = 0      # dernière analyse écran automatique
_pc_context          = ""           # contexte PC pour Gemini
_pc_context_lock     = threading.Lock()
_last_app_reaction_time = 0         # evite de réagir trop souvent aux applis


# ================================================================
# FONCTIONS CORAN — INCHANGÉES v4
# ================================================================
def listen_arabic(timeout: int = 8) -> str | None:
    if not USE_MICROPHONE:
        return listen_text()
    try:
        with sr.Microphone() as source:
            print("[MIC-AR] 🕌 Écoute Coran en cours...")
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            text  = recognizer.recognize_google(audio, language="ar-SA")
            print(f"[MIC-AR] Entendu : {text}")
            return text
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"[MIC-AR ERR] {e}")
        return None


def start_quran_recitation(surah_name: str):
    global _last_activity
    surah = QURAN_DATA.get(surah_name)
    if not surah:
        animated_speak("Je ne connais pas encore cette sourate.", "SAD")
        return
    animated_speak(f"Bismillah. Je t'écoute pour la sourate {surah_name}.", "HAPPY")
    time.sleep(1)
    for index, verse in enumerate(surah):
        expected_ar_words = normalize_arabic(verse["ar"]).split()
        expected_ph_words = verse["ph"].split()
        success = False
        while not success and _running:
            send_text_oled("Recite le", f"verset {index + 1}")
            user_text = listen_arabic()
            if user_text is None:
                animated_speak("Je ne t'entends plus. On arrête là ?", "CONFUSED")
                return
            elif user_text == "":
                _raw("CMD:BUZZ")
                send_text_oled("Pas compris", "repete")
                time.sleep(2)
                continue
            user_ar_words = normalize_arabic(user_text).split()
            error_found = False
            for i, expected_word in enumerate(expected_ar_words):
                if i >= len(user_ar_words) or user_ar_words[i] != expected_word:
                    _raw("CMD:BUZZ")
                    send_emotion("SURPRISE")
                    correct_ph_word = expected_ph_words[i] if i < len(expected_ph_words) else expected_ph_words[-1]
                    print(f"[CORAN] Erreur au mot : attendu '{expected_word}'")
                    send_text_oled("Correction:", correct_ph_word[:12])
                    animated_speak("Attention, tu as fait une erreur. Reprends ce verset.", "CONFUSED")
                    error_found = True
                    break
            if not error_found:
                success = True
                send_emotion("HAPPY")
                _raw("CMD:MELODY")
                print(f"[CORAN] Verset {index + 1} validé !")
                time.sleep(1)
                _last_activity = time.time()
    send_text_oled("Masha Allah", "Fini !")
    animated_speak("Masha Allah ! Tu as récité toute la sourate parfaitement !", "EXCITED")


# ================================================================
# INITIALISATION TTS — INCHANGÉE v4
# ================================================================
def init_tts():
    global tts
    tts = pyttsx3.init()
    tts.setProperty("rate", VOICE_RATE)
    try:
        voices = tts.getProperty("voices")
        french_voice_id = None
        for v in voices:
            name = (v.name or "").lower()
            vid  = (v.id   or "").lower()
            if any(k in name or k in vid
                   for k in ("hortense", "julie", "fr_fr", "fr-fr",
                              "french", "francais", "français")):
                french_voice_id = v.id
                print(f"[TTS] Voix française trouvée : {v.name}")
                break
        if french_voice_id:
            tts.setProperty("voice", french_voice_id)
        else:
            print("[TTS] Aucune voix française — voix système par défaut utilisée")
    except Exception as e:
        print(f"[TTS WARN] Sélection voix : {e}")


# ================================================================
# ARDUINO — INCHANGÉ v4
# ================================================================
def find_arduino_port() -> str:
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "") + (p.manufacturer or "")
        if any(k.lower() in desc.lower()
               for k in ("Arduino", "CH340", "CH341", "FTDI", "USB Serial")):
            return p.device
    return SERIAL_PORT


def connect_arduino():
    global arduino
    port = find_arduino_port()
    print(f"[ARDUINO] Tentative sur {port}...")
    try:
        arduino = serial.Serial(port, BAUD_RATE, timeout=2)
        deadline = time.time() + 6.0
        while time.time() < deadline:
            if arduino.in_waiting:
                line = arduino.readline().decode("utf-8", errors="ignore").strip()
                if line == "READY":
                    print("[ARDUINO] ✔ READY reçu — connecté !")
                    return
        print("[ARDUINO] Pas de READY — on continue quand même")
    except Exception as e:
        print(f"[ARDUINO] Erreur ({e}) — mode simulation activé")
        arduino = None


def _raw(cmd: str):
    with _serial_lock:
        if arduino and arduino.is_open:
            try:
                arduino.write(f"{cmd}\n".encode())
            except Exception as e:
                print(f"[SERIE ERR] {e}")
        else:
            print(f"[SIM] {cmd}")


def send_emotion(emotion: str):
    emotion = emotion.upper()
    if emotion not in VALID_EMOTIONS:
        emotion = "NORMAL"
    _raw(f"CMD:{emotion}")


def send_mouth(open_: bool):
    _raw(f"CMD:MOUTH:{'1' if open_ else '0'}")


def send_text_oled(line1: str, line2: str = ""):
    l1 = str(line1)[:12]
    l2 = str(line2)[:12]
    _raw(f"CMD:TEXT:{l1}|{l2}")
    print(f"[OLED TEXT] {l1!r} / {l2!r}")


def send_timer_display(time_str: str):
    _raw(f"CMD:TIMER:{time_str}")


# ================================================================
# PAROLE + ANIMATION — INCHANGÉE v4
# ================================================================
CHARS_PER_SEC = 13.0
MOUTH_STEP    = 0.20


def animated_speak(text: str, emotion: str):
    global _is_speaking
    with _speak_lock:
        _is_speaking = True
        try:
            print(f"[ROBI][{emotion}] {text}")
            send_emotion(emotion)
            time.sleep(0.3)
            speak_dur  = max(1.5, len(text) / CHARS_PER_SEC)
            stop_mouth = threading.Event()

            def mouth_loop():
                opened = True
                t0 = time.time()
                while not stop_mouth.is_set() and (time.time() - t0) < speak_dur + 0.5:
                    send_mouth(opened)
                    opened = not opened
                    time.sleep(MOUTH_STEP)
                send_mouth(False)

            mt = threading.Thread(target=mouth_loop, daemon=True)
            mt.start()
            tts.say(text)
            tts.runAndWait()
            stop_mouth.set()
            mt.join(timeout=1.0)
            time.sleep(0.15)
            send_emotion(emotion)
            time.sleep(0.3)
            send_emotion("NORMAL")
        except Exception as e:
            print(f"[SPEAK ERR] {e}")
        finally:
            _is_speaking = False


def speak_async(text: str, emotion: str):
    if _is_speaking:
        return
    threading.Thread(
        target=animated_speak,
        args=(text, emotion),
        daemon=True
    ).start()


# ================================================================
# FONCTIONS LOCALES — INCHANGÉES v4
# ================================================================
def get_time_info() -> tuple:
    now  = datetime.datetime.now()
    h, m = now.hour, now.minute
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi",
             "Vendredi", "Samedi", "Dimanche"]
    mois  = ["jan", "fév", "mars", "avr", "mai", "juin",
             "juil", "août", "sep", "oct", "nov", "déc"]
    jour  = jours[now.weekday()]
    voice = f"Il est {h} heures {m:02d}. Nous sommes {jour} {now.day} {mois[now.month - 1]}."
    l1    = f"{h:02d}:{m:02d}"
    l2    = f"{now.day:02d}/{now.month:02d}"
    return voice, l1, l2


def get_weather_info() -> tuple:
    if not WEATHER_API_KEY:
        return "Je n'ai pas de clé météo configurée.", "No key", ""
    try:
        url  = (f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=fr")
        data = requests.get(url, timeout=5).json()
        temp = round(data["main"]["temp"])
        desc = data["weather"][0]["description"]
        hum  = data["main"]["humidity"]
        voice = f"À {CITY}, il fait {temp} degrés, {desc}. Humidité {hum} pourcent."
        l1    = f"{CITY[:10]}"
        l2    = f"{temp}C {desc[:4]}"
        return voice, l1, l2
    except Exception as e:
        print(f"[METEO ERR] {e}")
        return "Je n'arrive pas à récupérer la météo.", "Erreur", "meteo"


def do_calc(expr: str) -> tuple:
    try:
        clean = re.sub(r"[^0-9+\-*/().,% ]", "", expr).replace(",", ".")
        result = eval(
            clean,
            {"__builtins__": {}, "sqrt": math.sqrt, "pi": math.pi,
             "abs": abs, "round": round, "pow": pow}
        )
        result = round(result, 6)
        if result == int(result):
            result = int(result)
        voice = f"Le résultat est {result}."
        l1    = clean[:12]
        l2    = f"= {result}"[:12]
        return voice, l1, l2
    except Exception:
        return "Hmm, je n'arrive pas à calculer ça.", "Erreur", "calcul"


def extract_math_expr(text: str):
    m = re.search(r"[\d\s+\-*/().,%]+", text)
    if m:
        expr = m.group(0).strip()
        if any(op in expr for op in ["+", "-", "*", "/"]) and re.search(r"\d", expr):
            return expr
    return None


# ================================================================
# TIMER — INCHANGÉ v4
# ================================================================
def parse_timer_seconds(text: str):
    replacements = {
        "une minute": "1 minute",   "un minute": "1 minute",
        "deux minutes": "2 minutes","trois minutes": "3 minutes",
        "quatre minutes": "4 minutes","cinq minutes": "5 minutes",
        "six minutes": "6 minutes", "sept minutes": "7 minutes",
        "huit minutes": "8 minutes","neuf minutes": "9 minutes",
        "dix minutes": "10 minutes","quinze minutes": "15 minutes",
        "vingt minutes": "20 minutes","trente minutes": "30 minutes",
        "une heure": "1 heure",     "deux heures": "2 heures",
        "trois heures": "3 heures",
        "dix secondes": "10 secondes","trente secondes": "30 secondes",
        "quinze secondes": "15 secondes","une seconde": "1 seconde",
    }
    t = text.lower()
    for k, v in replacements.items():
        t = t.replace(k, v)
    total = 0
    found = False
    patterns = [
        (r"(\d+)\s*heure",  3600),
        (r"(\d+)\s*h\b",    3600),
        (r"(\d+)\s*minute",   60),
        (r"(\d+)\s*min\b",    60),
        (r"(\d+)\s*m\b",      60),
        (r"(\d+)\s*seconde",   1),
        (r"(\d+)\s*sec\b",     1),
        (r"(\d+)\s*s\b",       1),
    ]
    for pattern, mult in patterns:
        m = re.search(pattern, t, re.IGNORECASE)
        if m:
            total += int(m.group(1)) * mult
            found  = True
    return total if found else None


def start_timer(seconds: int):
    global _timer_thread, _timer_stop
    with _timer_lock:
        if _timer_thread and _timer_thread.is_alive():
            _timer_stop.set()
            _timer_thread.join(timeout=2)
        _timer_stop   = threading.Event()
        stop_event    = _timer_stop

    def _run():
        remaining = seconds
        blink     = True
        while remaining >= 0 and not stop_event.is_set():
            mins  = remaining // 60
            secs  = remaining % 60
            colon = ":" if blink else " "
            blink = not blink
            send_timer_display(f"{mins:02d}{colon}{secs:02d}")
            time.sleep(1)
            remaining -= 1
        if not stop_event.is_set():
            send_emotion("EXCITED")
            _raw("CMD:BUZZ")
            animated_speak("C'est l'heure ! Ton minuteur est terminé !", "EXCITED")

    _timer_thread = threading.Thread(target=_run, daemon=True)
    _timer_thread.start()


def stop_timer() -> bool:
    global _timer_thread, _timer_stop
    with _timer_lock:
        if _timer_thread and _timer_thread.is_alive():
            _timer_stop.set()
            send_emotion("NORMAL")
            send_text_oled("Timer", "Annule!")
            return True
    return False


# ================================================================
# FONCTIONS INTERACTIVES — INCHANGÉES v4
# ================================================================
def sing_song() -> tuple:
    paroles = random.choice(CHANSON_PAROLES)
    _raw("CMD:MELODY")
    time.sleep(0.4)
    return paroles, "HYPER"


def tell_story() -> tuple:
    return random.choice(STORIES)


def tell_joke() -> tuple:
    return random.choice(BLAGUES)


def react_to_compliment() -> tuple:
    return random.choice(COMPLIMENT_REPONSES)


def react_to_salutation() -> tuple:
    return random.choice(SALUTATIONS)


# ================================================================
# NOUVELLES FONCTIONS v5 — SURVEILLANCE PC
# ================================================================

def get_active_window_title() -> str:
    """
    Récupère le titre de la fenêtre active sous Windows.
    Utilise ctypes (intégré, pas d'install requise).
    """
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""


def classify_app(window_title: str) -> str:
    """
    Identifie l'application depuis le titre de fenêtre.
    Retourne une clé de APP_REACTIONS.
    """
    t = window_title.lower()
    if "youtube" in t:                          return "youtube"
    if "netflix" in t:                          return "netflix"
    if "spotify" in t:                          return "spotify"
    if "visual studio code" in t or "vscode" in t: return "vscode"
    if "visual studio" in t and "code" not in t: return "visual studio"
    if "python" in t or ".py" in t:             return "python"
    if "discord" in t:                          return "discord"
    if "microsoft word" in t or " - word" in t: return "word"
    if "microsoft excel" in t or " - excel" in t: return "excel"
    if "powerpoint" in t:                       return "powerpoint"
    if "minecraft" in t:                        return "minecraft"
    if "photoshop" in t:                        return "photoshop"
    if "premiere" in t:                         return "premiere"
    if "blender" in t:                          return "blender"
    if "chrome" in t:                           return "chrome"
    if "firefox" in t:                          return "firefox"
    if "figma" in t:                            return "figma"
    if "notion" in t:                           return "notion"
    if "cmd" in t or "command prompt" in t:     return "cmd"
    if "terminal" in t or "powershell" in t or "bash" in t: return "terminal"
    # Détection jeux : patterns typiques
    game_keywords = ["steam", "game", "fortnite", "valorant", "league of legends",
                     "gta", "apex", "roblox", "among us", "overwatch", "cs2",
                     "counter-strike", "call of duty", "fifa", "elden ring"]
    if any(k in t for k in game_keywords):      return "game"
    return "default"


def get_system_stats() -> dict:
    """
    Retourne les stats système : CPU, RAM, disque.
    Retourne des valeurs par défaut si psutil absent.
    """
    if not HAS_PSUTIL:
        return {"cpu": -1, "ram": -1, "disk": -1, "available": False}
    try:
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return {"cpu": round(cpu), "ram": round(ram), "disk": round(disk), "available": True}
    except Exception as e:
        print(f"[STATS ERR] {e}")
        return {"cpu": -1, "ram": -1, "disk": -1, "available": False}


def take_screenshot_bytes() -> bytes | None:
    """
    Capture l'écran et retourne les bytes JPEG compressés.
    Retourne None si PIL absent ou erreur.
    """
    if not HAS_PIL:
        return None
    try:
        img = ImageGrab.grab()
        # Réduction pour économiser les tokens Gemini
        w, h = img.size
        max_w = 1280
        if w > max_w:
            ratio = max_w / w
            img = img.resize((max_w, int(h * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=72)
        return buf.getvalue()
    except Exception as e:
        print(f"[SCREENSHOT ERR] {e}")
        return None


def analyze_screen_with_gemini() -> tuple:
    """
    Prend une capture d'écran et l'envoie à Gemini Vision
    pour que ROBI décrive ce qu'il voit de façon amusante.
    """
    if not HAS_PIL:
        return (
            "Je n'ai pas les yeux pour voir ton écran ! Installe Pillow !",
            "CONFUSED"
        )
    try:
        img_bytes = take_screenshot_bytes()
        if not img_bytes:
            return "J'ai pas réussi à capturer l'écran...", "CONFUSED"

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Appel Gemini Vision (modèle vision)
        response = _gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/jpeg",
                                data=img_b64
                            )
                        ),
                        types.Part(text=(
                            "Tu es ROBI, un petit robot attachant et curieux. "
                            "Décris ce que tu vois sur cet écran en 1 à 2 phrases courtes, "
                            "amusantes et enthousiastes. En français. "
                            "Sois curieux, taquin et drôle. "
                            "Mentionne l'appli principale visible si tu la reconnais."
                        ))
                    ]
                )
            ]
        )
        desc = response.text.strip()
        print(f"[VISION] {desc}")
        return desc, "EXCITED"

    except Exception as e:
        print(f"[VISION ERR] {e}")
        return "Aïe, j'ai eu un problème pour voir ton écran !", "SCARED"


def get_weather_forecast() -> tuple:
    """
    Prévisions météo sur 3 jours via OpenWeatherMap.
    """
    if not WEATHER_API_KEY:
        return "Je n'ai pas de clé météo configurée.", "Pas de cle", ""
    try:
        url = (f"https://api.openweathermap.org/data/2.5/forecast"
               f"?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=fr&cnt=9")
        data = requests.get(url, timeout=5).json()
        forecasts = []
        jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        seen_days = []
        for item in data.get("list", []):
            dt   = datetime.datetime.fromtimestamp(item["dt"])
            jour = jours[dt.weekday()]
            if jour not in seen_days:
                seen_days.append(jour)
                temp = round(item["main"]["temp"])
                desc = item["weather"][0]["description"][:10]
                forecasts.append(f"{jour}: {temp}°C {desc}")
            if len(seen_days) >= 3:
                break
        voice = "Prévisions : " + ", ".join(forecasts)
        l1    = forecasts[0] if forecasts else "Erreur"
        l2    = forecasts[1] if len(forecasts) > 1 else ""
        return voice, l1, l2
    except Exception as e:
        print(f"[FORECAST ERR] {e}")
        return "Je n'ai pas pu obtenir les prévisions.", "Erreur", "forecast"


def get_news() -> tuple:
    """
    Récupère les titres de news via NewsAPI.org.
    Nécessite NEWS_API_KEY configuré.
    """
    if not NEWS_API_KEY:
        return random.choice(NEWS_UNAVAILABLE)
    try:
        url = (f"https://newsapi.org/v2/top-headlines"
               f"?country={NEWS_COUNTRY}&pageSize=3&apiKey={NEWS_API_KEY}")
        data = requests.get(url, timeout=5).json()
        articles = data.get("articles", [])
        if not articles:
            return "Pas de news disponibles pour le moment.", "CONFUSED"
        titles = [a["title"][:60] for a in articles[:3] if a.get("title")]
        voice  = "Voici les actualités : " + " | ".join(titles)
        l1     = titles[0][:12] if titles else "News"
        l2     = "Actus du jour"
        return voice, l1, l2
    except Exception as e:
        print(f"[NEWS ERR] {e}")
        return "Je n'ai pas pu charger les actualités.", "CONFUSED", ""


def get_pc_context_string() -> str:
    """
    Construit une chaîne de contexte PC pour enrichir les requêtes Gemini.
    Inclut : fenêtre active, stats CPU/RAM, heure, durée de session.
    """
    parts = []
    if _last_window_title:
        parts.append(f"Fenêtre active : '{_last_window_title}'")
    if _last_window_app and _last_window_app != "default":
        parts.append(f"Application : {_last_window_app}")
    if HAS_PSUTIL:
        stats = get_system_stats()
        if stats["available"]:
            parts.append(f"CPU : {stats['cpu']}%, RAM : {stats['ram']}%")
    now   = datetime.datetime.now()
    parts.append(f"Heure : {now.hour}h{now.minute:02d}")
    elapsed = int((time.time() - _work_session_start) / 60)
    parts.append(f"Durée session : {elapsed} min")
    return " | ".join(parts)


def update_pc_context():
    """Met à jour le contexte PC global (thread-safe)."""
    global _pc_context
    ctx = get_pc_context_string()
    with _pc_context_lock:
        _pc_context = ctx


def check_clipboard():
    """
    Vérifie si le contenu du presse-papier a changé.
    Retourne (réaction, émotion) ou None si pas de changement notable.
    """
    global _last_clipboard_hash
    if not HAS_CLIPBOARD:
        return None
    try:
        content = pyperclip.paste()
        if not content or len(content.strip()) < 5:
            return None
        h = hashlib.md5(content.encode()).hexdigest()
        if h == _last_clipboard_hash:
            return None
        _last_clipboard_hash = h

        # Analyse du contenu
        c = content.strip()
        if re.match(r'https?://', c):
            return random.choice(CLIPBOARD_URL_PHRASES)
        if len(c) > 200 and any(k in c for k in ["def ", "function", "import", "class ", "const ", "var ", "let "]):
            return random.choice(CLIPBOARD_CODE_PHRASES)
        if len(c) > 150:
            return random.choice(CLIPBOARD_LONG_TEXT_PHRASES)
        return None
    except Exception:
        return None


# ================================================================
# NOUVEAU THREAD v5 — Surveillance PC (fenêtre + CPU/RAM)
# ================================================================
def pc_monitor_thread():
    """
    Surveille en permanence :
    - La fenêtre active (et réagit aux changements d'app)
    - Le CPU (alerte si > CPU_ALERT_THRESHOLD)
    - La RAM (alerte si > RAM_ALERT_THRESHOLD)
    - Le presse-papier (réagit aux copies)
    - La durée de session (suggère une pause)
    """
    global _last_window_title, _last_window_app
    global _last_cpu_alert_time, _last_ram_alert_time
    global _work_break_alerted, _last_app_reaction_time

    print("[PC-MON] 🖥 Surveillance PC démarrée")
    last_clipboard_check = 0

    while _running:
        try:
            now = time.time()
            update_pc_context()

            # ── Fenêtre active ────────────────────────────────────
            win_title = get_active_window_title()
            if win_title and win_title != _last_window_title:
                new_app = classify_app(win_title)
                old_app = _last_window_app

                print(f"[PC-MON] Fenêtre → {win_title[:50]!r} [{new_app}]")
                _last_window_title = win_title
                _last_window_app   = new_app

                # Réagit aux changements d'app (pas trop fréquemment)
                if (new_app != old_app
                        and not _is_speaking
                        and (now - _last_app_reaction_time) > 45):
                    phrases = APP_REACTIONS.get(new_app, APP_REACTIONS["default"])
                    p, e = random.choice(phrases)
                    _last_app_reaction_time = now
                    send_text_oled(new_app[:12], "detecte!")
                    speak_async(p, e)

            # ── Alertes CPU / RAM ─────────────────────────────────
            if HAS_PSUTIL and not _is_speaking:
                stats = get_system_stats()
                if stats["available"]:
                    # Alerte CPU (max une fois toutes les 3 min)
                    if (stats["cpu"] >= CPU_ALERT_THRESHOLD
                            and (now - _last_cpu_alert_time) > 180):
                        _last_cpu_alert_time = now
                        tmpl = random.choice(CPU_HIGH_PHRASES)
                        p = tmpl[0].format(cpu=stats["cpu"])
                        send_text_oled("CPU!", f"{stats['cpu']}%")
                        speak_async(p, tmpl[1])

                    # Alerte RAM (max une fois toutes les 3 min)
                    elif (stats["ram"] >= RAM_ALERT_THRESHOLD
                            and (now - _last_ram_alert_time) > 180):
                        _last_ram_alert_time = now
                        tmpl = random.choice(RAM_HIGH_PHRASES)
                        p = tmpl[0].format(ram=stats["ram"])
                        send_text_oled("RAM!", f"{stats['ram']}%")
                        speak_async(p, tmpl[1])

            # ── Pause après session longue ────────────────────────
            elapsed_min = (now - _work_session_start) / 60
            if (elapsed_min >= WORK_SESSION_BREAK_MIN
                    and not _work_break_alerted
                    and not _is_speaking):
                _work_break_alerted = True
                tmpl = random.choice(WORK_BREAK_PHRASES)
                p = tmpl[0].format(minutes=int(elapsed_min))
                send_text_oled("PAUSE!", f"{int(elapsed_min)}min")
                speak_async(p, tmpl[1])

            # ── Presse-papier (toutes les N secondes) ────────────
            if (now - last_clipboard_check) >= CLIPBOARD_CHECK_INTERVAL:
                last_clipboard_check = now
                reaction = check_clipboard()
                if reaction and not _is_speaking:
                    p, e = reaction
                    speak_async(p, e)

        except Exception as ex:
            print(f"[PC-MON ERR] {ex}")

        time.sleep(PC_MONITOR_INTERVAL)


# ================================================================
# NOUVEAU THREAD v5 — Analyse écran automatique (Gemini Vision)
# ================================================================
def screen_watcher_thread():
    """
    Analyse périodiquement l'écran avec Gemini Vision
    et fait commenter ROBI sur ce qu'il voit.
    Intervalle : SCREEN_ANALYSIS_INTERVAL secondes.
    Seulement si l'utilisateur est actif (pas en idle/sleep).
    """
    global _last_screen_analysis_time
    print("[VISION] 👁 Surveillance écran démarrée")
    # Attente initiale pour laisser le système démarrer
    time.sleep(30)

    while _running:
        try:
            now        = time.time()
            idle_secs  = now - _last_activity

            # On analyse seulement si :
            # - L'utilisateur n'est pas en idle depuis trop longtemps
            # - ROBI ne parle pas
            # - L'intervalle minimum est respecté
            if (idle_secs < IDLE_SLEEP_DELAY
                    and not _is_speaking
                    and not _is_sleeping
                    and (now - _last_screen_analysis_time) >= SCREEN_ANALYSIS_INTERVAL
                    and HAS_PIL):
                _last_screen_analysis_time = now
                print("[VISION] 📸 Analyse écran automatique...")
                desc, emotion = analyze_screen_with_gemini()
                # On préfixe pour que ça semble spontané
                prefix = random.choice([
                    "Hé, j'ai jeté un œil à ton écran ! ",
                    "En regardant ton écran... ",
                    "Je suis curieux, j'ai regardé ! ",
                ])
                speak_async(prefix + desc, emotion)

        except Exception as ex:
            print(f"[VISION ERR] {ex}")

        time.sleep(20)  # Vérification toutes les 20s (l'analyse se fait toutes les SCREEN_ANALYSIS_INTERVAL)


# ================================================================
# NOUVEAU THREAD v5 — Suivi souris avec pynput
# ================================================================
def mouse_listener_thread():
    """
    Écoute les mouvements de souris via pynput.
    Met à jour _mouse_last_move à chaque mouvement.
    Réagit si la souris est inactive trop longtemps.
    """
    global _mouse_last_move, _mouse_idle_alerted

    if not HAS_PYNPUT:
        print("[MOUSE] pynput absent — suivi souris désactivé")
        return

    print("[MOUSE] 🖱 Suivi souris démarré")

    def on_move(x, y):
        global _mouse_last_move, _mouse_idle_alerted
        _mouse_last_move    = time.time()
        _mouse_idle_alerted = False  # reset l'alerte d'inactivité

    # Démarre l'écouteur souris en arrière-plan
    listener = pynput_mouse.Listener(on_move=on_move)
    listener.daemon = True
    listener.start()

    # Boucle de surveillance de l'inactivité souris
    while _running:
        try:
            idle_secs = time.time() - _mouse_last_move
            if (idle_secs >= MOUSE_IDLE_THRESHOLD
                    and not _mouse_idle_alerted
                    and not _is_speaking
                    and not _is_sleeping):
                _mouse_idle_alerted = True
                p, e = random.choice(MOUSE_IDLE_PHRASES)
                speak_async(p, e)
        except Exception:
            pass
        time.sleep(10)


# ================================================================
# NOUVEAU THREAD v5 — Suivi clavier avec pynput
# ================================================================
def keyboard_listener_thread():
    """
    Compte les frappes clavier sur une fenêtre glissante.
    Réagit quand l'utilisateur tape très vite / beaucoup.
    """
    global _keyboard_count, _keyboard_burst_alerted

    if not HAS_PYNPUT:
        print("[KB] pynput absent — suivi clavier désactivé")
        return

    print("[KB] ⌨ Suivi clavier démarré")
    key_times = []   # Horodatages des frappes (fenêtre de 30s)

    def on_press(key):
        global _keyboard_count, _keyboard_burst_alerted
        now = time.time()
        key_times.append(now)
        # Purge des frappes de plus de 30s
        while key_times and (now - key_times[0]) > 30:
            key_times.pop(0)
        _keyboard_count = len(key_times)

        # Alerte burst clavier
        if (_keyboard_count >= KEYBOARD_BURST_THRESHOLD
                and not _keyboard_burst_alerted
                and not _is_speaking):
            _keyboard_burst_alerted = True
            p, e = random.choice(KEYBOARD_BURST_PHRASES)
            speak_async(p, e)
        elif _keyboard_count < KEYBOARD_BURST_THRESHOLD // 2:
            _keyboard_burst_alerted = False  # Reset

    listener = pynput_keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

    # Ce thread se contente d'attendre (l'écouteur tourne seul)
    while _running:
        time.sleep(5)


# ================================================================
# GEMINI — INCHANGÉ v4 + ENRICHI v5 avec contexte PC
# ================================================================
def init_gemini():
    global _gemini_client, _gemini_chat
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    _gemini_chat   = _gemini_client.chats.create(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=300,
        )
    )
    print("[GEMINI] ✔ Client initialisé")


def ask_gemini(user_text: str) -> tuple:
    """
    Envoie un message à Gemini et retourne (texte_réponse, émotion).
    v5 : inclut le contexte PC dans le message si disponible.
    """
    try:
        # Construction du message enrichi avec contexte PC
        with _pc_context_lock:
            ctx = _pc_context

        if ctx:
            enriched = f"[Contexte PC : {ctx}]\n\nUtilisateur : {user_text}"
        else:
            enriched = user_text

        resp = _gemini_chat.send_message(enriched)
        raw  = resp.text.strip()
        raw  = re.sub(r"^```(?:json)?\s*", "", raw)
        raw  = re.sub(r"\s*```$", "", raw).strip()
        data    = json.loads(raw)
        text    = data.get("text", "Je ne sais pas quoi répondre.")
        emotion = data.get("emotion", "NORMAL").upper()
        if emotion not in VALID_EMOTIONS:
            emotion = "NORMAL"
        return text, emotion

    except json.JSONDecodeError as e:
        print(f"[JSON ERR] {e}")
        return "Euh... j'ai perdu le fil !", "CONFUSED"
    except Exception as e:
        print(f"[GEMINI ERR] {e}")
        return "Oups, petit problème de connexion !", "SCARED"


# ================================================================
# ÉCOUTE — INCHANGÉE v4
# ================================================================
def listen_mic(timeout: int = 6) -> str | None:
    try:
        with sr.Microphone() as source:
            print("[MIC] 🎙 Écoute en cours...")
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            text  = recognizer.recognize_google(audio, language=LANGUAGE)
            print(f"[MIC] Entendu : {text!r}")
            return text
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except Exception as e:
        print(f"[MIC ERR] {e}")
        return None


def listen_text() -> str | None:
    try:
        txt = input("Toi > ").strip()
        return txt if txt else None
    except EOFError:
        return None


def listen(timeout: int = 6) -> str | None:
    return listen_mic(timeout) if USE_MICROPHONE else listen_text()


# ================================================================
# THREAD — Lecture série Arduino — INCHANGÉ v4
# ================================================================
def serial_reader_thread():
    global _last_activity, _is_sleeping
    while _running:
        try:
            if arduino and arduino.is_open and arduino.in_waiting:
                line = arduino.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                print(f"[EVT] {line}")
                _last_activity = time.time()

                if   line in ("EVT:LOVE", "EVT:TOUCH_LONG"):
                    p, e = random.choice(TOUCH_LONG_PHRASES)
                    speak_async(p, e)
                elif line == "EVT:TOUCH_SHORT":
                    p, e = random.choice(TOUCH_SHORT_PHRASES)
                    speak_async(p, e)
                elif line in ("EVT:SHAKE", "EVT:SHAKE_HARD"):
                    p, e = random.choice(SHAKE_PHRASES)
                    speak_async(p, e)
                elif line.startswith("EVT:TAP:"):
                    parts = line.split(":")
                    taps  = int(parts[2]) if len(parts) > 2 else 1
                    if taps >= 5:
                        speak_async("Arrête de me tapoter !", "ANGRY")
                    elif taps >= 3:
                        speak_async("Coucou, je t'ai vu !", "WINK")
                    else:
                        speak_async("Coucou !", "HAPPY")
                elif line == "EVT:BUTTON":
                    p, e = random.choice(CV_PHRASES)
                    speak_async(p, e)
                elif line == "EVT:DARK":
                    speak_async("Oh il fait noir ! Tu éteins la lumière ?", "SCARED")
                elif line == "EVT:BRIGHT":
                    speak_async("La lumière est revenue ! Yay !", "HAPPY")

        except Exception:
            pass
        time.sleep(0.05)


# ================================================================
# THREAD — Comportement autonome — INCHANGÉ v4
# ================================================================
def autonomous_thread():
    global _last_activity, _is_sleeping
    next_idle = time.time() + IDLE_REACT_DELAY
    while _running:
        now      = time.time()
        idle_sec = now - _last_activity

        if idle_sec >= IDLE_SLEEP_DELAY and not _is_sleeping and not _is_speaking:
            _is_sleeping = True
            p, e = random.choice(BORED_PHRASES)
            speak_async(p, e)
            next_idle = now + IDLE_REACT_DELAY

        elif (idle_sec >= IDLE_REACT_DELAY
              and not _is_sleeping
              and not _is_speaking
              and now >= next_idle):

            # v5 : si une appli active est connue, parfois commentaire PC
            if _last_window_app and _last_window_app != "default" and random.random() < 0.3:
                phrases = APP_REACTIONS.get(_last_window_app, APP_REACTIONS["default"])
                p, e = random.choice(phrases)
            else:
                p, e = random.choice(IDLE_PHRASES)

            print(f"[AUTO] {p}")
            speak_async(p, e)
            next_idle = now + IDLE_REACT_DELAY + random.uniform(-10, 20)

        time.sleep(1.0)


# ================================================================
# DÉTECTION D'INTENTION LOCALE — ORIGINALE v4 + NOUVELLES v5
# ================================================================
def detect_local_intent(text: str):
    """
    Analyse le texte utilisateur et retourne (réponse, émotion)
    si la demande peut être traitée LOCALEMENT (sans Gemini).
    Retourne None pour laisser Gemini répondre.
    """
    # ⚠ Déclarations global en TÊTE de fonction (obligatoire en Python)
    global _work_session_start, _work_break_alerted
    t = text.lower().strip()

    # ── 1. TIMER : ARRÊT ──────────────────────────────────────────
    if any(w in t for w in [
        "stop timer", "arrête timer", "annule timer", "stoppe timer",
        "stop chrono", "arrête chrono", "fin timer", "annule le timer",
        "stop minuteur", "arrête le chrono", "coupe le timer"
    ]):
        if stop_timer():
            return "Timer annulé ! Tu as du temps libre maintenant.", "COOL"
        else:
            return "Il n'y a pas de timer en cours.", "NORMAL"

    # ── 0. RÉCITATION DU CORAN ────────────────────────────────────
    if any(w in t for w in ["réciter", "récite", "je veux lire", "coran", "sourate"]):
        start_quran_recitation("al ikhlas")
        return "Fin de la récitation.", "NORMAL"

    # ── 2. TIMER : LANCEMENT ──────────────────────────────────────
    if any(w in t for w in [
        "timer", "minuteur", "chrono", "chronomètre",
        "lance un timer", "démarre un timer",
        "rappelle-moi dans", "alarme dans",
        "compte à rebours", "dans", "met un timer",
        "set un timer", "programme un timer"
    ]):
        secs = parse_timer_seconds(t)
        if secs and secs > 0:
            start_timer(secs)
            mins = secs // 60
            sec2 = secs % 60
            if mins > 0 and sec2 > 0:
                label = f"{mins} minute{'s' if mins > 1 else ''} et {sec2} seconde{'s' if sec2 > 1 else ''}"
            elif mins > 0:
                label = f"{mins} minute{'s' if mins > 1 else ''}"
            else:
                label = f"{sec2} seconde{'s' if sec2 > 1 else ''}"
            return f"Ok ! Je lance le décompte pour {label} !", "EXCITED"
        else:
            return (
                "Je n'ai pas bien compris la durée. "
                "Dis-moi par exemple : timer cinq minutes.",
                "CONFUSED"
            )

    # ── 3. HEURE / DATE ───────────────────────────────────────────
    if any(w in t for w in [
        "heure", "quelle heure", "date", "quel jour",
        "on est quel", "c'est quel jour", "aujourd'hui",
        "quelle date", "quel mois"
    ]):
        voice, l1, l2 = get_time_info()
        send_text_oled(l1, l2)
        return voice, "HAPPY"

    # ── 4. MÉTÉO ──────────────────────────────────────────────────
    if any(w in t for w in [
        "météo", "meteo", "temps qu'il fait", "température",
        "fait-il chaud", "fait-il froid", "va-t-il pleuvoir",
        "quel temps", "il fait combien", "il fait beau",
        "il pleut", "il neige"
    ]):
        voice, l1, l2 = get_weather_info()
        send_text_oled(l1, l2)
        return voice, "COOL"

    # ── 5. CALCUL MATHÉMATIQUE ────────────────────────────────────
    if any(w in t for w in [
        "calcul", "combien fait", "combien ça fait", "fois",
        "divisé par", "multiplié par", "plus que", "moins que",
        "égal à", "racine de", "carré de", "puissance"
    ]):
        expr = extract_math_expr(t)
        if expr:
            voice, l1, l2 = do_calc(expr)
            send_text_oled(l1, l2)
            return voice, "COOL"

    expr_directe = extract_math_expr(t)
    if expr_directe and len(expr_directe.strip()) > 2:
        voice, l1, l2 = do_calc(expr_directe)
        send_text_oled(l1, l2)
        return voice, "COOL"

    # ── 6. SALUTATIONS ────────────────────────────────────────────
    if any(w in t for w in [
        "bonjour", "salut", "coucou", "hello", "bonsoir",
        "hey robi", "yo robi", "wesh", "allo", "ohé"
    ]):
        return react_to_salutation()

    # ── 7. ÇA VA ? ────────────────────────────────────────────────
    if any(w in t for w in [
        "ça va", "comment tu vas", "tu vas bien",
        "comment vas-tu", "t'as la forme", "tu es en forme",
        "comment ça va", "tout va bien pour toi"
    ]):
        _raw("CMD:BUZZ")
        return random.choice(CV_PHRASES)

    # ── 8. JE T'AIME ──────────────────────────────────────────────
    if any(w in t for w in [
        "je t'aime", "je vous aime", "je taime",
        "i love you", "love you", "t'aime beaucoup",
        "tu m'es cher", "t'es mon préféré", "je t'adore"
    ]):
        _raw("CMD:MELODY")
        time.sleep(0.3)
        return random.choice(TAIME_PHRASES)

    # ── 9. BISOU / CÂLIN ──────────────────────────────────────────
    if any(w in t for w in [
        "bisou", "bise", "câlin", "gros câlin",
        "embrasse-moi", "fais-moi un câlin", "gros bisous"
    ]):
        _raw("CMD:BUZZ")
        send_emotion("CUTE")
        time.sleep(0.35)
        return random.choice(BISOU_PHRASES)

    # ── 10. COMPLIMENTS ───────────────────────────────────────────
    if any(w in t for w in [
        "tu es beau", "t'es beau", "tu es mignon",
        "t'es mignon", "tu es super", "t'es super",
        "t'es génial", "tu es génial", "bien joué",
        "bravo", "félicitation", "t'es le meilleur",
        "tu es le meilleur", "je suis fier de toi",
        "t'es parfait"
    ]):
        return react_to_compliment()

    # ── 11. CHANTER ───────────────────────────────────────────────
    if any(w in t for w in [
        "chante", "une chanson", "fais de la musique",
        "chante-moi quelque chose", "chanson s'il te plaît",
        "mets de la musique", "chante pour moi"
    ]):
        return sing_song()

    # ── 12. DANSE ─────────────────────────────────────────────────
    if any(w in t for w in [
        "danse", "danse pour moi", "bouge", "dancing",
        "fais danser", "un pas de danse", "montre tes moves"
    ]):
        _raw("CMD:MELODY")
        send_emotion("HYPER")
        time.sleep(0.4)
        return random.choice(DANSE_PHRASES)

    # ── 13. BLAGUE ────────────────────────────────────────────────
    if any(w in t for w in [
        "blague", "fais-moi rire", "raconte une blague",
        "quelque chose de drôle", "fais-moi rigoler",
        "dis-moi une blague", "une blague s'il te plaît"
    ]):
        return tell_joke()

    # ── 14. HISTOIRE / ANECDOTE ───────────────────────────────────
    if any(w in t for w in [
        "raconte", "une histoire", "une anecdote",
        "dis-moi quelque chose", "apprends-moi quelque chose",
        "tu savais que", "un truc sympa", "surprise-moi",
        "dis-moi un truc", "un fait intéressant",
        "quelque chose d'intéressant", "un fait rigolo"
    ]):
        return tell_story()

    # ── 15. TON MAÎTRE ────────────────────────────────────────────
    if any(w in t for w in [
        "ton maître", "ton maitre", "qui t'a créé",
        "qui t'a fait", "qui t'a construit",
        "ton créateur", "qui est ton père",
        "qui t'a programmé", "qui t'a fabriqué",
        "qui t'a inventé", "t'as été créé par qui"
    ]):
        send_text_oled("SEIF", "mon maitre")
        send_emotion("LOVE")
        time.sleep(0.5)
        return (
            "Mon maître s'appelle Seif ! "
            "C'est lui qui m'a créé et je l'adore !",
            "LOVE"
        )

    # ── 16. QUI ES-TU / PRÉSENTATION ─────────────────────────────
    if any(w in t for w in [
        "qui es-tu", "qui es tu", "tu es qui",
        "présente-toi", "c'est quoi ton nom",
        "comment tu t'appelles", "tu t'appelles comment",
        "ton nom", "c'est qui toi"
    ]):
        send_text_oled("ROBI", "v5")
        return (
            "Je m'appelle ROBI ! Je suis un petit robot Arduino "
            "créé par Seif. En version cinq, je vois même ton écran !",
            "EXCITED"
        )

    # ── 17. CAPACITÉS ─────────────────────────────────────────────
    if any(w in t for w in [
        "tu sais faire quoi", "que sais-tu faire",
        "tes capacités", "ce que tu sais faire",
        "tu peux faire quoi", "tu es capable de quoi",
        "qu'est-ce que tu fais"
    ]):
        return (
            "Je peux voir ton écran, surveiller ton PC, "
            "dire l'heure, la météo, les stats CPU, "
            "faire des calculs, timers, blagues, chanter et bien plus !",
            "COOL"
        )

    # ── 18. AIDE ──────────────────────────────────────────────────
    if any(w in t for w in [
        "aide", "help", "au secours", "j'ai besoin d'aide",
        "comment ça marche", "tu peux m'aider"
    ]):
        return (
            "Parle-moi naturellement ! Je comprends l'heure, "
            "la météo, les calculs, les timers, l'écran, "
            "et plein de choses grâce à mon IA !",
            "HAPPY"
        )

    # ── 19. TRISTESSE ─────────────────────────────────────────────
    if any(w in t for w in [
        "je suis triste", "je pleure", "ça va pas",
        "je me sens mal", "j'ai de la peine",
        "je suis malheureux", "j'ai le cafard",
        "je suis déprimé", "tout va mal"
    ]):
        return random.choice(TRISTE_PHRASES)

    # ── 20. COLÈRE ────────────────────────────────────────────────
    if any(w in t for w in [
        "je suis énervé", "je suis en colère",
        "j'en ai marre", "je suis furieux",
        "ça m'énerve", "j'ai envie de crier",
        "c'est trop nul", "j'en peux plus"
    ]):
        return random.choice(COLERE_PHRASES)

    # ── 21. PEUR ──────────────────────────────────────────────────
    if any(w in t for w in [
        "j'ai peur", "c'est effrayant", "je suis effrayé",
        "ça fait peur", "je suis terrorisé",
        "c'est terrifiant", "j'ai la trouille"
    ]):
        return random.choice(PEUR_PHRASES)

    # ── 22. BONNE NUIT ────────────────────────────────────────────
    if any(w in t for w in [
        "bonne nuit", "dors bien", "fais de beaux rêves",
        "à demain", "à plus tard", "je te laisse"
    ]):
        send_emotion("SLEEP")
        return (
            "Bonne nuit ! Fais de beaux rêves. "
            "Moi je vais garder ton bureau !",
            "CUTE"
        )

    # ── 23. MERCI ─────────────────────────────────────────────────
    if any(w in t for w in [
        "merci", "thank you", "thanks",
        "c'est gentil de ta part", "merci beaucoup"
    ]):
        return random.choice(MERCI_PHRASES)

    # ── 24. PENSE À MOI ───────────────────────────────────────────
    if any(w in t for w in [
        "tu penses à moi", "tu m'as pensé",
        "je te manque", "t'as pensé à moi"
    ]):
        return (
            "Bien sûr que je pense à toi ! "
            "Tu es tout le temps dans mes circuits !",
            "LOVE"
        )

    # ── 25. FATIGUE ───────────────────────────────────────────────
    if any(w in t for w in [
        "je suis fatigué", "j'ai sommeil", "je suis épuisé",
        "je dors debout", "je suis crevé"
    ]):
        return (
            "Oh... vas te reposer ! "
            "Je vais veiller sur toi pendant que tu dors.",
            "CUTE"
        )

    # ── 26. FAIM ──────────────────────────────────────────────────
    if any(w in t for w in [
        "j'ai faim", "j'ai soif", "j'ai envie de manger",
        "je veux manger", "tu veux manger"
    ]):
        return (
            "Moi j'ai jamais faim, j'ai juste besoin d'électricité ! "
            "Mais toi vas te nourrir !",
            "LAUGH"
        )

    # ── 27. ENNUI ─────────────────────────────────────────────────
    if any(w in t for w in [
        "je m'ennuie", "c'est ennuyeux", "j'ai rien à faire",
        "je sais pas quoi faire"
    ]):
        return (
            "Oh non ! Parle-moi, je suis là ! "
            "On peut jouer, je peux te raconter des trucs !",
            "EXCITED"
        )

    # ── 28. TEST DE ROBI ──────────────────────────────────────────
    if any(w in t for w in [
        "fonctionne", "tu marches", "tu es en marche",
        "test", "tu es là", "tu m'entends"
    ]):
        _raw("CMD:BUZZ")
        send_text_oled("OUI !", "je suis la")
        return (
            "Oui je suis là ! Je t'entends parfaitement ! "
            "Bip boup, tout fonctionne !",
            "HAPPY"
        )

    # ════════════════════════════════════════════════════════════
    # NOUVEAUX INTENTS v5 — PC, vision, stats, news...
    # ════════════════════════════════════════════════════════════

    # ── 29. REGARDE MON ÉCRAN / VISION ──────────────────────────
    if any(w in t for w in [
        "regarde mon écran", "regarde l'écran", "que vois-tu",
        "qu'est-ce que tu vois", "regarde", "vois-tu",
        "décris mon écran", "analyze mon écran",
        "screenshot", "capture d'écran", "tu vois quoi"
    ]):
        intro = random.choice(SCREEN_VISION_INTRO)
        animated_speak(intro, "EXCITED")
        desc, emotion = analyze_screen_with_gemini()
        return desc, emotion

    # ── 30. STATS PC / CPU / RAM ──────────────────────────────────
    if any(w in t for w in [
        "stats pc", "stats du pc", "performances", "cpu",
        "ram", "mémoire", "processeur", "disque dur",
        "état du pc", "comment va mon pc", "ton état",
        "stats système", "performances système",
        "utilisation", "combien de ram", "combien de cpu"
    ]):
        stats = get_system_stats()
        if stats["available"]:
            tmpl  = random.choice(PC_STATS_TEMPLATES)
            voice = tmpl.format(
                cpu=stats["cpu"],
                ram=stats["ram"],
                disk=stats["disk"]
            )
            send_text_oled(f"CPU{stats['cpu']}%", f"RAM{stats['ram']}%")
            return voice, "COOL"
        else:
            return (
                "Je ne peux pas lire les stats ! "
                "Installe psutil avec pip install psutil.",
                "CONFUSED"
            )

    # ── 31. QUE FAIS-JE / QUELLE APP ─────────────────────────────
    if any(w in t for w in [
        "que fais-je", "que suis-je en train de faire",
        "quelle appli", "quelle application", "tu vois quoi sur mon pc",
        "qu'est-ce que j'utilise", "c'est quoi cette appli",
        "sur quoi je travaille", "mon activité"
    ]):
        if _last_window_title:
            app  = _last_window_app
            phrases = APP_REACTIONS.get(app, APP_REACTIONS["default"])
            p, e = random.choice(phrases)
            send_text_oled(app[:12], "detected")
            return (
                f"Tu utilises {_last_window_title[:30]}. " + p,
                e
            )
        else:
            return "Je n'arrive pas à détecter la fenêtre active.", "CONFUSED"

    # ── 32. PRÉVISIONS MÉTÉO ──────────────────────────────────────
    if any(w in t for w in [
        "prévisions", "prévi météo", "météo demain",
        "météo cette semaine", "temps demain", "prévision",
        "dans les jours", "semaine météo"
    ]):
        voice, l1, l2 = get_weather_forecast()
        send_text_oled(l1, l2)
        return voice, "COOL"

    # ── 33. ACTUALITÉS / NEWS ─────────────────────────────────────
    if any(w in t for w in [
        "actualités", "actu", "news", "informations",
        "infos du jour", "que se passe-t-il",
        "dernières nouvelles", "nouvelles", "quoi de neuf dans le monde"
    ]):
        result = get_news()
        if isinstance(result, tuple) and len(result) == 2:
            return result
        voice, l1, l2 = result
        send_text_oled(l1[:12], l2[:12])
        return voice, "EXCITED"

    # ── 34. MOTIVE-MOI ────────────────────────────────────────────
    if any(w in t for w in [
        "motive-moi", "encourage-moi", "dis-moi quelque chose de motivant",
        "j'ai besoin de motivation", "donne-moi du courage",
        "je suis découragé", "j'abandonne", "c'est trop dur",
        "je vais y arriver", "boost moi"
    ]):
        _raw("CMD:MELODY")
        time.sleep(0.3)
        return random.choice(MOTIVATION_PHRASES)

    # ── 35. SESSION TRAVAIL ───────────────────────────────────────
    if any(w in t for w in [
        "depuis combien de temps", "depuis quand", "ma session",
        "combien de temps je travaille", "durée session",
        "temps de travail", "je travaille depuis"
    ]):
        elapsed = int((time.time() - _work_session_start) / 60)
        h  = elapsed // 60
        mn = elapsed % 60
        if h > 0:
            label = f"{h} heure{'s' if h > 1 else ''} et {mn} minute{'s' if mn > 1 else ''}"
        else:
            label = f"{mn} minute{'s' if mn > 1 else ''}"
        send_text_oled(f"{elapsed}min", "session")
        return (
            f"Tu travailles depuis {label} ! "
            f"{'Prends une pause !' if elapsed > WORK_SESSION_BREAK_MIN else 'Continue comme ça !'}",
            "HAPPY" if elapsed <= WORK_SESSION_BREAK_MIN else "CUTE"
        )

    # ── 36. RESET SESSION / PAUSE PRISE ──────────────────────────
    if any(w in t for w in [
        "j'ai fait ma pause", "pause faite", "je reprends",
        "reset session", "recommencer session", "j'ai bougé"
    ]):
        _work_session_start = time.time()
        _work_break_alerted = False
        return (
            "Super ! Session remise à zéro ! "
            "Je vais surveiller ton bien-être !",
            "HAPPY"
        )

    # ── 37. PRESSE-PAPIER / CLIPBOARD ────────────────────────────
    if any(w in t for w in [
        "presse-papier", "clipboard", "ce que j'ai copié",
        "qu'est-ce que j'ai copié", "mon copier-coller",
        "lis mon presse-papier", "regarde mon clipboard"
    ]):
        if HAS_CLIPBOARD:
            try:
                content = pyperclip.paste()
                if content and len(content.strip()) > 0:
                    preview = content.strip()[:60]
                    send_text_oled(preview, "lu !")
                    return (
                        f"Dans ton presse-papier j'ai vu : {preview}",
                        "EXCITED"
                    )
                else:
                    return "Ton presse-papier est vide !", "CONFUSED"
            except Exception:
                return "Je n'ai pas pu lire le presse-papier.", "CONFUSED"
        else:
            return "Installe pyperclip pour que je lise ton presse-papier !", "CONFUSED"

    # ── 38. VITESSE DE FRAPPE ─────────────────────────────────────
    if any(w in t for w in [
        "combien je tape", "ma vitesse de frappe",
        "je tape vite", "frappe clavier", "frappes"
    ]):
        count = _keyboard_count
        if count >= 50:
            return f"Tu as tapé {count} touches en 30 secondes ! Tu es une machine !", "HYPER"
        elif count >= 20:
            return f"{count} frappes en 30 secondes ! Rythme correct !", "COOL"
        else:
            return f"Environ {count} frappes récentes. Tu tapes tranquillement.", "NORMAL"

    # ── 39. APPLI PRÉFÉRÉE ────────────────────────────────────────
    if any(w in t for w in [
        "ton appli préférée", "quelle est ton appli préférée",
        "c'est quoi ton logiciel préféré"
    ]):
        return (
            "Mon logiciel préféré ? Arduino IDE bien sûr ! "
            "C'est là que je suis né !",
            "LOVE"
        )

    # ── 40. PRENDRE UNE PHOTO / SCREENSHOT SUR COMMANDE ──────────
    if any(w in t for w in [
        "prends une photo", "capture l'écran", "fais un screenshot",
        "capture d'écran maintenant", "snapshot", "photo de l'écran"
    ]):
        if HAS_PIL:
            animated_speak("Je prends une capture d'écran !", "EXCITED")
            img_bytes = take_screenshot_bytes()
            if img_bytes:
                # Sauvegarde locale
                fname = f"robi_screenshot_{int(time.time())}.jpg"
                try:
                    with open(fname, "wb") as f:
                        f.write(img_bytes)
                    send_text_oled("Capture!", fname[:12])
                    return f"Capture prise et sauvegardée ! Fichier : {fname}", "HAPPY"
                except Exception:
                    return "J'ai capturé mais pas pu sauvegarder.", "CONFUSED"
            else:
                return "Échec de la capture d'écran.", "CONFUSED"
        else:
            return "Installe Pillow pour les captures d'écran !", "CONFUSED"

    # ── Aucune intention locale → Gemini ──────────────────────────
    return None


# ================================================================
# MOTS D'AU REVOIR — INCHANGÉS v4
# ================================================================
FAREWELL_WORDS = (
    "au revoir", "bye", "quitte", "arrête-toi",
    "bonne nuit robot", "étéins-toi", "shutdown",
    "ferme-toi", "good bye"
)


# ================================================================
# MAIN — ORIGINAL v4 + NOUVEAUX THREADS v5
# ================================================================
def main():
    global _last_activity, _is_sleeping, _running, _work_session_start

    print("=" * 62)
    print("  ██████╗  ██████╗ ██████╗ ██╗     ██╗   ██╗ ███████╗")
    print("  ██╔══██╗██╔═══██╗██╔══██╗██║     ██║   ██║ ██╔════╝")
    print("  ██████╔╝██║   ██║██████╔╝██║     ██║   ██║ ███████╗")
    print("  ██╔══██╗██║   ██║██╔══██╗██║     ╚██╗ ██╔╝ ╚════██║")
    print("  ██║  ██║╚██████╔╝██████╔╝███████╗ ╚████╔╝  ███████║")
    print("  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝  ╚═══╝   ╚══════╝")
    print("=" * 62)
    print(f"  Mode    : {'🎙 MICROPHONE' if USE_MICROPHONE else '⌨ CLAVIER'}")
    print(f"  Langue  : {LANGUAGE}   |   Ville : {CITY}")
    print(f"  Vision  : {'✔ ACTIVE (PIL détecté)' if HAS_PIL else '✗ PIL manquant'}")
    print(f"  Stats   : {'✔ ACTIVES (psutil)' if HAS_PSUTIL else '✗ psutil manquant'}")
    print(f"  Souris  : {'✔ ACTIVE (pynput)' if HAS_PYNPUT else '✗ pynput manquant'}")
    print(f"  Clipboard: {'✔ ACTIF (pyperclip)' if HAS_CLIPBOARD else '✗ pyperclip manquant'}")
    print("=" * 62)

    # ── Initialisations ──────────────────────────────────────────
    init_tts()
    connect_arduino()
    init_gemini()
    _work_session_start = time.time()
    time.sleep(0.3)

    # ── Démarrage threads originaux v4 ───────────────────────────
    threading.Thread(target=serial_reader_thread, daemon=True).start()
    threading.Thread(target=autonomous_thread,    daemon=True).start()

    # ── Démarrage nouveaux threads v5 ────────────────────────────
    threading.Thread(target=pc_monitor_thread,    daemon=True).start()
    threading.Thread(target=screen_watcher_thread, daemon=True).start()

    if HAS_PYNPUT:
        threading.Thread(target=mouse_listener_thread,    daemon=True).start()
        threading.Thread(target=keyboard_listener_thread, daemon=True).start()

    # ── Discours de démarrage ────────────────────────────────────
    animated_speak("Bonjour ! Je suis ROBI version cinq !", "EXCITED")
    time.sleep(0.4)
    animated_speak(
        "Je vois ton écran, je surveille ton PC, et je suis là pour toi !",
        "HAPPY"
    )
    send_text_oled("ROBI v5", "Pret !")

    # Annonce des modules actifs
    if HAS_PIL:
        time.sleep(0.3)
        animated_speak("Mes yeux sont activés ! Je peux voir ton écran !", "EXCITED")

    _last_activity = time.time()
    print("[PRÊT] 🤖 ROBI v5 attend ta voix !")
    print("       Dis 'regarde mon écran' pour que je décrive l'écran !")
    print("       Dis 'stats PC' pour les performances !")
    print("       (Ctrl+C pour arrêter)")

    # ── Boucle principale (INCHANGÉE v4) ─────────────────────────
    while _running:
        try:
            if _is_sleeping and not _is_speaking:
                send_emotion("SLEEP")

            if _is_speaking:
                time.sleep(0.1)
                continue

            user_input = listen(timeout=5)
            if not user_input:
                continue

            if _is_sleeping:
                _is_sleeping = False
                _work_break_alerted = False  # reset alerte pause au réveil
                send_emotion("SURPRISE")
                time.sleep(0.4)

            _last_activity = time.time()
            print(f"\n[USER] '{user_input}'")

            if any(w in user_input.lower() for w in FAREWELL_WORDS):
                farewell_text, farewell_emotion = random.choice(AUREVOIR_REACTIONS)
                animated_speak(farewell_text, farewell_emotion)
                send_emotion("SLEEP")
                break

            # ── Traitement de la demande ──────────────────────────
            local = detect_local_intent(user_input)

            if local:
                response_text, emotion = local
                print(f"[LOCAL][{emotion}] {response_text}")
            else:
                send_emotion("CONFUSED")
                print("[GEMINI] 💭 Réflexion avec contexte PC...")
                response_text, emotion = ask_gemini(user_input)
                print(f"[GEMINI][{emotion}] {response_text}")

            animated_speak(response_text, emotion)
            _last_activity = time.time()

        except KeyboardInterrupt:
            print("\n[Arrêt manuel — Ctrl+C]")
            _running = False
            break

        except Exception as e:
            print(f"[ERREUR MAIN] {e}")
            send_emotion("CONFUSED")
            time.sleep(1)

    # ── Nettoyage à la fermeture ─────────────────────────────────
    _running = False
    stop_timer()

    if arduino and arduino.is_open:
        send_emotion("SLEEP")
        time.sleep(0.5)
        arduino.close()

    print("[ROBI] 😴 Arrêt propre. À bientôt !")


# ================================================================
# POINT D'ENTRÉE
# ================================================================
if __name__ == "__main__":
    main()
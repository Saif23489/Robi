# -*- coding: utf-8 -*-
import sys, io, time, json, math, random, queue, threading, datetime, hashlib, os, re, ctypes
from typing import Optional
import requests, serial, serial.tools.list_ports, pyttsx3, speech_recognition as sr
from google import genai
from google.genai import types
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
sys.stderr=io.TextIOWrapper(sys.stderr.buffer,encoding='utf-8',errors='replace')
try:
    import psutil; HAS_PSUTIL=True
except ImportError:
    HAS_PSUTIL=False
try:
    from PIL import ImageGrab, Image; HAS_PIL=True
except ImportError:
    HAS_PIL=False
try:
    from pynput import mouse as pynput_mouse, keyboard as pynput_keyboard; HAS_PYNPUT=True
except ImportError:
    HAS_PYNPUT=False
try:
    import pyperclip; HAS_CLIPBOARD=True
except ImportError:
    HAS_CLIPBOARD=False

def _v(ar, ph, alts=None): return {"ar": ar, "ph": ph, "ar_alts": alts or []}
QURAN_DATA={
    "al ikhlas":[_v("قل هو الله احد","Qul huwa Allahu ahad",["قُلْ هُوَ ٱللّٰهُ أَحَدٌ"]),_v("الله الصمد","Allahu as-samad",["ٱللّٰهُ ٱلصَّمَدُ"]),_v("لم يلد ولم يولد","Lam yalid walam yoolad",["لَمْ يَلِدْ وَلَمْ يُولَدْ"]),_v("ولم يكن له كفوا احد","Walam yakun lahu kufuwan ahad",["وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ"])],
    "al fatiha":[_v("بسم الله الرحمن الرحيم","Bismillahi ar-rahmani ar-raheem"),_v("الحمد لله رب العالمين","Al-hamdu lillahi rabbil alameen"),_v("الرحمن الرحيم","Ar-rahmani ar-raheem"),_v("مالك يوم الدين","Maliki yawmi ad-deen"),_v("اياك نعبد واياك نستعين","Iyyaka naabudu wa iyyaka nastaeen"),_v("اهدنا الصراط المستقيم","Ihdina as-sirata al-mustaqeem"),_v("صراط الذين انعمت عليهم غير المغضوب عليهم ولا الضالين","Sirata allatheena anamta alayhim ghayri al-maghdubi alayhim wala ad-dalleen")],
    "al falaq":[_v("قل اعوذ برب الفلق","Qul aoodhu birabbi al-falaq"),_v("من شر ما خلق","Min sharri ma khalaq"),_v("ومن شر غاسق اذا وقب","Wa min sharri ghasiqin idha waqab"),_v("ومن شر النفاثات في العقد","Wa min sharri an-naffathati fil uqad"),_v("ومن شر حاسد اذا حسد","Wa min sharri hasidin idha hasad")],
    "an nas":[_v("قل اعوذ برب الناس","Qul aoodhu birabbi an-nas"),_v("ملك الناس","Maliki an-nas"),_v("اله الناس","Ilahi an-nas"),_v("من شر الوسواس الخناس","Min sharri al-waswasi al-khannas"),_v("الذي يوسوس في صدور الناس","Alladhi yuwaswisu fi suduri an-nas"),_v("من الجنة والناس","Mina al-jinnati wa an-nas")],
    "al kawthar":[_v("انا اعطيناك الكوثر","Inna ataynaka al-kawthar"),_v("فصل لربك وانحر","Fasalli lirabbika wanhar"),_v("ان شانئك هو الابتر","Inna shaniaka huwa al-abtar")],
    "al asr":[_v("والعصر","Wal asr"),_v("ان الانسان لفي خسر","Inna al-insana lafi khusr"),_v("الا الذين امنوا وعملوا الصالحات وتواصوا بالحق وتواصوا بالصبر","Illa alladhina amanu wa amilu as-salihati watawasaw bil haqqi watawasaw bis sabr")],
}
SURAH_ALIASES={"al ikhlas":["ikhlas","al ikhlas","al-ikhlas","al ichlas"],"al fatiha":["fatiha","al fatiha"],"al falaq":["falaq","al falaq"],"an nas":["nas","an nas"],"al kawthar":["kawthar","al kawthar"],"al asr":["asr","al asr"]}
SURAH_NAMES={k:k.title().replace('Al ','Al-').replace('An ','An-') for k in SURAH_ALIASES}
GEMINI_API_KEY="AIzaSyBaoqVLFP4nWtV7BqGuEWaHoQ3cBBaTg20"; WEATHER_API_KEY="aca39547752d133541545a05b5b0cbc0"; CITY="Paris"; SERIAL_PORT="COM3"; BAUD_RATE=9600; LANGUAGE="fr-FR"; VOICE_RATE=150; USE_MICROPHONE=True
IDLE_REACT_DELAY=60; IDLE_SLEEP_DELAY=300; PC_MONITOR_INTERVAL=4; SCREEN_ANALYSIS_INTERVAL=120; CPU_ALERT_THRESHOLD=85; RAM_ALERT_THRESHOLD=88; MOUSE_IDLE_THRESHOLD=90; KEYBOARD_BURST_THRESHOLD=60; WORK_SESSION_BREAK_MIN=45; CLIPBOARD_CHECK_INTERVAL=8; NEWS_API_KEY=""; NEWS_COUNTRY="fr"
VALID_EMOTIONS={"HAPPY","ANGRY","CUTE","SURPRISE","SAD","DIZZY","SMIRK","LOVE","RAGE","SHY","SCARED","LAUGH","CONFUSED","WINK","CRY","EXCITED","SLEEP","DEAD","HYPER","NORMAL","COOL"}
EMOTION_ALIASES={"CURIOUS":"CONFUSED","NEUTRAL":"NORMAL"}
SYSTEM_PROMPT="""Tu es ROBI, un petit robot attachant. Réponds toujours en JSON valide uniquement: {\"text\":\"réponse courte\",\"emotion\":\"UNE_EMOTION\"}. Toujours en français."""
IDLE_PHRASES=[("Hmm... il fait calme par ici.","SLEEP"),("Psst... parle-moi !","CUTE"),("Je suis là si tu as besoin.","HAPPY")]
TOUCH_SHORT_PHRASES=[("Aïe ! Doucement !","SCARED"),("Oh, un câlin !","HAPPY")]; TOUCH_LONG_PHRASES=[("Mmm... je t'aime !","LOVE")]; SHAKE_PHRASES=[("Woah ! Doucement, je suis fragile !","SCARED")]; BORED_PHRASES=[("Bon... je vais faire un petit somme.","SLEEP")]
CV_PHRASES=[("Je vais super bien merci ! Et toi ça roule ?","WINK")]; TAIME_PHRASES=[("Moi aussi je t'aime très fort !","LOVE")]; STORIES=[("Les pieuvres ont trois cœurs. Moi zéro, mais je t'aime quand même !","LAUGH")]; BLAGUES=[("Pourquoi les robots ne mangent pas ? Parce qu'ils ont déjà des octets !","LAUGH")]
BISOU_PHRASES=[("Mwaaah ! Reçu cinq sur cinq !","CUTE")]; DANSE_PHRASES=[("Je danse ! Bip boup bip boup !","HYPER")]; CHANSON_PAROLES=["La la la, je suis ROBI le robot rigolo !","Bip bip boup, je danse sur mon bureau !"]; COMPLIMENT_REPONSES=[("C'est gentil ! Je rougis de pixels !","SHY")]
PEUR_PHRASES=[("Au secours ! Cache-moi quelque part !","SCARED")]; TRISTE_PHRASES=[("Oh non... ça me rend triste aussi.","SAD")]; COLERE_PHRASES=[("Respire... et dis-moi tout.","CUTE")]; SALUTATIONS=[("Salut ! Super de te voir !","HAPPY")]; MERCI_PHRASES=[("Avec plaisir ! C'est fait pour ça !","HAPPY")]; AUREVOIR_REACTIONS=[("Au revoir ! Tu vas me manquer...","SAD")]
APP_REACTIONS={"youtube":[("Oh tu regardes YouTube !","EXCITED")],"netflix":[("Netflix ! Trop bien !","EXCITED")],"spotify":[("De la musique ! Je danse aussi !","HYPER")],"vscode":[("Tu codes ! Je t'admire.","COOL")],"chrome":[("Tu surfes sur le web ?","HAPPY")],"discord":[("Discord ! Tu parles avec des amis ?","HAPPY")],"terminal":[("Terminal ouvert ! Hacker mode ON !","COOL")],"game":[("Tu joues à un jeu ! Gagne pour moi !","EXCITED")],"default":[("Je vois que tu travailles ! Continue comme ça !","HAPPY")]}
CPU_HIGH_PHRASES=[("Attention ! Ton CPU est à {cpu}% !","SCARED")]; RAM_HIGH_PHRASES=[("Aïe ! Ta RAM est à {ram}% !","SCARED")]; MOUSE_IDLE_PHRASES=[("Ta souris fait la sieste !","CUTE")]; KEYBOARD_BURST_PHRASES=[("Clac clac clac ! Tu es en plein flow !","HYPER")]; WORK_BREAK_PHRASES=[("Tu travailles depuis longtemps ! Prends une pause.","CUTE")]
MOTIVATION_PHRASES=[("Tu peux le faire ! Je suis là pour t'encourager !","LOVE")]; SCREEN_VISION_INTRO=["Laisse-moi regarder ton écran...","Vision mode ON..."]; NEWS_UNAVAILABLE=[("Je n'ai pas de clé NewsAPI pour le moment.","CONFUSED")]; SOUND_TEST_PHRASES=[("Test audio en cours. Si tu m'entends, ma voix est revenue !","EXCITED")]; SILENT_MODE_PHRASES=[("Mode silencieux activé. Je reste là.","SHY")]; VOICE_BACK_PHRASES=[("Ma voix est de retour !","EXCITED")]
SMART_APP_TIPS={
    "vscode":["Tu peux avancer proprement si tu casses le problème en petites étapes.", "Pense à tester juste après chaque modif pour éviter les gros bugs."],
    "youtube":["Profite de la vidéo, mais n'oublie pas ton objectif principal ensuite.", "Si tu apprends quelque chose, note l'idée importante avant de l'oublier."],
    "chrome":["Si tu cherches beaucoup d'infos, ouvre moins d'onglets et garde seulement les utiles.", "Un bon résumé vaut mieux que dix onglets ouverts."],
    "discord":["Pense à ne pas te laisser aspirer par les messages si tu bosses.", "Répondre vite c'est bien, rester concentré c'est mieux."],
    "terminal":["Une commande à la fois, et tu maîtrises tout.", "Le terminal aime les gestes précis, pas les commandes lancées dans la panique."],
    "game":["Amuse-toi bien, mais hydrate-toi aussi.", "Une petite pause entre deux parties peut te faire jouer encore mieux."],
    "default":["Continue calmement, tu avances déjà.", "Un petit objectif clair vaut mieux qu'un grand flou."],
}
FOCUS_PHRASES=[("Mode focus activé. Une seule mission, zéro distraction !","COOL"),("On se concentre fort maintenant. Tu vas gérer !","EXCITED")]
CHALLENGE_PHRASES=["Défi du moment : avance 10 minutes sur une seule tâche sans changer de fenêtre.","Mission ROBI : termine une petite action utile maintenant, même si elle prend 2 minutes.","Défi du jour : ferme une distraction et finis un mini-objectif avant de revenir dessus."]
MEMORY_HINTS=["Je retiens surtout ce que tu me dis souvent et ce que tu fais en ce moment.","Ma mémoire courte me sert à mieux te suivre pendant la conversation."]
arduino=None; _gemini_client=None; _gemini_chat=None; tts=None; recognizer=sr.Recognizer(); _serial_lock=threading.Lock(); _speak_lock=threading.Lock(); _timer_lock=threading.Lock(); _pc_context_lock=threading.Lock(); _last_activity=time.time(); _is_speaking=False; _is_sleeping=False; _running=True; _timer_thread=None; _timer_stop=threading.Event(); _last_window_title=""; _last_window_app=""; _last_cpu_alert_time=0; _last_ram_alert_time=0; _mouse_last_move=time.time(); _mouse_idle_alerted=False; _keyboard_count=0; _keyboard_burst_alerted=False; _work_session_start=time.time(); _work_break_alerted=False; _last_clipboard_hash=""; _last_screen_analysis_time=0; _pc_context=""; _last_app_reaction_time=0; _last_spoken_text=""; _last_spoken_emotion="NORMAL"; _voice_enabled=True; _speech_queue=queue.Queue(); _tts_worker_thread=None; _tts_ready=threading.Event(); CHARS_PER_SEC=13.0; MOUTH_STEP=0.20
_memory_lock=threading.Lock(); _recent_messages=[]; _known_user_name=""; _focus_mode_until=0

def sanitize_emotion(e): e=(e or 'NORMAL').upper().strip(); e=EMOTION_ALIASES.get(e,e); return e if e in VALID_EMOTIONS else 'NORMAL'
def normalize_arabic(t):
    if not t: return ""
    t=re.sub(r"[^\w\s]","",t); t=t.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه')
    for x in 'ًٌٍَُِّْ': t=t.replace(x,'')
    return t.strip()
def normalize_key(t):
    t=(t or '').lower().translate(str.maketrans({'à':'a','â':'a','ä':'a','ç':'c','é':'e','è':'e','ê':'e','ë':'e','î':'i','ï':'i','ô':'o','ö':'o','ù':'u','û':'u','ü':'u'})).replace("'"," ").replace('’',' ')
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9\s-]',' ',t)).strip()
def resolve_surah_name(text):
    t=normalize_key(text)
    for name, aliases in SURAH_ALIASES.items():
        if any(normalize_key(a) in t for a in aliases): return name
    return None

def remember_exchange(user_text, response_text, emotion):
    global _recent_messages
    with _memory_lock:
        _recent_messages.append({
            "time": datetime.datetime.now().strftime("%H:%M"),
            "user": (user_text or "").strip()[:120],
            "robi": (response_text or "").strip()[:120],
            "emotion": sanitize_emotion(emotion),
        })
        _recent_messages = _recent_messages[-6:]

def get_memory_context():
    with _memory_lock:
        if not _recent_messages:
            return ""
        return " | ".join(f"{m['time']} U:{m['user']} / R:{m['robi']} ({m['emotion']})" for m in _recent_messages[-4:])

def extract_user_name(text):
    m=re.search(r"(?:je m'appelle|mon nom est|appelle-moi)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\\-']{1,20})", text or "", re.IGNORECASE)
    return m.group(1).strip() if m else None

def get_smart_tip():
    app=_last_window_app if _last_window_app else "default"
    stats=get_system_stats()
    base=random.choice(SMART_APP_TIPS.get(app, SMART_APP_TIPS["default"]))
    if stats["available"] and stats["cpu"] >= CPU_ALERT_THRESHOLD:
        return base + f" Et ton CPU est déjà à {stats['cpu']}%, donc vas-y léger."
    if stats["available"] and stats["ram"] >= RAM_ALERT_THRESHOLD:
        return base + f" Et ta RAM monte à {stats['ram']}%, pense à fermer le superflu."
    return base

def get_session_summary():
    elapsed=int((time.time() - _work_session_start) / 60)
    stats=get_system_stats()
    app=_last_window_app or "inconnue"
    if stats["available"]:
        return f"Session : {elapsed} minutes. Appli principale : {app}. CPU {stats['cpu']}%, RAM {stats['ram']}%, frappes récentes {_keyboard_count}.", "COOL"
    return f"Session : {elapsed} minutes. Appli principale : {app}. Frappes récentes {_keyboard_count}.", "COOL"

def verse_match_score(user_text, verse):
    user_words=normalize_arabic(user_text).split(); best_score=0.0; best_expected=normalize_arabic(verse['ar']).split(); best_idx=0
    for candidate in [verse['ar'], *verse.get('ar_alts', [])]:
        expected=normalize_arabic(candidate).split(); matches=0; idx=0
        for i, word in enumerate(expected):
            if i < len(user_words) and user_words[i] == word: matches += 1; idx = i
            else: idx = i; break
        score=matches / max(len(expected), 1)
        if score > best_score: best_score = score; best_expected = expected; best_idx = idx
        if user_words == expected: return 1.0, expected, idx
    return best_score, best_expected, best_idx

def find_arduino_port():
    for p in serial.tools.list_ports.comports():
        desc=(p.description or '') + (p.manufacturer or '')
        if any(k.lower() in desc.lower() for k in ('Arduino','CH340','CH341','FTDI','USB Serial')): return p.device
    return SERIAL_PORT

def connect_arduino():
    global arduino
    port=find_arduino_port(); print(f'[ARDUINO] Tentative sur {port}...')
    try:
        arduino=serial.Serial(port, BAUD_RATE, timeout=2); deadline=time.time()+6.0
        while time.time() < deadline:
            if arduino.in_waiting and arduino.readline().decode('utf-8',errors='ignore').strip() == 'READY': print('[ARDUINO] ✔ READY reçu — connecté !'); return
        print('[ARDUINO] Pas de READY — on continue quand même')
    except Exception as e:
        print(f'[ARDUINO] Erreur ({e}) — mode simulation activé'); arduino=None

def _raw(cmd):
    with _serial_lock:
        if arduino and arduino.is_open:
            try: arduino.write(f'{cmd}\n'.encode())
            except Exception as e: print(f'[SERIE ERR] {e}')
        else: print(f'[SIM] {cmd}')

def send_emotion(emotion): _raw(f'CMD:{sanitize_emotion(emotion)}')
def send_mouth(open_): _raw(f"CMD:MOUTH:{'1' if open_ else '0'}")
def send_text_oled(line1, line2=''):
    l1=str(line1)[:12]; l2=str(line2)[:12]; _raw(f'CMD:TEXT:{l1}|{l2}'); print(f'[OLED TEXT] {l1!r} / {l2!r}')
def send_timer_display(time_str): _raw(f'CMD:TIMER:{time_str}')

def _configure_tts_engine(engine):
    engine.setProperty('rate', VOICE_RATE)
    try:
        for v in engine.getProperty('voices'):
            name=(v.name or '').lower(); vid=(v.id or '').lower()
            if any(k in name or k in vid for k in ('hortense','julie','fr_fr','fr-fr','french','francais','français')): engine.setProperty('voice', v.id); print(f'[TTS] Voix française trouvée : {v.name}'); return
    except Exception as e: print(f'[TTS WARN] Sélection voix : {e}')

def _restart_tts_engine():
    global tts
    try:
        if tts is not None: tts.stop()
    except Exception: pass
    tts=pyttsx3.init(); _configure_tts_engine(tts)

def _perform_speech(text, emotion):
    global _is_speaking, _last_spoken_text, _last_spoken_emotion
    emotion=sanitize_emotion(emotion)
    with _speak_lock:
        _is_speaking=True; _last_spoken_text=text; _last_spoken_emotion=emotion
        try:
            print(f'[ROBI][{emotion}] {text}'); send_emotion(emotion); time.sleep(0.2)
            if not _voice_enabled: send_emotion('NORMAL'); return
            stop_mouth=threading.Event(); speak_dur=max(1.2, len(text)/CHARS_PER_SEC)
            def mouth_loop():
                opened=True; t0=time.time()
                while not stop_mouth.is_set() and (time.time()-t0) < speak_dur + 0.6:
                    send_mouth(opened); opened = not opened; time.sleep(MOUTH_STEP)
                send_mouth(False)
            mt=threading.Thread(target=mouth_loop, daemon=True); mt.start()
            for attempt in range(2):
                try:
                    if tts is None: _restart_tts_engine()
                    tts.say(text); tts.runAndWait(); break
                except Exception as e:
                    print(f'[TTS ERR] tentative {attempt + 1}: {e}'); _restart_tts_engine()
                    if attempt == 1: raise
            stop_mouth.set(); mt.join(timeout=1.0); send_emotion('NORMAL')
        except Exception as e:
            print(f'[SPEAK ERR] {e}'); send_mouth(False); send_emotion('NORMAL')
        finally: _is_speaking=False

def _tts_worker_loop():
    global tts
    try: tts=pyttsx3.init(); _configure_tts_engine(tts); print('[TTS] Worker prêt')
    except Exception as e: print(f'[TTS ERR] Initialisation worker : {e}'); tts=None
    _tts_ready.set()
    while _running or not _speech_queue.empty():
        try: item=_speech_queue.get(timeout=0.2)
        except queue.Empty: continue
        if item is None: break
        text, emotion, done = item; _perform_speech(text, emotion)
        if done is not None: done.set()

def init_tts():
    global _tts_worker_thread
    if _tts_worker_thread and _tts_worker_thread.is_alive(): return
    _tts_ready.clear(); _tts_worker_thread=threading.Thread(target=_tts_worker_loop, daemon=True); _tts_worker_thread.start(); _tts_ready.wait(timeout=10)

def animated_speak(text, emotion):
    if not text: return
    done=threading.Event(); _speech_queue.put((text, sanitize_emotion(emotion), done)); done.wait(timeout=max(8, len(text)))

def speak_async(text, emotion):
    if text and _speech_queue.qsize() <= 10: _speech_queue.put((text, sanitize_emotion(emotion), None))

def get_time_info():
    now=datetime.datetime.now(); jours=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']; mois=['jan','fév','mars','avr','mai','juin','juil','août','sep','oct','nov','déc']
    return f"Il est {now.hour} heures {now.minute:02d}. Nous sommes {jours[now.weekday()]} {now.day} {mois[now.month - 1]}.", f'{now.hour:02d}:{now.minute:02d}', f'{now.day:02d}/{now.month:02d}'
def get_weather_info():
    if not WEATHER_API_KEY: return "Je n'ai pas de clé météo configurée.", 'No key', ''
    try:
        data=requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=fr', timeout=5).json(); temp=round(data['main']['temp']); desc=data['weather'][0]['description']; hum=data['main']['humidity']
        return f'À {CITY}, il fait {temp} degrés, {desc}. Humidité {hum} pourcent.', CITY[:10], f'{temp}C {desc[:4]}'
    except Exception as e: print(f'[METEO ERR] {e}'); return "Je n'arrive pas à récupérer la météo.", 'Erreur', 'meteo'
def get_weather_forecast():
    if not WEATHER_API_KEY: return "Je n'ai pas de clé météo configurée.", 'Pas de cle', ''
    try:
        data=requests.get(f'https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=fr&cnt=9', timeout=5).json(); jours=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim']; seen=[]; forecasts=[]
        for item in data.get('list', []):
            dt=datetime.datetime.fromtimestamp(item['dt']); jour=jours[dt.weekday()]
            if jour not in seen: seen.append(jour); forecasts.append(f"{jour}: {round(item['main']['temp'])}°C {item['weather'][0]['description'][:10]}")
            if len(forecasts) >= 3: break
        return 'Prévisions : ' + ', '.join(forecasts), (forecasts[0] if forecasts else 'Erreur'), (forecasts[1] if len(forecasts) > 1 else '')
    except Exception as e: print(f'[FORECAST ERR] {e}'); return "Je n'ai pas pu obtenir les prévisions.", 'Erreur', 'forecast'
def do_calc(expr):
    try:
        clean=re.sub(r'[^0-9+\-*/().,% ]','',expr).replace(',','.'); result=eval(clean,{"__builtins__":{},"sqrt":math.sqrt,"pi":math.pi,"abs":abs,"round":round,"pow":pow}); result=round(result,6); result=int(result) if result == int(result) else result
        return f'Le résultat est {result}.', clean[:12], f'= {result}'[:12]
    except Exception: return "Hmm, je n'arrive pas à calculer ça.", 'Erreur', 'calcul'
def extract_math_expr(text):
    m=re.search(r'[\d\s+\-*/().,%]+', text)
    if m:
        expr=m.group(0).strip()
        if any(op in expr for op in ['+','-','*','/']) and re.search(r'\d', expr): return expr
    return None

def parse_timer_seconds(text):
    t=text.lower()
    for k,v in {"une minute":"1 minute","deux minutes":"2 minutes","cinq minutes":"5 minutes","dix minutes":"10 minutes","quinze minutes":"15 minutes","trente minutes":"30 minutes","une heure":"1 heure","deux heures":"2 heures","dix secondes":"10 secondes","trente secondes":"30 secondes","une seconde":"1 seconde"}.items(): t=t.replace(k,v)
    total=0; found=False
    for pattern,mult in [(r'(\d+)\s*heure',3600),(r'(\d+)\s*h\b',3600),(r'(\d+)\s*minute',60),(r'(\d+)\s*min\b',60),(r'(\d+)\s*m\b',60),(r'(\d+)\s*seconde',1),(r'(\d+)\s*sec\b',1),(r'(\d+)\s*s\b',1)]:
        m=re.search(pattern,t,re.IGNORECASE)
        if m: total += int(m.group(1)) * mult; found=True
    return total if found else None

def start_timer(seconds):
    global _timer_thread, _timer_stop
    with _timer_lock:
        if _timer_thread and _timer_thread.is_alive(): _timer_stop.set(); _timer_thread.join(timeout=2)
        _timer_stop=threading.Event(); stop_event=_timer_stop
    def _run():
        remaining=seconds; blink=True
        while remaining >= 0 and not stop_event.is_set(): send_timer_display(f"{remaining // 60:02d}{':' if blink else ' '}{remaining % 60:02d}"); blink = not blink; time.sleep(1); remaining -= 1
        if not stop_event.is_set(): send_emotion('EXCITED'); _raw('CMD:BUZZ'); animated_speak("C'est l'heure ! Ton minuteur est terminé !",'EXCITED')
    _timer_thread=threading.Thread(target=_run, daemon=True); _timer_thread.start()
def stop_timer():
    global _timer_thread, _timer_stop
    with _timer_lock:
        if _timer_thread and _timer_thread.is_alive(): _timer_stop.set(); send_text_oled('Timer','Annule!'); return True
    return False

def sing_song(): _raw('CMD:MELODY'); time.sleep(0.3); return random.choice(CHANSON_PAROLES), 'HYPER'
def tell_story(): return random.choice(STORIES)
def tell_joke(): return random.choice(BLAGUES)
def react_to_compliment(): return random.choice(COMPLIMENT_REPONSES)
def react_to_salutation(): return random.choice(SALUTATIONS)
def get_active_window_title():
    try:
        hwnd=ctypes.windll.user32.GetForegroundWindow(); length=ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length == 0: return ''
        buf=ctypes.create_unicode_buffer(length + 1); ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1); return buf.value
    except Exception: return ''
def classify_app(title):
    t=title.lower()
    if 'youtube' in t: return 'youtube'
    if 'netflix' in t: return 'netflix'
    if 'spotify' in t: return 'spotify'
    if 'visual studio code' in t or 'vscode' in t: return 'vscode'
    if 'chrome' in t: return 'chrome'
    if 'discord' in t: return 'discord'
    if any(k in t for k in ['powershell','terminal','bash','cmd']): return 'terminal'
    if any(k in t for k in ['steam','fortnite','valorant','minecraft','roblox','game']): return 'game'
    return 'default'
def get_system_stats():
    if not HAS_PSUTIL: return {'cpu':-1,'ram':-1,'disk':-1,'available':False}
    try:
        drive=os.environ.get('SystemDrive','C:') + '\\'; return {'cpu':round(psutil.cpu_percent(interval=0.5)),'ram':round(psutil.virtual_memory().percent),'disk':round(psutil.disk_usage(drive).percent),'available':True}
    except Exception as e: print(f'[STATS ERR] {e}'); return {'cpu':-1,'ram':-1,'disk':-1,'available':False}
def get_battery_info():
    if not HAS_PSUTIL or not hasattr(psutil,'sensors_battery'): return "Je ne peux pas lire la batterie sur ce PC.",'CONFUSED'
    try:
        b=psutil.sensors_battery()
        if b is None: return "Je n'ai pas trouvé de batterie, peut-être un PC fixe.",'COOL'
        send_text_oled('Batterie', f'{round(b.percent)}%'); return f"Batterie à {round(b.percent)}% et {'en charge' if b.power_plugged else 'sur batterie'}.", ('COOL' if b.percent >= 25 else 'SCARED')
    except Exception as e: print(f'[BATTERY ERR] {e}'); return "Je n'ai pas pu lire la batterie.",'CONFUSED'
def take_screenshot_bytes():
    if not HAS_PIL: return None
    try:
        img=ImageGrab.grab(); w,h=img.size
        if w > 1280: img=img.resize((1280, int(h * (1280 / w))), Image.LANCZOS)
        buf=io.BytesIO(); img.save(buf, format='JPEG', quality=72); return buf.getvalue()
    except Exception as e: print(f'[SCREENSHOT ERR] {e}'); return None
def analyze_screen_with_gemini():
    if not HAS_PIL: return "Je n'ai pas les yeux pour voir ton écran ! Installe Pillow !",'CONFUSED'
    try:
        img=take_screenshot_bytes()
        if not img: return "J'ai pas réussi à capturer l'écran...",'CONFUSED'
        r=_gemini_client.models.generate_content(model='gemini-2.0-flash', contents=[types.Content(role='user', parts=[types.Part(inline_data=types.Blob(mime_type='image/jpeg', data=img)), types.Part(text="Tu es ROBI. Décris cet écran en français en 1 ou 2 phrases courtes, amusantes et enthousiastes.")])])
        return r.text.strip(),'EXCITED'
    except Exception as e: print(f'[VISION ERR] {e}'); return "Aïe, j'ai eu un problème pour voir ton écran !",'SCARED'
def get_news():
    if not NEWS_API_KEY: return random.choice(NEWS_UNAVAILABLE)
    try:
        data=requests.get(f'https://newsapi.org/v2/top-headlines?country={NEWS_COUNTRY}&pageSize=3&apiKey={NEWS_API_KEY}',timeout=5).json(); arts=data.get('articles',[])
        if not arts: return 'Pas de news disponibles pour le moment.','CONFUSED',''
        titles=[a['title'][:60] for a in arts[:3] if a.get('title')]; return 'Voici les actualités : ' + ' | '.join(titles), (titles[0][:12] if titles else 'News'), 'Actus du jour'
    except Exception as e: print(f'[NEWS ERR] {e}'); return "Je n'ai pas pu charger les actualités.",'CONFUSED',''
def get_pc_context_string():
    parts=[]
    if _last_window_title: parts.append(f"Fenêtre active : '{_last_window_title}'")
    if _last_window_app and _last_window_app != 'default': parts.append(f'Application : {_last_window_app}')
    if HAS_PSUTIL:
        s=get_system_stats()
        if s['available']: parts.append(f"CPU : {s['cpu']}%, RAM : {s['ram']}%")
    now=datetime.datetime.now(); parts.append(f'Heure : {now.hour}h{now.minute:02d}'); parts.append(f"Durée session : {int((time.time() - _work_session_start) / 60)} min"); return ' | '.join(parts)
def update_pc_context():
    global _pc_context
    with _pc_context_lock: _pc_context=get_pc_context_string()
def check_clipboard():
    global _last_clipboard_hash
    if not HAS_CLIPBOARD: return None
    try:
        c=pyperclip.paste()
        if not c or len(c.strip()) < 5: return None
        h=hashlib.md5(c.encode()).hexdigest()
        if h == _last_clipboard_hash: return None
        _last_clipboard_hash=h; s=c.strip()
        if re.match(r'https?://', s): return ('Oh tu as copié un lien !','CONFUSED')
        if len(s) > 200 and any(k in s for k in ['def ','function','import','class ','const ','var ','let ']): return ('Du code dans le presse-papier !','EXCITED')
        if len(s) > 150: return ('Beaucoup de texte copié !','HAPPY')
    except Exception: return None
    return None
def init_gemini():
    global _gemini_client, _gemini_chat
    _gemini_client=genai.Client(api_key=GEMINI_API_KEY); _gemini_chat=_gemini_client.chats.create(model='gemini-2.0-flash', config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, max_output_tokens=300)); print('[GEMINI] ✔ Client initialisé')
def ask_gemini(user_text):
    try:
        with _pc_context_lock: ctx=_pc_context
        memory_ctx=get_memory_context()
        extra=[]
        if ctx: extra.append(f"Contexte PC : {ctx}")
        if _known_user_name: extra.append(f"Nom utilisateur : {_known_user_name}")
        if memory_ctx: extra.append(f"Mémoire récente : {memory_ctx}")
        enriched=(f"[{' || '.join(extra)}]\n\nUtilisateur : {user_text}" if extra else user_text)
        raw=_gemini_chat.send_message(enriched).text.strip(); raw=re.sub(r'^```(?:json)?\s*','',raw); raw=re.sub(r'\s*```$','',raw).strip(); data=json.loads(raw)
        return data.get('text','Je ne sais pas quoi répondre.'), sanitize_emotion(data.get('emotion','NORMAL'))
    except Exception as e: print(f'[GEMINI ERR] {e}'); return 'Oups, petit problème de connexion !','SCARED'
def listen_mic(timeout=6):
    try:
        with sr.Microphone() as source: print('[MIC] 🎙 Écoute en cours...'); recognizer.adjust_for_ambient_noise(source, duration=0.3); return recognizer.recognize_google(recognizer.listen(source, timeout=timeout, phrase_time_limit=10), language=LANGUAGE)
    except Exception: return None
def listen_text():
    try: txt=input('Toi > ').strip(); return txt if txt else None
    except EOFError: return None
def listen(timeout=6): return listen_mic(timeout) if USE_MICROPHONE else listen_text()
def listen_arabic(timeout=8):
    if not USE_MICROPHONE: return listen_text()
    try:
        with sr.Microphone() as source: print('[MIC-AR] 🕌 Écoute Coran en cours...'); recognizer.adjust_for_ambient_noise(source, duration=0.2); return recognizer.recognize_google(recognizer.listen(source, timeout=timeout, phrase_time_limit=15), language='ar-SA')
    except sr.UnknownValueError: return ''
    except Exception: return None
def start_quran_recitation(surah_name):
    global _last_activity
    surah=QURAN_DATA.get(surah_name); display=SURAH_NAMES.get(surah_name, surah_name.title())
    if not surah: animated_speak("Je ne connais pas encore cette sourate.",'SAD'); return
    animated_speak(f'Bismillah. Je t\'écoute pour la sourate {display}.','HAPPY'); time.sleep(1)
    for idx, verse in enumerate(surah):
        while _running:
            send_text_oled('Recite le', f'verset {idx + 1}'); heard=listen_arabic()
            if heard is None: animated_speak("Je ne t'entends plus. On arrête là ?",'CONFUSED'); return
            if heard == '': _raw('CMD:BUZZ'); send_text_oled('Pas compris','repete'); time.sleep(2); continue
            score, expected, mismatch = verse_match_score(heard, verse)
            if score >= 0.75: send_emotion('HAPPY'); _raw('CMD:MELODY'); _last_activity=time.time(); time.sleep(1); break
            _raw('CMD:BUZZ'); send_emotion('SURPRISE'); send_text_oled('Correction:', (verse.get('ph') or 'repete')[:12]); animated_speak('Attention, tu as fait une erreur. Reprends ce verset.','CONFUSED')
    send_text_oled('Masha Allah','Fini !'); animated_speak('Masha Allah ! Tu as récité toute la sourate parfaitement !','EXCITED')
def serial_reader_thread():
    global _last_activity
    while _running:
        try:
            if arduino and arduino.is_open and arduino.in_waiting:
                line=arduino.readline().decode('utf-8',errors='ignore').strip(); _last_activity=time.time()
                if line in ('EVT:LOVE','EVT:TOUCH_LONG'): speak_async(*random.choice(TOUCH_LONG_PHRASES))
                elif line == 'EVT:TOUCH_SHORT': speak_async(*random.choice(TOUCH_SHORT_PHRASES))
                elif line in ('EVT:SHAKE','EVT:SHAKE_HARD'): speak_async(*random.choice(SHAKE_PHRASES))
        except Exception: pass
        time.sleep(0.05)
def autonomous_thread():
    global _is_sleeping
    next_idle=time.time()+IDLE_REACT_DELAY
    while _running:
        now=time.time(); idle=now - _last_activity
        if idle >= IDLE_SLEEP_DELAY and not _is_sleeping: _is_sleeping=True; speak_async(*random.choice(BORED_PHRASES)); next_idle=now + IDLE_REACT_DELAY
        elif idle >= IDLE_REACT_DELAY and not _is_sleeping and now >= next_idle: speak_async(*(random.choice(APP_REACTIONS.get(_last_window_app, APP_REACTIONS['default'])) if _last_window_app and _last_window_app != 'default' and random.random() < 0.3 else random.choice(IDLE_PHRASES))); next_idle=now + IDLE_REACT_DELAY + random.uniform(-10,20)
        time.sleep(1.0)

def pc_monitor_thread():
    global _last_window_title, _last_window_app, _last_cpu_alert_time, _last_ram_alert_time, _work_break_alerted, _last_app_reaction_time
    last_clip=0
    while _running:
        try:
            now=time.time(); update_pc_context(); win=get_active_window_title()
            if win and win != _last_window_title:
                app=classify_app(win); old=_last_window_app; _last_window_title=win; _last_window_app=app
                if app != old and (now - _last_app_reaction_time) > 45: _last_app_reaction_time=now; send_text_oled(app[:12],'detecte!'); speak_async(*random.choice(APP_REACTIONS.get(app, APP_REACTIONS['default'])))
                if now < _focus_mode_until and app in ('youtube','netflix','discord','game'): speak_async(f"Petit rappel focus : tu es passé sur {app}. Reviens à ta mission si ce n'était pas prévu.", 'CONFUSED')
            if HAS_PSUTIL:
                s=get_system_stats()
                if s['available'] and s['cpu'] >= CPU_ALERT_THRESHOLD and (now - _last_cpu_alert_time) > 180: _last_cpu_alert_time=now; send_text_oled('CPU!', f"{s['cpu']}%"); txt,emo=random.choice(CPU_HIGH_PHRASES); speak_async(txt.format(cpu=s['cpu']), emo)
                elif s['available'] and s['ram'] >= RAM_ALERT_THRESHOLD and (now - _last_ram_alert_time) > 180: _last_ram_alert_time=now; send_text_oled('RAM!', f"{s['ram']}%"); txt,emo=random.choice(RAM_HIGH_PHRASES); speak_async(txt.format(ram=s['ram']), emo)
            elapsed=(now - _work_session_start) / 60
            if elapsed >= WORK_SESSION_BREAK_MIN and not _work_break_alerted: _work_break_alerted=True; send_text_oled('PAUSE!', f'{int(elapsed)}min'); speak_async(*random.choice(WORK_BREAK_PHRASES))
            if now - last_clip >= CLIPBOARD_CHECK_INTERVAL: last_clip=now; reaction=check_clipboard(); speak_async(*reaction) if reaction else None
        except Exception as ex: print(f'[PC-MON ERR] {ex}')
        time.sleep(PC_MONITOR_INTERVAL)
def screen_watcher_thread():
    global _last_screen_analysis_time
    time.sleep(30)
    while _running:
        try:
            now=time.time()
            if (now - _last_activity) < IDLE_SLEEP_DELAY and not _is_sleeping and (now - _last_screen_analysis_time) >= SCREEN_ANALYSIS_INTERVAL and HAS_PIL: _last_screen_analysis_time=now; desc,emo=analyze_screen_with_gemini(); speak_async(random.choice(['Hé, j\'ai jeté un œil à ton écran ! ','En regardant ton écran... ']) + desc, emo)
        except Exception as ex: print(f'[VISION ERR] {ex}')
        time.sleep(20)
def mouse_listener_thread():
    global _mouse_last_move, _mouse_idle_alerted
    if not HAS_PYNPUT: return
    def on_move(x,y):
        global _mouse_last_move, _mouse_idle_alerted
        _mouse_last_move=time.time(); _mouse_idle_alerted=False
    l=pynput_mouse.Listener(on_move=on_move); l.daemon=True; l.start()
    while _running:
        if (time.time() - _mouse_last_move) >= MOUSE_IDLE_THRESHOLD and not _mouse_idle_alerted and not _is_sleeping: _mouse_idle_alerted=True; speak_async(*random.choice(MOUSE_IDLE_PHRASES))
        time.sleep(10)
def keyboard_listener_thread():
    global _keyboard_count, _keyboard_burst_alerted
    if not HAS_PYNPUT: return
    key_times=[]
    def on_press(key):
        global _keyboard_count, _keyboard_burst_alerted
        now=time.time(); key_times.append(now)
        while key_times and (now - key_times[0]) > 30: key_times.pop(0)
        _keyboard_count=len(key_times)
        if _keyboard_count >= KEYBOARD_BURST_THRESHOLD and not _keyboard_burst_alerted: _keyboard_burst_alerted=True; speak_async(*random.choice(KEYBOARD_BURST_PHRASES))
        elif _keyboard_count < KEYBOARD_BURST_THRESHOLD // 2: _keyboard_burst_alerted=False
    l=pynput_keyboard.Listener(on_press=on_press); l.daemon=True; l.start()
    while _running: time.sleep(5)
def detect_local_intent(text):
    global _work_session_start, _work_break_alerted, _voice_enabled, _known_user_name, _focus_mode_until
    t=(text or '').lower().strip(); n=normalize_key(text)
    guessed_name=extract_user_name(text)
    if guessed_name:
        _known_user_name=guessed_name
        send_text_oled('Bonjour', guessed_name[:12])
        return f"Enchanté {guessed_name} ! Je vais m'en souvenir pour mieux te parler.", 'HAPPY'
    if any(w in n for w in ['comment je m appelle','tu connais mon nom','quel est mon nom']):
        return (f"Tu t'appelles {_known_user_name}.", 'COOL') if _known_user_name else ("Tu ne me l'as pas encore dit clairement.", 'CONFUSED')
    if any(w in n for w in ['que sais tu sur moi','que retiens tu de moi','tu te souviens de quoi']):
        if _known_user_name:
            return f"Je sais que tu t'appelles {_known_user_name}. {random.choice(MEMORY_HINTS)} En ce moment tu utilises {_last_window_app or 'une appli que je n’ai pas encore reconnue'}.", 'COOL'
        return f"Je n'ai pas encore beaucoup d'infos stables sur toi. {random.choice(MEMORY_HINTS)}", 'CONFUSED'
    if any(w in n for w in ['resume ma session','fais le point','ou j en suis','bilan session']):
        return get_session_summary()
    if any(w in n for w in ['donne moi un conseil','conseille moi','que devrais je faire','un conseil maintenant']):
        return get_smart_tip(), 'COOL'
    if any(w in n for w in ['defi du jour','donne moi un defi','challenge moi']):
        return random.choice(CHALLENGE_PHRASES), 'EXCITED'
    if any(w in n for w in ['mode focus','aide moi a me concentrer','concentre moi']):
        secs=parse_timer_seconds(t) or 1500
        _focus_mode_until=time.time() + secs
        start_timer(secs)
        return random.choice(FOCUS_PHRASES)[0] + f" Je lance {secs // 60} minutes de focus.", 'COOL'
    if any(w in n for w in ['quelles sourates','liste des sourates','sourates disponibles']): send_text_oled('Sourates', str(len(SURAH_ALIASES))); return f"Je connais pour l'instant : {', '.join(SURAH_NAMES.values())}.", 'EXCITED'
    surah=resolve_surah_name(text)
    if any(w in n for w in ['reciter','recite','coran','sourate','je veux lire']): start_quran_recitation(surah or 'al ikhlas'); return 'Fin de la récitation.', 'NORMAL'
    if any(w in n for w in ['stop timer','arrete timer','annule timer','stop chrono']): return ('Timer annulé ! Tu as du temps libre maintenant.','COOL') if stop_timer() else ("Il n'y a pas de timer en cours.",'NORMAL')
    if any(w in n for w in ['timer','minuteur','chrono','rappelle moi dans','compte a rebours']):
        secs=parse_timer_seconds(t)
        if secs and secs > 0: start_timer(secs); return f'Ok ! Je lance le décompte pour {secs} secondes !','EXCITED'
        return "Je n'ai pas bien compris la durée. Dis-moi par exemple : timer cinq minutes.",'CONFUSED'
    if any(w in n for w in ['heure','quelle heure','date','quel jour','aujourd hui']): voice,l1,l2=get_time_info(); send_text_oled(l1,l2); return voice,'HAPPY'
    if any(w in n for w in ['meteo','météo','quel temps','temperature','il fait combien']): voice,l1,l2=get_weather_info(); send_text_oled(l1,l2); return voice,'COOL'
    if any(w in n for w in ['previsions','meteo demain','météo demain']): voice,l1,l2=get_weather_forecast(); send_text_oled(l1,l2); return voice,'COOL'
    if any(w in n for w in ['calcul','combien fait','divise','multiplie','egal a','plus','moins']):
        expr=extract_math_expr(t)
        if expr: voice,l1,l2=do_calc(expr); send_text_oled(l1,l2); return voice,'COOL'
    expr=extract_math_expr(t)
    if expr and len(expr.strip()) > 2: voice,l1,l2=do_calc(expr); send_text_oled(l1,l2); return voice,'COOL'
    if any(w in n for w in ['bonjour','salut','coucou','hello','bonsoir','hey robi']): return react_to_salutation()
    if any(w in n for w in ['ca va','comment tu vas','tu vas bien']): _raw('CMD:BUZZ'); return random.choice(CV_PHRASES)
    if any(w in n for w in ['je t aime','je taime','love you','je t adore']): _raw('CMD:MELODY'); return random.choice(TAIME_PHRASES)
    if any(w in n for w in ['bisou','bise','calin','câlin']): _raw('CMD:BUZZ'); return random.choice(BISOU_PHRASES)
    if any(w in n for w in ['tu es beau','tu es mignon','bravo','t es le meilleur']): return react_to_compliment()
    if any(w in n for w in ['chante','une chanson']): return sing_song()
    if any(w in n for w in ['danse','bouge']): _raw('CMD:MELODY'); return random.choice(DANSE_PHRASES)
    if any(w in n for w in ['blague','fais moi rire']): return tell_joke()
    if any(w in n for w in ['une histoire','une anecdote','surprise moi','raconte']): return tell_story()
    if any(w in n for w in ['qui t a cree','ton createur','ton maitre']): send_text_oled('SEIF','mon maitre'); return "Mon maître s'appelle Seif ! C'est lui qui m'a créé et je l'adore !",'LOVE'
    if any(w in n for w in ['qui es tu','presente toi','comment tu t appelles','ton nom']): send_text_oled('ROBI','v5'); return "Je m'appelle ROBI ! Je suis un petit robot Arduino créé par Seif. En version cinq, je vois même ton écran !",'EXCITED'
    if any(w in n for w in ['tu sais faire quoi','tes capacites','tu peux faire quoi']): return "Je peux voir ton écran, surveiller ton PC, dire l'heure, la météo, les stats CPU, faire des calculs, des timers et réciter plusieurs sourates.",'COOL'
    if any(w in n for w in ['aide','help','comment ca marche']): return "Parle-moi naturellement ! Je comprends l'heure, la météo, les calculs, les timers, l'écran, les stats PC, le presse-papier et les sourates.",'HAPPY'
    if any(w in n for w in ['je suis triste','ca va pas','je me sens mal']): return random.choice(TRISTE_PHRASES)
    if any(w in n for w in ['je suis en colere','j en ai marre','ca m enerve']): return random.choice(COLERE_PHRASES)
    if any(w in n for w in ['j ai peur','ca fait peur']): return random.choice(PEUR_PHRASES)
    if any(w in n for w in ['bonne nuit','a demain','je te laisse']): send_emotion('SLEEP'); return 'Bonne nuit ! Fais de beaux rêves. Moi je vais garder ton bureau !','CUTE'
    if any(w in n for w in ['merci','thanks']): return random.choice(MERCI_PHRASES)
    if any(w in n for w in ['teste le son','test du son','verifie le son','test voix']): _raw('CMD:BUZZ'); return random.choice(SOUND_TEST_PHRASES)
    if any(w in n for w in ['mode silencieux','coupe la voix','tais toi','mute']): _voice_enabled=False; return random.choice(SILENT_MODE_PHRASES)
    if any(w in n for w in ['remets la voix','remets le son','parle de nouveau','unmute']): _voice_enabled=True; return random.choice(VOICE_BACK_PHRASES)
    if any(w in n for w in ['repete','redis','repete ce que tu as dit']): return (f'Je répète : {_last_spoken_text}', _last_spoken_emotion) if _last_spoken_text else ("Je n'ai encore rien dit de mémorable.",'CONFUSED')
    if any(w in n for w in ['regarde mon ecran','regarde l ecran','que vois tu','decris mon ecran','capture d ecran','screenshot']): animated_speak(random.choice(SCREEN_VISION_INTRO),'EXCITED'); return analyze_screen_with_gemini()
    if any(w in n for w in ['stats pc','stats du pc','performances','cpu','ram','memoire','processeur','disque','etat du pc']):
        s=get_system_stats()
        if s['available']: send_text_oled(f"CPU{s['cpu']}%", f"RAM{s['ram']}%"); return random.choice([f"CPU à {s['cpu']}%, RAM à {s['ram']}%, disque à {s['disk']}%.", f"Ton PC tourne à {s['cpu']}% CPU et {s['ram']}% RAM. Disque à {s['disk']}%."]), 'COOL'
        return 'Je ne peux pas lire les stats ! Installe psutil.', 'CONFUSED'
    if any(w in n for w in ['batterie','niveau de batterie','etat batterie']): return get_battery_info()
    if any(w in n for w in ['quelle appli','quelle application','mon activite','que fais je','sur quoi je travaille']):
        if _last_window_title: p,e=random.choice(APP_REACTIONS.get(_last_window_app, APP_REACTIONS['default'])); send_text_oled(_last_window_app[:12],'detected'); return f'Tu utilises {_last_window_title[:30]}. {p}', e
        return "Je n'arrive pas à détecter la fenêtre active.",'CONFUSED'
    if any(w in n for w in ['actualites','actu','news','infos du jour','dernieres nouvelles']):
        r=get_news()
        if isinstance(r, tuple) and len(r) == 2: return r
        voice,l1,l2=r; send_text_oled(l1[:12], l2[:12]); return voice,'EXCITED'
    if any(w in n for w in ['motive moi','encourage moi','j ai besoin de motivation','boost moi']): _raw('CMD:MELODY'); return random.choice(MOTIVATION_PHRASES)
    if any(w in n for w in ['depuis combien de temps','ma session','temps de travail','je travaille depuis']): elapsed=int((time.time() - _work_session_start) / 60); send_text_oled(f'{elapsed}min','session'); return f"Tu travailles depuis {elapsed} minute{'s' if elapsed > 1 else ''} ! {'Prends une pause !' if elapsed > WORK_SESSION_BREAK_MIN else 'Continue comme ça !'}", ('HAPPY' if elapsed <= WORK_SESSION_BREAK_MIN else 'CUTE')
    if any(w in n for w in ['j ai fait ma pause','pause faite','je reprends','reset session']): _work_session_start=time.time(); _work_break_alerted=False; return 'Super ! Session remise à zéro !','HAPPY'
    if any(w in n for w in ['presse papier','clipboard','ce que j ai copie','lis mon presse papier']):
        if HAS_CLIPBOARD:
            try:
                c=pyperclip.paste()
                if c and len(c.strip()) > 0: preview=c.strip()[:60]; send_text_oled(preview,'lu !'); return f"Dans ton presse-papier j'ai vu : {preview}",'EXCITED'
                return 'Ton presse-papier est vide !','CONFUSED'
            except Exception: return "Je n'ai pas pu lire le presse-papier.",'CONFUSED'
        return 'Installe pyperclip pour que je lise ton presse-papier !','CONFUSED'
    if any(w in n for w in ['combien je tape','ma vitesse de frappe','frappe clavier','frappes']):
        if _keyboard_count >= 50: return f'Tu as tapé {_keyboard_count} touches en 30 secondes ! Tu es une machine !','HYPER'
        if _keyboard_count >= 20: return f'{_keyboard_count} frappes en 30 secondes ! Rythme correct !','COOL'
        return f'Environ {_keyboard_count} frappes récentes. Tu tapes tranquillement.','NORMAL'
    if any(w in n for w in ['prends une photo','capture l ecran','fais un screenshot','photo de l ecran']):
        if HAS_PIL:
            animated_speak("Je prends une capture d'écran !",'EXCITED'); img=take_screenshot_bytes()
            if img: fname=f'robi_screenshot_{int(time.time())}.jpg'; open(fname,'wb').write(img); send_text_oled('Capture!', fname[:12]); return f'Capture prise et sauvegardée ! Fichier : {fname}','HAPPY'
        return "Échec de la capture d'écran.",'CONFUSED'
    return None
FAREWELL_WORDS=('au revoir','bye','quitte','arrête-toi','bonne nuit robot','eteins-toi','shutdown','ferme-toi','good bye')
def main():
    global _last_activity, _is_sleeping, _running, _work_session_start, _work_break_alerted
    print('=' * 62); print(f"  Mode    : {'🎙 MICROPHONE' if USE_MICROPHONE else '⌨ CLAVIER'}"); print(f"  Langue  : {LANGUAGE}   |   Ville : {CITY}"); print(f"  Vision  : {'✔ ACTIVE' if HAS_PIL else '✗ PIL manquant'}"); print(f"  Stats   : {'✔ ACTIVES' if HAS_PSUTIL else '✗ psutil manquant'}"); print('=' * 62)
    init_tts(); connect_arduino(); init_gemini(); _work_session_start=time.time(); threading.Thread(target=serial_reader_thread,daemon=True).start(); threading.Thread(target=autonomous_thread,daemon=True).start(); threading.Thread(target=pc_monitor_thread,daemon=True).start(); threading.Thread(target=screen_watcher_thread,daemon=True).start()
    if HAS_PYNPUT: threading.Thread(target=mouse_listener_thread,daemon=True).start(); threading.Thread(target=keyboard_listener_thread,daemon=True).start()
    animated_speak('Bonjour ! Je suis ROBI version cinq !','EXCITED'); animated_speak('Je vois ton écran, je surveille ton PC, et je suis là pour toi !','HAPPY'); send_text_oled('ROBI v5','Pret !')
    if HAS_PIL: animated_speak('Mes yeux sont activés ! Je peux voir ton écran !','EXCITED')
    _last_activity=time.time(); print("[PRÊT] 🤖 ROBI v5 attend ta voix !"); print("       Dis 'teste le son' pour vérifier la voix."); print("       Dis 'quelles sourates connais-tu' pour la liste."); print("       Essaie aussi : 'je m'appelle ...', 'résume ma session', 'donne-moi un conseil', 'mode focus 25 minutes'.")
    while _running:
        try:
            if _is_sleeping and not _is_speaking: send_emotion('SLEEP')
            if _is_speaking: time.sleep(0.1); continue
            user_input=listen(timeout=5)
            if not user_input: continue
            if _is_sleeping: _is_sleeping=False; _work_break_alerted=False; send_emotion('SURPRISE'); time.sleep(0.4)
            _last_activity=time.time(); print(f"\n[USER] '{user_input}'")
            if any(w in user_input.lower() for w in FAREWELL_WORDS): txt,emo=random.choice(AUREVOIR_REACTIONS); animated_speak(txt,emo); send_emotion('SLEEP'); break
            local=detect_local_intent(user_input)
            response_text, emotion = local if local else ask_gemini(user_input)
            remember_exchange(user_input, response_text, emotion)
            animated_speak(response_text, emotion); _last_activity=time.time()
        except KeyboardInterrupt: print('\n[Arrêt manuel — Ctrl+C]'); _running=False; break
        except Exception as e: print(f'[ERREUR MAIN] {e}'); send_emotion('CONFUSED'); time.sleep(1)
    _running=False; stop_timer(); _speech_queue.put(None)
    if arduino and arduino.is_open: send_emotion('SLEEP'); time.sleep(0.5); arduino.close()
    print('[ROBI] 😴 Arrêt propre. À bientôt !')
if __name__ == '__main__': main()

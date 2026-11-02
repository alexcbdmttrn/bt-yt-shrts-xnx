# -*- coding: utf-8 -*-
"""
BOT VIDEOS LARGOS HERBOLARIA - SEO ELITE v3
ARCHIVO ÚNICO Y AUTÓNOMO: incluye el motor SEO (política, autocompletado, títulos con score, tags).

Mejoras vs. v2:
  - Filtro de política por palabras completas (regex), duro vs suave. Arreglado el bug de emojis vacíos.
  - Autocompletado real de YouTube México -> keywords reales en guion, título, tags y descripción.
  - Títulos: IA + fórmulas -> candidatos puntuados 0-100, elige el mejor.
  - Tags en capas (exacto, específicos, generales, cola larga, variantes) con 500 caracteres aprovechados.
  - Miniaturas: 3 variantes, scoring de legibilidad a tamaño pequeño, sin barra que repite el título,
    zona de duración libre, historial de variante usada.
  - Subtítulos SRT subidos a YouTube (con tiempos reales de edge-tts).
  - Capítulos con keywords, descripción optimizada, hashtag del ingrediente primero.
  - Playlist automática por problema.
  - Voz consistente (si una voz falla, se cambia para el resto del video).
  - Contactos y contraseña leídos de variables de entorno (secrets).
"""
import asyncio
import base64
import io
import json
import os
import random
import re
import sys
import time
import unicodedata
from datetime import datetime

import numpy as np
import pandas as pd
import pytz
import requests
import urllib3
import edge_tts
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import (
    AudioFileClip, CompositeAudioClip, ImageClip,
    concatenate_audioclips, concatenate_videoclips, AudioClip,
    CompositeVideoClip,
)
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
from rembg import remove

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN")) if os.getenv("YOUTUBE_USER_TOKEN") else {}

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

# Recomendado: definirlos como secrets/variables en GitHub. Los valores por defecto
# mantienen el comportamiento anterior, pero NO dejes una contraseña real en el código.
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "+52 3123395334")
TELEFONO_NUMBER = os.getenv("TELEFONO_NUMBER", "3123395334")
TELEGRAM_BOT = os.getenv("TELEGRAM_BOT", "@alex_xanax_bot")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD", "A")

ESTADO_FILE = "estado_largos_herbolaria.json"
INGREDIENTES_LARGOS_FILE = "ingredientes_largos_usados.json"
TITULOS_FILE = "titulos_largos_publicados.json"
MINIATURAS_HIST_FILE = "miniaturas_largos_historial.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES = "catalogo_curiosidades_salud.json"

ANCHO, ALTO = 1920, 1080

MAX_LARGOS_DIA = 1
INTERVALO_MIN_HORAS = 18
INTERVALO_MAX_HORAS = 24
RETRASO_MAX_MINUTOS = 30
PAUSA_ENTRE_SEGMENTOS = 0.5

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

HORA_EXCLUIR_INICIO = 0   # hora CDMX
HORA_EXCLUIR_FIN = 4

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ORDEN_SEGMENTOS = ["hook", "problema", "ingrediente", "beneficio_1", "beneficio_2",
                   "beneficio_3", "producto", "cta"]

KEYWORDS_VIRALES = {
    "generales_alto_volumen": [
        {"kw": "remedios naturales", "peso": 10},
        {"kw": "remedios caseros", "peso": 10},
        {"kw": "salud natural", "peso": 10},
        {"kw": "medicina natural", "peso": 10},
        {"kw": "herbolaria mexicana", "peso": 9},
        {"kw": "hierbas medicinales", "peso": 9},
        {"kw": "plantas medicinales", "peso": 9},
        {"kw": "tips de salud", "peso": 8},
        {"kw": "consejos naturales", "peso": 8},
        {"kw": "bienestar natural", "peso": 8},
    ],
    "patrones_busqueda": [
        {"kw": "para qué sirve", "peso": 10},
        {"kw": "beneficios de", "peso": 10},
        {"kw": "propiedades de", "peso": 9},
        {"kw": "cómo usar", "peso": 9},
        {"kw": "cómo preparar", "peso": 8},
        {"kw": "sabías que", "peso": 8},
        {"kw": "lo que no sabías", "peso": 8},
        {"kw": "secreto ancestral", "peso": 7},
        {"kw": "tradición mexicana", "peso": 7},
        {"kw": "usos tradicionales", "peso": 7},
    ],
    "sintomas_alta_busqueda": [
        {"kw": "dolor articular", "peso": 9},
        {"kw": "inflamación", "peso": 9},
        {"kw": "colesterol alto", "peso": 9},
        {"kw": "presión alta", "peso": 9},
        {"kw": "azúcar en sangre", "peso": 9},
        {"kw": "dormir mejor", "peso": 8},
        {"kw": "insomnio", "peso": 8},
        {"kw": "estrés y ansiedad", "peso": 8},
        {"kw": "defensas bajas", "peso": 8},
        {"kw": "digestión pesada", "peso": 8},
        {"kw": "gastritis", "peso": 8},
        {"kw": "várices", "peso": 8},
        {"kw": "circulación", "peso": 8},
        {"kw": "energía y vitalidad", "peso": 7},
        {"kw": "menopausia", "peso": 7},
        {"kw": "próstata", "peso": 7},
    ],
    "engagement": [
        {"kw": "bienestar diario", "peso": 7},
        {"kw": "vida saludable", "peso": 7},
        {"kw": "aliado natural", "peso": 7},
        {"kw": "apoyo tradicional", "peso": 7},
        {"kw": "estilo de vida", "peso": 6},
    ],
}

TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "remedios naturales", "para qué sirve"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales de las hierbas", "remedios naturales efectivos"], "ctr_potencial": 9.2},
    {"tema": "remedio_casero", "keywords_cortas": ["remedios caseros", "natural", "tradición", "hierbas medicinales"], "keywords_largas": ["remedios caseros efectivos", "tratamiento natural con hierbas", "remedios de la abuela"], "ctr_potencial": 9.5},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "evidencia"], "keywords_largas": ["estudios sobre hierbas", "evidencia tradicional"], "ctr_potencial": 10.5},
    {"tema": "alivio_natural", "keywords_cortas": ["alivio natural", "bienestar", "medicina natural", "plantas medicinales"], "keywords_largas": ["alivio natural tradicional", "remedios mexicanos para el bienestar", "hierbas que alivian"], "ctr_potencial": 10.8},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "herbolaria mexicana", "tradición"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional mexicana", "herbolaria que pocos conocen"], "ctr_potencial": 9.8},
]

VOCES_DISPONIBLES = [
    {"voz": "es-MX-JorgeNeural", "velocidad": "+10%", "estilo": "profesional México"},
    {"voz": "es-MX-DaliaNeural", "velocidad": "+10%", "estilo": "claro México"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+12%", "estilo": "entusiasta España"},
    {"voz": "es-ES-AlvaroNeural", "velocidad": "+10%", "estilo": "profesional España"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+10%", "estilo": "natural Colombia"},
    {"voz": "es-AR-ElenaNeural", "velocidad": "+9%", "estilo": "cálido Argentina"},
    {"voz": "es-US-PalomaNeural", "velocidad": "+10%", "estilo": "neutral USA"},
    {"voz": "es-MX-BeatrizNeural", "velocidad": "+11%", "estilo": "amigable México"},
]

TEMAS_PLAYLIST = [
    ("circul", "circulación"), ("varice", "circulación"), ("sueno", "sueño y descanso"),
    ("insomn", "sueño y descanso"), ("digest", "digestión"), ("gastri", "digestión"),
    ("estomag", "digestión"), ("estrenimiento", "digestión"), ("estres", "estrés y ansiedad"),
    ("ansied", "estrés y ansiedad"), ("nervio", "estrés y ansiedad"), ("defensa", "defensas"),
    ("inmun", "defensas"), ("gripe", "defensas"), ("articul", "articulaciones y dolor"),
    ("dolor", "articulaciones y dolor"), ("inflam", "articulaciones y dolor"),
    ("energ", "energía y vitalidad"), ("cansancio", "energía y vitalidad"),
    ("piel", "piel y cabello"), ("cabello", "piel y cabello"), ("colesterol", "corazón y colesterol"),
    ("corazon", "corazón y colesterol"), ("presion", "corazón y colesterol"),
    ("azucar", "azúcar y metabolismo"), ("peso", "azúcar y metabolismo"),
    ("prostata", "salud masculina"), ("menopausia", "salud femenina"), ("higado", "hígado y riñones"),
    ("rinon", "hígado y riñones"), ("memoria", "mente y memoria"), ("respir", "respiración"),
]


# ================================================================
# UTILIDADES
# ================================================================
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50]")


def normalizar(t):
    """minúsculas, sin acentos/ñ, espacios simples."""
    t = unicodedata.normalize("NFD", str(t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).strip()


def contar_emojis(t):
    return len(EMOJI_RE.findall(t or ""))


def quitar_emojis(t):
    return re.sub(r"\s+", " ", EMOJI_RE.sub("", t or "").replace("\uFE0F", "")).strip()


def sin_acentos_tag(t):
    return normalizar(t)


# ================================================================
# 1) POLÍTICA DE SALUD (palabras completas, sin acentos)
# ================================================================
# BLOQUEO DURO: promesas de cura, garantías, urgencia médica, enfermedades graves,
# sustitución de tratamientos, plazos de resultados.
HARD_TERMS = [
    "cura", "curar", "cura milagrosa", "curacion", "milagro", "milagros", "milagrosa",
    "milagroso", "sanar", "sanacion", "sanarlo", "sanarte", "erradica", "erradicar",
    "desaparece por completo", "desaparecer por completo", "remedio definitivo",
    "tratamiento definitivo", "termina con", "acaba con", "adios", "nunca mas",
    "para siempre", "de raiz", "desde la raiz", "elimina de raiz",
    "cientificamente comprobado", "comprobado cientificamente", "clinicamente probado",
    "avalado por medicos", "aprobado por medicos", "recomendado por medicos",
    "avalado por doctores", "aprobado por la fda", "aprobado por fda",
    "respaldado por estudios", "estudios lo confirman", "eficacia probada",
    "efectividad probada", "funciona siempre", "sin fallar", "sin excepciones",
    "100% efectivo", "100 % efectivo", "cien por ciento efectivo", "garantizado",
    "garantia de resultados", "revolucionario", "breakthrough", "descubrimiento medico",
    "innovacion medica", "patentado medicamente", "reemplaza", "sustituye",
    "no necesitas medico", "sin ir al medico", "olvida al doctor",
    "mejor que las pastillas", "mejor que los medicamentos", "olvida la medicina",
    "tira tus pastillas", "deja tu tratamiento", "sin farmacos", "sin medicamentos",
    "sin receta medica", "alternativa a medicamentos", "en vez de medicamentos",
    "hoy mismo", "esta noche", "manana mismo", "al instante", "inmediatamente",
    "instantaneo", "instantanea", "resultados inmediatos", "efecto inmediato",
    "rapido y facil", "express", "peligroso", "peligrosa", "mortal", "mortales",
    "asesino silencioso", "asesina silenciosa", "te esta matando", "te mata",
    "te matara", "veneno", "toxico", "toxina mortal", "muerte", "fatal", "terminal",
    "alerta roja", "conspiracion", "lo que te ocultan", "la verdad oculta",
    "ellos no quieren que sepas", "te mienten", "transforma tu cuerpo",
    "transforma tu vida", "cambia tu vida", "antes y despues", "resultados increibles",
    "pierde peso rapido", "quema grasa milagrosa", "quema grasa express",
    "derrite la grasa", "elimina grasa localizada", "adelgaza sin dieta", "sin dieta",
    "sin ejercicio", "sin esfuerzo", "come lo que quieras", "barriga plana",
    "rejuvenece 20 anos", "rejuvenece 10 anos", "eterna juventud", "juventud eterna",
    "inmortal", "no vas a creer", "no lo vas a creer", "te sorprendera",
    "te dejara impactado", "quedaras impactado", "quedaras asombrado",
    "lo que nadie dice", "lo que nadie sabe", "el mejor del mundo", "el peor del mundo",
    "cancer", "tumor", "tumores", "vih", "sida", "alzheimer", "parkinson",
    "esclerosis", "leucemia", "infarto", "derrame cerebral", "ictus", "metastasis",
    "solucion", "elimina", "limpiar tu cuerpo", "limpieza total del cuerpo",
]

# ADVERTENCIA SUAVE: clickbait / hipérbole. Penaliza el score, no bloquea.
SOFT_TERMS = [
    "top", "increible", "asombroso", "alucinante", "impactante", "shock", "shocking",
    "brutal", "bestial", "perfecto", "definitivo", "urgente", "emergencia",
    "revelacion", "revelador", "los 10 mejores", "los 5 peores", "fin de", "fin del",
]


def _compilar(terminos):
    pats = sorted({normalizar(t) for t in terminos}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(p) for p in pats) + r")(?!\w)")


_RE_DURAS = _compilar(HARD_TERMS)
_RE_SUAVES = _compilar(SOFT_TERMS)
_RE_DURAS_EXTRA = [
    re.compile(r"\ben \d+ (?:dias?|horas?|semanas?|meses)\b"),
    re.compile(r"\b(?:pierde|baja|adelgaza)\s+\d+\s*(?:kilos?|kg)\b"),
    re.compile(r"\b100\s*%"),
]
_RE_DESCARGO = re.compile(r"\bno (?:sustituye|reemplaza)[^.;:!?]*")


def auditar_texto(texto, es_guion=False):
    """Devuelve {'duras': [...], 'suaves': [...]} con palabras COMPLETAS detectadas.
    Si es_guion=True, ignora los descargos tipo 'no sustituye la consulta médica'."""
    tn = normalizar(texto)
    if es_guion:
        tn = _RE_DESCARGO.sub(" ", tn)
    duras = sorted(set(_RE_DURAS.findall(tn)))
    for rx in _RE_DURAS_EXTRA:
        duras += [m if isinstance(m, str) else m[0] for m in rx.findall(tn)]
    suaves = sorted(set(_RE_SUAVES.findall(tn)))
    return {"duras": duras, "suaves": suaves}


def texto_seguro(texto, es_guion=False):
    return not auditar_texto(texto, es_guion)["duras"]


# ================================================================
# 2) AUTOCOMPLETADO REAL DE YOUTUBE (gratis, sin cuota)
# ================================================================
AC_CACHE_FILE = "autocompletado_cache.json"
AC_CACHE_DIAS = 7


def _cargar_cache():
    try:
        with open(AC_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar_cache(c):
    try:
        with open(AC_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False)
    except Exception:
        pass


def _ac_request(q):
    r = requests.get(
        "https://suggestqueries.google.com/complete/search",
        params={"client": "firefox", "ds": "yt", "q": q, "hl": "es", "gl": "mx"},
        headers={"User-Agent": "Mozilla/5.0"}, timeout=8,
    )
    r.raise_for_status()
    data = json.loads(r.content.decode("utf-8", errors="ignore"))
    return [s for s in data[1] if isinstance(s, str)]


def obtener_sugerencias(ingrediente, max_resultados=25, usar_alfabeto=True, tiempo_max=40):
    """Frases reales que la gente busca en YouTube México para este ingrediente.
    Devuelve [{'frase': str, 'score': float}] ordenadas. Si falla la red -> []."""
    ing = str(ingrediente or "").lower().strip()
    if not ing:
        return []
    semillas = [(f"para qué sirve {ing}", 1.0), (f"{ing} beneficios", 1.0),
                (f"{ing} propiedades", 1.0), (f"{ing} té", 0.9),
                (f"cómo tomar {ing}", 0.9), (f"{ing} para", 0.9),
                (f"cómo se usa {ing}", 0.8), (f"{ing} contraindicaciones", 0.6),
                (f"remedios con {ing}", 0.7)]
    if usar_alfabeto:
        semillas += [(f"{ing} {l}", 0.4) for l in "abcdefghijlmnoprstuv"]

    cache = _cargar_cache()
    ahora = time.time()
    t0 = ahora
    puntaje, tokens = {}, [t for t in normalizar(ing).split() if len(t) > 3] or [normalizar(ing)]
    fallos = 0
    for semilla, peso in semillas:
        if time.time() - t0 > tiempo_max or fallos >= 4:
            break
        entrada = cache.get(semilla)
        if entrada and ahora - entrada.get("t", 0) < AC_CACHE_DIAS * 86400:
            res = entrada["res"]
        else:
            try:
                res = _ac_request(semilla)
                cache[semilla] = {"t": ahora, "res": res}
                time.sleep(0.15)
            except Exception:
                fallos += 1
                continue
        for rank, frase in enumerate(res):
            fn = normalizar(frase)
            if len(fn) > 70 or not re.match(r"^[a-z0-9\s]+$", fn):
                continue
            if not any(tok in fn for tok in tokens):
                continue
            if not texto_seguro(frase):
                continue
            puntaje[fn] = puntaje.get(fn, 0.0) + peso / (rank + 1)
            puntaje.setdefault("__orig__" + fn, frase.lower().strip())
    _guardar_cache(cache)
    out = []
    for k, v in puntaje.items():
        if k.startswith("__orig__"):
            continue
        out.append({"frase": puntaje.get("__orig__" + k, k), "score": round(v, 3)})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:max_resultados]


# ================================================================
# 3) TÍTULOS: familia, tipo, candidatos, SCORE 0-100
# ================================================================
EMOJIS_TITULO = ["🌿", "✨", "🌱", "🍃", "🌼", "💚", "☀️", "🍵", "⚡", "🔥", "💪"]  # neutros / botánicos
PALABRAS_PODER = ["secreto", "poder", "verdad", "oculto", "nadie", "pocos", "abuelo", "abuela",
                  "descubre", "mito", "razones", "ancestral", "tradicion", "sabias"]

# {Ing} = capitalizada (inicio), {ing} = tal cual (mitad), {prob} = problema corto
FORMULAS_TITULO = {
    "busqueda": [
        "{Ing}: para qué sirve y cómo usarlo {e}",
        "Para qué sirve {ing}: usos y beneficios {e}",
        "{Ing}: propiedades y beneficios tradicionales {e}",
        "Cómo tomar {ing} correctamente {e}",
        "Beneficios de {ing} para {prob} {e}",
        "{Ing}: qué es y cómo se usa en la herbolaria {e}",
    ],
    "curiosidad": [
        "{Ing}: {num} cosas que nadie te explicó {e}",
        "¿Por qué tu abuela usaba {ing}? {e}",
        "El poder oculto de {ing} para {prob} {e}",
        "{num} secretos de {ing} que pocos conocen {e}",
        "¿Qué pasa si tomas {ing} a diario? {e}",
        "{Ing}: ¿mito o tradición real? {e}",
        "Lo que los abuelos sabían de {ing} {e}",
    ],
    "problema_solucion": [
        "{prob_cap}: así apoya {ing} tu bienestar {e}",
        "Si tienes {prob}, conoce {ing} {e}",
        "{Ing} para {prob}: lo que dice la tradición {e}",
        "{Ing}: aliado natural para {prob} {e}",
        "¿{prob_cap}? Esto hace {ing} en tu cuerpo {e}",
    ],
}


# Fórmulas del bot original (POWER y VARIADAS): ahora alimentan el pool de candidatos,
# que luego se filtra por política y se puntúa. e1 se deja vacío para respetar "1 emoji máximo".
FORMULAS_POWER_LARGO = [
    "{e1} {ingrediente}: {num} secretos para {problema} que pocos conocen {e2}",
    "{e1} ¿{problema_cap}? Esto es lo que {ingrediente} hace en tu cuerpo {e2}",
    "{e1} {ingrediente}: {num} beneficios reales según la herbolaria {e2}",
    "{e1} El poder oculto de {ingrediente} para {problema} {e2}",
    "{e1} {problema_cap}: así apoya {ingrediente} tu bienestar {e2}",
    "{e1} {ingrediente} + tradición: {num} usos que debes conocer {e2}",
    "{e1} Lo que los abuelos sabían de {ingrediente} para {problema} {e2}",
    "{e1} ¿Usas {ingrediente}? {num} cosas que nadie te explicó {e2}",
    "{e1} {ingrediente} para {problema}: mito o tradición real {e2}",
    "{e1} {num} razones por las que {ingrediente} sigue vigente {e2}",
    "{e1} {ingrediente}: el aliado ancestral para {problema} {e2}",
    "{e1} {ingrediente} por dentro: {num} efectos en tu bienestar {e2}",
]

FORMULAS_TITULOS_VARIADAS = {
    "busqueda": [
        "Para qué sirve {ingrediente} en remedios naturales",
        "Para qué sirve {ingrediente} y cómo usarlo",
        "Qué es {ingrediente} y por qué lo necesitas",
    ],
    "pregunta": [
        "¿Sabías que {ingrediente} ayuda con {problema}?",
        "¿Conocías este uso del {ingrediente}?",
        "¿Por qué tu abuela usaba {ingrediente}?",
        "¿{ingrediente} realmente funciona para {problema}?",
        "¿Qué pasa si consumes {ingrediente} todos los días?",
    ],
    "secreto": [
        "El secreto ancestral del {ingrediente} para {problema}",
        "Lo que nadie te contó sobre el {ingrediente}",
        "El poder oculto del {ingrediente} en tu salud",
        "La verdad sobre {ingrediente} que pocos conocen",
        "{ingrediente}: secreto de la herbolaria mexicana",
    ],
    "problema_solucion": [
        "{problema}: el remedio natural con {ingrediente}",
        "Si sufres de {problema}, prueba {ingrediente}",
        "{ingrediente}: el aliado natural contra {problema}",
        "Adiós {problema}: descubre {ingrediente}",
        "¿Cansado de {problema}? Conoce {ingrediente}",
    ],
    "beneficios": [
        "5 formas en que {ingrediente} mejora tu salud",
        "{ingrediente}: 3 beneficios que cambiarán tu vida",
        "Los beneficios del {ingrediente} que debes conocer",
        "Cómo {ingrediente} transforma tu bienestar diario",
    ],
    "tradicional": [
        "Por qué los abuelos confiaban en el {ingrediente}",
        "{ingrediente}: la herencia de la medicina tradicional",
        "La sabiduría ancestral del {ingrediente} para tu salud",
        "{ingrediente}: remedio tradicional mexicano",
    ],
    "como_usar": [
        "Cómo usar {ingrediente} correctamente para {problema}",
        "La forma correcta de aprovechar {ingrediente}",
        "{ingrediente}: guía completa de uso tradicional",
        "Prepara {ingrediente} así y siente la diferencia",
    ],
    "cientifico": [
        "Lo que dice la ciencia sobre {ingrediente}",
        "{ingrediente}: entre la tradición y la evidencia",
        "Por qué {ingrediente} es reconocido en herbolaria",
    ],
    "verdad": [
        "Lo que debes saber antes de usar {ingrediente}",
        "Errores comunes al usar {ingrediente}",
        "La verdad sobre {ingrediente} en remedios caseros",
    ],
}


def _problema_corto(problema, maxlen=24):
    ps = [p.strip() for p in str(problema or "").split(",") if p.strip()]
    prob = ps[0].lower() if ps else "tu bienestar"
    if len(prob) > maxlen:
        prob = prob[:maxlen].rsplit(" ", 1)[0]
    return prob


def firma_titulo(t):
    return " ".join(re.findall(r"\w+", normalizar(quitar_emojis(t)))[:3])


def familia_titulo(t):
    tn = normalizar(quitar_emojis(t))
    if tn.startswith("para que sirve"):
        return "para_que_sirve"
    if "secreto" in tn:
        return "secretos"
    if "?" in t or t.strip().startswith("¿"):
        return "pregunta"
    if "beneficios" in tn:
        return "beneficios"
    if re.search(r"como (usar|tomar|preparar)", tn):
        return "como_usar"
    if re.search(r"abuel|tradicion|ancestral", tn):
        return "tradicional"
    if re.search(r"verdad|mito|nadie", tn):
        return "verdad"
    if "poder oculto" in tn:
        return "poder"
    if re.search(r"razones|cosas que", tn):
        return "lista"
    return "otro"


def tipo_titulo(t):
    tn = normalizar(quitar_emojis(t))
    if re.search(r"para que sirve|beneficios de|como tomar|como usar|propiedades|que es ", tn):
        return "busqueda"
    if re.search(r"aliado natural|asi apoya|si tienes|lo que dice la tradicion|esto hace", tn):
        return "problema_solucion"
    return "curiosidad"


def _limpiar_titulo(t):
    t = re.sub(r"#\w+", "", t or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1].upper() + t[1:]


def ajustar_titulo(t):
    """Limpia hashtags y asegura 1 emoji si cabe. No trunca con '...'."""
    t = _limpiar_titulo(t)
    if t and contar_emojis(t) == 0 and len(t) <= 66:
        t = f"{t} {random.choice(EMOJIS_TITULO)}"
    return t


def generar_candidatos_codigo(ingrediente, problema):
    ing = str(ingrediente).strip()
    ing_cap = ing[:1].upper() + ing[1:]
    prob = _problema_corto(problema)
    cands = []
    for formulas in FORMULAS_TITULO.values():
        for f in formulas:
            cands.append(_limpiar_titulo(f.format(
                ing=ing.lower() if len(ing.split()) == 1 else ing, Ing=ing_cap, prob=prob,
                prob_cap=prob[:1].upper() + prob[1:], num=random.choice([3, 4, 5, 7]),
                e=random.choice(EMOJIS_TITULO))))
    prob_c = prob[:1].upper() + prob[1:]
    for f in FORMULAS_POWER_LARGO:
        cands.append(_limpiar_titulo(f.format(
            e1="", e2=random.choice(EMOJIS_TITULO), ingrediente=ing, problema=prob,
            problema_cap=prob_c, num=random.choice([3, 4, 5, 7]))))
    for formulas in FORMULAS_TITULOS_VARIADAS.values():
        for f in formulas:
            cands.append(_limpiar_titulo(f.format(ingrediente=ing, problema=prob)))
    return cands


def puntuar_titulo(titulo, ingrediente, sugerencias=None, historial=None):
    """Devuelve (score 0-100, detalle). Score -100 = rechazado."""
    t = _limpiar_titulo(titulo)
    historial = historial or []
    tn = normalizar(quitar_emojis(t))
    ing_n = normalizar(ingrediente)
    det = {}

    aud = auditar_texto(t)
    if aud["duras"]:
        return -100, {"rechazo": f"palabra prohibida: {aud['duras']}"}
    if len(t) > 70:
        return -100, {"rechazo": f"largo ({len(t)}>70)"}
    if len(t) < 25:
        return -100, {"rechazo": "muy corto"}

    recientes = historial[-6:]
    fam = familia_titulo(t)
    if sum(1 for x in recientes if familia_titulo(x) == fam) >= 2:
        return -100, {"rechazo": f"familia saturada ({fam})"}
    if firma_titulo(t) in [firma_titulo(x) for x in recientes]:
        return -100, {"rechazo": "firma repetida"}
    pc = set(re.findall(r"\w+", tn))
    for h in historial:
        ph = set(re.findall(r"\w+", normalizar(quitar_emojis(h))))
        if pc and ph and len(pc & ph) / len(pc | ph) > 0.8:
            return -100, {"rechazo": "casi idéntico a uno publicado"}

    pts = 0
    # keyword principal temprana
    idx = tn.find(ing_n)
    toks = [x for x in ing_n.split() if len(x) > 3]
    if idx != -1 and idx + len(ing_n) <= 45:
        det["keyword"] = 25
    elif toks and any(x in tn[:40] for x in toks):
        det["keyword"] = 12
    pts += det.get("keyword", 0)
    # longitud
    n = len(t)
    det["longitud"] = 15 if 50 <= n <= 62 else 8 if 44 <= n <= 70 else 0
    pts += det["longitud"]
    # brecha de curiosidad
    if "?" in t or any(pw in tn for pw in PALABRAS_PODER):
        det["curiosidad"] = 10
        pts += 10
    # número
    if re.search(r"\b\d{1,2}\b", t):
        det["numero"] = 8
        pts += 8
    # emoji (máximo uno)
    ne = contar_emojis(t)
    det["emoji"] = 8 if ne == 1 else (-6 if ne > 1 else 0)
    pts += det["emoji"]
    # coincidencia con autocompletado real
    for s in (sugerencias or [])[:8]:
        sn = normalizar(s["frase"])
        for tok in ing_n.split():
            sn = re.sub(r"(?<!\w)" + re.escape(tok) + r"(?!\w)", " ", sn)
        resto = re.sub(r"\s+", " ", sn).strip()
        if len(resto) >= 3 and resto in tn:
            det["autocompletado"] = 10
            pts += 10
            break
    # novedad: familia y tipo poco usados
    if sum(1 for x in recientes if familia_titulo(x) == fam) == 0:
        det["familia_nueva"] = 10
        pts += 10
    usos_tipo = sum(1 for x in recientes if tipo_titulo(x) == tipo_titulo(t))
    det["rotacion_tipo"] = 10 if usos_tipo == 0 else 5 if usos_tipo == 1 else -5 if usos_tipo >= 3 else 0
    pts += det["rotacion_tipo"]
    # sin truncados
    if "..." in t or "…" in t:
        pts -= 20
    else:
        pts += 4
    # clickbait suave
    if aud["suaves"]:
        det["suaves"] = -10 * min(2, len(aud["suaves"]))
        pts += det["suaves"]
    return max(1, min(100, pts)), det


def elegir_mejor_titulo(candidatos_ia, ingrediente, problema, sugerencias, historial, verbose=True):
    pool, vistos = [], set()
    for c in (candidatos_ia or []):
        c = ajustar_titulo(c)
        if c and c.lower() not in vistos:
            vistos.add(c.lower())
            pool.append((c, "IA"))
    for c in generar_candidatos_codigo(ingrediente, problema):
        c = ajustar_titulo(c)
        if c.lower() not in vistos:
            vistos.add(c.lower())
            pool.append((c, "fórmula"))
    evaluados = []
    for t, origen in pool:
        s, det = puntuar_titulo(t, ingrediente, sugerencias, historial)
        evaluados.append((s, t, origen, det))
    validos = [x for x in evaluados if x[0] > 0]
    if verbose:
        print(f"   🧪 {len(pool)} candidatos de título | {len(validos)} válidos")
    if not validos:
        ing = str(ingrediente)
        return f"{ing[:1].upper() + ing[1:]}: tradición y bienestar 🌿", 0, {}
    validos.sort(key=lambda x: x[0] + random.uniform(0, 1.5), reverse=True)
    if verbose:
        for s, t, o, _ in validos[:3]:
            print(f"      [{s:>3}] ({o}) {t}")
    s, t, o, det = validos[0]
    return t, s, det


# ================================================================
# 4) TAGS EN CAPAS
# ================================================================
TAGS_MEGA_VOLUMEN = [
    "remedios naturales", "remedios caseros", "plantas medicinales", "hierbas medicinales",
    "medicina natural", "salud natural", "herbolaria mexicana", "herbolaria",
    "beneficios de las plantas", "vida saludable", "salud y bienestar",
    "remedios de la abuela", "medicina tradicional", "bienestar natural",
]

TAGS_SINTOMAS_VOLUMEN = {
    "circul": ["circulación sanguínea", "mejorar la circulación"],
    "presión": ["presión alta remedios", "bajar la presión naturalmente"],
    "insomnio": ["insomnio remedios", "dormir mejor naturalmente"],
    "sueño": ["dormir bien remedios", "insomnio remedios naturales"],
    "digest": ["mejorar la digestión", "digestión pesada remedios"],
    "gastritis": ["gastritis remedios naturales", "estómago sano remedios"],
    "estómago": ["dolor de estómago remedios", "estómago inflamado"],
    "colesterol": ["colesterol alto remedios", "bajar el colesterol naturalmente"],
    "energ": ["energía natural", "fatiga remedios naturales"],
    "cansancio": ["cansancio crónico remedios", "energía vital"],
    "defensas": ["defensas bajas remedios", "subir defensas naturalmente"],
    "inmunol": ["sistema inmunológico fuerte", "defensas naturales"],
    "estrés": ["estrés remedios naturales", "relajarse naturalmente"],
    "ansiedad": ["ansiedad remedios naturales", "calmar la ansiedad"],
    "nervios": ["nervios alterados remedios", "calmar los nervios naturalmente"],
    "azúcar": ["azúcar en sangre remedios", "controlar el azúcar naturalmente"],
    "diabetes": ["diabetes remedios naturales", "glucosa alta remedios"],
    "piel": ["cuidado de la piel natural", "piel sana remedios"],
    "acné": ["acné remedios naturales", "piel limpia remedios"],
    "cabello": ["cabello sano remedios", "caída del cabello remedios"],
    "uñas": ["uñas fuertes remedios", "uñas quebradizas remedios"],
    "várices": ["várices remedios naturales", "piernas cansadas remedios"],
    "hemorroides": ["hemorroides remedios naturales", "aliviar hemorroides"],
    "memoria": ["memoria y concentración", "mente clara remedios"],
    "cerebro": ["salud cerebral natural", "concentración remedios"],
    "inflam": ["desinflamar naturalmente", "inflamación remedios"],
    "dolor": ["dolor muscular remedios", "aliviar el dolor naturalmente"],
    "detox": ["desintoxicar el cuerpo", "riñones sanos remedios"],
    "menopausia": ["menopausia remedios naturales", "sofocos remedios"],
    "próstata": ["próstata sana remedios", "salud prostática natural"],
    "corazón": ["salud del corazón natural", "corazón sano remedios"],
    "cardio": ["salud cardiovascular natural", "corazón fuerte remedios"],
    "hígado": ["hígado sano remedios", "desintoxicar el hígado"],
    "pulmones": ["pulmones sanos remedios", "salud respiratoria natural"],
    "respir": ["bronquios remedios", "resfriado remedios naturales"],
    "gripe": ["gripe remedios naturales", "resfriado remedios"],
    "tos": ["tos remedios naturales", "aliviar la tos"],
    "alergia": ["alergia remedios naturales", "antihistamínico natural"],
    "artritis": ["artritis remedios naturales", "dolor articular remedios"],
    "articulaciones": ["articulaciones sanas remedios", "dolor de rodilla"],
    "envejecimiento": ["antienvejecimiento natural", "rejuvenecer naturalmente"],
    "quemaduras": ["quemaduras remedios naturales", "piel quemada remedios"],
    "laxante": ["estreñimiento remedios", "laxante natural"],
    "estreñimiento": ["estreñimiento remedios naturales", "digestión lenta"],
    "obesidad": ["control de peso natural", "bajar de peso naturalmente"],
    "adelgaz": ["perder peso naturalmente", "remedios para adelgazar"],
    "retención": ["retención de líquidos remedios", "desinflamar líquidos"],
    "sudor": ["sudoración excesiva remedios", "mal olor corporal"],
    "olor": ["mal olor remedios", "desodorante natural"],
}

# Temas médicos sensibles: se permiten pocos tags y siempre en formato "remedios/bienestar"
SENSIBLES = ["diabetes", "artritis", "presion", "colesterol", "azucar", "glucosa",
             "tiroides", "hipertension", "gastritis", "menopausia", "prostata"]


def clasificar_ingrediente(ingrediente):
    il = ingrediente.lower()
    grupos = [
        ("compuesto", ["mentol", "alcanfor", "eucaliptol", "terpeno", "extracto", "aceite esencial", "resina"]),
        ("lipido", ["omega", "dha", "epa", "ácido graso", "aceite de pescado", "krill", "linaza", "chía"]),
        ("proteina", ["colágeno", "colageno", "proteína", "proteina", "aminoácido", "whey", "creatina", "bcaa", "arginina", "glicina"]),
        ("micronutriente", ["vitamina", "vit ", "biotina", "magnesio", "zinc", "hierro", "calcio", "potasio",
                            "selenio", "cromo", "yodo", "cobre", "manganeso", "ácido fólico"]),
        ("fruta", ["naranja", "limón", "limon", "fresa", "manzana", "plátano", "piña", "mango", "papaya", "arándano",
                   "uva", "sandía", "kiwi", "guayaba", "granada", "cereza", "ciruela", "durazno", "tamarindo", "coco", "jitomate"]),
        ("probiotico", ["hongo", "reishi", "shiitake", "melena de león", "cordyceps", "levadura", "probiótico", "lactobacillus"]),
        ("raiz", ["cúrcuma", "curcuma", "jengibre", "ginseng", "maca", "ashwagandha", "valeriana", "regaliz",
                  "alcachofa", "betabel", "remolacha", "camote", "raíz", "raiz"]),
    ]
    for tipo, claves in grupos:
        if any(k in il for k in claves):
            return tipo
    return "planta"


_TAG_OK = re.compile(r"^[a-záéíóúüñ0-9\s]+$")


def construir_tags(ingrediente, problema, titulo="", sugerencias=None, tema_viral=None,
                   estricto=False, presupuesto=480):
    """Tags en capas, ordenados por prioridad. estricto=True limita a 30 chars/tag
    (modo seguro que se usa si YouTube rechaza los tags)."""
    max_len = 30 if estricto else 40
    ing = str(ingrediente).lower().strip()
    tipo = clasificar_ingrediente(ing)
    probs = [p.strip().lower() for p in str(problema or "").split(",") if p.strip()][:4]

    exacto = [ing]
    especificos = [f"{ing} beneficios", f"beneficios de {ing}", f"{ing} propiedades",
                   f"para qué sirve {ing}", f"cómo usar {ing}", f"{ing} remedios naturales",
                   f"{ing} uso tradicional"]
    extras_tipo = {
        "planta": [f"té de {ing}", f"infusión de {ing}", f"{ing} medicinal", f"planta {ing}"],
        "raiz": [f"raíz de {ing}", f"{ing} medicinal", f"té de {ing}"],
        "fruta": [f"fruta {ing}", f"jugo de {ing}", f"{ing} natural"],
        "compuesto": [f"{ing} natural", f"extracto {ing}"],
        "lipido": [f"suplemento {ing}", "omega 3 natural"],
        "proteina": [f"suplemento {ing}", f"{ing} natural"],
        "micronutriente": [f"suplemento {ing}", f"{ing} natural"],
        "probiotico": [f"suplemento {ing}", f"{ing} natural"],
    }
    especificos += extras_tipo.get(tipo, [])
    prob_txt = " ".join(probs)
    esp_prob = []
    for p in probs:
        esp_prob += [f"{ing} para {p}", f"remedios para {p}", f"{p} remedios naturales", p]
    for clave, frases in TAGS_SINTOMAS_VOLUMEN.items():
        if clave in prob_txt:
            esp_prob += frases[:2]
    generales = list(TAGS_MEGA_VOLUMEN)
    if tema_viral:
        generales = [k.lower() for k in tema_viral.get("keywords_cortas", [])[:2]] + generales
    cola = [s["frase"] for s in (sugerencias or [])[:20]]
    variantes = []
    for t in (exacto + especificos[:8] + esp_prob[:4]):
        sa = sin_acentos_tag(t)
        if sa != t:
            variantes.append(sa)
    variantes += [f"te de {sin_acentos_tag(ing)}", f"{sin_acentos_tag(ing)} propiedades"]
    if titulo:
        variantes += [p for p in re.findall(r"[a-záéíóúüñ]+", titulo.lower()) if 5 < len(p) <= 20][:3]

    orden = (exacto + especificos[:4] + generales[:3] + esp_prob[:6] + cola[:6] + especificos[4:]
             + esp_prob[6:] + variantes + generales[3:] + cola[6:])

    out, vistos, total, sensibles = [], set(), 0, 0
    for tag in orden:
        tg = re.sub(r"\s+", " ", str(tag).strip().lower())
        if tg in vistos or not (3 <= len(tg) <= max_len) or not _TAG_OK.match(tg):
            continue
        if not texto_seguro(tg):
            continue
        if any(s in normalizar(tg) for s in SENSIBLES):
            if sensibles >= 3:
                continue
            sensibles += 1
        costo = len(tg) + (2 if " " in tg else 0) + 1  # comillas implícitas + coma
        if total + costo > presupuesto:
            continue
        out.append(tg)
        vistos.add(tg)
        total += costo
        if len(out) >= 40:
            break
    if len(out) < 3:
        out = ["remedios naturales", "salud natural", ing[:max_len]]
    return ", ".join(out)


def generar_tags_emergencia(ingrediente):
    ing = str(ingrediente).lower().strip()
    base = [ing, f"{ing} beneficios", "remedios naturales", "remedios caseros", "salud natural",
            "medicina natural", "herbolaria mexicana", "plantas medicinales", "hierbas medicinales"]
    out = [t for t in base if 3 <= len(t) <= 30 and _TAG_OK.match(t)]
    return ", ".join(out)


# ================================================================
# 5) GANCHOS DE MINIATURA (complementan el título, no lo copian)
# ================================================================
GANCHOS_MINIATURA = {
    "busqueda": ["GUÍA COMPLETA", "USO TRADICIONAL", "ASÍ SE USA", "LO ESENCIAL"],
    "curiosidad": ["¿MITO O REAL?", "POCOS LO SABEN", "SABIDURÍA ANCESTRAL", "TE LO EXPLICO"],
    "problema_solucion": ["ALIADO NATURAL", "APOYO TRADICIONAL", "TRADICIÓN VIVA", "BIENESTAR DIARIO"],
}


def elegir_gancho_miniatura(titulo):
    tn_words = set(re.findall(r"\w+", normalizar(quitar_emojis(titulo))))
    tipo = tipo_titulo(titulo)
    orden_tipos = [tipo] + [t for t in GANCHOS_MINIATURA if t != tipo]
    mejor, mejor_sol = None, 99
    for i, tp in enumerate(orden_tipos):
        for g in GANCHOS_MINIATURA[tp]:
            if not texto_seguro(g):
                continue
            sol = len(set(re.findall(r"\w+", normalizar(g))) & tn_words) + i * 0.5
            if sol < mejor_sol or (sol == mejor_sol and random.random() < 0.4):
                mejor, mejor_sol = g, sol
    return mejor or "TRADICIÓN VIVA"


# Compatibilidad con el bot original
PALABRAS_PROHIBIDAS_TITULO = sorted(set(HARD_TERMS + SOFT_TERMS))


def generar_tags_seo_elite(ingrediente, problema, titulo, tema_viral=None, sugerencias=None):
    return construir_tags(ingrediente, problema, titulo, sugerencias, tema_viral)


def generar_tags_virales(ingrediente, problema=None, tema_viral=None):
    return construir_tags(ingrediente, problema, "", None, tema_viral)


def validar_tags_youtube(tags_str, max_len=40, presupuesto=495):
    """Validación final de tags (caracteres, longitud y presupuesto de 500)."""
    if not tags_str:
        return "remedios naturales, salud natural, bienestar"
    vistos, out, total = set(), [], 0
    for tag in [t.strip().lower() for t in tags_str.split(",") if t.strip()]:
        tg = re.sub(r"\s+", " ", tag)
        if tg in vistos or not (2 <= len(tg) <= max_len) or not _TAG_OK.match(tg) or "..." in tg:
            continue
        costo = len(tg) + (2 if " " in tg else 0) + 1
        if total + costo > presupuesto:
            continue
        vistos.add(tg)
        out.append(tg)
        total += costo
    if len(out) < 3:
        out = ["remedios naturales", "salud natural", "bienestar"]
    return ", ".join(out[:40])


# ================================================================
# UTILIDADES ASYNC
# ================================================================
def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ================================================================
# ESTADO Y ANTI-REPETICIÓN
# ================================================================
def _leer_json(ruta, defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def _escribir_json(ruta, data):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cargar_estado():
    return _leer_json(ESTADO_FILE, {"publicaciones_hoy": 0, "fecha": None, "ultima_publicacion": None})


def guardar_estado(estado):
    _escribir_json(ESTADO_FILE, estado)


def cargar_ingredientes_largos_usados():
    d = _leer_json(INGREDIENTES_LARGOS_FILE, {})
    return d.get("ingredientes", []) if isinstance(d, dict) else []


def guardar_ingrediente_largo_usado(ingrediente, producto):
    lista = cargar_ingredientes_largos_usados()
    entry = f"{ingrediente}|{producto}"
    if entry not in lista:
        lista.append(entry)
    _escribir_json(INGREDIENTES_LARGOS_FILE, {"ingredientes": lista[-80:]})


def reiniciar_ingredientes_largos():
    _escribir_json(INGREDIENTES_LARGOS_FILE, {"ingredientes": []})


def cargar_titulos():
    d = _leer_json(TITULOS_FILE, {"titulos": []})
    return d.get("titulos", []) if isinstance(d, dict) else []


def guardar_titulo(titulo):
    lista = cargar_titulos()
    if titulo not in lista:
        lista.append(titulo)
    _escribir_json(TITULOS_FILE, {"titulos": lista[-100:]})


def deberia_publicar_ahora(estado):
    tz = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(tz)
    hoy = ahora.date().isoformat()
    if estado.get("fecha") != hoy:
        estado["fecha"] = hoy
        estado["publicaciones_hoy"] = 0
    if estado.get("publicaciones_hoy", 0) >= MAX_LARGOS_DIA:
        print("✅ Límite diario de videos largos alcanzado.")
        return False

    forzar = os.getenv("FORZAR_PUBLICACION", "0") == "1"
    if not forzar and HORA_EXCLUIR_INICIO <= ahora.hour < HORA_EXCLUIR_FIN:
        print(f"🌙 Madrugada ({ahora.hour}h CDMX). No publico entre {HORA_EXCLUIR_INICIO}:00 y {HORA_EXCLUIR_FIN}:00.")
        return False

    ultima = estado.get("ultima_publicacion")
    if ultima and not forzar:
        diff = (ahora - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(INTERVALO_MIN_HORAS, INTERVALO_MAX_HORAS)
        if diff < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h (han pasado {diff:.1f}h).")
            return False
    if not forzar:
        retraso = random.randint(0, RETRASO_MAX_MINUTOS * 60)
        if retraso > 0:
            print(f"⏳ Retraso aleatorio: {retraso // 60} min...")
            time.sleep(retraso)
    return True


def seleccionar_producto_e_ingrediente_largo():
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    df = df[df["imagen_url"].notna() & (df["imagen_url"] != "")]
    df = df[df["ingredientes_clave"].notna() & (df["ingredientes_clave"] != "")]
    usados = cargar_ingredientes_largos_usados()

    for _ in range(60):
        producto = df.sample(1).iloc[0].to_dict()
        ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",") if i.strip()]
        if not ingredientes:
            continue
        ingrediente = random.choice(ingredientes)
        if f"{ingrediente}|{producto['nombre']}" not in usados:
            print(f"✅ Par elegido: {ingrediente} → {producto['nombre']}")
            return producto, ingrediente

    print("🔄 Pool de ingredientes agotado. Reiniciando historial...")
    reiniciar_ingredientes_largos()
    producto = df.sample(1).iloc[0].to_dict()
    ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",") if i.strip()]
    return producto, random.choice(ingredientes)


def cargar_json_catalogo(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def obtener_info_ingrediente_catalogo(ingrediente):
    for item in cargar_json_catalogo(CATALOGO_INGREDIENTES):
        nombre = str(item.get("nombre", "")).lower()
        if nombre and (ingrediente.lower() in nombre or nombre in ingrediente.lower()):
            partes = []
            for clave in ["descripcion", "beneficios", "propiedades", "formas_de_uso", "caracteristicas_visuales", "datos_curiosos"]:
                val = item.get(clave)
                if val:
                    if isinstance(val, list):
                        val = ", ".join(map(str, val))
                    partes.append(f"{clave}: {val}")
            return " | ".join(partes)
    return ""


def obtener_curiosidad_catalogo(ingrediente):
    curios = cargar_json_catalogo(CATALOGO_CURIOSIDADES)
    if not curios:
        return ""
    relacionadas = [c for c in curios if ingrediente.lower() in json.dumps(c, ensure_ascii=False).lower()]
    elegida = random.choice(relacionadas) if relacionadas else random.choice(curios)
    return f"{elegida.get('titulo', '')} {elegida.get('dato_curioso', '')}".strip()


def obtener_keywords_aleatorias_virales(cantidad=5):
    todas = []
    for categoria, kws in KEYWORDS_VIRALES.items():
        todas.extend(kws)
    seleccionadas = []
    for _ in range(cantidad):
        if not todas:
            break
        pesos = [kw["peso"] for kw in todas]
        elegida = random.choices(todas, weights=pesos, k=1)[0]
        seleccionadas.append(elegida["kw"])
        todas.remove(elegida)
    return seleccionadas


# ================================================================
# IA: GUION (con keywords reales + auditoría de política)
# ================================================================
def ia_genera_guion_largo(producto, ingrediente, tema_viral, sugerencias):
    info_catalogo = obtener_info_ingrediente_catalogo(ingrediente) or "Sin ficha en catálogo; usa conocimiento general verificado."
    curiosidad = obtener_curiosidad_catalogo(ingrediente) or ""
    problema = producto.get("recomendado_para", "")
    kws = obtener_keywords_aleatorias_virales(6)
    frases_reales = [s["frase"] for s in sugerencias[:10]]
    prohibidas_str = ", ".join(f'"{p}"' for p in HARD_TERMS[:60]) + "..."

    base_prompt = f"""Eres guionista experto en salud natural, SEO para YouTube y herbolaria mexicana. Creas videos LARGOS (3 a 4 minutos, horizontal) optimizados para búsquedas reales y 100% SEGUROS ante las políticas de YouTube.

📦 PRODUCTO COMPLETO:
NOMBRE: {producto.get('nombre')}
PRESENTACIÓN: {producto.get('presentacion')}
RECOMENDADO PARA: {problema}
INGREDIENTES CLAVE: {producto.get('ingredientes_clave')}
BENEFICIOS: {producto.get('beneficios')}
MODO DE EMPLEO: {producto.get('MODO DE EMPLEO / DOSIS')}

🌱 INGREDIENTE ESTRELLA OBLIGATORIO (NO lo cambies): {ingrediente}
📚 FICHA DEL CATÁLOGO: {info_catalogo}
💡 DATO CURIOSO (úsalo en el hook o en un beneficio): {curiosidad}
🎯 TEMA VIRAL: {tema_viral['tema'].upper()} (keywords: {', '.join(tema_viral['keywords_cortas'])})
💊 PROBLEMA: {problema}

🔎 FRASES QUE LA GENTE BUSCA REALMENTE EN YOUTUBE MÉXICO (autocompletado). Incorpóralas de forma NATURAL en el guion hablado (sin forzar) y úsalas para inspirar los títulos:
{chr(10).join('- ' + f for f in frases_reales) if frases_reales else '- (sin datos; usa remedios naturales, beneficios, propiedades)'}

🔑 KEYWORDS GENERALES: {', '.join(kws)}

⚠️ DURACIÓN OBJETIVO 3 A 4 MINUTOS. Sé directo, sin relleno. Respeta los conteos de palabras.

🎬 ESTRUCTURA OBLIGATORIA (8 segmentos):
1. "hook" (35-45 palabras): ⚠️ La PRIMERA ORACIÓN debe decir el nombre del ingrediente Y el beneficio principal en menos de 15 palabras. Ejemplo: "La zarzaparrilla es la raíz que tu circulación estaba esperando."
2. "problema" (65-80): el problema/síntoma de la audiencia ({problema}).
3. "ingrediente" (95-110): presenta el ingrediente, origen breve. Menciona su nombre al menos 2 veces.
4. "beneficio_1" (65-80): primer beneficio según la tradición.
5. "beneficio_2" (65-80): segundo beneficio.
6. "beneficio_3" (65-80): tercer beneficio.
7. "producto" (120-140): presenta {producto.get('nombre')}, cómo contiene el ingrediente y modo de empleo.
8. "cta" (100-120): resumen breve + DEBE terminar EXACTAMENTE con: "¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

REGLAS:
- Si el ingrediente suena a saborizante, habla del ingrediente REAL.
- NO digas números de WhatsApp/Telegram en el audio.
- Tono educativo, cálido y cercano. Sin emojis en el texto hablado.
- Incluye un disclaimer natural: "esto es información educativa basada en la tradición herbolaria, no sustituye la consulta médica".
- Cada segmento lleva "texto_pantalla" (MÁX 3-4 palabras, será título de capítulo en beneficios) y "query_pexels" (inglés, descripción visual horizontal 16:9).

🚨 POLÍTICA DE SALUD DE YOUTUBE (CRÍTICO). NUNCA uses: {prohibidas_str}
✅ MARCOS SEGUROS: "apoya", "favorece", "contribuye al bienestar", "según la tradición", "aliado natural", "complemento para", "parte de un estilo de vida saludable".

📝 TÍTULOS: devuelve 8 CANDIDATOS distintos (máx 66 caracteres, SIN hashtags, 1 emoji como máximo, keyword del ingrediente en las primeras palabras). Mezcla 3 tipos:
- BÚSQUEDA (2): usa una frase real de la lista de arriba (ej. "Para qué sirve X", "X beneficios", "Cómo tomar X").
- CURIOSIDAD (3): brecha de curiosidad honesta, con número o pregunta.
- PROBLEMA-SOLUCIÓN (3): conecta el ingrediente con {problema} usando "apoya", "tradición", "aliado".
Cada candidato debe empezar de forma DIFERENTE. Nada de promesas de cura ni clickbait exagerado.

Devuelve ESTRICTAMENTE este JSON:
{{
  "ingrediente_real": "nombre real normalizado del ingrediente",
  "titulos_candidatos": ["...", "...", "...", "...", "...", "...", "...", "..."],
  "segmentos": {{
    "hook": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "problema": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "ingrediente": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "beneficio_1": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "beneficio_2": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "beneficio_3": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "producto": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}},
    "cta": {{"texto": "...", "texto_pantalla": "...", "query_pexels": "..."}}
  }},
  "gancho_descripcion": "Gancho SEO con keyword (máx 90 caracteres)",
  "contexto_descripcion": "1-2 oraciones educativas con keywords naturales"
}}"""

    aviso_extra = ""
    for intento in range(5):
        try:
            print(f"🤖 IA escribiendo guion... (intento {intento + 1}/5)")
            r = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": base_prompt + aviso_extra}],
                      "temperature": 0.9, "max_tokens": 4000, "response_format": {"type": "json_object"}},
                timeout=150)
            r.raise_for_status()
            resp = r.json()["choices"][0]["message"]["content"].strip()
            resp = re.sub(r'`json\s*', '', resp).replace('`', '')
            i0, i1 = resp.find('{'), resp.rfind('}')
            data = json.loads(resp[i0:i1 + 1], strict=False)

            segs = data.get("segmentos", {})
            for k in ORDEN_SEGMENTOS:
                if k not in segs or len(segs[k].get("texto", "")) < 30:
                    raise ValueError(f"Segmento {k} faltante o corto")

            # CTA exacto
            cta_txt = segs["cta"]["texto"]
            if "contactos están en la descripción" not in cta_txt.lower():
                segs["cta"]["texto"] = cta_txt.rstrip() + " ¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

            # Auditoría de política del guion hablado (ignora el descargo "no sustituye...")
            texto_total = " ".join(segs[k]["texto"] for k in ORDEN_SEGMENTOS)
            aud = auditar_texto(texto_total, es_guion=True)
            if aud["duras"]:
                aviso_extra = f"\n\n⚠️ En el intento anterior usaste palabras PROHIBIDAS: {aud['duras']}. Reescribe sin ellas ni sinónimos que prometan curas."
                raise ValueError(f"Guion con palabras prohibidas: {aud['duras']}")

            # SEO hablado: ingrediente en la primera oración del hook
            real = data.get("ingrediente_real") or ingrediente
            primera = " ".join(segs["hook"]["texto"].split()[:18])
            toks = [t for t in normalizar(real).split() if len(t) > 3] or [normalizar(real)]
            if not any(t in normalizar(primera) for t in toks):
                aviso_extra = f"\n\n⚠️ La primera oración del hook DEBE nombrar '{real}' y su beneficio."
                raise ValueError("El hook no nombra el ingrediente al inicio")

            palabras = sum(len(segs[k]["texto"].split()) for k in ORDEN_SEGMENTOS)
            print(f"   📏 Guion: {palabras} palabras (~{palabras / 2.7 / 60:.1f} min)")
            if palabras < 450 or palabras > 850:
                print("   ⚠️ Duración fuera del objetivo 3-4 min, se continúa igualmente.")

            data["ingrediente_real"] = real
            print(f"✅ Guion listo. Ingrediente real: {real}")
            return data
        except Exception as e:
            print(f"⚠️ Intento {intento + 1} falló: {e}")
            if intento == 4:
                sys.exit(1)
            time.sleep(8)


# ================================================================
# VOZ (con tiempos de palabra para subtítulos)
# ================================================================
async def _tts(texto, path, voz):
    try:
        com = edge_tts.Communicate(texto, voz["voz"], rate=voz["velocidad"], boundary="WordBoundary")
    except TypeError:
        com = edge_tts.Communicate(texto, voz["voz"], rate=voz["velocidad"])
    eventos = []
    with open(path, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
                eventos.append((ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
    return eventos


def _audio_ok(path):
    return os.path.exists(path) and os.path.getsize(path) > 100


def validar_voz():
    for voz in VOCES_DISPONIBLES:
        try:
            print(f"🎤 Probando voz: {voz['voz']} ({voz['estilo']})...")
            _run(_tts("Prueba de voz para verificar disponibilidad.", "test_voz.mp3", voz))
            if _audio_ok("test_voz.mp3"):
                os.remove("test_voz.mp3")
                print(f"✅ Voz seleccionada: {voz['voz']}")
                return voz
        except Exception as e:
            print(f"⚠️ Voz {voz['voz']} no disponible: {str(e)[:100]}")
    print("❌ Ninguna voz respondió, usando la primera por defecto")
    return VOCES_DISPONIBLES[0]


def generar_audio(texto, path, voz, max_intentos=3):
    """Devuelve (eventos, voz_usada) o None. Si cambia de voz, el llamador la mantiene."""
    limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9.,;:!?¿¡\'"]', '', texto)
    for intento in range(max_intentos):
        try:
            ev = _run(_tts(limpio, path, voz))
            if _audio_ok(path):
                return ev, voz
        except Exception as e:
            print(f"   ⚠️ Audio intento {intento + 1}/{max_intentos}: {str(e)[:80]}")
            if intento < max_intentos - 1:
                time.sleep(2 ** intento)
    print(f"   🔄 Voz {voz['voz']} falló. Probando alternativas...")
    for alt in VOCES_DISPONIBLES:
        if alt["voz"] == voz["voz"]:
            continue
        try:
            ev = _run(_tts(limpio, path, alt))
            if _audio_ok(path):
                print(f"   ✅ Cambio a voz {alt['voz']} para el resto del video")
                return ev, alt
        except Exception as e:
            print(f"   ⚠️ {alt['voz']} falló: {str(e)[:60]}")
    return None


# ================================================================
# IMÁGENES DE SEGMENTO
# ================================================================
def buscar_imagen_pexels_horizontal(query, intentos=3):
    if not PEXELS_API_KEY:
        return None
    for _ in range(intentos):
        try:
            params = {"query": f"{query} {random.choice(['natural', 'healthy', 'close up', 'cinematic'])}",
                      "orientation": "landscape", "per_page": 6, "page": random.randint(1, 5)}
            r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": PEXELS_API_KEY},
                             params=params, timeout=15)
            if r.status_code == 200 and r.json().get("photos"):
                return random.choice(r.json()["photos"][:4])["src"]["large2x"]
        except Exception:
            pass
        time.sleep(3)
    return None


def descargar_imagen(url, salida):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    if img.mode != "RGB":
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA", "P"):
            rgba = img.convert("RGBA")
            fondo.paste(rgba, mask=rgba.split()[3])
            img = fondo
        else:
            img = img.convert("RGB")
    img = ImageOps.fit(img, (ANCHO, ALTO), Image.Resampling.LANCZOS)
    img.save(salida, "JPEG", quality=90)
    return salida


SEGMENTO_FLUX_SUFFIX = (", ultra vivid saturated colors, dramatic cinematic lighting, high-contrast macro photography, "
                        "lush botanical herbal theme, glossy dew textures, dark vignette edges with bright glowing subject, "
                        "clean negative space in the lower third for text overlay, "
                        "no text, no watermark, no people, widescreen 16:9")


def _flux_cloudflare(prompt, salida, size=(ANCHO, ALTO), timeout=90):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    r = requests.post(url, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
                      json={"prompt": prompt, "steps": 4}, timeout=timeout)
    r.raise_for_status()
    b64 = (r.json().get("result") or {}).get("image")
    if not b64:
        raise ValueError("Cloudflare no devolvió imagen")
    with open(salida, "wb") as f:
        f.write(base64.b64decode(b64))
    with Image.open(salida) as im:
        ImageOps.fit(im.convert("RGB"), size, Image.Resampling.LANCZOS).save(salida, "JPEG", quality=90)
    return salida


def buscar_imagen_segmento(query_en, salida):
    if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:
        for intento in range(1, 4):
            try:
                print(f"   🎨 Flux segmento intento {intento}/3...")
                _flux_cloudflare(query_en + SEGMENTO_FLUX_SUFFIX, salida)
                print("   ✅ Imagen generada con Flux (Cloudflare)")
                return salida
            except Exception as e:
                print(f"   ⚠️ Flux intento {intento} falló: {e}")
                time.sleep(2)
        print("   ⚠️ Flux falló 3 veces. Usando Pexels.")
    else:
        print("   ⚠️ Sin keys de Cloudflare. Usando Pexels.")
    url_img = buscar_imagen_pexels_horizontal(query_en)
    if url_img:
        try:
            return descargar_imagen(url_img, salida)
        except Exception as e:
            print(f"   ⚠️ Pexels falló ({e}). Imagen por defecto.")
    return descargar_imagen("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1920&fit=crop", salida)


def potenciar_imagen_segmento(img_path):
    try:
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            im = ImageEnhance.Color(im).enhance(1.35)
            im = ImageEnhance.Contrast(im).enhance(1.18)
            im = ImageEnhance.Brightness(im).enhance(1.05)
            im = ImageEnhance.Sharpness(im).enhance(1.3)
            im.save(img_path, "JPEG", quality=90)
    except Exception as e:
        print(f"⚠️ Error potenciando imagen: {e}")
    return img_path


# ================================================================
# TIPOGRAFÍA / RENDER DE TEXTO
# ================================================================
FONT_THUMB_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_THUMB_LOCAL = "Anton-Regular.ttf"


def asegurar_fuente_thumbnail():
    if os.path.exists(FONT_THUMB_LOCAL):
        return FONT_THUMB_LOCAL
    try:
        r = requests.get(FONT_THUMB_URL, timeout=30)
        r.raise_for_status()
        with open(FONT_THUMB_LOCAL, "wb") as f:
            f.write(r.content)
        print("✅ Fuente Anton descargada")
        return FONT_THUMB_LOCAL
    except Exception:
        print("⚠️ No se pudo descargar Anton, usando DejaVu")
        return FUENTE


def _medir(texto, font, stroke=0):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    return d.textbbox((0, 0), texto, font=font, stroke_width=stroke)


def render_texto_gradiente(texto, font_path, size, stroke=10, top=(255, 242, 90), bottom=(255, 150, 0)):
    font = ImageFont.truetype(font_path, size)
    b = _medir(texto, font, stroke)
    w = (b[2] - b[0]) + stroke * 2 + 8
    h = (b[3] - b[1]) + stroke * 2 + 8
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    ox, oy = stroke + 4 - b[0], stroke + 4 - b[1]
    d.text((ox, oy), texto, font=font, fill=(10, 10, 10, 255), stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
    grad = np.zeros((h, w, 4), dtype=np.uint8)
    t = np.linspace(0, 1, h)[:, None]
    grad_rgb = (np.array(top, float) * (1 - t) + np.array(bottom, float) * t).astype(np.uint8)
    grad[:, :, :3] = np.broadcast_to(grad_rgb[:, None, :], (h, w, 3))
    grad[:, :, 3] = 255
    grad_img = Image.fromarray(grad, "RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((ox, oy), texto, font=font, fill=255)
    grad_img.putalpha(mask)
    return Image.alpha_composite(out, grad_img)


def render_texto_solido(texto, font_path, size, fill=(255, 255, 255), stroke=8):
    font = ImageFont.truetype(font_path, size)
    b = _medir(texto, font, stroke)
    w = (b[2] - b[0]) + stroke * 2 + 8
    h = (b[3] - b[1]) + stroke * 2 + 8
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((stroke + 4 - b[0], stroke + 4 - b[1]), texto, font=font,
                             fill=fill + (255,), stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
    return img


def render_banner(texto, font_path, size, bg=(198, 30, 30), fg=(255, 255, 255), borde=(255, 235, 59), pad_x=28, pad_y=12):
    font = ImageFont.truetype(font_path, size)
    b = _medir(texto, font)
    tw, th = b[2] - b[0], b[3] - b[1]
    w = tw + pad_x * 2 + 8
    h = th + pad_y * 2 + 8
    img = Image.new("RGBA", (w + 14, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([7, 10, w + 7, h + 10], radius=14, fill=(0, 0, 0, 140))
    d.rounded_rectangle([7, 6, w + 7, h + 6], radius=14, fill=bg + (255,), outline=borde + (255,), width=4)
    d.text((7 + pad_x - b[0], 6 + pad_y - b[1]), texto, font=font, fill=fg + (255,))
    return img


def _fit(texto, font_path, size_max, size_min, ancho_max, renderer, **kw):
    size = size_max
    while size > size_min:
        img = renderer(texto, font_path, size, **kw)
        if img.width <= ancho_max:
            return img
        size -= 6
    return renderer(texto, font_path, size_min, **kw)


# ================================================================
# PRODUCTO RECORTADO (cache: rembg corre una sola vez por video)
# ================================================================
_CACHE_PROD = {}


def producto_recortado(url):
    if url not in _CACHE_PROD:
        rp = requests.get(url, timeout=20, verify=False)
        prod = Image.open(io.BytesIO(rp.content)).convert("RGBA")
        try:
            prod = remove(prod)
            print("   ✂️ Fondo del producto eliminado")
        except Exception as e:
            print(f"   ⚠️ rembg falló ({e}), usando imagen original")
        bbox = prod.getbbox()
        if bbox:
            prod = prod.crop(bbox)
        _CACHE_PROD[url] = prod
    return _CACHE_PROD[url].copy()


def _cargar_fondo(url_o_ruta):
    if os.path.exists(url_o_ruta):
        return Image.open(url_o_ruta).convert("RGB")
    r = requests.get(url_o_ruta, timeout=20)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def componer_producto_horizontal(url_producto, fondo, salida="img_producto_largo.jpg"):
    try:
        fondo_img = ImageOps.fit(_cargar_fondo(fondo), (ANCHO, ALTO), Image.Resampling.LANCZOS)
        prod = producto_recortado(url_producto)
        th = int(ALTO * 0.75)
        prod = prod.resize((int(prod.width * (th / prod.height)), th), Image.Resampling.LANCZOS)
        sombra = prod.copy().filter(ImageFilter.GaussianBlur(radius=25))
        x, y = ANCHO - prod.width - 140, (ALTO - th) // 2
        fondo_img.paste(sombra, (x - 12, y - 12), sombra)
        fondo_img.paste(prod, (x, y), prod)
        fondo_img.save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error componiendo producto: {e}")
        return None


def quemar_texto_pantalla(img_path, texto, salida, estilo="lower"):
    try:
        fuente = asegurar_fuente_thumbnail()
        with Image.open(img_path) as im:
            img = im.convert("RGBA")
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        texto_up = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ¡!¿?]', '', texto or "").upper().strip()
        if not texto_up:
            img.convert("RGB").save(salida, "JPEG", quality=90)
            return salida
        if estilo == "center":
            bloque = _fit(texto_up, fuente, 170, 70, int(ANCHO * 0.92), render_texto_gradiente)
            bloque = bloque.rotate(2, expand=True, resample=Image.BICUBIC)
            x = (ANCHO - bloque.width) // 2
            y = (ALTO - bloque.height) // 2 - 60
            d.rounded_rectangle([x - 50, y - 40, x + bloque.width + 50, y + bloque.height + 40],
                                radius=36, fill=(0, 0, 0, 150))
            capa.paste(bloque, (x, y), bloque)
            badge = render_banner("SALUD NATURAL", fuente, 46, bg=(198, 30, 30))
            capa.paste(badge, ((ANCHO - badge.width) // 2, y + bloque.height + 60), badge)
        else:
            for yy in range(ALTO - 380, ALTO):
                a = int(150 * ((yy - (ALTO - 380)) / 380))
                d.line([(0, yy), (ANCHO, yy)], fill=(0, 0, 0, a))
            banner = _fit(texto_up, fuente, 110, 48, int(ANCHO * 0.86), render_banner, bg=(198, 30, 30))
            banner = banner.rotate(-2, expand=True, resample=Image.BICUBIC)
            capa.paste(banner, ((ANCHO - banner.width) // 2, ALTO - banner.height - 150), banner)
        Image.alpha_composite(img, capa).convert("RGB").save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error quemando texto: {e}")
        return img_path


def crear_overlay_cta(salida="cta_overlay.png"):
    try:
        img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, ALTO - 150), (ANCHO, ALTO)], fill=(0, 0, 0, 185))
        texto = "CONTACTOS EN LA DESCRIPCIÓN"
        font = ImageFont.truetype(FUENTE, 62)
        tw = draw.textbbox((0, 0), texto, font=font)[2]
        draw.text(((ANCHO - tw) // 2, ALTO - 122), texto, font=font, fill=(255, 214, 102, 255))
        img.save(salida)
        return salida
    except Exception as e:
        print(f"⚠️ Error overlay CTA: {e}")
        return None


def crear_overlay_aviso(salida="aviso_overlay.png"):
    try:
        img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        txt = "Contenido educativo. No sustituye la consulta médica."
        f = ImageFont.truetype(FUENTE, 40)
        tw = d.textbbox((0, 0), txt, font=f)[2]
        d.rounded_rectangle([((ANCHO - tw) // 2 - 30, 60), ((ANCHO + tw) // 2 + 30, 130)], radius=18, fill=(0, 0, 0, 165))
        d.text(((ANCHO - tw) // 2, 76), txt, font=f, fill=(255, 255, 255, 235))
        img.save(salida)
        return salida
    except Exception as e:
        print(f"⚠️ Error overlay aviso: {e}")
        return None


# ================================================================
# VIDEO
# ================================================================
def efecto_ken_burns(img_path, duracion, direccion="in"):
    clip = ImageClip(img_path).set_duration(duracion)
    if direccion == "in":
        clip = clip.resize(lambda t: 1.0 + 0.25 * (t / duracion))
    else:
        clip = clip.resize(lambda t: 1.25 - 0.25 * (t / duracion))

    def crop_center(frame):
        h, w = frame.shape[:2]
        x1 = max(0, (w - ANCHO) // 2)
        y1 = max(0, (h - ALTO) // 2)
        return frame[y1:min(h, y1 + ALTO), x1:min(w, x1 + ANCHO)]

    return clip.fl_image(crop_center)


def montar_video_largo(segmentos_img, salida="largo_final.mp4"):
    clips_video, clips_audio, duraciones = [], [], []
    for i, seg in enumerate(segmentos_img):
        audio = AudioFileClip(seg["audio_path"])
        dur = audio.duration + (PAUSA_ENTRE_SEGMENTOS if i < len(segmentos_img) - 1 else 0)
        duraciones.append(dur)
        clips_video.append(efecto_ken_burns(seg["img_path"], dur, "in" if i % 2 == 0 else "out"))
        clips_audio.append(audio)
        if i < len(segmentos_img) - 1:
            clips_audio.append(AudioClip(lambda t: 0, duration=PAUSA_ENTRE_SEGMENTOS))

    audio_narracion = concatenate_audioclips(clips_audio)
    video = concatenate_videoclips(clips_video, method="compose")
    duracion_total = audio_narracion.duration

    musicas = [f for f in os.listdir(".") if f.lower().endswith(".mp3")
               and not f.startswith(("seg", "test", "audio")) and os.path.getsize(f) > 100]
    random.shuffle(musicas)
    audio_final = audio_narracion
    for m in musicas:
        try:
            mc = AudioFileClip(m)
            if mc.duration < duracion_total:
                mc = concatenate_audioclips([mc] * (int(duracion_total / mc.duration) + 1))
            mc = mc.subclip(0, duracion_total).volumex(0.09)
            audio_final = CompositeAudioClip([audio_narracion, mc])
            print(f"🎵 Música de fondo: {m} (9%)")
            break
        except Exception:
            continue
    video = video.set_audio(audio_final)

    overlays = [video]
    aviso = crear_overlay_aviso()
    if aviso:
        overlays.append(ImageClip(aviso, transparent=True).set_start(0).set_duration(6))
    cta = crear_overlay_cta()
    if cta:
        overlays.append(ImageClip(cta, transparent=True).set_start(max(duracion_total - 15, 0)).set_duration(15))
    video = CompositeVideoClip(overlays, size=(ANCHO, ALTO))

    print("🎬 Renderizando video largo (puede tardar varios minutos)...")
    video.write_videofile(salida, fps=24, codec="libx264", audio_codec="aac",
                          threads=4, preset="ultrafast", verbose=False, logger=None)
    return salida, duraciones, duracion_total


# ================================================================
# SUBTÍTULOS SRT + CAPÍTULOS CON KEYWORDS
# ================================================================
def formatear_timestamp(segundos):
    return f"{int(segundos) // 60:02d}:{int(segundos) % 60:02d}"


def _fmt_srt(t):
    t = max(0.0, t)
    ms = int(round((t - int(t)) * 1000))
    s = int(t)
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


def _palabras_con_tiempo(eventos, texto, duracion):
    palabras = []
    for inicio, dur, txt in eventos:
        ws = txt.split()
        total = sum(len(w) for w in ws) or 1
        t = inicio
        for w in ws:
            d = dur * len(w) / total
            palabras.append((t, t + d, w))
            t += d
    if not palabras:  # sin eventos: reparto proporcional
        ws = texto.split()
        total = sum(len(w) for w in ws) or 1
        t = 0.0
        for w in ws:
            d = duracion * len(w) / total
            palabras.append((t, t + d, w))
            t += d
    return palabras


def construir_srt(segmentos_info, salida="subtitulos_largo.srt"):
    cues = []
    for seg in segmentos_info:
        pals = _palabras_con_tiempo(seg["eventos"], seg["texto"], seg["duracion"])
        grupo = []

        def volcar():
            if grupo:
                ini = seg["inicio"] + grupo[0][0]
                fin = seg["inicio"] + grupo[-1][1]
                cues.append([ini, max(fin, ini + 0.4), " ".join(x[2] for x in grupo)])
                grupo.clear()

        for p in pals:
            grupo.append(p)
            fin_frase = p[2].endswith((".", "?", "!", ",", ";", ":"))
            if len(grupo) >= 8 or (grupo[-1][1] - grupo[0][0]) >= 3.5 or (fin_frase and len(grupo) >= 4):
                volcar()
        volcar()
    for i in range(len(cues) - 1):  # evita solapes
        if cues[i][1] > cues[i + 1][0]:
            cues[i][1] = max(cues[i][0] + 0.2, cues[i + 1][0] - 0.01)
    with open(salida, "w", encoding="utf-8") as f:
        for i, (ini, fin, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{_fmt_srt(ini)} --> {_fmt_srt(fin)}\n{txt}\n\n")
    print(f"📝 SRT generado: {len(cues)} líneas")
    return salida


def generar_capitulos_seo(duraciones, guion, ing, problema):
    prob = (str(problema).split(",")[0].strip().lower() or "bienestar")
    Ing = ing[:1].upper() + ing[1:]
    segs = guion["segmentos"]

    def beneficio(k, n):
        t = (segs.get(k, {}).get("texto_pantalla") or "").strip().title()
        return f"Beneficio {n}: {t}" if t else f"Beneficio {n} tradicional de {ing}"

    nombres = [
        f"Qué es {Ing} y para qué se usa",
        f"{prob.capitalize()}: lo que debes saber",
        f"Origen y uso tradicional de {ing}",
        beneficio("beneficio_1", 1), beneficio("beneficio_2", 2), beneficio("beneficio_3", 3),
        f"Producto con {ing} y cómo usarlo",
        "Contacto y cómo conseguirlo",
    ]
    lineas, acumulado = [], 0.0
    for i, dur in enumerate(duraciones):
        nombre = nombres[i] if i < len(nombres) else f"Capítulo {i + 1}"
        if not texto_seguro(nombre):
            nombre = f"Parte {i + 1}: {ing}"
        lineas.append(f"{formatear_timestamp(acumulado)} {nombre}")
        acumulado += dur
    return "\n".join(lineas)


# ================================================================
# 🎨 FONDO DE MINIATURA: FLUX (Cloudflare → HuggingFace) → Pexels
# ================================================================
FLUX_PROMPT_SUFFIX = (", dramatic macro photography, vivid saturated colors, cinematic lighting, "
                      "professional youtube thumbnail background, no text, no watermark, widescreen 16:9")


def buscar_fondo_flux_cloudflare(query, salida="bg_ia.jpg"):
    return _flux_cloudflare(query + FLUX_PROMPT_SUFFIX, salida, size=(1280, 720), timeout=120)


def buscar_fondo_flux_huggingface(query, salida="bg_ia.jpg"):
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    r = requests.post(url, headers={"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"},
                      json={"inputs": query + FLUX_PROMPT_SUFFIX}, timeout=120)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "")
    if "image" not in ctype or len(r.content) < 20000:
        raise ValueError(f"HF no devolvió imagen válida (ctype={ctype}, bytes={len(r.content)})")
    with open(salida, "wb") as f:
        f.write(r.content)
    with Image.open(salida) as im:
        ImageOps.fit(im.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS).save(salida, "JPEG", quality=90)
    return salida


def buscar_fondo_ia_flux(query, salida="bg_ia.jpg", intentos=3):
    providers = []
    if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:
        providers.append(("Cloudflare", buscar_fondo_flux_cloudflare))
    if HUGGINGFACE_TOKEN:
        providers.append(("HuggingFace", buscar_fondo_flux_huggingface))
    if not providers:
        print("⚠️ Sin keys de Flux configuradas. Se usará Pexels para la miniatura.")
        return None
    for intento in range(1, intentos + 1):
        nombre, fn = providers[(intento - 1) % len(providers)]
        try:
            print(f"🎨 Generando fondo de miniatura con Flux ({nombre}) - intento {intento}/{intentos}...")
            resultado = fn(query, salida)
            print(f"✅ Fondo Flux generado ({nombre})")
            return resultado
        except Exception as e:
            print(f"⚠️ Flux ({nombre}) falló: {e}")
            time.sleep(3)
    print("⚠️ Flux falló tras 3 intentos. Usando Pexels.")
    return None


# ================================================================
# MINIATURAS: 3 VARIANTES + SCORE
# ================================================================
def _preparar_base(img_base):
    with Image.open(img_base) as f:
        bg = ImageOps.fit(f.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
    bg = ImageEnhance.Color(bg).enhance(1.45)
    bg = ImageEnhance.Contrast(bg).enhance(1.22)
    bg = ImageEnhance.Brightness(bg).enhance(1.05)
    return bg.convert("RGBA")


def _gradiente_izq(bg, ancho=900, alpha=210):
    capa = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for x in range(ancho):
        d.line([(x, 0), (x, bg.height)], fill=(0, 0, 0, int(alpha * (1 - x / ancho))))
    return Image.alpha_composite(bg, capa)


def _pegar_bloques(bg, bloques, x=46, y=34, y_max=590, rot=2):
    for b in bloques:
        try:
            r = b.rotate(rot, expand=True, resample=Image.BICUBIC)
            bg.paste(r, (x, y), r)
            y += r.height + 8
        except Exception as e:
            print(f"⚠️ Bloque de texto falló: {e}")
        if y > y_max:
            break
    return bg


def _bloque_ingrediente(ing, fuente, ancho_max, size_max):
    linea = (" ".join(ing.split()[:2]) or "REMEDIOS NATURALES").upper()
    try:
        return _fit(linea, fuente, size_max, 64, ancho_max, render_texto_gradiente)
    except Exception as e:
        print(f"⚠️ Degradado falló ({e}); texto sólido")
        return _fit(linea, fuente, size_max, 64, ancho_max, render_texto_solido, fill=(255, 214, 102))


def _pegar_producto(bg, url, alto, y=None, margen_der=30):
    prod = producto_recortado(url)
    prod = prod.resize((max(1, int(prod.width * (alto / prod.height))), alto), Image.Resampling.LANCZOS)
    gx = bg.width - prod.width - margen_der
    gy = y if y is not None else (bg.height - alto) // 2 - 20
    halo = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([gx - 60, gy + alto * 0.45, gx + prod.width + 60, gy + alto + 80], fill=(255, 255, 255, 120))
    halo = halo.filter(ImageFilter.GaussianBlur(40))
    bg = Image.alpha_composite(bg, halo)
    bg.paste(prod, (gx, gy), prod)
    return bg


def crear_miniatura_variante(variante, base, url_producto, ingrediente, problema, gancho, salida):
    """Zona inferior derecha (duración de YouTube) queda libre. No hay barra con el título."""
    fuente = asegurar_fuente_thumbnail()
    bg = _preparar_base(base)
    gancho = gancho.upper()

    if variante == "A_texto_grande":
        bg = _gradiente_izq(bg, 900, 215)
        bloques = [_bloque_ingrediente(ingrediente, fuente, 820, 180),
                   _fit(gancho, fuente, 92, 44, 760, render_banner, bg=(198, 30, 30))]
        bg = _pegar_bloques(bg, bloques, y=60)
        try:
            bg = _pegar_producto(bg, url_producto, 430, y=60)
        except Exception as e:
            print(f"⚠️ Producto en miniatura A falló: {e}")

    elif variante == "B_ingrediente":
        bg = _gradiente_izq(bg, 760, 170)
        bloques = [_bloque_ingrediente(ingrediente, fuente, 1000, 210),
                   _fit(gancho, fuente, 90, 44, 900, render_banner, bg=(20, 90, 40), borde=(255, 255, 255))]
        bg = _pegar_bloques(bg, bloques, y=170)

    else:  # C_producto
        bg = _gradiente_izq(bg, 880, 205)
        bloques = [_bloque_ingrediente(ingrediente, fuente, 720, 150), render_texto_solido("PARA", fuente, 56)]
        partes = [p.strip() for p in (problema or "").split(",") if p.strip()][:3] or ["BIENESTAR NATURAL"]
        b1, b2 = [], []
        for p in partes:
            if not b2 and len(" ".join(b1 + [p])) <= 30:
                b1.append(p)
            else:
                b2.append(p)
        bloques.append(_fit(" ".join(b1).upper(), fuente, 74, 40, 700, render_banner, bg=(198, 30, 30)))
        if b2:
            bloques.append(_fit(("Y " + " ".join(b2)).upper(), fuente, 74, 40, 700, render_banner,
                                bg=(20, 90, 40), borde=(255, 255, 255)))
        bg = _pegar_bloques(bg, bloques, y=28)
        try:
            bg = _pegar_producto(bg, url_producto, 620, y=10)
        except Exception as e:
            print(f"⚠️ Producto en miniatura C falló: {e}")

    rgb = bg.convert("RGB")
    rgb.save(salida, "JPEG", quality=92)
    if os.path.getsize(salida) > 1_900_000:  # límite de YouTube: 2 MB
        rgb.save(salida, "JPEG", quality=78)
    return salida


def puntuar_miniatura(path, num_palabras_texto):
    """Heurística 0-100: contraste, saturación y legibilidad del texto a ~170 px de ancho."""
    try:
        im = Image.open(path).convert("RGB").resize((336, 189), Image.Resampling.LANCZOS)
        arr = np.asarray(im).astype(float)
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        contraste = lum.std()
        sat = np.asarray(im.convert("HSV"))[:, :, 1].mean()
        izq = lum[:, :int(336 * 0.55)]
        legibilidad = (np.abs(np.diff(izq, axis=1)).mean() + np.abs(np.diff(izq, axis=0)).mean()) / 2
        score = (min(contraste / 70, 1) * 30 + min(sat / 140, 1) * 20 +
                 min(legibilidad / 14, 1) * 35 + (15 if num_palabras_texto <= 4 else 0))
        return round(score, 1)
    except Exception:
        return 0.0


def generar_y_elegir_miniatura(base, url_producto, ingrediente, problema, titulo):
    gancho = elegir_gancho_miniatura(titulo)
    print(f"🖼️ Gancho de miniatura (complementa el título): {gancho}")
    variantes = ["A_texto_grande", "B_ingrediente", "C_producto"]
    resultados = []
    for v in variantes:
        ruta = f"thumb_largo_{v}.jpg"
        try:
            crear_miniatura_variante(v, base, url_producto, ingrediente, problema, gancho, ruta)
            n_pal = len(gancho.split()) + len(ingrediente.split()[:2])
            sc = puntuar_miniatura(ruta, n_pal)
            resultados.append((sc, v, ruta))
            print(f"   🖼️ Variante {v}: score {sc}")
        except Exception as e:
            print(f"⚠️ Variante {v} falló: {e}")
    if not resultados:
        return None, None, gancho
    resultados.sort(reverse=True)
    elegido = resultados[0]
    # 20% de exploración para recolectar datos de CTR de otras variantes
    if len(resultados) > 1 and random.random() < 0.2:
        elegido = random.choice(resultados[1:])
        print("   🔬 Exploración: se usa una variante alternativa para comparar CTR")
    print(f"✅ Miniatura elegida: {elegido[1]} (score {elegido[0]})")
    return elegido[2], elegido[1], gancho


def registrar_miniatura(video_id, variante, titulo, gancho):
    hist = _leer_json(MINIATURAS_HIST_FILE, [])
    hist.append({"video_id": video_id, "variante": variante, "titulo": titulo, "gancho": gancho,
                 "fecha": datetime.now().isoformat()})
    _escribir_json(MINIATURAS_HIST_FILE, hist[-200:])


# ================================================================
# YOUTUBE
# ================================================================
def obtener_credenciales_youtube():
    creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
    if creds.expired and creds.refresh_token:
        print("🔄 Token expirado, refrescando...")
        try:
            creds.refresh(Request())
            print("✅ Token refrescado")
        except Exception as e:
            print(f"❌ Error refrescando token: {e}")
            sys.exit(1)
    return creds


def tema_playlist(problema):
    pn = normalizar(problema)
    for clave, nombre in TEMAS_PLAYLIST:
        if clave in pn:
            return nombre
    return "bienestar general"


def asignar_playlist(youtube, video_id, problema):
    titulo_pl = f"Remedios naturales: {tema_playlist(problema)}"
    try:
        pid, token = None, None
        while True:
            r = youtube.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute()
            for it in r.get("items", []):
                if it["snippet"]["title"] == titulo_pl:
                    pid = it["id"]
            token = r.get("nextPageToken")
            if pid or not token:
                break
        if not pid:
            r = youtube.playlists().insert(
                part="snippet,status",
                body={"snippet": {"title": titulo_pl, "defaultLanguage": "es",
                                  "description": f"Videos educativos de herbolaria mexicana y remedios naturales sobre {tema_playlist(problema)}."},
                      "status": {"privacyStatus": "public"}}).execute()
            pid = r["id"]
            print(f"📚 Playlist creada: {titulo_pl}")
        youtube.playlistItems().insert(
            part="snippet",
            body={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
        print(f"✅ Video añadido a playlist: {titulo_pl}")
    except Exception as e:
        print(f"⚠️ Playlist no asignada (¿falta scope 'youtube'?): {str(e)[:150]}")


def subir_subtitulos(youtube, video_id, srt_path):
    try:
        youtube.captions().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id, "language": "es", "name": "Español", "isDraft": False}},
            media_body=MediaFileUpload(srt_path, mimetype="application/octet-stream", resumable=True)).execute()
        print("✅ Subtítulos SRT subidos (YouTube los indexa)")
    except Exception as e:
        print(f"⚠️ Subtítulos no subidos (requiere scope youtube.force-ssl): {str(e)[:150]}")


def publicar_comentario_contacto(youtube, video_id, ingrediente="", problema=""):
    """Publica un comentario con pregunta. La API NO permite fijarlo: hay que fijarlo a mano en Studio."""
    try:
        prob = problema.split(",")[0].strip().lower() if problema else "tu bienestar"
        texto = (f"🌿 {ingrediente.upper()} para {prob}: ¿lo habías usado antes?\n"
                 f"👇 Cuéntame en los comentarios qué otro remedio natural quieres que investigue\n\n"
                 f"📲 WhatsApp: {WHATSAPP_NUMBER}\n📞 Teléfono: {TELEFONO_NUMBER}\n"
                 f"🤖 Asistente inteligente en Telegram: {TELEGRAM_BOT}\n🔑 CONTRASEÑA DEL BOT: {TELEGRAM_PASSWORD}")
        youtube.commentThreads().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": texto}}}}).execute()
        print("✅ Comentario con pregunta publicado (fíjalo manualmente en Studio)")
    except Exception as e:
        print(f"⚠️ Error comentario: {e}")


def construir_descripcion(ing, problema, gancho, contexto, capitulos, sugerencias):
    Ing = ing[:1].upper() + ing[1:]
    prob = problema.split(",")[0].strip().lower() if problema else ""
    linea1 = (f"{Ing} para {prob}: beneficios y uso tradicional | remedios naturales" if prob
              else f"{Ing}: para qué sirve, beneficios y cómo usarlo | remedios naturales")
    tag_ing = re.sub(r"[^a-z0-9áéíóúüñ]", "", ing.lower())
    hashtags = [f"#{tag_ing}", "#remediosnaturales", "#herbolaria", "#saludnatural",
                "#medicinanatural", "#plantasmedicinales", "#remedioscaseros"]
    relacionadas = []
    for s in sugerencias[:12]:
        if s["frase"] not in relacionadas:
            relacionadas.append(s["frase"])
    busquedas = ", ".join(relacionadas[:8]) or f"{ing} beneficios, {ing} propiedades, para qué sirve {ing}"
    problema_str = f"\n🎯 Útil para: {problema}" if problema else ""

    d = f"""{linea1}

{gancho}

{contexto}

📲 ¿QUIERES SABER MÁS O ADQUIRIR ESTE PRODUCTO?
💬 WhatsApp: {WHATSAPP_NUMBER}
📞 Teléfono: {TELEFONO_NUMBER}
🤖 Asistente Inteligente: {TELEGRAM_BOT}
🔑 CONTRASEÑA DEL BOT: {TELEGRAM_PASSWORD}
{problema_str}

⏱️ CAPÍTULOS:
{capitulos}

🌿 EN ESTE VIDEO:
• {Ing}: origen y uso tradicional en México
• Cómo se relaciona {ing} con {prob or 'el bienestar'} según la herbolaria
• 3 beneficios tradicionales
• El producto con {ing} y cómo usarlo

🔎 Búsquedas relacionadas: {busquedas}

⚕️ AVISO: Contenido educativo basado en la tradición herbolaria mexicana. No sustituye la consulta médica profesional.

{' '.join(hashtags)}"""
    if ACTIVAR_DISCLOSURE_IA:
        d += DISCLOSURE_TEXT
    return d.replace("<", "").replace(">", "")[:5000]


def subir_video_largo(video_path, thumb_path, titulo, tags_por_nivel, gancho, contexto, ingrediente,
                      problema, capitulos, sugerencias, srt_path):
    creds = obtener_credenciales_youtube()
    youtube = build("youtube", "v3", credentials=creds)

    descripcion = construir_descripcion(ingrediente, problema, gancho, contexto, capitulos, sugerencias)
    nivel = 0
    body = {
        "snippet": {"title": titulo[:100], "description": descripcion,
                    "tags": [t.strip() for t in tags_por_nivel[nivel].split(",") if t.strip()],
                    "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }
    print(f"🏷️ Tags nivel {nivel}: {len(body['snippet']['tags'])} tags")

    video_id = None
    for intento in range(1, 6):
        try:
            print(f"📤 Subiendo video (intento {intento}/5)...")
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            video_id = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()["id"]
            print(f"✅ Video subido: https://youtu.be/{video_id}")
            break
        except Exception as e:
            s = str(e)
            if "invalidTags" in s or "invalid video keywords" in s.lower():
                nivel += 1
                if nivel >= len(tags_por_nivel):
                    print("❌ Los tags de emergencia también fueron rechazados")
                    raise
                print(f"⚠️ YouTube rechazó los tags. Bajando a nivel {nivel} ({'estricto' if nivel == 1 else 'emergencia'})...")
                body["snippet"]["tags"] = [t.strip() for t in tags_por_nivel[nivel].split(",") if t.strip()]
                time.sleep(5)
            elif any(c in s for c in ("502", "503", "504", "Bad Gateway")):
                if intento >= 5:
                    raise
                espera = 30 * intento
                print(f"⚠️ Error temporal de YouTube. Esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"❌ Error subiendo a YouTube: {e}")
                raise
    if not video_id:
        raise RuntimeError("No se pudo subir el video")

    if thumb_path and os.path.exists(thumb_path):
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")).execute()
            print("✅ Miniatura personalizada subida")
        except Exception as e:
            print(f"⚠️ Error miniatura: {e}")

    if srt_path and os.path.exists(srt_path):
        subir_subtitulos(youtube, video_id, srt_path)
    asignar_playlist(youtube, video_id, problema or "")
    publicar_comentario_contacto(youtube, video_id, ingrediente, problema or "")
    return video_id


# ================================================================
# MAIN
# ================================================================
def main():
    print("🎬 Bot VIDEOS LARGOS Herbolaria — SEO ELITE v3")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    estado = cargar_estado()
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encuentra {EXCEL_FILE}")
        sys.exit(1)

    producto, ingrediente = seleccionar_producto_e_ingrediente_largo()
    tema_viral = max(TEMAS_VIRALES_SALUD, key=lambda x: x["ctr_potencial"] * random.uniform(0.8, 1.2))
    problema = producto.get("recomendado_para", "")
    print(f"📦 Producto: {producto['nombre']} | 🌱 Ingrediente: {ingrediente}")
    print(f"🎯 Tema: {tema_viral['tema']} | 💊 Problema: {problema}")

    # 1) Keywords reales (autocompletado YouTube México)
    print("🔎 Consultando autocompletado de YouTube...")
    sugerencias = obtener_sugerencias(ingrediente)
    print(f"   {len(sugerencias)} frases reales. Top: {[s['frase'] for s in sugerencias[:5]]}")

    # 2) Guion
    guion = ia_genera_guion_largo(producto, ingrediente, tema_viral, sugerencias)
    ing_real = guion["ingrediente_real"]
    if normalizar(ing_real) != normalizar(ingrediente):
        sugerencias = obtener_sugerencias(ing_real) or sugerencias

    # 3) Título con score
    print("⚡ Eligiendo título por score...")
    historial = cargar_titulos()
    titulo, score_t, det_t = elegir_mejor_titulo(guion.get("titulos_candidatos", []), ing_real,
                                                     problema, sugerencias, historial)
    print(f"🔥 TÍTULO [{score_t}/100]: {titulo}  ({len(titulo)} caracteres)")

    # 4) Tags en 3 niveles (normal → estricto → emergencia)
    tags_normal = construir_tags(ing_real, problema, titulo, sugerencias, tema_viral)
    tags_estricto = construir_tags(ing_real, problema, titulo, sugerencias, tema_viral, estricto=True)
    tags_emergencia = generar_tags_emergencia(ing_real)
    print(f"🏷️ Tags ({len(tags_normal.split(','))}): {tags_normal[:140]}...")

    # 5) Voz + imágenes + audio por segmento
    voz = validar_voz()
    fondo_producto = buscar_imagen_segmento(
        guion["segmentos"]["producto"].get("query_pexels", f"{ing_real} natural"), "bg_producto.jpg")

    segmentos_img, segmentos_info = [], []
    for i, clave in enumerate(ORDEN_SEGMENTOS):
        seg = guion["segmentos"][clave]
        print(f"\n🎬 Segmento {i + 1}/8: {clave}")
        img_path = f"img_largo_{i}.jpg"

        if clave in ("producto", "cta"):
            if not componer_producto_horizontal(producto["imagen_url"], fondo_producto, img_path):
                with Image.open(fondo_producto) as im:
                    ImageOps.fit(im.convert("RGB"), (ANCHO, ALTO), Image.Resampling.LANCZOS).save(img_path, "JPEG", quality=90)
        else:
            buscar_imagen_segmento(seg.get("query_pexels", f"{ing_real} plant natural"), img_path)

        img_path = potenciar_imagen_segmento(img_path)
        tp = seg.get("texto_pantalla", "")
        if tp and texto_seguro(tp):
            img_path = quemar_texto_pantalla(img_path, tp, img_path, estilo="center" if clave == "hook" else "lower")

        audio_path = f"audio_largo_{i}.mp3"
        res = generar_audio(seg["texto"], audio_path, voz, max_intentos=3)
        if not res:
            print(f"❌ Falló el audio del segmento {clave}")
            sys.exit(1)
        eventos, voz = res  # la voz se mantiene para el resto del video
        segmentos_img.append({"img_path": img_path, "audio_path": audio_path})
        segmentos_info.append({"texto": seg["texto"], "eventos": eventos})

    # 6) Montaje
    video_path, duraciones, duracion_total = montar_video_largo(segmentos_img)
    inicio = 0.0
    for info, dur in zip(segmentos_info, duraciones):
        info["inicio"] = inicio
        info["duracion"] = dur
        inicio += dur

    capitulos = generar_capitulos_seo(duraciones, guion, ing_real, problema)
    print(f"\n⏱️ Capítulos:\n{capitulos}\n⏱️ Duración total: {formatear_timestamp(duracion_total)}")
    srt_path = construir_srt(segmentos_info)

    # 7) Miniatura: 3 variantes + score
    base_thumb = buscar_fondo_ia_flux(f"{ing_real} plant natural vivid macro")
    if not base_thumb:
        url_bg = buscar_imagen_pexels_horizontal(f"{ing_real} plant natural")
        base_thumb = descargar_imagen(url_bg, "bg_pexels.jpg") if url_bg else "img_largo_2.jpg"
    thumb, variante, gancho_thumb = generar_y_elegir_miniatura(base_thumb, producto["imagen_url"], ing_real, problema, titulo)

    # 8) Subida
    video_id = subir_video_largo(
        video_path, thumb, titulo, [tags_normal, tags_estricto, tags_emergencia],
        guion.get("gancho_descripcion", ""), guion.get("contexto_descripcion", ""),
        ing_real, problema, capitulos, sugerencias, srt_path)

    # 9) Estado
    guardar_ingrediente_largo_usado(ingrediente, producto["nombre"])
    guardar_titulo(titulo)
    if variante:
        registrar_miniatura(video_id, variante, titulo, gancho_thumb)
    estado["publicaciones_hoy"] = estado.get("publicaciones_hoy", 0) + 1
    estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
    guardar_estado(estado)

    print(f"\n🎉 VIDEO PUBLICADO: https://youtu.be/{video_id}")
    print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
    print(f"   📞 Teléfono: {TELEFONO_NUMBER}")
    print(f"   🤖 Telegram: {TELEGRAM_BOT}")
    print("   ℹ️ Recuerda fijar el comentario manualmente en YouTube Studio (la API no lo permite).")

    for f in os.listdir("."):
        if f.startswith(("img_largo_", "audio_largo_", "thumb_largo_")) or f in (
                "cta_overlay.png", "aviso_overlay.png", "largo_final.mp4", "bg_ia.jpg", "bg_pexels.jpg",
                "bg_producto.jpg", "subtitulos_largo.srt", "test_voz.mp3"):
            try:
                os.remove(f)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# -*- coding: utf-8 -*-
"""
BOT SHORTS HERBOLARIA - SEO ELITE v3 (ARCHIVO ÚNICO Y AUTÓNOMO)

Incluye el motor SEO (política, autocompletado de YouTube, títulos con score, tags en capas).

Mejoras vs. v2:
  - Anti-repetición REAL: el historial de productos/ingredientes ya no se reinicia cada día.
  - Filtro de política por palabras completas (regex). Auditoría del guion hablado.
  - Autocompletado real de YouTube México -> keywords reales en guion, título, tags y descripción.
  - Títulos de Short: IA + fórmulas -> candidatos puntuados 0-100 (perfil corto, <= 60 caracteres).
    Sin hashtags dentro del título (ahora van en la descripción, con #shorts entre los 3 primeros).
  - 6 ESCENAS (cambio visual cada ~4-5 s) en lugar de 2, con zoom alternado.
  - SUBTÍTULOS QUEMADOS palabra por palabra (palabra activa en amarillo) con tiempos reales de edge-tts.
  - PRIMER FRAME GANCHO: texto grande desde el segundo 0 (es lo que ve el feed de Shorts).
  - Zonas seguras de la interfaz de Shorts (aviso arriba, subtítulos al centro-bajo, CTA sobre la zona inferior).
  - Subtítulos SRT subidos a YouTube, playlist automática por problema, tags en 3 niveles.
  - Voz consistente (si una falla, se mantiene la alternativa), música en bucle sin errores.
  - Contactos y contraseña leídos de variables de entorno (secrets).
"""
import asyncio
import base64
import io
import json
import os
import random
import re
import shutil
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
    concatenate_audioclips, concatenate_videoclips, CompositeVideoClip,
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

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

# Recomendado: definirlos como secrets/variables en GitHub. Los valores por defecto
# mantienen el comportamiento anterior, pero NO dejes una contraseña real en el código.
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "+52 3123395334")
TELEFONO_NUMBER = os.getenv("TELEFONO_NUMBER", "3123395334")
TELEGRAM_BOT = os.getenv("TELEGRAM_BOT", "@alex_xanax_bot")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD", "A")

ESTADO_FILE = "estado_herbolaria.json"
INGREDIENTES_USADOS_FILE = "ingredientes_usados.json"
TITULOS_FILE = "titulos_herbolaria_publicados.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"

MAX_VIDEOS_DIA = 1

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

HORA_EXCLUIR_INICIO = 0   # hora CDMX
HORA_EXCLUIR_FIN = 4

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ANCHO, ALTO = 1080, 1920          # vertical 9:16
ESCENAS = ["hook", "dato_1", "dato_2", "dato_3", "producto", "cta"]
Y_SUBTITULOS = 1240               # centro de los subtítulos (zona segura de Shorts)
Y_AVISO = 150
Y_CTA = 1420

# ================================================================
# KEYWORDS, TEMAS, HASHTAGS, VOCES (originales)
# ================================================================
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

HASHTAGS_VIRALES = [
    "#remediosnaturales", "#remedioscaseros", "#saludnatural",
    "#medicinanatural", "#herbolaria", "#hierbasmedicinales",
    "#plantasmedicinales", "#bienestar", "#tipsdesalud",
    "#salud", "#natural", "#tradicionmexicana", "#shorts",
]

TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "remedios naturales", "para qué sirve"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales de las hierbas", "remedios naturales efectivos"], "busquedas": 850000, "ctr_potencial": 9.2, "retencion_objetivo": 78, "tendencia": "creciente"},
    {"tema": "remedio_casero", "keywords_cortas": ["remedios caseros", "natural", "tradición", "hierbas medicinales"], "keywords_largas": ["remedios caseros efectivos", "tratamiento natural con hierbas", "remedios de la abuela"], "busquedas": 920000, "ctr_potencial": 9.5, "retencion_objetivo": 75, "tendencia": "estable"},
    {"tema": "alivio_natural", "keywords_cortas": ["alivio natural", "bienestar", "medicina natural", "plantas medicinales"], "keywords_largas": ["alivio natural tradicional", "remedios mexicanos para el bienestar", "hierbas que alivian"], "busquedas": 750000, "ctr_potencial": 10.8, "retencion_objetivo": 80, "tendencia": "creciente"},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "herbolaria mexicana", "tradición"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional mexicana", "herbolaria que pocos conocen"], "busquedas": 540000, "ctr_potencial": 9.8, "retencion_objetivo": 77, "tendencia": "creciente"},
    {"tema": "como_usar", "keywords_cortas": ["cómo usar", "cómo preparar", "tips de salud", "guía natural"], "keywords_largas": ["cómo usar hierbas medicinales", "preparación tradicional de hierbas", "guía de herbolaria"], "busquedas": 610000, "ctr_potencial": 9.0, "retencion_objetivo": 76, "tendencia": "creciente"},
]

VOCES_DISPONIBLES = [
    {"voz": "es-MX-DaliaNeural", "velocidad": "+10%", "estilo": "claro México"},
    {"voz": "es-MX-JorgeNeural", "velocidad": "+8%", "estilo": "profesional México"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+12%", "estilo": "entusiasta España"},
    {"voz": "es-ES-AlvaroNeural", "velocidad": "+10%", "estilo": "profesional España"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+10%", "estilo": "natural Colombia"},
    {"voz": "es-AR-ElenaNeural", "velocidad": "+9%", "estilo": "cálido Argentina"},
    {"voz": "es-US-PalomaNeural", "velocidad": "+10%", "estilo": "neutral USA"},
    {"voz": "es-MX-BeatrizNeural", "velocidad": "+11%", "estilo": "amigable México"},
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


def ajustar_titulo(t, limite_emoji=66):
    """Limpia hashtags y asegura 1 emoji si cabe. No trunca con '...'."""
    t = _limpiar_titulo(t)
    if t and contar_emojis(t) == 0 and len(t) <= limite_emoji:
        t = f"{t} {random.choice(EMOJIS_TITULO)}"
    return t


# Perfiles de longitud: largo (50-62 ideal) y short (28-50 ideal, máx. 60: el feed de Shorts trunca)
PERFILES_TITULO = {
    "largo": {"max": 70, "min": 25, "ideal": (50, 62), "ok": (44, 70), "emoji": 66},
    "short": {"max": 60, "min": 20, "ideal": (28, 50), "ok": (22, 58), "emoji": 56},
}

# Fórmulas extra SOLO para Shorts: las originales del bot de shorts (POWER) + cortas nuevas.
# Se formatean con todos los marcadores posibles ({ing}, {Ing}, {prob}, {ingrediente}, {e}, {e1}, {e2}...).
FORMULAS_SHORT = [
    "{e1} {ingrediente}: {num} SECRETOS para {problema} {e2}",
    "{e1} ¿{problema_cap}? {ingrediente} lo cambia todo {e2}",
    "{e1} El PODER oculto de {ingrediente} {e2}",
    "{e1} {ingrediente}: {num} beneficios que nadie te contó {e2}",
    "{e1} La VERDAD sobre {ingrediente} {e2}",
    "{e1} {ingrediente} activa tu bienestar {e2}",
    "{e1} ¿Usas {ingrediente}? Esto te sorprende {e2}",
    "{e1} {ingrediente}: el aliado que tu cuerpo pedía {e2}",
    "{e1} {problema_cap}: {ingrediente} al rescate {e2}",
    "{e1} Lo que los abuelos sabían de {ingrediente} {e2}",
    "{e1} {ingrediente} + tradición: el duo perfecto {e2}",
    "{e1} Descubre {ingrediente} en {num} pasos {e2}",
    "{e1} {ingrediente}: la joya de la herbolaria {e2}",
    "{e1} ¿Conoces {ingrediente}? Esto te impactará {e2}",
    "{e1} {num} razones para usar {ingrediente} hoy {e2}",
    "{e1} {ingrediente}: el remedio que tu abuela amaba {e2}",
    "{Ing}: {num} cosas que nadie te explicó {e}",
    "¿Conoces {ing}? Tradición para {prob} {e}",
    "Para qué sirve {ing} {e}",
    "{Ing}: el aliado natural {e}",
    "{prob_cap} y {ing}: lo que dice la tradición {e}",
    "Así se usa {ing} {e}",
    "{num} usos tradicionales de {ing} {e}",
    "Cómo tomar {ing} correctamente {e}",
    "{Ing}: ¿mito o tradición? {e}",
    "¿Por qué tu abuela usaba {ing}? {e}",
    "{Ing} para {prob}: tradición {e}",
]


def generar_candidatos_codigo(ingrediente, problema, modo="largo"):
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
    if modo == "short":
        for f in FORMULAS_SHORT:
            cands.append(_limpiar_titulo(f.format(
                ing=ing.lower() if len(ing.split()) == 1 else ing, Ing=ing_cap, prob=prob, prob_cap=prob_c,
                num=random.choice([3, 4, 5]), e=random.choice(EMOJIS_TITULO), e1="",
                e2=random.choice(EMOJIS_TITULO), ingrediente=ing, problema=prob, problema_cap=prob_c)))
    return cands


def puntuar_titulo(titulo, ingrediente, sugerencias=None, historial=None, modo="largo"):
    """Devuelve (score 0-100, detalle). Score -100 = rechazado."""
    t = _limpiar_titulo(titulo)
    historial = historial or []
    tn = normalizar(quitar_emojis(t))
    ing_n = normalizar(ingrediente)
    det = {}

    aud = auditar_texto(t)
    if aud["duras"]:
        return -100, {"rechazo": f"palabra prohibida: {aud['duras']}"}
    perfil = PERFILES_TITULO[modo]
    if len(t) > perfil["max"]:
        return -100, {"rechazo": f"largo ({len(t)}>{perfil['max']})"}
    if len(t) < perfil["min"]:
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
    det["longitud"] = (15 if perfil["ideal"][0] <= n <= perfil["ideal"][1]
                       else 8 if perfil["ok"][0] <= n <= perfil["ok"][1] else 0)
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


def elegir_mejor_titulo(candidatos_ia, ingrediente, problema, sugerencias, historial, verbose=True, modo="largo"):
    pool, vistos = [], set()
    lim_emoji = PERFILES_TITULO[modo]["emoji"]
    for c in (candidatos_ia or []):
        c = ajustar_titulo(c, lim_emoji)
        if c and c.lower() not in vistos:
            vistos.add(c.lower())
            pool.append((c, "IA"))
    for c in generar_candidatos_codigo(ingrediente, problema, modo):
        c = ajustar_titulo(c, lim_emoji)
        if c.lower() not in vistos:
            vistos.add(c.lower())
            pool.append((c, "fórmula"))
    evaluados = []
    for t, origen in pool:
        s, det = puntuar_titulo(t, ingrediente, sugerencias, historial, modo)
        evaluados.append((s, t, origen, det))
    validos = [x for x in evaluados if x[0] > 0]
    if verbose:
        print(f"   🧪 {len(pool)} candidatos de título | {len(validos)} válidos")
    if not validos:
        ing = str(ingrediente)
        return f"{ing[:1].upper() + ing[1:]}: tradición y bienestar 🌿"[:PERFILES_TITULO[modo]["max"]], 0, {}
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
# HELPERS COMPARTIDOS (voz con tiempos de palabra, SRT, render, playlist, YouTube)
# ================================================================
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


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _leer_json(ruta, defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def _escribir_json(ruta, data):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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


def asignar_playlist(youtube, video_id, problema, prefijo="Remedios naturales: "):
    titulo_pl = f"{prefijo}{tema_playlist(problema)}"
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


# ================================================================
# ESTADO Y SELECCIÓN (anti-repetición persistente)
# ================================================================
def cargar_estado():
    return _leer_json(ESTADO_FILE, {"publicaciones_hoy": 0, "fecha": None, "ultima_publicacion": None})


def guardar_estado(estado):
    _escribir_json(ESTADO_FILE, estado)


def cargar_ingredientes_usados():
    d = _leer_json(INGREDIENTES_USADOS_FILE, {})
    return d.get("ingredientes", []) if isinstance(d, dict) else []


def guardar_ingrediente_usado(ingrediente, producto):
    """Historial PERSISTENTE (últimos 80). Antes se reiniciaba cada día y no evitaba repeticiones."""
    lista = cargar_ingredientes_usados()
    entry = f"{ingrediente}|{producto}"
    if entry not in lista:
        lista.append(entry)
    _escribir_json(INGREDIENTES_USADOS_FILE, {"ingredientes": lista[-80:]})


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
    if estado.get("publicaciones_hoy", 0) >= MAX_VIDEOS_DIA:
        print("✅ Límite diario alcanzado.")
        return False

    forzar = os.getenv("FORZAR_PUBLICACION", "0") == "1"
    if not forzar and HORA_EXCLUIR_INICIO <= ahora.hour < HORA_EXCLUIR_FIN:
        print(f"🌙 Madrugada ({ahora.hour}h CDMX). No publico entre {HORA_EXCLUIR_INICIO}:00 y {HORA_EXCLUIR_FIN}:00.")
        return False

    ultima = estado.get("ultima_publicacion")
    if ultima and not forzar:
        diff = (ahora - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(3, 5)
        if diff < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h (han pasado {diff:.1f}h).")
            return False
    return True


def seleccionar_producto_e_ingrediente():
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    df = df[df["imagen_url"].notna() & (df["imagen_url"] != "")]
    df = df[df["ingredientes_clave"].notna() & (df["ingredientes_clave"] != "")]
    usados = cargar_ingredientes_usados()

    def elegir():
        producto = df.sample(1).iloc[0].to_dict()
        ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",") if i.strip()]
        return producto, (random.choice(ingredientes) if ingredientes else None)

    for _ in range(80):
        producto, ingrediente = elegir()
        if ingrediente and f"{ingrediente}|{producto.get('nombre', '')}" not in usados:
            print(f"✅ Par elegido: {ingrediente} → {producto.get('nombre')}")
            return producto, ingrediente

    print("🔄 Pool agotado. Reiniciando historial...")
    _escribir_json(INGREDIENTES_USADOS_FILE, {"ingredientes": []})
    while True:
        producto, ingrediente = elegir()
        if ingrediente:
            return producto, ingrediente


# ================================================================
# IA: GUION DE 6 ESCENAS (25-30 s)
# ================================================================
def ia_genera_guion_short(producto, ingrediente, tema_viral, sugerencias):
    producto_info = f"""NOMBRE: {producto.get('nombre', 'N/A')}
PRESENTACIÓN: {producto.get('presentacion', 'N/A')}
RECOMENDADO PARA: {producto.get('recomendado_para', 'N/A')}
INGREDIENTES CLAVE: {producto.get('ingredientes_clave', 'N/A')}
BENEFICIOS: {producto.get('beneficios', 'N/A')}
MODO DE EMPLEO: {producto.get('MODO DE EMPLEO / DOSIS', 'N/A')}"""
    problema = producto.get("recomendado_para", "")
    kws = obtener_keywords_aleatorias_virales(6)
    frases_reales = [s["frase"] for s in sugerencias[:8]]
    prohibidas_str = ", ".join(f'"{p}"' for p in HARD_TERMS[:60]) + "..."
    reales_txt = "\n".join("- " + f for f in frases_reales) if frases_reales else "- (sin datos; usa remedios naturales, beneficios, propiedades)"

    esquema = '''{
  "ingrediente_real": "nombre real normalizado del ingrediente",
  "titulos_candidatos": ["...", "...", "...", "...", "...", "...", "...", "..."],
  "escenas": {
    "hook":     {"texto": "...", "texto_pantalla": "...", "query_pexels": "..."},
    "dato_1":   {"texto": "...", "texto_pantalla": "...", "query_pexels": "..."},
    "dato_2":   {"texto": "...", "texto_pantalla": "...", "query_pexels": "..."},
    "dato_3":   {"texto": "...", "texto_pantalla": "...", "query_pexels": "..."},
    "producto": {"texto": "...", "texto_pantalla": "...", "query_pexels": "..."},
    "cta":      {"texto": "...", "texto_pantalla": "", "query_pexels": ""}
  },
  "gancho_descripcion": "Gancho con keyword (máx 90 caracteres)",
  "contexto_descripcion": "1-2 oraciones educativas con keywords naturales"
}'''

    base_prompt = f"""Eres experto en herbolaria mexicana, nutrición y SEO para YouTube Shorts. Creas guiones VIRALES y 100% SEGUROS ante las políticas de YouTube, de 25 a 30 segundos, en 6 ESCENAS cortas (cambio visual cada 4-5 segundos).

📦 PRODUCTO:
{producto_info}

🌱 INGREDIENTE ESTRELLA OBLIGATORIO (NO lo cambies): {ingrediente}
🎯 TEMA VIRAL: {tema_viral['tema'].upper()} (keywords: {', '.join(tema_viral['keywords_cortas'])})
💊 PROBLEMA: {problema}

🔎 FRASES QUE LA GENTE BUSCA REALMENTE EN YOUTUBE MÉXICO (autocompletado). Incorpóralas de forma natural y úsalas para inspirar los títulos:
{reales_txt}

🔑 KEYWORDS GENERALES: {', '.join(kws)}

🎬 6 ESCENAS (TOTAL MÁXIMO 85 PALABRAS HABLADAS; si te pasas, el Short pierde retención):
1. "hook" (14-18 palabras): ⚠️ La PRIMERA ORACIÓN nombra el ingrediente Y su beneficio principal en menos de 15 palabras. Ej: "La zarzaparrilla es la raíz que tu circulación estaba esperando." Gancho emocional.
2. "dato_1" (10-14 palabras): primer dato según la tradición.
3. "dato_2" (10-14 palabras): segundo dato.
4. "dato_3" (10-14 palabras): tercer dato. Termina con "Es información educativa tradicional."
5. "producto" (12-16 palabras): presenta el producto {producto.get('nombre')} y cómo contiene el ingrediente.
6. "cta": EXACTAMENTE esta frase y nada más: "¿Quieres saber más? Contáctanos por WhatsApp o Telegram, los contactos están en la descripción."

REGLAS:
- Si el ingrediente suena a saborizante, habla del ingrediente REAL.
- Tono educativo, cálido, ritmo ágil. Sin emojis ni números de contacto en el texto hablado.
- Cada escena incluye "texto_pantalla" (MÁX 3 palabras, en mayúsculas, gancho visual; en el hook debe despertar curiosidad sin prometer nada) y "query_pexels" (inglés, descripción visual VERTICAL 9:16, sin personas).

🚨 POLÍTICA DE SALUD DE YOUTUBE (CRÍTICO). NUNCA uses: {prohibidas_str}
✅ MARCOS SEGUROS: "apoya", "favorece", "contribuye al bienestar", "según la tradición", "aliado natural", "parte de un estilo de vida saludable".

📝 TÍTULOS: devuelve 8 CANDIDATOS distintos (MÁX 55 caracteres, SIN hashtags, 1 emoji como máximo, keyword del ingrediente en las primeras palabras). Mezcla:
- BÚSQUEDA (2): usa una frase real de la lista (ej. "Para qué sirve X", "Cómo tomar X").
- CURIOSIDAD (3): brecha de curiosidad honesta, con número o pregunta.
- PROBLEMA-SOLUCIÓN (3): conecta el ingrediente con {problema} usando "apoya", "tradición", "aliado".
Cada candidato empieza distinto. Sin promesas de cura ni clickbait exagerado.

Devuelve ESTRICTAMENTE este JSON:
"""
    prompt_base = base_prompt + esquema

    aviso_extra = ""
    for intento in range(6):
        try:
            print(f"🤖 IA escribiendo guion de 6 escenas... (intento {intento + 1}/6)")
            r = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_base + aviso_extra}],
                      "temperature": 0.9, "max_tokens": 2500, "response_format": {"type": "json_object"}},
                timeout=120)
            r.raise_for_status()
            resp = r.json()["choices"][0]["message"]["content"].strip()
            resp = re.sub(r'`json\s*', '', resp).replace('`', '')
            i0, i1 = resp.find('{'), resp.rfind('}')
            data = json.loads(resp[i0:i1 + 1], strict=False)

            escenas = data.get("escenas", {})
            for k in ESCENAS:
                if k not in escenas or len(escenas[k].get("texto", "")) < 12:
                    raise ValueError(f"Escena {k} faltante o corta")

            # CTA exacto
            cta_exacto = "¿Quieres saber más? Contáctanos por WhatsApp o Telegram, los contactos están en la descripción."
            if "contactos están en la descripción" not in escenas["cta"]["texto"].lower():
                escenas["cta"]["texto"] = cta_exacto

            # Auditoría de política del guion hablado
            texto_total = " ".join(escenas[k]["texto"] for k in ESCENAS)
            aud = auditar_texto(texto_total, es_guion=True)
            if aud["duras"]:
                aviso_extra = f"\n\n⚠️ En el intento anterior usaste palabras PROHIBIDAS: {aud['duras']}. Reescribe sin ellas."
                raise ValueError(f"Guion con palabras prohibidas: {aud['duras']}")

            # SEO hablado: ingrediente en la primera oración
            real = data.get("ingrediente_real") or ingrediente
            primera = " ".join(escenas["hook"]["texto"].split()[:18])
            toks = [t for t in normalizar(real).split() if len(t) > 3] or [normalizar(real)]
            if not any(t in normalizar(primera) for t in toks):
                aviso_extra = f"\n\n⚠️ La primera oración del hook DEBE nombrar '{real}' y su beneficio."
                raise ValueError("El hook no nombra el ingrediente al inicio")

            palabras = sum(len(escenas[k]["texto"].split()) for k in ESCENAS)
            print(f"   📏 Guion: {palabras} palabras (~{palabras / 2.8:.0f} s)")
            if palabras > 100:
                aviso_extra = f"\n\n⚠️ El intento anterior tuvo {palabras} palabras. MÁXIMO 85. Sé más breve."
                raise ValueError(f"Guion demasiado largo ({palabras} palabras)")
            if palabras < 50:
                aviso_extra = f"\n\n⚠️ El intento anterior tuvo solo {palabras} palabras. Apunta a 75-85."
                raise ValueError(f"Guion demasiado corto ({palabras} palabras)")

            data["ingrediente_real"] = real
            print(f"✅ Guion listo. Ingrediente real: {real}")
            return data
        except Exception as e:
            print(f"❌ Intento {intento + 1} falló: {e}")
            if intento == 5:
                print("❌ Todos los intentos de IA fallaron")
                sys.exit(1)
            time.sleep(6)


# ================================================================
# IMÁGENES VERTICALES: FLUX (Cloudflare) → PEXELS
# ================================================================
SEGMENTO_FLUX_SUFFIX_SHORT = (", photorealistic photography, natural lighting, vivid saturated colors, "
                              "cinematic composition, botanical and herbal theme, shallow depth of field, "
                              "no text, no watermark, no people, vertical portrait 9:16")


def buscar_imagen_pexels_vertical(query, intentos=3):
    if not PEXELS_API_KEY:
        return None
    variantes = ["natural", "healthy", "organic", "fresh", "herbal", "medicinal", "close up", "macro"]
    for _ in range(intentos):
        try:
            params = {"query": f"{query} {random.choice(variantes)}", "orientation": "portrait",
                      "per_page": 6, "page": random.randint(1, 4)}
            r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": PEXELS_API_KEY},
                             params=params, timeout=15)
            if r.status_code == 200 and r.json().get("photos"):
                return random.choice(r.json()["photos"][:4])["src"]["large2x"]
        except Exception:
            pass
        time.sleep(2)
    return None


def buscar_imagen_escena(query_en, salida):
    if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:
        for intento in range(1, 4):
            try:
                print(f"   🎨 Flux escena intento {intento}/3...")
                _flux_cloudflare(query_en + SEGMENTO_FLUX_SUFFIX_SHORT, salida)  # tamaño 1080x1920
                print("   ✅ Imagen generada con Flux (Cloudflare)")
                return salida
            except Exception as e:
                print(f"   ⚠️ Flux intento {intento} falló: {e}")
                time.sleep(2)
        print("   ⚠️ Flux falló 3 veces. Usando Pexels.")
    else:
        print("   ⚠️ Sin keys de Cloudflare. Usando Pexels.")
    url_img = buscar_imagen_pexels_vertical(query_en)
    if url_img:
        try:
            return descargar_imagen(url_img, salida)
        except Exception as e:
            print(f"   ⚠️ Pexels falló ({e}). Imagen por defecto.")
    return descargar_imagen("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop", salida)


def componer_producto_vertical(url_producto, fondo, salida):
    """Producto recortado sobre el fondo, ubicado ARRIBA de la zona de subtítulos."""
    try:
        fondo_img = ImageOps.fit(_cargar_fondo(fondo), (ANCHO, ALTO), Image.Resampling.LANCZOS)
        fondo_img = ImageEnhance.Brightness(fondo_img).enhance(0.85)
        prod = producto_recortado(url_producto)
        th = int(ALTO * 0.38)
        prod = prod.resize((max(1, int(prod.width * (th / prod.height))), th), Image.Resampling.LANCZOS)
        if prod.width > int(ANCHO * 0.86):
            ratio = (ANCHO * 0.86) / prod.width
            prod = prod.resize((int(prod.width * ratio), int(prod.height * ratio)), Image.Resampling.LANCZOS)
        sombra = prod.copy().filter(ImageFilter.GaussianBlur(radius=30))
        x = (ANCHO - prod.width) // 2
        y = int(ALTO * 0.22)
        fondo_img.paste(sombra, (x - 15, y - 15), sombra)
        fondo_img.paste(prod, (x, y), prod)
        fondo_img.save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error componiendo producto: {e}")
        return None


# ================================================================
# TEXTO EN PANTALLA: HOOK (primer frame), ETIQUETAS, SUBTÍTULOS, OVERLAYS
# ================================================================
def _limpiar_pantalla(texto):
    return re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ¡!¿?]', '', texto or "").upper().strip()


def _degradado_inferior(capa, alto=760, alpha=170):
    d = ImageDraw.Draw(capa)
    for yy in range(ALTO - alto, ALTO):
        a = int(alpha * ((yy - (ALTO - alto)) / alto))
        d.line([(0, yy), (ANCHO, yy)], fill=(0, 0, 0, a))


def quemar_hook_vertical(img_path, texto, salida):
    """Primer frame gancho: texto grande desde el segundo 0."""
    try:
        fuente = asegurar_fuente_thumbnail()
        with Image.open(img_path) as im:
            img = im.convert("RGBA")
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        _degradado_inferior(capa)
        d = ImageDraw.Draw(capa)
        txt = _limpiar_pantalla(texto)
        if not txt:
            Image.alpha_composite(img, capa).convert("RGB").save(salida, "JPEG", quality=90)
            return salida
        palabras = txt.split()
        if len(txt) > 14 and len(palabras) >= 2:
            mid = (len(palabras) + 1) // 2
            lineas = [" ".join(palabras[:mid]), " ".join(palabras[mid:])]
        else:
            lineas = [txt]
        bloques = []
        for ln in lineas:
            try:
                bloques.append(_fit(ln, fuente, 190, 70, int(ANCHO * 0.88), render_texto_gradiente))
            except Exception:
                bloques.append(_fit(ln, fuente, 190, 70, int(ANCHO * 0.88), render_texto_solido, fill=(255, 214, 102)))
        alto_total = sum(b.height for b in bloques) + 12 * (len(bloques) - 1)
        ancho_max = max(b.width for b in bloques)
        y0 = 360
        d.rounded_rectangle([(ANCHO - ancho_max) // 2 - 50, y0 - 40, (ANCHO + ancho_max) // 2 + 50, y0 + alto_total + 40],
                            radius=36, fill=(0, 0, 0, 140))
        y = y0
        for b in bloques:
            capa.paste(b, ((ANCHO - b.width) // 2, y), b)
            y += b.height + 12
        badge = render_banner("HERBOLARIA MEXICANA", fuente, 44, bg=(198, 30, 30))
        capa.paste(badge, ((ANCHO - badge.width) // 2, y0 + alto_total + 70), badge)
        Image.alpha_composite(img, capa).convert("RGB").save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error quemando hook: {e}")
        return img_path


def quemar_etiqueta_vertical(img_path, texto, salida, y=300):
    try:
        fuente = asegurar_fuente_thumbnail()
        with Image.open(img_path) as im:
            img = im.convert("RGBA")
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        _degradado_inferior(capa)
        txt = _limpiar_pantalla(texto)
        if txt:
            banner = _fit(txt, fuente, 96, 46, int(ANCHO * 0.86), render_banner, bg=(198, 30, 30))
            capa.paste(banner, ((ANCHO - banner.width) // 2, y), banner)
        Image.alpha_composite(img, capa).convert("RGB").save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error quemando etiqueta: {e}")
        return img_path


def limpiar_display(palabra):
    return re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9¿?¡!%]', '', palabra or "").upper().strip()


def agrupar_cues(palabras):
    """Agrupa palabras (ini, fin, texto) en cues de máx. 3 palabras / ~20 caracteres."""
    cues, grupo = [], []
    for ini, fin, txt in palabras:
        disp = limpiar_display(txt)
        if not disp:
            continue
        grupo.append((ini, fin, disp))
        cierra = txt.rstrip().endswith((".", "?", "!", ",", ";", ":"))
        if len(grupo) >= 3 or sum(len(g[2]) for g in grupo) >= 20 or cierra:
            cues.append(grupo)
            grupo = []
    if grupo:
        cues.append(grupo)
    return cues


def render_caption(textos, activo, fuente, size=92, ancho_max=940):
    """Imagen RGBA ajustada de un cue; la palabra activa va en amarillo."""
    stroke = 9
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    while True:
        font = ImageFont.truetype(fuente, size)
        gap = int(size * 0.30)
        anchos = [dummy.textlength(t, font=font) for t in textos]
        total = sum(anchos) + gap * (len(textos) - 1)
        if total <= ancho_max or size <= 44:
            break
        size -= 4
    asc, desc = font.getmetrics()
    pad = stroke + 10
    w = int(total) + pad * 2
    h = asc + desc + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    for i, t in enumerate(textos):
        color = (255, 214, 0, 255) if i == activo else (255, 255, 255, 255)
        d.text((x, pad + asc), t, font=font, fill=color, stroke_width=stroke, stroke_fill=(0, 0, 0, 255), anchor="ls")
        x += anchos[i] + gap
    return img


def crear_clips_subtitulos(escenas, fuente):
    flat = []
    for esc in escenas:
        pals = _palabras_con_tiempo(esc["eventos"], esc["texto"], esc["duracion"])
        pals = [(esc["inicio"] + a, esc["inicio"] + b, t) for a, b, t in pals]
        for cue in agrupar_cues(pals):
            for j in range(len(cue)):
                flat.append((cue, j))
    clips = []
    for k, (cue, j) in enumerate(flat):
        ini = cue[j][0]
        if k + 1 < len(flat):
            sig_cue, sig_j = flat[k + 1]
            fin = sig_cue[sig_j][0]
        else:
            fin = cue[-1][1] + 0.3
        if fin - ini < 0.08:
            fin = ini + 0.08
        img = render_caption([w[2] for w in cue], j, fuente)
        clip = (ImageClip(np.array(img), transparent=True)
                .set_start(ini).set_duration(fin - ini)
                .set_pos(("center", Y_SUBTITULOS - img.height // 2)))
        clips.append(clip)
    print(f"💬 {len(clips)} subtítulos palabra por palabra")
    return clips


def crear_overlay_texto(texto, fuente, size, ancho_max, color, bg_alpha=170):
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    while True:
        font = ImageFont.truetype(fuente, size)
        tw = dummy.textlength(texto, font=font)
        if tw <= ancho_max - 70 or size <= 24:
            break
        size -= 2
    asc, desc = font.getmetrics()
    w, h = int(tw) + 70, asc + desc + 36
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=22, fill=(0, 0, 0, bg_alpha))
    d.text((35, 18 + asc), texto, font=font, fill=color, anchor="ls")
    return img


# ================================================================
# VIDEO
# ================================================================
def ken_burns_vertical(img_path, dur, direccion="in", zoom=0.08):
    clip = ImageClip(img_path).set_duration(dur)
    if direccion == "in":
        clip = clip.resize(lambda t: 1.0 + zoom * (t / dur))
    else:
        clip = clip.resize(lambda t: 1.0 + zoom - zoom * (t / dur))

    def crop_center(frame):
        h, w = frame.shape[:2]
        x1 = max(0, (w - ANCHO) // 2)
        y1 = max(0, (h - ALTO) // 2)
        return frame[y1:y1 + ALTO, x1:x1 + ANCHO]

    return clip.fl_image(crop_center)


def montar_short(escenas, salida="short_final.mp4"):
    fuente = asegurar_fuente_thumbnail()
    clips_video, clips_audio = [], []
    inicio = 0.0
    for i, esc in enumerate(escenas):
        audio = AudioFileClip(esc["audio_path"])
        dur = audio.duration
        esc["inicio"], esc["duracion"] = inicio, dur
        inicio += dur
        print(f"   ⏱️ Escena {i + 1}: {dur:.1f}s")
        clips_video.append(ken_burns_vertical(esc["img_path"], dur, "in" if i % 2 == 0 else "out"))
        clips_audio.append(audio)

    narracion = concatenate_audioclips(clips_audio)
    video = concatenate_videoclips(clips_video, method="compose")
    duracion_total = narracion.duration
    print(f"⏱️ Duración TOTAL: {duracion_total:.1f}s")
    if duracion_total > 40:
        print("⚠️ Short largo (>40 s): el guion debería ser más breve.")

    # Música en bucle (sin errores si es más corta que el video)
    musicas = [f for f in os.listdir(".") if f.lower().endswith(".mp3")
               and not f.startswith(("seg", "test", "audio")) and os.path.getsize(f) > 100]
    random.shuffle(musicas)
    audio_final = narracion
    for m in musicas:
        try:
            mc = AudioFileClip(m)
            if mc.duration < duracion_total:
                mc = concatenate_audioclips([mc] * (int(duracion_total / mc.duration) + 1))
            mc = mc.subclip(0, duracion_total).volumex(0.12)
            audio_final = CompositeAudioClip([narracion, mc])
            print(f"🎵 Música de fondo: {m} (12%)")
            break
        except Exception as e:
            print(f"   ⚠️ La música '{m}' falló: {e}")

    capas = [video]
    # Aviso legal arriba (zona segura) durante los primeros 4.5 s
    try:
        av = crear_overlay_texto("Contenido educativo. No sustituye la consulta médica.", FUENTE, 34, 980, (255, 255, 255, 240))
        capas.append(ImageClip(np.array(av), transparent=True).set_start(0).set_duration(4.5)
                     .set_pos(("center", Y_AVISO)))
    except Exception as e:
        print(f"⚠️ Error overlay aviso: {e}")
    # CTA sobre la zona inferior, últimos 6 s
    try:
        cta = crear_overlay_texto("CONTACTOS EN LA DESCRIPCIÓN", fuente, 64, 1000, (255, 214, 102, 255), bg_alpha=185)
        capas.append(ImageClip(np.array(cta), transparent=True)
                     .set_start(max(duracion_total - 6, 0)).set_duration(min(6, duracion_total))
                     .set_pos(("center", Y_CTA)))
    except Exception as e:
        print(f"⚠️ Error overlay CTA: {e}")
    # Subtítulos palabra por palabra
    try:
        capas.extend(crear_clips_subtitulos(escenas, fuente))
    except Exception as e:
        print(f"⚠️ Error subtítulos: {e}. Continuando sin ellos...")

    final = CompositeVideoClip(capas, size=(ANCHO, ALTO)).set_audio(audio_final)
    print("🎬 Renderizando Short...")
    final.write_videofile(salida, fps=30, codec="libx264", audio_codec="aac", preset="veryfast",
                          threads=4, verbose=False, logger=None)
    return salida, duracion_total


# ================================================================
# YOUTUBE
# ================================================================
def construir_descripcion_short(ing, problema, gancho, contexto, sugerencias):
    Ing = ing[:1].upper() + ing[1:]
    prob = problema.split(",")[0].strip().lower() if problema else ""
    linea1 = (f"{Ing} para {prob}: usos tradicionales | remedios naturales" if prob
              else f"{Ing}: para qué sirve y cómo usarlo | remedios naturales")
    tag_ing = re.sub(r"[^a-z0-9áéíóúüñ]", "", ing.lower())
    hashtags = [f"#{tag_ing}", "#remediosnaturales", "#shorts"]
    for h in HASHTAGS_VIRALES:
        if h not in hashtags and len(hashtags) < 9:
            hashtags.append(h)
    relacionadas = []
    for s in sugerencias[:12]:
        if s["frase"] not in relacionadas:
            relacionadas.append(s["frase"])
    busquedas = ", ".join(relacionadas[:6]) or f"{ing} beneficios, {ing} propiedades, para qué sirve {ing}"
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

🌿 INGREDIENTE ESTRELLA: {Ing}

🔍 En este Short:
• {Ing} en la herbolaria mexicana y sus usos tradicionales
• Cómo se relaciona {ing} con {prob or 'el bienestar'} según la tradición
• El producto con {ing} y dónde conseguirlo

🔎 Búsquedas relacionadas: {busquedas}

⚕️ AVISO: Contenido educativo basado en la tradición herbolaria mexicana. No sustituye la consulta médica profesional.

{' '.join(hashtags)}"""
    if ACTIVAR_DISCLOSURE_IA:
        d += DISCLOSURE_TEXT
    return d.replace("<", "").replace(">", "")[:5000]


def subir_short(video_path, titulo, tags_por_nivel, gancho, contexto, ingrediente, problema, sugerencias, srt_path):
    try:
        creds = obtener_credenciales_youtube()
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None

    descripcion = construir_descripcion_short(ingrediente, problema, gancho, contexto, sugerencias)
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
            print(f"📤 Subiendo Short (intento {intento}/5)...")
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            video_id = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()["id"]
            print(f"✅ Short subido: https://youtu.be/{video_id}")
            break
        except Exception as e:
            s = str(e)
            if "invalidTags" in s or "invalid video keywords" in s.lower():
                nivel += 1
                if nivel >= len(tags_por_nivel):
                    print("❌ Los tags de emergencia también fueron rechazados")
                    return None
                print(f"⚠️ YouTube rechazó los tags. Bajando a nivel {nivel} ({'estricto' if nivel == 1 else 'emergencia'})...")
                body["snippet"]["tags"] = [t.strip() for t in tags_por_nivel[nivel].split(",") if t.strip()]
                time.sleep(5)
            elif any(c in s for c in ("502", "503", "504", "Bad Gateway")):
                if intento >= 5:
                    print(f"❌ Falló tras 5 intentos: {e}")
                    return None
                espera = 30 * intento
                print(f"⚠️ Error temporal de YouTube. Esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"❌ Error subiendo a YouTube: {e}")
                return None
    if not video_id:
        return None

    if srt_path and os.path.exists(srt_path):
        subir_subtitulos(youtube, video_id, srt_path)
    asignar_playlist(youtube, video_id, problema or "", prefijo="Shorts de remedios naturales: ")
    publicar_comentario_contacto(youtube, video_id, ingrediente, problema or "")
    return video_id


# ================================================================
# MAIN
# ================================================================
def main():
    print("🚀 Bot Shorts HERBOLARIA — SEO ELITE v3 (6 escenas + subtítulos palabra por palabra)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    estado = cargar_estado()
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encuentra {EXCEL_FILE}")
        sys.exit(1)

    producto, ingrediente = seleccionar_producto_e_ingrediente()
    problema = producto.get("recomendado_para", "")
    tema_viral = random.choice(TEMAS_VIRALES_SALUD)
    print(f"📦 Producto: {producto.get('nombre')} | 🌱 Ingrediente: {ingrediente}")
    print(f"🎯 Tema: {tema_viral['tema']} | 💊 Problema: {problema}")

    # 1) Keywords reales
    print("🔎 Consultando autocompletado de YouTube...")
    sugerencias = obtener_sugerencias(ingrediente, usar_alfabeto=False, tiempo_max=20)
    print(f"   {len(sugerencias)} frases reales. Top: {[s['frase'] for s in sugerencias[:4]]}")

    # 2) Guion
    guion = ia_genera_guion_short(producto, ingrediente, tema_viral, sugerencias)
    ing_real = guion["ingrediente_real"]
    if normalizar(ing_real) != normalizar(ingrediente):
        sugerencias = obtener_sugerencias(ing_real, usar_alfabeto=False, tiempo_max=20) or sugerencias

    # 3) Título con score (perfil Short)
    print("⚡ Eligiendo título por score...")
    titulo, score_t, _ = elegir_mejor_titulo(guion.get("titulos_candidatos", []), ing_real, problema,
                                             sugerencias, cargar_titulos(), modo="short")
    print(f"🔥 TÍTULO [{score_t}/100]: {titulo}  ({len(titulo)} caracteres)")

    # 4) Tags en 3 niveles
    tags_normal = construir_tags(ing_real, problema, titulo, sugerencias, tema_viral)
    tags_estricto = construir_tags(ing_real, problema, titulo, sugerencias, tema_viral, estricto=True)
    tags_emergencia = generar_tags_emergencia(ing_real)
    print(f"🏷️ Tags ({len(tags_normal.split(','))}): {tags_normal[:120]}...")

    # 5) Escenas: imagen + audio
    voz = random.choice(VOCES_DISPONIBLES)
    print(f"🎤 Voz principal: {voz['voz']} ({voz['estilo']})")
    print("\n🎬 Fondo para el producto...")
    fondo_producto = buscar_imagen_escena(f"{ing_real} natural healthy background", "bg_producto_short.jpg")

    escenas, img_producto = [], None
    for i, clave in enumerate(ESCENAS):
        esc = guion["escenas"][clave]
        print(f"\n🎬 Escena {i + 1}/{len(ESCENAS)}: {clave}")
        img_path = f"escena_short_{i}.jpg"

        if clave == "producto":
            if not componer_producto_vertical(producto["imagen_url"], fondo_producto, img_path):
                with Image.open(fondo_producto) as im:
                    ImageOps.fit(im.convert("RGB"), (ANCHO, ALTO), Image.Resampling.LANCZOS).save(img_path, "JPEG", quality=90)
            img_producto = img_path
        elif clave == "cta":
            shutil.copy(img_producto, img_path)  # reutiliza la composición del producto
        else:
            buscar_imagen_escena(esc.get("query_pexels") or f"{ing_real} plant natural", img_path)

        img_path = potenciar_imagen_segmento(img_path)

        tp = esc.get("texto_pantalla", "")
        if clave == "hook":
            if not tp or not texto_seguro(tp):
                tp = elegir_gancho_miniatura(titulo)
            img_path = quemar_hook_vertical(img_path, tp, img_path)
        elif clave != "cta" and tp and texto_seguro(tp):
            img_path = quemar_etiqueta_vertical(img_path, tp, img_path, y=260 if clave == "producto" else 300)

        audio_path = f"audio_short_{i}.mp3"
        res = generar_audio(esc["texto"], audio_path, voz, max_intentos=3)
        if not res:
            print(f"❌ Falló el audio de la escena {clave}")
            sys.exit(1)
        eventos, voz = res  # la voz se mantiene en el resto del video
        escenas.append({"img_path": img_path, "audio_path": audio_path, "texto": esc["texto"], "eventos": eventos})

    # 6) Montaje
    video_path, duracion_total = montar_short(escenas)
    srt_path = construir_srt(
        [{"texto": e["texto"], "eventos": e["eventos"], "inicio": e["inicio"], "duracion": e["duracion"]} for e in escenas],
        "subtitulos_short.srt")

    # 7) Subida
    video_id = subir_short(video_path, titulo, [tags_normal, tags_estricto, tags_emergencia],
                           guion.get("gancho_descripcion", ""), guion.get("contexto_descripcion", ""),
                           ing_real, problema, sugerencias, srt_path)

    if video_id:
        guardar_ingrediente_usado(ingrediente, producto.get("nombre", ""))
        guardar_titulo(titulo)
        estado["publicaciones_hoy"] = estado.get("publicaciones_hoy", 0) + 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        print(f"\n🎉 ¡Short publicado! ({duracion_total:.0f}s)")
        print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
        print(f"   📞 Teléfono: {TELEFONO_NUMBER}")
        print(f"   🤖 Telegram: {TELEGRAM_BOT}")
        print(f"   🔗 URL: https://youtu.be/{video_id}")
        print(f"   📊 Publicaciones hoy: {estado['publicaciones_hoy']}/{MAX_VIDEOS_DIA}")
        print("   ℹ️ Recuerda fijar el comentario manualmente en YouTube Studio (la API no lo permite).")
    else:
        print("❌ El Short no se pudo subir; no se actualiza el estado.")

    for f in os.listdir("."):
        if f.startswith(("escena_short_", "audio_short_")) or f in (
                "short_final.mp4", "bg_producto_short.jpg", "subtitulos_short.srt", "test_voz.mp3"):
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

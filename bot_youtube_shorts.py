import asyncio
import base64
from datetime import datetime
import json
import os
import random
import re
import sys
import time
import pandas as pd
import io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    concatenate_audioclips,
    concatenate_videoclips,
    CompositeVideoClip,
)
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import requests
import edge_tts
import pytz
import urllib3
from rembg import remove

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
# CONFIGURACIÓN ÉLITE - HERBOLARIA XANAX (SHORTS)
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN")) if os.getenv("YOUTUBE_USER_TOKEN") else {}

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

WHATSAPP_NUMBER = "+52 3123395334"
TELEFONO_NUMBER = "3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"
TELEGRAM_PASSWORD = "A"

ESTADO_FILE = "estado_herbolaria.json"
INGREDIENTES_USADOS_FILE = "ingredientes_usados.json"
TITULOS_FILE = "titulos_herbolaria_publicados.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"

MAX_VIDEOS_DIA = 1

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ⏰ VENTANA DE PUBLICACIÓN (hora CDMX)
HORA_EXCLUIR_INICIO = 0
HORA_EXCLUIR_FIN = 4

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ================================================================
# 🛡️ PALABRAS PROHIBIDAS (Política de salud de YouTube)
# ================================================================
PALABRAS_PROHIBIDAS_TITULO = [
    "cura", "curar", "cura milagrosa", "curación",
    "milagrosa", "milagroso", "milagro", "milagros",
    "sana", "sanar", "sanación", "sanarlo", "sanarte",
    "erradica", "erradicar",
    "desaparece por completo", "desaparecer por completo",
    "remedio definitivo", "tratamiento definitivo",
    "fin del", "fin de", "termina con", "acaba con",
    "adiós al", "adiós definitivo", "adiós para siempre",
    "nunca más", "para siempre",
    "de raíz", "desde la raíz", "elimina de raíz",
    "científicamente comprobado", "cientificamente comprobado",
    "comprobado científicamente", "comprobado cientificamente",
    "clínicamente probado", "clinicamente probado",
    "avalado por médicos", "aprobado por médicos",
    "recomendado por médicos", "avalado por doctores",
    "aprobado por la FDA", "aprobado por fda",
    "respaldado por estudios", "estudios lo confirman",
    "eficacia probada", "efectividad probada",
    "funciona siempre", "sin fallar", "sin excepciones",
    "100% efectivo", "100 % efectivo", "cien por ciento efectivo",
    "garantizado", "garantía de resultados",
    "revolucionario", "breakthrough", "descubrimiento médico",
    "innovación médica", "patentado médicamente",
    "reemplaza", "reemplaza medicamentos", "reemplaza tu tratamiento",
    "sustituye", "sustituye medicamentos", "sustituye tu tratamiento",
    "no necesitas médico", "sin ir al médico", "olvida al doctor",
    "mejor que las pastillas", "mejor que los medicamentos",
    "olvida la medicina", "tira tus pastillas", "deja tu tratamiento",
    "sin fármacos", "sin medicamentos", "sin receta médica",
    "alternativa a medicamentos", "en vez de medicamentos",
    "en 24 horas", "en un día", "hoy mismo",
    "en 3 días", "en tres días",
    "en 7 días", "en una semana", "en siete días",
    "en un mes", "en 30 días",
    "esta noche", "mañana mismo",
    "al instante", "inmediatamente", "instantáneo", "instantanea",
    "resultados inmediatos", "efecto inmediato",
    "rápido y fácil", "exprés", "express",
    "peligroso", "peligrosa", "mortal", "mortales",
    "asesino silencioso", "asesina silenciosa",
    "te está matando", "te mata", "te matará",
    "veneno", "tóxico", "toxina mortal",
    "muerte", "fatal", "terminal",
    "urgente", "emergencia", "alerta roja",
    "impactante", "shock", "shocking",
    "revelación", "revelador",
    "increíble", "asombroso", "alucinante",
    "conspiración", "lo que te ocultan", "la verdad oculta",
    "ellos no quieren que sepas", "te mienten",
    "transforma tu cuerpo", "transforma tu vida",
    "cambia tu vida", "nuevo tú", "nueva tú",
    "antes y después", "resultados increíbles",
    "pierde 10 kilos", "baja 10 kilos", "pierde peso rápido",
    "quema grasa milagrosa", "quema grasa express",
    "derrite la grasa", "elimina grasa localizada",
    "adelgaza sin dieta", "sin dieta", "sin ejercicio",
    "sin esfuerzo", "come lo que quieras",
    "barriga plana", "abdomen plano en días",
    "rejuvenece 20 años", "rejuvenece 10 años",
    "eterna juventud", "juventud eterna", "inmortal",
    "no vas a creer", "no lo vas a creer",
    "te sorprenderá", "te dejará impactado",
    "quedarás impactado", "quedarás asombrado",
    "brutal", "bestial",
    "top", "los 10 mejores", "los 5 peores",
    "lo que nadie dice", "lo que nadie sabe",
    "el mejor del mundo", "el peor del mundo",
    "definitivo", "perfecto",
    "cáncer", "cancer", "tumor", "tumores",
    "VIH", "SIDA", "sida",
    "alzheimer", "parkinson", "esclerosis",
    "leucemia", "infarto", "derrame cerebral",
    "ictus", "metástasis",
    "solución", "elimina",
    "limpiar tu cuerpo", "limpieza total del cuerpo",
]

# ================================================================
# 🔥 BASE DE DATOS DE KEYWORDS VIRALES
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

# ================================================================
# 🎤 VOCES NEURALES PREMIUM (8 voces con fallback)
# ================================================================
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
# 🎯 MOTOR DE FÓRMULAS DE TÍTULOS VARIADAS (ANTI-REPETICIÓN)
# ================================================================
# 30+ fórmulas de títulos que rotan para evitar que YouTube marque spam
FORMULAS_TITULOS_VARIADAS = {
    # 🔍 Búsqueda (2% - muy bajo para no abusar)
    "busqueda": [
        "Para qué sirve {ingrediente} en remedios naturales",
        "Para qué sirve {ingrediente} y cómo usarlo",
        "Qué es {ingrediente} y por qué lo necesitas",
    ],
    # 🤔 Preguntas impactantes (15%)
    "pregunta": [
        "¿Sabías que {ingrediente} ayuda con {problema}?",
        "¿Conocías este uso del {ingrediente}?",
        "¿Por qué tu abuela usaba {ingrediente}?",
        "¿{ingrediente} realmente funciona para {problema}?",
        "¿Qué pasa si usas {ingrediente} todos los días?",
    ],
    # 🔐 Secretos y revelaciones (15%)
    "secreto": [
        "El secreto ancestral del {ingrediente} para {problema}",
        "Lo que nadie te contó sobre el {ingrediente}",
        "El poder oculto del {ingrediente} en tu salud",
        "La verdad sobre {ingrediente} que pocos conocen",
        "{ingrediente}: secreto de la herbolaria mexicana",
    ],
    # 🎯 Problema-Solución (18%)
    "problema_solucion": [
        "{problema}: el remedio natural con {ingrediente}",
        "Si sufres de {problema}, prueba {ingrediente}",
        "{ingrediente}: el aliado natural contra {problema}",
        "Adiós {problema}: descubre {ingrediente}",
        "¿Cansado de {problema}? Conoce {ingrediente}",
    ],
    # 📊 Beneficios específicos (15%)
    "beneficios": [
        "5 formas en que {ingrediente} mejora tu salud",
        "{ingrediente}: 3 beneficios que cambiarán tu vida",
        "Los beneficios del {ingrediente} que debes conocer",
        "Cómo {ingrediente} transforma tu bienestar diario",
    ],
    # 🌿 Tradición y abuelos (12%)
    "tradicional": [
        "Por qué los abuelos confiaban en el {ingrediente}",
        "{ingrediente}: la herencia de la medicina tradicional",
        "La sabiduría ancestral del {ingrediente} para tu salud",
        "{ingrediente}: remedio tradicional mexicano",
    ],
    # ⚡ Acción directa / Cómo usar (12%)
    "como_usar": [
        "Cómo usar {ingrediente} correctamente para {problema}",
        "La forma correcta de aprovechar {ingrediente}",
        "{ingrediente}: guía completa de uso tradicional",
        "Prepara {ingrediente} así y siente la diferencia",
    ],
    # 💊 Ciencia y evidencia (7%)
    "cientifico": [
        "Lo que dice la ciencia sobre {ingrediente}",
        "{ingrediente}: entre la tradición y la evidencia",
        "Por qué {ingrediente} es reconocido en herbolaria",
    ],
    # ⚠️ Advertencias / Verdades (4%)
    "verdad": [
        "Lo que debes saber antes de usar {ingrediente}",
        "Errores comunes al usar {ingrediente}",
        "La verdad sobre {ingrediente} en remedios caseros",
    ],
}

# ================================================================
# 🧠 ESTADO Y SELECCIÓN ANTI-REPETICIÓN
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"publicaciones_hoy": 0, "fecha": None, "ultima_publicacion": None}

def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f: json.dump(estado, f, indent=2, ensure_ascii=False)

def cargar_ingredientes_usados():
    try:
        with open(INGREDIENTES_USADOS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"ingredientes": [], "fecha_reinicio": None}

def guardar_ingrediente_usado(ingrediente, producto):
    data = cargar_ingredientes_usados()
    hoy = datetime.now().date().isoformat()
    if data.get("fecha_reinicio") != hoy:
        data["ingredientes"] = []
        data["fecha_reinicio"] = hoy
    entry = f"{ingrediente}|{producto}"
    if entry not in data["ingredientes"]:
        data["ingredientes"].append(entry)
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def seleccionar_producto_aleatorio():
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    data_usados = cargar_ingredientes_usados()
    usados = data_usados.get("ingredientes", [])

    df = df[df["imagen_url"].notna() & (df["imagen_url"] != "")]
    df = df[df["ingredientes_clave"].notna() & (df["ingredientes_clave"] != "")]

    for _ in range(50):
        producto = df.sample(1).iloc[0].to_dict()
        producto_nombre = producto.get("nombre", "")
        if producto_nombre not in [u.split("|")[1] for u in usados]:
            return producto

    print("🔄 Todos los productos usados. Reiniciando historial...")
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump({"ingredientes": [], "fecha_reinicio": datetime.now().date().isoformat()}, f)

    return df.sample(1).iloc[0].to_dict()

def cargar_titulos():
    try:
        with open(TITULOS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"titulos": []}

def guardar_titulo(titulo):
    data = cargar_titulos()
    if titulo not in data["titulos"]:
        data["titulos"].append(titulo)
        # Mantener solo los últimos 100 títulos para evitar spam
        if len(data["titulos"]) > 100:
            data["titulos"] = data["titulos"][-100:]
        with open(TITULOS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

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
    if not forzar:
        hora_actual = ahora.hour
        if HORA_EXCLUIR_INICIO <= hora_actual < HORA_EXCLUIR_FIN:
            print(f"🌙 Hora de madrugada ({hora_actual}h CDMX). No publico entre {HORA_EXCLUIR_INICIO}:00 y {HORA_EXCLUIR_FIN}:00 para evitar bajo alcance.")
            return False

    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff = (ahora - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(3, 5)
        if diff < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h (han pasado {diff:.1f}h).")
            return False
    return True

# ================================================================
# 🔥 MOTOR DE KEYWORDS VIRALES
# ================================================================
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
# 🎯 ANTI-REPETICIÓN + FÓRMULAS VARIADAS PARA SHORTS
# ================================================================
def titulo_ya_existe(titulo_candidato):
    """Verifica si un título (o uno muy similar) ya fue publicado."""
    titulos_publicados = cargar_titulos().get("titulos", [])
    candidato_lower = titulo_candidato.lower().strip()
    
    for t_pub in titulos_publicados:
        t_pub_lower = t_pub.lower().strip()
        # Coincidencia exacta
        if candidato_lower == t_pub_lower:
            return True
        # Coincidencia alta (más del 85% de palabras iguales)
        palabras_cand = set(re.findall(r'\w+', candidato_lower))
        palabras_pub = set(re.findall(r'\w+', t_pub_lower))
        if palabras_cand and palabras_pub:
            interseccion = palabras_cand & palabras_pub
            union = palabras_cand | palabras_pub
            similitud = len(interseccion) / len(union)
            if similitud > 0.85:
                return True
    return False

def generar_titulo_variado(ingrediente, problema=None):
    """
    Genera un título usando una fórmula aleatoria de las 30+ disponibles.
    Evita repetir patrones recientes y verifica contra títulos publicados.
    """
    categorias_pesos = {
        "busqueda": 2,            # Solo 2% - ya no abusa de "Para qué sirve"
        "pregunta": 15,
        "secreto": 15,
        "problema_solucion": 18,
        "beneficios": 15,
        "tradicional": 12,
        "como_usar": 12,
        "cientifico": 7,
        "verdad": 4,
    }
    
    problema_limpio = ""
    if problema:
        problemas_lista = [p.strip() for p in str(problema).split(",") if p.strip()]
        if problemas_lista:
            problema_limpio = random.choice(problemas_lista[:3])
    
    for _ in range(10):
        categorias = list(categorias_pesos.keys())
        pesos = [categorias_pesos[c] for c in categorias]
        categoria_elegida = random.choices(categorias, weights=pesos, k=1)[0]
        
        formulas = FORMULAS_TITULOS_VARIADAS[categoria_elegida]
        formula = random.choice(formulas)
        
        titulo = formula.format(
            ingrediente=ingrediente,
            problema=problema_limpio or "tu bienestar"
        )
        
        if not titulo_ya_existe(titulo):
            return titulo, categoria_elegida
    
    return titulo, categoria_elegida

def optimizar_titulo_short(titulo_ia, ingrediente, problema=None):
    """
    Optimiza el título con un sistema INTELIGENTE:
    1. Si la IA generó un título variado y seguro → lo RESPETA
    2. Si el título es genérico o tiene palabras prohibidas → inyecta fórmula variada
    3. Verifica que no esté repetido contra títulos publicados
    4. Agrega hashtags virales al final
    """
    t = (titulo_ia or "").strip()
    hashtags_existentes = re.findall(r'#\w+', t)
    titulo_limpio = re.sub(r'#\w+', '', t).strip()
    lower = titulo_limpio.lower()

    # 1) Si tiene palabras prohibidas → descartar
    if any(p in lower for p in PALABRAS_PROHIBIDAS_TITULO):
        print(f"🛡️ Título con palabra prohibida → generando fórmula variada...")
        titulo_limpio = ""

    # 2) Analizar si el título de la IA ya es bueno y variado
    titulo_ia_es_bueno = False
    if titulo_limpio and len(titulo_limpio) >= 20:
        inicia_con_para_que_sirve = lower.startswith("para qué sirve") or lower.startswith("para que sirve")
        
        keywords_presentes = ["remedios", "salud natural", "medicina natural", "hierbas",
                              "beneficios", "propiedades", "cómo usar", "herbolaria",
                              "plantas medicinales", "remedio casero", "tradición",
                              "sabías", "aliado", "apoya", "usos", "secreto",
                              "verdad", "abuelos", "ancestral"]
        tiene_keyword = any(kw in lower for kw in keywords_presentes)
        
        if not inicia_con_para_que_sirve and tiene_keyword and not titulo_ya_existe(titulo_limpio):
            titulo_ia_es_bueno = True
            print(f"✅ Respetando título variado de la IA: {titulo_limpio}")

    # 3) Si el título de la IA es bueno, usarlo; si no, generar uno variado
    if titulo_ia_es_bueno:
        titulo_final_base = titulo_limpio[:60]
    else:
        print("🎲 Generando título con fórmula variada (anti-repetición)...")
        titulo_variado, categoria = generar_titulo_variado(ingrediente, problema)
        print(f"🔥 Fórmula usada: [{categoria}] → {titulo_variado}")
        titulo_final_base = titulo_variado[:60]

    # 4) Agregar hashtags virales (2-3) + hashtag del ingrediente
    hashtags = hashtags_existentes[:1]
    if not hashtags:
        hashtags = [f"#{ingrediente.replace(' ', '').lower()}"]
    hashtags += random.sample(HASHTAGS_VIRALES[:9], 2)

    titulo_final = f"{titulo_final_base} {' '.join(hashtags)}"
    return titulo_final[:100]

# ================================================================
# 🎯 CLASIFICADOR DE INGREDIENTES
# ================================================================
def clasificar_ingrediente(ingrediente):
    ing_lower = ingrediente.lower()
    
    aceites_grasas = ["omega", "dha", "epa", "ácido graso", "aceite de pescado",
                     "aceite de krill", "linaza", "chía", "linoleico"]
    if any(k in ing_lower for k in aceites_grasas):
        return "lipido"
    
    proteinas = ["colágeno", "colageno", "proteína", "proteina", "aminoácido", 
                 "aminoacido", "whey", "creatina", "bcaa", "arginina", "glicina"]
    if any(k in ing_lower for k in proteinas):
        return "proteina"
    
    vitaminas = ["vitamina", "vit ", "vit.", "ácido fólico", "acido folico", 
                 "biotina", "retinol", "tiamina", "riboflavina"]
    minerales = ["magnesio", "zinc", "hierro", "calcio", "potasio", "selenio", 
                 "cromo", "yodo", "cobre", "manganeso"]
    if any(k in ing_lower for k in vitaminas + minerales):
        return "micronutriente"
    
    frutas = ["naranja", "limón", "limon", "fresa", "manzana", "plátano", "platano",
              "piña", "piña", "mango", "papaya", "arándano", "arandano", "uva",
              "sandía", "sandia", "kiwi", "guayaba", "granada", "cereza", "ciruela",
              "durazno", "chabacano", "tamarindo", "coco", "jitomate"]
    if any(k in ing_lower for k in frutas):
        return "fruta"
    
    hongos_probioticos = ["hongo", "reishi", "shiitake", "melena de león", 
                         "cordyceps", "levadura", "probiótico", "probiotico", 
                         "lactobacillus", "bifidobacterium"]
    if any(k in ing_lower for k in hongos_probioticos):
        return "probiotico"
    
    raices = ["cúrcuma", "curcuma", "jengibre", "ginseng", "maca", "ashwagandha",
              "valeriana", "regaliz", "alcachofa", "betabel", "remolacha", "camote"]
    if any(k in ing_lower for k in raices):
        return "raiz"
    
    return "planta"

# ================================================================
# 🎯 GENERADOR DE TAGS SEO ELITE
# ================================================================
def generar_tags_seo_elite(ingrediente, problema, titulo, tema_viral=None):
    tags = []
    ing_lower = ingrediente.lower().strip()
    tipo = clasificar_ingrediente(ingrediente)
    
    print(f"   🎯 Ingrediente clasificado como: {tipo}")
    
    tags.append(ing_lower)
    
    if tipo == "planta":
        tags.extend([
            f"planta {ing_lower}",
            f"hierba {ing_lower}",
            f"té de {ing_lower}",
            f"infusión de {ing_lower}",
            f"remedio de {ing_lower}",
            f"{ing_lower} medicinal",
        ])
    elif tipo == "lipido":
        tags.extend([
            f"ácido graso {ing_lower}",
            f"suplemento {ing_lower}",
            f"{ing_lower} beneficios",
            f"{ing_lower} natural",
            f"{ing_lower} para salud",
        ])
    elif tipo == "proteina":
        tags.extend([
            f"suplemento {ing_lower}",
            f"{ing_lower} beneficios",
            f"{ing_lower} para salud",
            f"{ing_lower} natural",
        ])
    elif tipo == "micronutriente":
        tags.extend([
            f"suplemento {ing_lower}",
            f"{ing_lower} beneficios",
            f"{ing_lower} para salud",
            f"{ing_lower} natural",
        ])
    elif tipo == "fruta":
        tags.extend([
            f"fruta {ing_lower}",
            f"{ing_lower} beneficios",
            f"jugo de {ing_lower}",
            f"{ing_lower} natural",
        ])
    elif tipo == "probiotico":
        tags.extend([
            f"suplemento {ing_lower}",
            f"{ing_lower} beneficios",
            f"{ing_lower} natural",
            f"{ing_lower} para salud",
        ])
    elif tipo == "raiz":
        tags.extend([
            f"raíz de {ing_lower}",
            f"{ing_lower} medicinal",
            f"remedio de {ing_lower}",
            f"{ing_lower} beneficios",
        ])
    
    tags.extend([
        f"beneficios de {ing_lower}",
        f"propiedades de {ing_lower}",
        f"para qué sirve {ing_lower}",
    ])
    
    tags.extend([
        f"{ing_lower} en remedios naturales",
        f"{ing_lower} usos y beneficios",
    ])
    
    if problema:
        problemas_individuales = [p.strip() for p in str(problema).split(",") if p.strip()]
        for prob in problemas_individuales[:5]:
            prob_limpio = prob.lower().strip()
            if 3 < len(prob_limpio) <= 28:
                tags.append(prob_limpio)
                tag_rem = f"{ing_lower} para {prob_limpio}"
                if len(tag_rem) <= 30:
                    tags.append(tag_rem)
    
    tags_generales = [
        "remedios naturales",
        "remedios caseros",
        "salud natural",
        "medicina natural",
        "bienestar natural",
        "salud y bienestar",
        "nutrición natural",
        "vida saludable",
        "suplementos naturales",
    ]
    
    if tipo == "planta":
        tags_generales.extend([
            "herbolaria mexicana",
            "plantas medicinales",
            "hierbas medicinales",
            "tradición mexicana",
        ])
    
    tags.extend(tags_generales)
    
    if titulo:
        palabras_titulo = [p.lower() for p in re.findall(r'\w+', titulo) if 4 < len(p) <= 20]
        for p in palabras_titulo[:4]:
            if p not in [t.lower() for t in tags]:
                tags.append(p)
    
    if tema_viral:
        for kw in tema_viral.get("keywords_cortas", [])[:2]:
            kw_l = kw.lower()
            if len(kw_l) <= 30 and kw_l not in [t.lower() for t in tags]:
                tags.append(kw_l)
    
    tags_unicos = []
    vistos = set()
    for tag in tags:
        tag_limpio = re.sub(r'\s+', ' ', tag.strip().lower())
        
        if len(tag_limpio) > 29:
            continue
        if len(tag_limpio) < 2:
            continue
        if not re.match(r'^[a-záéíóúüñ0-9\s]+$', tag_limpio):
            continue
        if any(p in tag_limpio for p in PALABRAS_PROHIBIDAS_TITULO[:50]):
            continue
        if tag_limpio in vistos:
            continue
            
        tags_unicos.append(tag_limpio)
        vistos.add(tag_limpio)
    
    resultado = []
    total_chars = 0
    for tag in tags_unicos:
        if total_chars + len(tag) + 1 > 495:
            break
        resultado.append(tag)
        total_chars += len(tag) + 1
    
    if len(resultado) < 3:
        resultado = ["remedios naturales", "salud natural", ingrediente.lower()][:3]
    
    return ", ".join(resultado[:15])

def generar_tags_virales(ingrediente, problema=None, tema_viral=None):
    return generar_tags_seo_elite(ingrediente, problema, "", tema_viral)

# ================================================================
# 🤖 IA GENERA CONTENIDO COMPLETO (MEJORADO - pide variedad)
# ================================================================
def ia_genera_contenido_completo(producto):
    producto_info = f"""
NOMBRE DEL PRODUCTO: {producto.get('nombre', 'N/A')}
PRESENTACIÓN: {producto.get('presentacion', 'N/A')}
RECOMENDADO PARA: {producto.get('recomendado_para', 'N/A')}
INGREDIENTES CLAVE: {producto.get('ingredientes_clave', 'N/A')}
BENEFICIOS: {producto.get('beneficios', 'N/A')}
MODO DE EMPLEO: {producto.get('MODO DE EMPLEO / DOSIS', 'N/A')}
"""
    problema = producto.get('recomendado_para', '')
    tema_viral = random.choice(TEMAS_VIRALES_SALUD)
    keywords_virales_prompt = obtener_keywords_aleatorias_virales(8)
    prohibidas_str = ", ".join(f'"{p}"' for p in PALABRAS_PROHIBIDAS_TITULO[:40]) + "..."

    prompt = f"""Eres experto en herbolaria, nutrición y SEO para YouTube Shorts. Creas contenido VIRAL y SEGURO optimizado para búsquedas de alto volumen.

📦 INFORMACIÓN COMPLETA DEL PRODUCTO:
{producto_info}

🎯 TEMA VIRAL: {tema_viral['tema'].upper()}
💊 PROBLEMA QUE RESUELVE: {problema}

🔑 KEYWORDS VIRALES DE ALTO VOLUMEN QUE DEBES USAR:
{', '.join(keywords_virales_prompt)}

🧠 ANÁLISIS REQUERIDO:
1. ANALIZA los ingredientes y ELIGE el mejor ingrediente REAL (NO uses "sabor X", usa el nombre real)
2. Genera TODO el contenido optimizado para SEO con keywords virales

📋 CONTENIDO A GENERAR (Devuelve ESTRICTAMENTE este JSON):

{{
    "ingrediente_elegido": "Nombre real del ingrediente (ej: Piña, no Sabor Piña)",
    "titulo": "Título VIRAL VARIADO (máx 60 chars SIN hashtags). ⚠️ NO inicies SIEMPRE con 'Para qué sirve'. Elige UNA fórmula variada entre: pregunta impactante, secreto ancestral, problema-solución, beneficio específico, tradición de abuelos, o cómo usar.",
    "guion_segmento_1": "Texto de 25 segundos sobre el ingrediente (65-75 palabras). Inicia con pregunta impactante que incluya una keyword viral. Menciona 2-3 beneficios según la tradición. Incluye disclaimer educativo. NO menciones el producto ni contacto.",
    "guion_segmento_2": "Texto de 20 segundos presentando el producto (50-60 palabras). Menciona el nombre del producto y que contiene el ingrediente. DEBE terminar exactamente con: '¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp al número en la descripción, o a nuestro asesor inteligente de telegram'",
    "tags": "NO generes tags, se generan automáticamente",
    "descripcion_corta": "Descripción SEO con keywords virales (máx 120 caracteres)",
    "gancho_descripcion": "Gancho inicial con keyword viral (máx 90 caracteres)",
    "contexto_descripcion": "Contexto educativo con keywords naturales (1 oración)",
    "query_pexels": "Query en inglés para imagen del ingrediente (descripción visual vertical)"
}}

⚠️ REGLAS CRÍTICAS:
- El ingrediente_elegido debe ser el nombre REAL
- El Segmento 2 DEBE terminar con la frase exacta de contacto
- ⚠️ TÍTULO VARIADO: NO uses siempre "Para qué sirve". Varía con preguntas, secretos, beneficios, tradiciones
- query_pexels debe ser en inglés y específico

🚨 POLÍTICA DE SALUD DE YOUTUBE:
NUNCA uses: {prohibidas_str}

✅ MARCOS SEGUROS:
- "apoya", "favorece", "contribuye al bienestar", "alivia tradicionalmente"
- "aliado natural", "complemento para", "parte de un estilo de vida saludable"

Ejemplos de TÍTULOS VIRALES VARIADOS:
- "El secreto ancestral del nopal para el colesterol"
- "¿Sabías que la manzanilla alivia la gastritis?"
- "Insomnio: el remedio natural con valeriana"
- "Por qué los abuelos usaban eucalipto"
- "3 beneficios de la lavanda que no conocías"
- "La verdad sobre el romero en herbolaria"
"""

    for intento in range(6):
        try:
            print(f"🤖 IA analizando producto con SEO viral... (intento {intento+1}/6)")
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.9, "max_tokens": 1200, "response_format": {"type": "json_object"}}, timeout=90)
            r.raise_for_status()
            respuesta = r.json()["choices"][0]["message"]["content"].strip()
            respuesta = re.sub(r'`json\s*', '', respuesta).replace('`', '')
            inicio, fin = respuesta.find('{'), respuesta.rfind('}')
            json_str = respuesta[inicio:fin+1] if inicio != -1 and fin != -1 else respuesta

            data = json.loads(json_str, strict=False)

            if "ingrediente_elegido" not in data:
                raise ValueError("La IA no eligió ingrediente")
            if "guion_segmento_1" not in data or len(data["guion_segmento_1"]) < 50:
                raise ValueError("Texto demasiado corto")

            guion_seg2 = data.get("guion_segmento_2", "")
            if "asesor inteligente de telegram" not in guion_seg2.lower():
                print("⚠️ La IA no incluyó el CTA exacto. Agregándolo...")
                cta_obligatorio = "¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp al número en la descripción, o a nuestro asesor inteligente de telegram"
                oraciones = re.split(r'(?<=[.!?])\s+', guion_seg2)
                if len(oraciones) > 1:
                    oraciones = oraciones[:-1]
                oraciones.append(cta_obligatorio)
                data["guion_segmento_2"] = " ".join(oraciones)

            ingrediente = data["ingrediente_elegido"]

            # 🔥 OPTIMIZAR TÍTULO CON FÓRMULAS VARIADAS + ANTI-REPETICIÓN
            data["titulo"] = optimizar_titulo_short(data.get("titulo", ""), ingrediente, problema)

            # 🔥 GENERAR TAGS SEO ELITE AUTOMÁTICAMENTE
            data["tags"] = generar_tags_seo_elite(ingrediente, problema, data.get("titulo", ""), tema_viral)

            if "query_pexels" not in data:
                data["query_pexels"] = f"{ingrediente} natural healthy"

            print(f"✅ IA generó contenido con SEO viral")
            print(f"   🌱 Ingrediente: {ingrediente}")
            print(f"   🔥 Título optimizado: {data['titulo']}")
            print(f"   🏷️ Tags SEO Elite ({len(data['tags'].split(','))} tags): {data['tags'][:80]}...")

            return data

        except Exception as e:
            print(f"❌ Intento {intento+1} falló: {e}")
            if intento == 5:
                print("❌ Todos los intentos de IA fallaron")
                sys.exit(1)
            time.sleep(5)

# ================================================================
# 🖼️ IMÁGENES: PEXELS VERTICAL (fallback)
# ================================================================
def buscar_imagen_pexels_salud(query, intentos=3):
    if not PEXELS_API_KEY: return None
    variantes = ["natural", "healthy", "organic", "fresh", "herbal", "medicinal", "close up", "macro"]
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}

    for intento in range(intentos):
        try:
            params = {"query": f"{query} {random.choice(variantes)}", "orientation": "portrait", "per_page": 5, "page": random.randint(1, 5)}
            r = requests.get(url, headers=headers, params=params, timeout=15)
            if r.status_code == 200 and r.json().get("photos"):
                return r.json()["photos"][0]["src"]["large2x"]
        except: pass
    return "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop"

def _descargar_imagen_vertical(url, salida):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageOps.fit(img, (1080, 1920), Image.Resampling.LANCZOS)
    img.save(salida, "JPEG", quality=90)
    return salida

# ================================================================
# 🎨 IMÁGENES DE ESCENAS: FLUX CLOUDFLARE → PEXELS
# ================================================================
SEGMENTO_FLUX_SUFFIX_SHORT = (", photorealistic photography, natural lighting, vivid saturated colors, "
                              "cinematic composition, botanical and herbal theme, shallow depth of field, "
                              "no text, no watermark, no people, vertical portrait 9:16")

def _flux_cloudflare_imagen_short(query, salida):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    payload = {
        "prompt": query + SEGMENTO_FLUX_SUFFIX_SHORT,
        "steps": 4
    }
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    b64 = (data.get("result") or {}).get("image")
    if not b64:
        raise ValueError(f"Cloudflare no devolvió imagen: {str(data)[:200]}")
    with open(salida, "wb") as f:
        f.write(base64.b64decode(b64))
    with Image.open(salida) as im:
        im = ImageOps.fit(im.convert("RGB"), (1080, 1920), Image.Resampling.LANCZOS)
        im.save(salida, "JPEG", quality=90)
    return salida

def buscar_imagen_segmento_short(query_en, salida):
    if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:
        for intento in range(1, 4):
            try:
                print(f"   🎨 Flux Short intento {intento}/3...")
                _flux_cloudflare_imagen_short(query_en, salida)
                print(f"   ✅ Imagen de Short generada con Flux (Cloudflare)")
                return salida
            except Exception as e:
                print(f"   ⚠️ Flux Short intento {intento} falló: {e}")
                time.sleep(2)
        print("   ⚠️ Flux falló tras 3 intentos en esta escena. Usando Pexels.")
    else:
        print("   ⚠️ Sin keys de Cloudflare configuradas. Usando Pexels para la escena.")

    url_img = buscar_imagen_pexels_salud(query_en)
    if url_img:
        try:
            return _descargar_imagen_vertical(url_img, salida)
        except Exception as e:
            print(f"   ⚠️ Pexels falló ({e}). Usando imagen por defecto.")
    return _descargar_imagen_vertical("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop", salida)

# ================================================================
# 🎤 AUDIO CON REINTENTOS + FALLBACK ENTRE VOCES
# ================================================================
async def _generar_audio_interno(texto, path, voz_config):
    texto_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\'\"]', '', texto)
    await edge_tts.Communicate(texto_limpio, voz_config["voz"], rate=voz_config["velocidad"]).save(path)

def generar_audio_con_reintentos(texto, path, voz_principal, max_intentos=3):
    for intento in range(max_intentos):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generar_audio_interno(texto, path, voz_principal))
            loop.close()
            
            if os.path.exists(path) and os.path.getsize(path) > 100:
                if intento > 0:
                    print(f"   ✅ Audio generado en intento {intento+1}/{max_intentos}")
                return path
                
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "401" in error_msg or "Forbidden" in error_msg:
                print(f"   ⚠️ Voz {voz_principal['voz']} bloqueada (intento {intento+1}/{max_intentos}): {error_msg[:80]}")
            else:
                print(f"   ⚠️ Error generando audio (intento {intento+1}/{max_intentos}): {error_msg[:80]}")
            
            if intento < max_intentos - 1:
                espera = 2 ** intento
                print(f"   ⏳ Esperando {espera}s antes de reintentar...")
                time.sleep(espera)
    
    print(f"   🔄 Voz {voz_principal['voz']} falló tras {max_intentos} intentos. Probando voces alternativas...")
    for voz_alt in VOCES_DISPONIBLES:
        if voz_alt["voz"] == voz_principal["voz"]:
            continue
        
        try:
            print(f"   🎤 Probando voz alternativa: {voz_alt['voz']}...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_generar_audio_interno(texto, path, voz_alt))
            loop.close()
            
            if os.path.exists(path) and os.path.getsize(path) > 100:
                print(f"   ✅ Audio generado con voz alternativa: {voz_alt['voz']}")
                return path
                
        except Exception as e:
            print(f"   ⚠️ Voz alternativa {voz_alt['voz']} también falló: {str(e)[:60]}")
            continue
    
    print(f"   ❌ Todas las voces fallaron para este segmento")
    return None

def crear_imagen_texto_cta(texto, ancho=1080, alto=220):
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    tamano_fuente = 55
    fuente = None
    for ruta in [FUENTE, "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if os.path.exists(ruta):
            fuente = ImageFont.truetype(ruta, tamano_fuente)
            break
    if fuente is None:
        fuente = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), texto, font=fuente)
    ancho_texto = bbox[2] - bbox[0]
    alto_texto = bbox[3] - bbox[1]
    pos_x = (ancho - ancho_texto) // 2
    pos_y = (alto - alto_texto) // 2
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx == 0 and dy == 0:
                continue
            draw.text((pos_x + dx, pos_y + dy), texto, font=fuente, fill=(0, 0, 0, 255))
    draw.text((pos_x, pos_y), texto, font=fuente, fill=(255, 255, 255, 255))
    return img

def crear_overlay_aviso(salida="aviso_overlay.png"):
    try:
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        txt = "Contenido educativo. No sustituye la consulta médica."
        f = ImageFont.truetype(FUENTE, 40)
        tw = d.textbbox((0, 0), txt, font=f)[2]
        d.rounded_rectangle([((1080 - tw) // 2 - 30, 1500), ((1080 + tw) // 2 + 30, 1570)], radius=18, fill=(0, 0, 0, 165))
        d.text(((1080 - tw) // 2, 1516), txt, font=f, fill=(255, 255, 255, 235))
        img.save(salida)
        return salida
    except Exception as e:
        print(f"⚠️ Error overlay aviso: {e}")
        return None

# ================================================================
# 🎥 CREAR VIDEO SHORT
# ================================================================
def crear_video_con_dos_imagenes_y_texto(guion, img_ingrediente_path, url_producto, ingrediente, bg_producto_path):
    print("🎬 Renderizando Short con 2 escenas + overlays...")
    
    voz_principal = random.choice(VOCES_DISPONIBLES)
    print(f"🎤 Voz principal: {voz_principal['voz']} ({voz_principal['estilo']})")
    
    audio1 = generar_audio_con_reintentos(guion["guion_segmento_1"], "seg1.mp3", voz_principal, max_intentos=3)
    audio2 = generar_audio_con_reintentos(guion["guion_segmento_2"], "seg2.mp3", voz_principal, max_intentos=3)

    if not audio1 or not audio2: 
        print("❌ Falló la generación de audio tras todos los intentos")
        return None

    clip1, clip2 = AudioFileClip(audio1), AudioFileClip(audio2)
    audio_total = concatenate_audioclips([clip1, clip2])
    duracion_seg1 = clip1.duration
    duracion_seg2 = clip2.duration
    duracion_total = duracion_seg1 + duracion_seg2

    clips_video = []

    try:
        img = ImageOps.fit(Image.open(img_ingrediente_path).convert("RGB"), (1080, 1920), Image.Resampling.LANCZOS)
        img.save("temp_ingrediente.jpg")
        video_ingrediente = ImageClip("temp_ingrediente.jpg").set_duration(duracion_seg1)
        video_ingrediente = video_ingrediente.resize(lambda t: 1 + 0.03 * (t / duracion_seg1))
        clips_video.append(video_ingrediente)
        print("✅ Escena 1: Imagen del ingrediente cargada (Flux/Pexels)")
    except Exception as e:
        print(f"⚠️ Error con imagen de ingrediente: {e}. Reintentando con Pexels directo...")
        try:
            url_alt = buscar_imagen_pexels_salud(ingrediente)
            _descargar_imagen_vertical(url_alt, "temp_ingrediente.jpg")
            video_ingrediente = ImageClip("temp_ingrediente.jpg").set_duration(duracion_seg1)
            video_ingrediente = video_ingrediente.resize(lambda t: 1 + 0.03 * (t / duracion_seg1))
            clips_video.append(video_ingrediente)
            print("✅ Escena 1: Imagen de respaldo cargada")
        except Exception as e2:
            print(f"❌ Escena 1 imposible: {e2}")

    try:
        print("   🎨 Preparando escena del producto recortado...")
        fondo = ImageOps.fit(Image.open(bg_producto_path).convert("RGB"), (1080, 1920), Image.Resampling.LANCZOS)
        r_prod = requests.get(url_producto, timeout=15, verify=False)
        img_prod_original = Image.open(io.BytesIO(r_prod.content)).convert("RGBA")
        print("   ✂️ Eliminando fondo del producto automáticamente...")
        img_prod_sin_fondo = remove(img_prod_original)
        target_h = int(1920 * 0.45)
        ratio = target_h / img_prod_sin_fondo.height
        nuevo_w = int(img_prod_sin_fondo.width * ratio)
        img_prod_resized = img_prod_sin_fondo.resize((nuevo_w, target_h), Image.Resampling.LANCZOS)
        sombra = img_prod_resized.copy().filter(ImageFilter.GaussianBlur(radius=30))
        x = (1080 - img_prod_resized.width) // 2
        y = int(1920 * 0.55)
        fondo.paste(sombra, (x - 15, y - 15), sombra)
        fondo.paste(img_prod_resized, (x, y), img_prod_resized)
        fondo.save("temp_producto_compuesto.jpg")
        video_producto = ImageClip("temp_producto_compuesto.jpg").set_duration(duracion_seg2)
        video_producto = video_producto.resize(lambda t: 1 + 0.03 * (t / duracion_seg2))
        clips_video.append(video_producto)
        print("✅ Escena 2: Producto recortado sobre fondo Flux/Pexels cargado")
    except Exception as e:
        print(f"⚠️ Error componiendo producto: {e}. Usando imagen original.")
        try:
            r_prod = requests.get(url_producto, timeout=15, verify=False)
            img = Image.open(io.BytesIO(r_prod.content)).convert("RGB").resize((1080, 1920))
            img.save("temp_producto_fallback.jpg")
            video_producto = ImageClip("temp_producto_fallback.jpg").set_duration(duracion_seg2)
            video_producto = video_producto.resize(lambda t: 1 + 0.03 * (t / duracion_seg2))
            clips_video.append(video_producto)
        except:
            pass

    if not clips_video:
        print("❌ No se pudieron cargar las imágenes")
        return None

    video_final = concatenate_videoclips(clips_video, method="compose")

    print("\n🔍 Buscando archivos de música...")
    mp3_files = [f for f in os.listdir(".") if f.lower().endswith(".mp3")]
    musicas = []
    for f in mp3_files:
        if f.startswith("seg"):
            continue
        if os.path.getsize(f) > 100:
            musicas.append(f)
    print(f"   ✅ Música válida: {musicas}")

    musica_aplicada = False
    if musicas:
        for musica_path in musicas:
            try:
                musica = AudioFileClip(musica_path)
                musica = musica.subclip(0, duracion_total).volumex(0.15)
                audio_final = CompositeAudioClip([audio_total, musica])
                video_final = video_final.set_audio(audio_final)
                print("   ✅ Música de fondo agregada al 15%")
                musica_aplicada = True
                break
            except Exception as e:
                print(f"   ⚠️ La música '{musica_path}' falló: {e}")
                continue

    if not musica_aplicada:
        print("⚠️ No se pudo cargar música. Solo voz.")
        video_final = video_final.set_audio(audio_total)

    print("\n✍️ Agregando overlays...")
    try:
        clips_overlays = [video_final]
        aviso = crear_overlay_aviso()
        if aviso:
            av_clip = ImageClip(aviso, transparent=True).set_start(0).set_duration(5)
            clips_overlays.append(av_clip)
            print("✅ Aviso legal agregado")
        texto_cta = "📩 Contáctanos en la descripción"
        img_texto = crear_imagen_texto_cta(texto_cta)
        img_texto.save("temp_texto_cta.png")
        txt_clip = ImageClip("temp_texto_cta.png").set_duration(15).set_start(max(duracion_total - 15, 0))
        txt_clip = txt_clip.set_pos(("center", 1650))
        clips_overlays.append(txt_clip)
        video_final = CompositeVideoClip(clips_overlays)
        print("✅ Overlays agregados exitosamente")
    except Exception as e:
        print(f"⚠️ Error agregando overlays: {e}. Continuando sin ellos...")

    video_final.write_videofile("short_final.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)

    for f in ["seg1.mp3", "seg2.mp3", "temp_ingrediente.jpg", "temp_producto_compuesto.jpg", "temp_producto_fallback.jpg", "temp_texto_cta.png", "aviso_overlay.png"]:
        if os.path.exists(f): os.remove(f)

    return "short_final.mp4"

# ================================================================
# 📤 SUBIR A YOUTUBE CON SEO VIRAL + REINTENTOS
# ================================================================
def obtener_credenciales_youtube():
    creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
    if creds.expired and creds.refresh_token:
        print("🔄 Token expirado, refrescando automáticamente...")
        try:
            creds.refresh(Request())
            print("✅ Token refrescado exitosamente")
        except Exception as e:
            print(f"❌ Error refrescando token: {e}")
            sys.exit(1)
    return creds

def fijar_comentario_contacto(youtube, video_id):
    try:
        texto = (
            "🌿 ¿Dudas o quieres adquirir este producto? Escríbenos:\n\n"
            f"📲 WhatsApp: {WHATSAPP_NUMBER}\n"
            f"📞 Teléfono: {TELEFONO_NUMBER}\n"
            f"🤖 Asistente inteligente en Telegram: {TELEGRAM_BOT}\n"
            f"🔑 CONTRASEÑA DEL BOT: {TELEGRAM_PASSWORD}\n\n"
            "👇 Coméntame qué remedio natural quieres que investiguemos en el próximo video."
        )
        youtube.commentThreads().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id,
                              "topLevelComment": {"snippet": {"textOriginal": texto}}}}
        ).execute()
        print("✅ Comentario de contacto publicado (con contraseña)")
    except Exception as e:
        print(f"⚠️ Error comentario: {e}")

def validar_tags_youtube(tags_str):
    if not tags_str:
        return "remedios naturales, salud natural, bienestar"
    
    tags_lista = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
    tags_validos = []
    
    for tag in tags_lista:
        tag_limpio = re.sub(r'\s+', ' ', tag).strip()
        
        if len(tag_limpio) > 29:
            continue
        
        if len(tag_limpio) < 2:
            continue
            
        if not re.match(r'^[a-záéíóúüñ0-9\s]+$', tag_limpio):
            continue
        
        if "..." in tag_limpio:
            continue
            
        if tag_limpio not in tags_validos:
            tags_validos.append(tag_limpio)
    
    if len(tags_validos) < 3:
        tags_validos = ["remedios naturales", "salud natural", "bienestar"]
    
    resultado = []
    total_chars = 0
    for tag in tags_validos[:15]:
        if total_chars + len(tag) + 1 > 495:
            break
        resultado.append(tag)
        total_chars += len(tag) + 1
    
    return ", ".join(resultado)

def subir_a_youtube(video_path, titulo, tags_str, descripcion_corta, gancho, contexto, ingrediente, problema=None):
    try:
        creds = obtener_credenciales_youtube()
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None

    problema_str = f"\n🎯 Útil para: {problema}" if problema else ""
    
    tags_validados = validar_tags_youtube(tags_str)
    print(f"🏷️ Tags validados para YouTube ({len(tags_validados.split(','))} tags)")

    descripcion = f"""{gancho}

{contexto}

📲 ¿QUIERES SABER MÁS O ADQUIRIR ESTE PRODUCTO?
💬 WhatsApp: {WHATSAPP_NUMBER}
📞 Teléfono: {TELEFONO_NUMBER}
🤖 Asistente Inteligente: {TELEGRAM_BOT}
🔑 CONTRASEÑA DEL BOT: {TELEGRAM_PASSWORD}
{problema_str}

🌿 INGREDIENTE ESTRELLA: {ingrediente}

⚕️ AVISO: Este video es contenido educativo basado en la tradición herbolaria mexicana. No sustituye la consulta médica profesional.

🔍 En este Short aprenderás:
• Para qué sirve el {ingrediente} en la herbolaria mexicana
• Beneficios y propiedades tradicionales del {ingrediente}
• El producto recomendado con {ingrediente} y dónde conseguirlo

#remediosnaturales #remedioscaseros #saludnatural #medicinanatural #herbolaria #hierbasmedicinales #{ingrediente.replace(' ', '')} #shorts"""

    if ACTIVAR_DISCLOSURE_IA: descripcion += DISCLOSURE_TEXT

    body = {
        "snippet": {"title": titulo[:100], "description": descripcion[:5000],
                    "tags": [t.strip() for t in tags_validados.split(",") if t.strip()][:15],
                    "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }

    video_id = None
    for intento in range(1, 4):
        try:
            print(f"📤 Subiendo Short a YouTube (intento {intento}/3)...")
            request = youtube.videos().insert(
                part="snippet,status", 
                body=body, 
                media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
            )
            response = request.execute()
            video_id = response["id"]
            print(f"✅ Short subido con SEO viral: https://youtu.be/{video_id}")
            fijar_comentario_contacto(youtube, video_id)
            return video_id
        except Exception as e:
            error_str = str(e)
            if "502" in error_str or "503" in error_str or "504" in error_str or "Bad Gateway" in error_str:
                print(f"⚠️ Error temporal de YouTube (intento {intento}/3): {error_str[:100]}...")
                if intento < 3:
                    espera = 30 * intento
                    print(f"⏳ Esperando {espera}s antes de reintentar...")
                    time.sleep(espera)
                else:
                    print(f"❌ Falló tras 3 intentos. Error: {e}")
                    return None
            elif "invalidTags" in error_str:
                print(f"❌ Tags inválidos detectados. Error: {error_str[:200]}")
                return None
            else:
                print(f"❌ Error subiendo a YouTube: {e}")
                return None
    
    return None

# ================================================================
# 🚀 MAIN
# ================================================================
def main():
    print("🌿 Bot Herbolaria ÉLITE - YouTube Shorts (SEO VIRAL + 30 Fórmulas Variadas + Anti-Repetición)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ Ventana de publicación: 4:00 AM a 11:59 PM CDMX (excepto madrugada)")
    print(f"🔥 Motor de títulos variados ACTIVO")

    estado = cargar_estado()
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)

    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encuentra {EXCEL_FILE}")
        sys.exit(1)

    producto = seleccionar_producto_aleatorio()
    print(f"📦 Producto seleccionado: {producto.get('nombre', 'N/A')}")

    contenido = ia_genera_contenido_completo(producto)

    ingrediente_elegido = contenido["ingrediente_elegido"]
    print(f"🌱 Ingrediente elegido por IA: {ingrediente_elegido}")
    print(f"🔥 Título final: {contenido['titulo']}")

    print(f"\n🎬 Escena 1: generando imagen del ingrediente...")
    img_ingrediente = buscar_imagen_segmento_short(
        contenido.get("query_pexels", f"{ingrediente_elegido} natural healthy"),
        "img_ingrediente_short.jpg"
    )

    print(f"\n🎬 Escena 2: generando fondo del producto...")
    bg_producto = buscar_imagen_segmento_short(
        f"{ingrediente_elegido} natural healthy background",
        "bg_producto_short.jpg"
    )

    url_producto = producto["imagen_url"]

    video_path = crear_video_con_dos_imagenes_y_texto(contenido, img_ingrediente, url_producto, ingrediente_elegido, bg_producto)
    if not video_path:
        print("❌ Error creando video")
        sys.exit(1)

    video_id = subir_a_youtube(video_path, contenido["titulo"], contenido["tags"],
                               contenido["descripcion_corta"], contenido["gancho_descripcion"],
                               contenido["contexto_descripcion"], ingrediente_elegido,
                               producto.get('recomendado_para', ''))

    if video_id:
        guardar_ingrediente_usado(ingrediente_elegido, producto.get("nombre", ""))
        guardar_titulo(contenido["titulo"])
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        print(f"\n🎉 ¡Short publicado con título variado!")
        print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
        print(f"   📞 Teléfono: {TELEFONO_NUMBER}")
        print(f"   🤖 Telegram: {TELEGRAM_BOT}")
        print(f"   🔑 Contraseña del bot: {TELEGRAM_PASSWORD}")
        print(f"   🔗 URL: https://youtu.be/{video_id}")
        print(f"   📊 Publicaciones hoy: {estado['publicaciones_hoy']}/{MAX_VIDEOS_DIA}")

    for f in ["short_final.mp4", "img_ingrediente_short.jpg", "bg_producto_short.jpg"]:
        if os.path.exists(f):
            try: os.remove(f)
            except Exception: pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

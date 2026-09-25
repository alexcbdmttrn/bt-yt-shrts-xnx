import asyncio
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
# CONFIGURACIÓN ÉLITE - HERBOLARIA XANAX
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN")) if os.getenv("YOUTUBE_USER_TOKEN") else {}

WHATSAPP_NUMBER = "+52 3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"
CANAL_LINK = "https://www.youtube.com/@sombrasdemedianocheoficial"
FACEBOOK_LINK = "https://www.facebook.com/profile.php?id=61593237382982"

ESTADO_FILE = "estado_herbolaria.json"
INGREDIENTES_USADOS_FILE = "ingredientes_usados.json"
TITULOS_FILE = "titulos_herbolaria_publicados.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"

MAX_VIDEOS_DIA = 1

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ⏰ VENTANA DE PUBLICACIÓN (hora CDMX)
HORA_MIN_PUBLICAR = 9
HORA_MAX_PUBLICAR = 17

# 🛡️ LISTA AMPLIADA DE PALABRAS PROHIBIDAS (Política de salud de YouTube)
PALABRAS_PROHIBIDAS_TITULO = [
    # ─────────── 1. CLAIMS DE CURACIÓN ───────────
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

    # ─────────── 2. CLAIMS MÉDICOS NO VERIFICADOS ───────────
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

    # ─────────── 3. REEMPLAZO DE TRATAMIENTO MÉDICO ───────────
    "reemplaza", "reemplaza medicamentos", "reemplaza tu tratamiento",
    "sustituye", "sustituye medicamentos", "sustituye tu tratamiento",
    "no necesitas médico", "sin ir al médico", "olvida al doctor",
    "mejor que las pastillas", "mejor que los medicamentos",
    "olvida la medicina", "tira tus pastillas", "deja tu tratamiento",
    "sin fármacos", "sin medicamentos", "sin receta médica",
    "alternativa a medicamentos", "en vez de medicamentos",

    # ─────────── 4. PROMESAS DE TIEMPO ESPECÍFICO ───────────
    "en 24 horas", "en un día", "hoy mismo",
    "en 3 días", "en tres días",
    "en 7 días", "en una semana", "en siete días",
    "en un mes", "en 30 días",
    "esta noche", "mañana mismo",
    "al instante", "inmediatamente", "instantáneo", "instantanea",
    "resultados inmediatos", "efecto inmediato",
    "rápido y fácil", "exprés", "express",

    # ─────────── 5. SENSACIONALISMO / MIEDO ───────────
    "peligroso", "peligrosa",
    "mortal", "mortales",
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

    # ─────────── 6. TRANSFORMACIÓN EXTREMA / PESO ───────────
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

    # ─────────── 7. CLICKBAIT GENÉRICO ───────────
    "no vas a creer", "no lo vas a creer",
    "te sorprenderá", "te dejará impactado",
    "quedarás impactado", "quedarás asombrado",
    "brutal", "bestial",
    "top", "los 10 mejores", "los 5 peores",
    "lo que nadie dice", "lo que nadie sabe",
    "el mejor del mundo", "el peor del mundo",
    "definitivo", "perfecto",

    # ─────────── 8. ENFERMEDADES GRAVES ───────────
    "cáncer", "cancer", "tumor", "tumores",
    "VIH", "SIDA", "sida",
    "alzheimer", "parkinson", "esclerosis",
    "leucemia", "infarto", "derrame cerebral",
    "ictus", "metástasis",

    # ─────────── 9. OTROS PROBLEMÁTICOS ───────────
    "solución", "elimina",
    "limpiar tu cuerpo", "limpieza total del cuerpo",
]

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ================================================================
# 🌿 TEMAS VIRALES DE SALUD (Seguros)
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "natural"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales"], "busquedas": 850000, "ctr_potencial": 9.2, "retencion_objetivo": 78, "tendencia": "creciente"},
    {"tema": "remedio_casero", "keywords_cortas": ["remedio casero", "natural", "tradicional"], "keywords_largas": ["remedios caseros", "tratamiento natural"], "busquedas": 920000, "ctr_potencial": 8.8, "retencion_objetivo": 75, "tendencia": "estable"},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "evidencia"], "keywords_largas": ["estudios sobre hierbas", "evidencia tradicional"], "busquedas": 680000, "ctr_potencial": 10.5, "retencion_objetivo": 82, "tendencia": "explosiva"},
    {"tema": "alivio_natural", "keywords_cortas": ["alivio natural", "bienestar", "tradición"], "keywords_largas": ["alivio natural tradicional", "remedio mexicano"], "busquedas": 750000, "ctr_potencial": 10.8, "retencion_objetivo": 80, "tendencia": "creciente"},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "tradicional"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional"], "busquedas": 540000, "ctr_potencial": 9.8, "retencion_objetivo": 77, "tendencia": "creciente"},
]

# ================================================================
# 🎯 FÓRMULAS DE TÍTULOS ÉLITE - VARIABILIDAD TOTAL (SEGURAS)
# ================================================================
FORMULAS_TITULOS_ELITE = {
    "secreto": [
        "El secreto del {ingrediente} que pocos conocen",
        "El poder oculto del {ingrediente}",
        "Lo que nadie te cuenta sobre el {ingrediente}",
    ],
    "pregunta": [
        "¿Sabías esto del {ingrediente}?",
        "¿Puede el {ingrediente} apoyar en {problema}?",
        "¿Conocías el {ingrediente}?",
        "¿Por qué deberías usar {ingrediente}?",
    ],
    "beneficio": [
        "{numero} beneficios del {ingrediente} que ignorabas",
        "Así apoya el {ingrediente} en tu {beneficio}",
        "{ingrediente}: El aliado para {beneficio}",
    ],
    "como_usar": [
        "Cómo usar {ingrediente} para {beneficio}",
        "{numero} formas de usar {ingrediente}",
        "La mejor forma de usar {ingrediente}",
    ],
    "verdad": [
        "La verdad sobre el {ingrediente}",
        "Lo que nadie sabe del {ingrediente}",
        "Mitos y verdades del {ingrediente}",
    ],
    "por_que": [
        "Por qué funciona el {ingrediente}",
        "Por qué deberías probar {ingrediente}",
        "Por qué el {ingrediente} es efectivo",
    ],
    "errores": [
        "{numero} errores al usar {ingrediente}",
        "No cometas este error con {ingrediente}",
    ],
    "comparacion": [
        "{ingrediente} vs {problema}: ¿Funciona?",
        "Antes y después de usar {ingrediente}",
    ],
    "tradicion": [
        "{ingrediente}: por qué la tradición herbal lo usa",
        "El papel del {ingrediente} en la herbolaria",
        "{ingrediente}: lo que tu abuela ya sabía",
    ],
}

# ================================================================
# 🎤 VOCES NEURALES PREMIUM
# ================================================================
VOCES_DISPONIBLES = [
    {"voz": "es-MX-DaliaNeural", "velocidad": "+10%", "tono": "+1Hz", "estilo": "claro"},
    {"voz": "es-MX-JorgeNeural", "velocidad": "+8%", "tono": "0Hz", "estilo": "profesional"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+12%", "tono": "+2Hz", "estilo": "entusiasta"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+10%", "tono": "+1Hz", "estilo": "natural"},
    {"voz": "es-AR-ElenaNeural", "velocidad": "+9%", "tono": "+1Hz", "estilo": "cálido"},
]
CONFIG_VOZ_ACTUAL = random.choice(VOCES_DISPONIBLES)

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
        with open(TITULOS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def sanitizar_titulo(titulo, ingrediente):
    """Si el título trae claims médicos prohibidos, lo reemplaza por una fórmula segura."""
    lower = (titulo or "").lower()
    if any(p in lower for p in PALABRAS_PROHIBIDAS_TITULO):
        plantillas = [
            f"{ingrediente}: por qué la tradición herbal lo usa",
            f"3 beneficios del {ingrediente} según la herbolaria",
            f"Cómo se usa el {ingrediente} en la medicina tradicional",
            f"{ingrediente}: lo que tu abuela ya sabía de esta planta",
            f"El papel del {ingrediente} en tu bienestar diario",
            f"¿Sabías esto del {ingrediente}?",
            f"{ingrediente}: el aliado tradicional que vale la pena conocer",
            f"Por qué la herbolaria mexicana usa el {ingrediente}",
            f"{ingrediente}: usos y beneficios en la tradición natural",
        ]
        nuevo = random.choice(plantillas)
        print(f"🛡️ Título con claim riesgoso detectado → reemplazado: {nuevo}")
        return nuevo[:70]
    return (titulo or "")[:70]

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

    # ⏰ Solo publicar dentro de la ventana 9:00-17:00 CDMX
    forzar = os.getenv("FORZAR_PUBLICACION", "0") == "1"
    if not forzar and not (HORA_MIN_PUBLICAR <= ahora.hour < HORA_MAX_PUBLICAR):
        print(f"⏰ Fuera de ventana horaria ({ahora.hour}h CDMX). Solo publico entre {HORA_MIN_PUBLICAR}:00 y {HORA_MAX_PUBLICAR}:00.")
        return False

    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff = (ahora - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(3, 5)  # Entre 3-5 horas entre shorts
        if diff < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h (han pasado {diff:.1f}h).")
            return False
    return True

# ================================================================
#  IA GENERA CONTENIDO COMPLETO CON SEO AVANZADO
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

    tema_viral = random.choice(TEMAS_VIRALES_SALUD)
    
    # Lista de prohibidas formateada para el prompt
    prohibidas_str = ", ".join(f'"{p}"' for p in PALABRAS_PROHIBIDAS_TITULO[:40]) + "..."

    prompt = f"""Eres un experto en herbolaria, nutrición y SEO para YouTube Shorts creando contenido VIRAL y SEGURO.

📦 INFORMACIÓN COMPLETA DEL PRODUCTO:
{producto_info}

🎯 TEMA VIRAL: {tema_viral['tema'].upper()}

🧠 ANÁLISIS REQUERIDO:
1. ANALIZA los ingredientes y ELIGE el mejor ingrediente REAL (NO uses "sabor X", usa el nombre real: si dice "Sabor Piña", el ingrediente es "PIÑA")
2. Genera TODO el contenido optimizado para SEO

📋 CONTENIDO A GENERAR (Devuelve ESTRICTAMENTE este JSON):

{{
    "ingrediente_elegido": "Nombre real del ingrediente (ej: Piña, no Sabor Piña)",
    "titulo": "Título viral corto con hashtags (máx 70 chars, usa fórmulas variadas y 100% SEGURAS)",
    "guion_segmento_1": "Texto de 25 segundos sobre el ingrediente (65-75 palabras). Inicia con pregunta impactante. Menciona 2-3 beneficios según la tradición. NO menciones el producto ni contacto. Incluye frase: 'esto es información educativa basada en la tradición herbolaria'.",
    "guion_segmento_2": "Texto de 20 segundos presentando el producto (50-60 palabras). Menciona el nombre del producto y que contiene el ingrediente. DEBE terminar exactamente con: '¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp al número en la descripción, o a nuestro asesor inteligente de telegram'",
    "tags": "tag1, tag2, tag3 (10-15 tags incluyendo keywords: {', '.join(tema_viral['keywords_cortas'][:2])}, {', '.join(tema_viral['keywords_largas'][:1])})",
    "descripcion_corta": "Descripción SEO del video (máx 120 caracteres, sin claims médicos)",
    "gancho_descripcion": "Gancho inicial para descripción (máx 90 caracteres, sin claims médicos)",
    "contexto_descripcion": "Contexto adicional educativo (1 oración)",
    "query_pexels": "Query en inglés para buscar imagen del ingrediente en Pexels (ej: 'pineapple fruit fresh healthy')"
}}

⚠️ REGLAS CRÍTICAS:
- El ingrediente_elegido debe ser el nombre REAL
- El Segmento 2 DEBE terminar con la frase exacta de contacto
- El título debe incluir hashtags y ser variado (NO siempre "El secreto de...")
- query_pexels debe ser en inglés y específico
- El guion DEBE incluir un disclaimer natural como "esto es información educativa basada en la tradición herbolaria, no sustituye la consulta médica"

🚨 POLÍTICA DE SALUD DE YOUTUBE (CRÍTICO — ESTO EVITA BANNEO DEL CANAL):
NUNCA uses en TÍTULO, GUION, NI DESCRIPCIÓN ninguna de estas palabras o conceptos:
{prohibidas_str}

TAMPOCO uses:
- Claims de curación absoluta ("cura", "sana", "elimina para siempre", "adiós a X", "milagrosa")
- Promesas de tiempo ("en 7 días", "en 24 horas", "hoy mismo", "inmediatamente")
- Reemplazo de tratamiento ("sustituye medicamentos", "mejor que pastillas", "sin ir al médico")
- Claims médicos no verificados ("clínicamente probado", "avalado por la FDA", "100% efectivo")
- Sensacionalismo ("peligroso", "mortal", "asesino silencioso", "conspiración")
- Transformación extrema ("pierde 10 kilos", "rejuvenece 20 años", "eterna juventud")
- Enfermedades graves en títulos (cáncer, VIH, alzheimer, parkinson)

✅ MARCOS SEGUROS que SÍ debes usar:
- "apoya", "favorece", "contribuye al bienestar", "alivia tradicionalmente"
- "uso en la herbolaria", "la tradición popular indica", "según la medicina tradicional"
- "aliado natural", "complemento para", "parte de un estilo de vida saludable"
- "¿sabías que...?", "por qué se usa", "3 beneficios tradicionales"

Ejemplos de TÍTULOS SEGUROS:
- "Aloe Vera: por qué la tradición lo usa en golpes y moretones #aloe #herbolaria"
- "¿Sabías esto del nopal? El aliado de tu abuela #nopal #saludnatural"
- "Cúrcuma: beneficios que ignorabas según la herbolaria #curcuma #bienestar"
- "Por qué funciona la manzanilla en la tradición mexicana #manzanilla #remedios"
"""

    for intento in range(6):
        try:
            print(f"🤖 IA analizando producto... (intento {intento+1}/6)")
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.85, "max_tokens": 1200, "response_format": {"type": "json_object"}}, timeout=90)
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

            # ✅ SANITIZAR TÍTULO
            ingrediente = data["ingrediente_elegido"]
            titulo = data.get("titulo", "").strip()
            data["titulo"] = sanitizar_titulo(titulo, ingrediente)

            # Asegurar hashtags
            titulo = data["titulo"]
            if "#" not in titulo or len(titulo) > 75:
                hashtags = [f"#{ingrediente.replace(' ', '').lower()}", "#saludnatural", "#herbolaria"]
                formulas_variadas = [
                    f"El secreto del {ingrediente}",
                    f"¿Sabías esto del {ingrediente}?",
                    f"{ingrediente}: Beneficios que ignorabas",
                    f"Por qué funciona el {ingrediente}",
                    f"Cómo usar {ingrediente}",
                    f"{ingrediente}: lo que tu abuela ya sabía",
                ]
                titulo_base = random.choice(formulas_variadas)
                titulo = f"{titulo_base} {' '.join(hashtags[:2])}"
            data["titulo"] = titulo[:70]

            # 🛡️ Sanitizar tags por si la IA mete palabras prohibidas
            if "tags" in data and data["tags"]:
                tags_lista = [t.strip() for t in data["tags"].split(",") if t.strip()]
                tags_limpia = [t for t in tags_lista if not any(p in t.lower() for p in PALABRAS_PROHIBIDAS_TITULO)]
                # Agregar keywords del tema si faltan
                for kw in tema_viral.get("keywords_cortas", [])[:2]:
                    if kw.lower() not in [t.lower() for t in tags_limpia]: tags_limpia.append(kw)
                for kw in tema_viral.get("keywords_largas", [])[:1]:
                    if kw.lower() not in [t.lower() for t in tags_limpia]: tags_limpia.append(kw)
                for ext in [ingrediente.lower(), "salud natural", "bienestar", "herbolaria"]:
                    if ext not in tags_limpia and len(tags_limpia) < 15: tags_limpia.append(ext)
                data["tags"] = ", ".join(tags_limpia[:15])
            else:
                tags_limpia = [ingrediente.lower(), "salud natural", "bienestar", "herbolaria", "remedios naturales"]
                data["tags"] = ", ".join(tags_limpia[:15])

            if "query_pexels" not in data:
                data["query_pexels"] = f"{ingrediente} natural healthy"

            print(f"✅ IA generó contenido exitosamente")
            print(f"   🌱 Ingrediente: {data['ingrediente_elegido']}")
            print(f"   📝 Título: {data['titulo']}")
            print(f"   🔍 Query Pexels: {data['query_pexels']}")

            return data

        except Exception as e:
            print(f"❌ Intento {intento+1} falló: {e}")
            if intento == 5:
                print("❌ Todos los intentos de IA fallaron")
                sys.exit(1)
            time.sleep(5)

# ================================================================
# 🖼️ IMÁGENES Y VIDEO CON TEXTO EN ÚLTIMOS 15 SEGUNDOS
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

async def generar_audio(texto, path):
    texto_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\'\"]', '', texto)
    try:
        await edge_tts.Communicate(texto_limpio, CONFIG_VOZ_ACTUAL["voz"], rate=CONFIG_VOZ_ACTUAL["velocidad"]).save(path)
        return path
    except Exception as e:
        print(f"⚠️ Error audio: {e}")
        return None

def crear_imagen_texto_cta(texto, ancho=1080, alto=220):
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    tamano_fuente = 55
    fuente = None
    rutas_fuente = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for ruta in rutas_fuente:
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

def crear_video_con_dos_imagenes_y_texto(guion, url_ingrediente, url_producto, ingrediente):
    print("🎬 Renderizando video con 2 escenas + TEXTO FINAL...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio1 = loop.run_until_complete(generar_audio(guion["guion_segmento_1"], "seg1.mp3"))
    audio2 = loop.run_until_complete(generar_audio(guion["guion_segmento_2"], "seg2.mp3"))
    loop.close()

    if not audio1 or not audio2: return None

    clip1, clip2 = AudioFileClip(audio1), AudioFileClip(audio2)
    audio_total = concatenate_audioclips([clip1, clip2])
    duracion_seg1 = clip1.duration
    duracion_seg2 = clip2.duration
    duracion_total = duracion_seg1 + duracion_seg2

    clips_video = []

    # ESCENA 1: Ingrediente (0-25s)
    try:
        r = requests.get(url_ingrediente, timeout=15)
        img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((1080, 1920))
        img.save("temp_ingrediente.jpg")

        video_ingrediente = ImageClip("temp_ingrediente.jpg").set_duration(duracion_seg1)
        video_ingrediente = video_ingrediente.resize(lambda t: 1 + 0.03 * (t / duracion_seg1))
        clips_video.append(video_ingrediente)
        print("✅ Escena 1: Imagen del ingrediente cargada")
    except Exception as e:
        print(f"⚠️ Error con imagen de ingrediente: {e}")

    # ESCENA 2: Producto RECORTADO sobre Fondo Bonito (25-45s)
    try:
        print("   🎨 Preparando escena del producto recortado...")
        url_fondo = buscar_imagen_pexels_salud(f"{ingrediente} natural healthy background")
        r_fondo = requests.get(url_fondo, timeout=15)
        fondo = Image.open(io.BytesIO(r_fondo.content)).convert("RGB").resize((1080, 1920))

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
        print("✅ Escena 2: Producto recortado sobre fondo profesional cargado")
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

    # Unir videos
    video_final = concatenate_videoclips(clips_video, method="compose")

    # 🎵 MEZCLA DE AUDIO CON MÚSICA
    print("\n🔍 Buscando archivos de música...")
    todos_archivos = os.listdir(".")
    mp3_files = [f for f in todos_archivos if f.lower().endswith(".mp3")]
    print(f"   📂 Archivos .mp3 encontrados: {mp3_files}")

    musicas = []
    for f in mp3_files:
        if f.startswith("seg"):
            print(f"   ⏭️ Saltando {f} (es audio generado)")
            continue
        tamano = os.path.getsize(f)
        print(f"   📄 {f}: {tamano} bytes")
        if tamano > 100:
            musicas.append(f)

    print(f"   ✅ Música válida: {musicas}")

    musica_aplicada = False
    if musicas:
        for musica_path in musicas:
            try:
                print(f"   🎵 Probando música: {musica_path}")
                musica = AudioFileClip(musica_path)
                print(f"      Duración: {musica.duration}s")
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

    # AGREGAR TEXTO CTA + AVISO LEGAL
    print("\n✍️ Agregando overlays...")
    try:
        clips_overlays = [video_final]
        
        # Aviso legal al inicio (5 segundos)
        aviso = crear_overlay_aviso()
        if aviso:
            av_clip = ImageClip(aviso, transparent=True).set_start(0).set_duration(5)
            clips_overlays.append(av_clip)
            print("✅ Aviso legal agregado")
        
        # Texto CTA en últimos 15 segundos
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
# 📤 SUBIR A YOUTUBE
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
            "🌿 ¿Dudas o quieres adquirir este producto? Escríbenos:\n"
            f"📲 WhatsApp: {WHATSAPP_NUMBER}\n"
            f"🤖 Asistente inteligente en Telegram: {TELEGRAM_BOT}\n"
            "👇 Coméntame qué remedio natural quieres que investiguemos en el próximo video."
        )
        youtube.commentThreads().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id,
                              "topLevelComment": {"snippet": {"textOriginal": texto}}}}
        ).execute()
        print("✅ Comentario de contacto publicado")
    except Exception as e:
        print(f"⚠️ Error comentario: {e}")

def subir_a_youtube(video_path, titulo, tags_str, descripcion_corta, gancho, contexto, ingrediente):
    try:
        creds = obtener_credenciales_youtube()
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None

    descripcion = f"""{gancho}

{contexto}

🌿 INGREDIENTE ESTRELLA: {ingrediente}

⚕️ AVISO: Este video es contenido educativo basado en la tradición herbolaria mexicana. No sustituye la consulta médica profesional.

📲 ¿QUIERES SABER MÁS O ADQUIRIR ESTE PRODUCTO?
💬 Contáctanos directamente por WhatsApp: {WHATSAPP_NUMBER}
🤖 O contacta a nuestro Asesor Inteligente en Telegram: {TELEGRAM_BOT}

🔗 Más contenido en nuestro canal: {CANAL_LINK}
📘 Síguenos en Facebook: {FACEBOOK_LINK}

#{' #'.join([t.strip() for t in tags_str.split(',')[:5]])} #Shorts #SaludNatural #Herbolaria #{ingrediente.replace(' ', '')}"""

    if ACTIVAR_DISCLOSURE_IA: descripcion += DISCLOSURE_TEXT

    body = {
        "snippet": {"title": titulo[:100], "description": descripcion[:5000], "tags": [t.strip() for t in tags_str.split(",")][:15], "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }

    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True))
        response = request.execute()
        video_id = response["id"]
        print(f"✅ Short subido: https://youtu.be/{video_id}")
        
        fijar_comentario_contacto(youtube, video_id)
        
        return video_id
    except Exception as e:
        print(f"❌ Error subiendo a YouTube: {e}")
        return None

# ================================================================
# 🚀 MAIN
# ================================================================
def main():
    print("🌿 Bot Herbolaria ÉLITE - YouTube Shorts (Blindado contra políticas)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎤 Voz: {CONFIG_VOZ_ACTUAL['voz']} ({CONFIG_VOZ_ACTUAL['estilo']})")

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
    print(f"📝 Título: {contenido['titulo']}")

    query_pexels = contenido.get("query_pexels", f"{ingrediente_elegido} natural healthy")
    url_ingrediente = buscar_imagen_pexels_salud(query_pexels)
    print(f"🔍 Imagen del ingrediente: {url_ingrediente[:80]}...")

    url_producto = producto["imagen_url"]

    video_path = crear_video_con_dos_imagenes_y_texto(contenido, url_ingrediente, url_producto, ingrediente_elegido)
    if not video_path:
        print("❌ Error creando video")
        sys.exit(1)

    video_id = subir_a_youtube(video_path, contenido["titulo"], contenido["tags"], contenido["descripcion_corta"], contenido["gancho_descripcion"], contenido["contexto_descripcion"], ingrediente_elegido)

    if video_id:
        guardar_ingrediente_usado(ingrediente_elegido, producto.get("nombre", ""))
        guardar_titulo(contenido["titulo"])
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        print(f"\n🎉 ¡Publicado exitosamente!")
        print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
        print(f"   🤖 Telegram: {TELEGRAM_BOT}")
        print(f"   🔗 URL: https://youtu.be/{video_id}")
        print(f"   📊 Publicaciones hoy: {estado['publicaciones_hoy']}/{MAX_VIDEOS_DIA}")

    if os.path.exists("short_final.mp4"):
        os.remove("short_final.mp4")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

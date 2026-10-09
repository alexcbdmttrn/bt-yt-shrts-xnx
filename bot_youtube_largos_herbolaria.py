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
import numpy as np
import urllib.parse
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
import requests
import edge_tts
import pytz
import urllib3
from rembg import remove

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
# CONFIGURACIÓN - VIDEOS LARGOS HERBOLARIA (HORIZONTAL 16:9)
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN")) if os.getenv("YOUTUBE_USER_TOKEN") else {}

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

WHATSAPP_NUMBER = "+52 3123395334"
TELEFONO_NUMBER = "3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"
TELEGRAM_PASSWORD = "A"

ESTADO_FILE = "estado_largos_herbolaria.json"
INGREDIENTES_LARGOS_FILE = "ingredientes_largos_usados.json"
TITULOS_FILE = "titulos_largos_publicados.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES = "catalogo_curiosidades_salud.json"

ANCHO, ALTO = 1920, 1080

MAX_LARGOS_DIA = 1
INTERVALO_MIN_HORAS = 20
INTERVALO_MAX_HORAS = 26
RETRASO_MAX_MINUTOS = 30
PAUSA_ENTRE_SEGMENTOS = 0.5

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

HORA_MIN_PUBLICAR = 9
HORA_MAX_PUBLICAR = 17

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

TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "remedios naturales", "para qué sirve"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales de las hierbas", "remedios naturales efectivos"], "ctr_potencial": 9.2},
    {"tema": "remedio_casero", "keywords_cortas": ["remedios caseros", "natural", "tradición", "hierbas medicinales"], "keywords_largas": ["remedios caseros efectivos", "tratamiento natural con hierbas", "remedios de la abuela"], "ctr_potencial": 9.5},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "evidencia"], "keywords_largas": ["estudios sobre hierbas", "evidencia tradicional"], "ctr_potencial": 10.5},
    {"tema": "alivio_natural", "keywords_cortas": ["alivio natural", "bienestar", "medicina natural", "plantas medicinales"], "keywords_largas": ["alivio natural tradicional", "remedios mexicanos para el bienestar", "hierbas que alivian"], "ctr_potencial": 10.8},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "herbolaria mexicana", "tradición"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional mexicana", "herbolaria que pocos conocen"], "ctr_potencial": 9.8},
]

VOCES_DISPONIBLES = [
    {"voz": "es-MX-JorgeNeural", "velocidad": "+10%", "estilo": "profesional"},
    {"voz": "es-MX-DaliaNeural", "velocidad": "+10%", "estilo": "claro"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+12%", "estilo": "entusiasta"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+10%", "estilo": "natural"},
    {"voz": "es-AR-ElenaNeural", "velocidad": "+9%", "estilo": "cálido"},
]

# ================================================================
# 🧠 ESTADO Y ANTI-REPETICIÓN
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"publicaciones_hoy": 0, "fecha": None, "ultima_publicacion": None}

def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f: json.dump(estado, f, indent=2, ensure_ascii=False)

def cargar_ingredientes_largos_usados():
    try:
        with open(INGREDIENTES_LARGOS_FILE, "r", encoding="utf-8") as f: return json.load(f).get("ingredientes", [])
    except: return []

def guardar_ingrediente_largo_usado(ingrediente, producto):
    data = {"ingredientes": cargar_ingredientes_largos_usados()}
    entry = f"{ingrediente}|{producto}"
    if entry not in data["ingredientes"]:
        data["ingredientes"].append(entry)
    with open(INGREDIENTES_LARGOS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def reiniciar_ingredientes_largos():
    with open(INGREDIENTES_LARGOS_FILE, "w", encoding="utf-8") as f: json.dump({"ingredientes": []}, f)

def cargar_titulos():
    try:
        with open(TITULOS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"titulos": []}

def guardar_titulo(titulo):
    data = cargar_titulos()
    if titulo not in data["titulos"]:
        data["titulos"].append(titulo)
        with open(TITULOS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

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
    if not forzar and not (HORA_MIN_PUBLICAR <= ahora.hour < HORA_MAX_PUBLICAR):
        print(f"⏰ Fuera de ventana horaria ({ahora.hour}h CDMX). Solo publico entre {HORA_MIN_PUBLICAR}:00 y {HORA_MAX_PUBLICAR}:00.")
        return False

    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff = (ahora - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(INTERVALO_MIN_HORAS, INTERVALO_MAX_HORAS)
        if diff < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h (han pasado {diff:.1f}h).")
            return False
    retraso = random.randint(0, RETRASO_MAX_MINUTOS * 60)
    if retraso > 0:
        print(f"⏳ Retraso aleatorio: {retraso//60} min...")
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
        if not ingredientes: continue
        ingrediente = random.choice(ingredientes)
        if f"{ingrediente}|{producto['nombre']}" not in usados:
            print(f"✅ Par elegido: {ingrediente} → {producto['nombre']}")
            return producto, ingrediente

    print("🔄 Pool de ingredientes agotado en largos. Reiniciando historial...")
    reiniciar_ingredientes_largos()
    producto = df.sample(1).iloc[0].to_dict()
    ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",") if i.strip()]
    return producto, random.choice(ingredientes)

def cargar_json_catalogo(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
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
                    if isinstance(val, list): val = ", ".join(map(str, val))
                    partes.append(f"{clave}: {val}")
            return " | ".join(partes)
    return ""

def obtener_curiosidad_catalogo(ingrediente):
    curios = cargar_json_catalogo(CATALOGO_CURIOSIDADES)
    if not curios: return ""
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

def optimizar_titulo_largo(titulo_ia, ingrediente, problema=None):
    t = re.sub(r'#\w+', '', (titulo_ia or "").strip()).strip()
    lower = t.lower()

    if any(p in lower for p in PALABRAS_PROHIBIDAS_TITULO):
        print("🛡️ Título con palabra prohibida → reemplazando por fórmula viral segura...")
        t = ""

    keywords_presentes = ["remedios", "salud natural", "medicina natural", "hierbas",
                          "para qué sirve", "beneficios", "propiedades", "cómo usar",
                          "herbolaria", "plantas medicinales", "remedio casero",
                          "tradición", "sabías", "aliado", "apoya", "usos"]
    if not t or not any(kw in t.lower() for kw in keywords_presentes):
        patrones = [
            f"Para qué sirve el {ingrediente} en remedios naturales",
            f"Beneficios del {ingrediente} en la herbolaria mexicana",
            f"Remedios caseros con {ingrediente}: usos tradicionales",
            f"Cómo usar el {ingrediente} como remedio natural",
            f"Propiedades del {ingrediente} que pocos conocen",
            f"{ingrediente}: aliado natural para tu bienestar",
            f"Medicina natural: el poder del {ingrediente}",
            f"Salud natural: secretos del {ingrediente}",
            f"{ingrediente} y sus beneficios para la salud",
            f"Remedios naturales con {ingrediente}: tradición mexicana",
            f"¿Sabías esto del {ingrediente}? Usos y beneficios",
        ]
        if problema:
            patrones.extend([
                f"Remedios naturales con {ingrediente} para {problema}",
                f"{ingrediente}: aliado natural para {problema}",
                f"Cómo usar {ingrediente} para {problema} (remedio casero)",
                f"Para qué sirve el {ingrediente} en {problema}",
            ])
        t = random.choice(patrones)
        print(f"🔥 Keyword viral inyectada en título: {t}")
    return t[:70]

# ================================================================
# 🎯 CLASIFICADOR DE INGREDIENTES (evita tags inválidos)
# ================================================================
def clasificar_ingrediente(ingrediente):
    """
    Detecta qué tipo de ingrediente es para evitar generar tags absurdos
    como "planta omega 3" o "té de colágeno".
    """
    ing_lower = ingrediente.lower()
    
    # Ácidos grasos, aceites y nutrientes
    aceites_grasas = ["omega", "dha", "epa", "ácido graso", "aceite de pescado",
                     "aceite de krill", "linaza", "chía", "linoleico"]
    if any(k in ing_lower for k in aceites_grasas):
        return "lipido"
    
    # Proteínas, colágenos, aminoácidos
    proteinas = ["colágeno", "colageno", "proteína", "proteina", "aminoácido", 
                 "aminoacido", "whey", "creatina", "bcaa", "arginina", "glicina"]
    if any(k in ing_lower for k in proteinas):
        return "proteina"
    
    # Vitaminas y minerales
    vitaminas = ["vitamina", "vit ", "vit.", "ácido fólico", "acido folico", 
                 "biotina", "retinol", "tiamina", "riboflavina"]
    minerales = ["magnesio", "zinc", "hierro", "calcio", "potasio", "selenio", 
                 "cromo", "yodo", "cobre", "manganeso"]
    if any(k in ing_lower for k in vitaminas + minerales):
        return "micronutriente"
    
    # Frutas
    frutas = ["naranja", "limón", "limon", "fresa", "manzana", "plátano", "platano",
              "piña", "piña", "mango", "papaya", "arándano", "arandano", "uva",
              "sandía", "sandia", "kiwi", "guayaba", "granada", "cereza", "ciruela",
              "durazno", "chabacano", "tamarindo", "coco", "jitomate"]
    if any(k in ing_lower for k in frutas):
        return "fruta"
    
    # Hongos, levaduras, probióticos
    hongos_probioticos = ["hongo", "reishi", "shiitake", "melena de león", 
                         "cordyceps", "levadura", "probiótico", "probiotico", 
                         "lactobacillus", "bifidobacterium"]
    if any(k in ing_lower for k in hongos_probioticos):
        return "probiotico"
    
    # Raíces, tubérculos, especias (NO son "hierbas" en sentido estricto)
    raices = ["cúrcuma", "curcuma", "jengibre", "ginseng", "maca", "ashwagandha",
              "valeriana", "regaliz", "alcachofa", "betabel", "remolacha", "camote"]
    if any(k in ing_lower for k in raices):
        return "raiz"
    
    # Por defecto: planta/herbolaria
    return "planta"

# ================================================================
# 🎯 GENERADOR DE TAGS SEO ELITE (CORREGIDO - sin tags inválidos)
# ================================================================
def generar_tags_seo_elite(ingrediente, problema, titulo, tema_viral=None):
    """
    Genera tags optimizados para YouTube:
    - Cada tag <= 30 caracteres (regla de YouTube)
    - Sin tags absurdos (ej: "planta omega 3" cuando Omega 3 no es planta)
    - Validación final para evitar rechazo de YouTube
    """
    tags = []
    ing_lower = ingrediente.lower().strip()
    tipo = clasificar_ingrediente(ingrediente)
    
    print(f"   🎯 Ingrediente clasificado como: {tipo}")
    
    # ============================================================
    # 1) TAGS CORTOS ESPECÍFICOS (siempre válidos)
    # ============================================================
    tags.append(ing_lower)  # "omega 3"
    
    # ============================================================
    # 2) TAGS SEGÚN TIPO DE INGREDIENTE
    # ============================================================
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
            f"omega 3 natural",
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
    
    # ============================================================
    # 3) TAGS DE PROPIEDADES/BENEFICIOS (universales)
    # ============================================================
    tags.extend([
        f"beneficios de {ing_lower}",
        f"propiedades de {ing_lower}",
        f"para qué sirve {ing_lower}",
    ])
    
    # ============================================================
    # 4) TAGS LONG-TAIL (búsquedas reales)
    # ============================================================
    tags.extend([
        f"{ing_lower} en remedios naturales",
        f"{ing_lower} usos y beneficios",
    ])
    
    # ============================================================
    # 5) TAGS DE SÍNTOMAS/PROBLEMAS (cada uno individual)
    # ============================================================
    if problema:
        problemas_individuales = [p.strip() for p in str(problema).split(",") if p.strip()]
        for prob in problemas_individuales[:5]:
            prob_limpio = prob.lower().strip()
            if 3 < len(prob_limpio) <= 28:
                tags.append(prob_limpio)
                tag_rem = f"{ing_lower} para {prob_limpio}"
                if len(tag_rem) <= 30:
                    tags.append(tag_rem)
    
    # ============================================================
    # 6) TAGS GENERALES DEL NICHO
    # ============================================================
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
    
    # Solo agregar "herbolaria mexicana" y similares si aplica
    if tipo == "planta":
        tags_generales.extend([
            "herbolaria mexicana",
            "plantas medicinales",
            "hierbas medicinales",
            "tradición mexicana",
        ])
    
    tags.extend(tags_generales)
    
    # ============================================================
    # 7) TAGS DEL TÍTULO (extraídos automáticamente)
    # ============================================================
    if titulo:
        palabras_titulo = [p.lower() for p in re.findall(r'\w+', titulo) if 4 < len(p) <= 20]
        for p in palabras_titulo[:4]:
            if p not in [t.lower() for t in tags]:
                tags.append(p)
    
    # ============================================================
    # 8) TAGS DEL TEMA VIRAL
    # ============================================================
    if tema_viral:
        for kw in tema_viral.get("keywords_cortas", [])[:2]:
            kw_l = kw.lower()
            if len(kw_l) <= 30 and kw_l not in [t.lower() for t in tags]:
                tags.append(kw_l)
    
    # ============================================================
    # 9) LIMPIEZA + VALIDACIÓN FINAL (CRÍTICO)
    # ============================================================
    tags_unicos = []
    vistos = set()
    for tag in tags:
        # Normalizar
        tag_limpio = re.sub(r'\s+', ' ', tag.strip().lower())
        
        # REGLAS DE YOUTUBE (evitar invalidTags):
        # 1. Longitud máxima por tag: 30 caracteres
        if len(tag_limpio) > 30:
            continue
        # 2. Longitud mínima: 2 caracteres
        if len(tag_limpio) < 2:
            continue
        # 3. Solo letras, números y espacios (sin caracteres raros)
        if not re.match(r'^[a-záéíóúüñ0-9\s]+$', tag_limpio):
            continue
        # 4. No palabras prohibidas
        if any(p in tag_limpio for p in PALABRAS_PROHIBIDAS_TITULO[:50]):
            continue
        # 5. No duplicados
        if tag_limpio in vistos:
            continue
            
        tags_unicos.append(tag_limpio)
        vistos.add(tag_limpio)
    
    # ============================================================
    # 10) RESPETAR LÍMITE DE 500 CARACTERES TOTALES
    # ============================================================
    resultado = []
    total_chars = 0
    for tag in tags_unicos:
        if total_chars + len(tag) + 1 > 495:
            break
        resultado.append(tag)
        total_chars += len(tag) + 1
    
    # Validación final: mínimo 3 tags, máximo 30
    if len(resultado) < 3:
        resultado = ["remedios naturales", "salud natural", ingrediente.lower()][:3]
    
    return ", ".join(resultado[:30])

def generar_tags_virales(ingrediente, problema=None, tema_viral=None):
    return generar_tags_seo_elite(ingrediente, problema, "", tema_viral)

# ================================================================
# 🤖 IA GENERA GUION
# ================================================================
def ia_genera_guion_largo(producto, ingrediente, tema_viral):
    info_catalogo = obtener_info_ingrediente_catalogo(ingrediente) or "Sin ficha en catálogo; usa conocimiento general verificado."
    curiosidad = obtener_curiosidad_catalogo(ingrediente) or ""
    problema = producto.get('recomendado_para', '')
    keywords_virales_prompt = obtener_keywords_aleatorias_virales(8)
    prohibidas_str = ", ".join(f'"{p}"' for p in PALABRAS_PROHIBIDAS_TITULO[:40]) + "..."

    prompt = f"""Eres guionista experto en salud natural, SEO para YouTube y herbolaria mexicana. Creas videos LARGOS (3 a 4 minutos máximo, horizontal) OPTIMIZADOS para búsquedas virales y 100% SEGUROS ante las políticas de YouTube.

📦 PRODUCTO COMPLETO:
NOMBRE: {producto.get('nombre')}
PRESENTACIÓN: {producto.get('presentacion')}
RECOMENDADO PARA: {problema}
INGREDIENTES CLAVE: {producto.get('ingredientes_clave')}
BENEFICIOS: {producto.get('beneficios')}
MODO DE EMPLEO: {producto.get('MODO DE EMPLEO / DOSIS')}

🌱 INGREDIENTE ESTRELLA OBLIGATORIO (NO lo cambies): {ingrediente}
📚 FICHA DEL CATÁLOGO DEL INGREDIENTE: {info_catalogo}
💡 DATO CURIOSO DEL CATÁLOGO (úsalo en el hook o en un beneficio): {curiosidad}
🎯 TEMA VIRAL DE ESTE VIDEO: {tema_viral['tema'].upper()} (keywords: {', '.join(tema_viral['keywords_cortas'])})
💊 PROBLEMA QUE RESUELVE: {problema}

🔑 KEYWORDS VIRALES DE ALTO VOLUMEN QUE DEBES USAR:
{', '.join(keywords_virales_prompt)}

⚠️ IMPORTANTE: DURACIÓN OBJETIVO 3 A 4 MINUTOS.
Sé directo, conciso y evita relleno. Cada palabra cuenta. Respeta estrictamente los conteos de palabras.

🎬 ESTRUCTURA OBLIGATORIA (8 segmentos, ~3:30 minutos reales):
1. "hook" (35-45 palabras): Pregunta o dato impactante del ingrediente (usa el dato curioso). INCLUYE una keyword viral.
2. "problema" (65-80 palabras): El problema/síntoma que sufre la audiencia ({problema}).
3. "ingrediente" (95-110 palabras): Presenta el ingrediente estrella, origen breve.
4. "beneficio_1" (65-80 palabras): Primer beneficio según la tradición.
5. "beneficio_2" (65-80 palabras): Segundo beneficio.
6. "beneficio_3" (65-80 palabras): Tercer beneficio.
7. "producto" (120-140 palabras): Presenta {producto.get('nombre')}, cómo contiene el ingrediente y modo de empleo.
8. "cta" (100-120 palabras): Resumen breve + DEBE terminar EXACTAMENTE con: "¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

REGLAS GENERALES:
- Si el ingrediente suena a saborizante, habla del ingrediente REAL.
- NO digas números de WhatsApp/Telegram en el audio (solo la frase final del cta).
- Tono educativo, cálido y cercano. Sin emojis en el texto hablado.
- Incluye SIEMPRE un disclaimer natural: "esto es información educativa basada en la tradición herbolaria, no sustituye la consulta médica".
- Cada segmento incluye "texto_pantalla" (MÁX 3-4 palabras) y "query_pexels" (en inglés, descripción visual horizontal 16:9).

🚨 POLÍTICA DE SALUD DE YOUTUBE (CRÍTICO):
NUNCA uses:
{prohibidas_str}

✅ MARCOS SEGUROS:
- "apoya", "favorece", "contribuye al bienestar", "alivia tradicionalmente"
- "aliado natural", "complemento para", "parte de un estilo de vida saludable"
- "remedios naturales", "remedios caseros", "medicina natural"

📝 TÍTULO DEL VIDEO:
DEBE contener al inicio una keyword viral: "Para qué sirve", "Beneficios de", "Remedios naturales", "Remedios caseros", "Cómo usar", "Propiedades de".

Devuelve ESTRICTAMENTE este JSON:
{{
  "ingrediente_real": "nombre real normalizado del ingrediente",
  "titulo": "Título SEO viral con keyword al inicio (máx 70 chars, SIN hashtags, 100% seguro)",
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
  "tags": "NO generes tags, se generan automáticamente",
  "gancho_descripcion": "Gancho SEO con keyword viral (máx 90 caracteres)",
  "contexto_descripcion": "1-2 oraciones educativas con keywords naturales"
}}"""

    for intento in range(5):
        try:
            print(f"🤖 IA escribiendo guion de 3-4 min con SEO viral... (intento {intento+1}/5)")
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.8, "max_tokens": 3000, "response_format": {"type": "json_object"}}, timeout=120)
            r.raise_for_status()
            resp = r.json()["choices"][0]["message"]["content"].strip()
            resp = re.sub(r'`json\s*', '', resp).replace('`', '')
            i0, i1 = resp.find('{'), resp.rfind('}')
            data = json.loads(resp[i0:i1+1], strict=False)

            orden = ["hook", "problema", "ingrediente", "beneficio_1", "beneficio_2", "beneficio_3", "producto", "cta"]
            for k in orden:
                if k not in data.get("segmentos", {}) or len(data["segmentos"][k].get("texto", "")) < 30:
                    raise ValueError(f"Segmento {k} faltante o corto")

            cta_txt = data["segmentos"]["cta"]["texto"]
            if "contactos están en la descripción" not in cta_txt.lower():
                data["segmentos"]["cta"]["texto"] = cta_txt.rstrip() + " ¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

            data["ingrediente_real"] = data.get("ingrediente_real") or ingrediente
            data["titulo"] = optimizar_titulo_largo(data.get("titulo"), data["ingrediente_real"], problema)
            data["tags"] = generar_tags_seo_elite(
                data["ingrediente_real"], 
                problema, 
                data.get("titulo", ""), 
                tema_viral
            )

            print(f"✅ Guion listo. Ingrediente real: {data['ingrediente_real']}")
            print(f"🔥 Título SEO: {data.get('titulo')}")
            print(f"🏷️ Tags SEO Elite ({len(data['tags'].split(','))} tags): {data.get('tags')[:120]}...")
            return data
        except Exception as e:
            print(f"⚠️ Intento {intento+1} falló: {e}")
            if intento == 4: sys.exit(1)
            time.sleep(8)

# ================================================================
# 🎤 VOZ CON FALLBACK
# ================================================================
def validar_voz():
    for voz in VOCES_DISPONIBLES:
        try:
            async def test():
                c = edge_tts.Communicate("Prueba de voz.", voz["voz"], rate=voz["velocidad"])
                await c.save("test_voz.mp3")
            asyncio.new_event_loop().run_until_complete(test())
            if os.path.exists("test_voz.mp3") and os.path.getsize("test_voz.mp3") > 100:
                os.remove("test_voz.mp3")
                print(f"🎤 Voz seleccionada: {voz['voz']} ({voz['estilo']})")
                return voz
        except Exception:
            continue
    return VOCES_DISPONIBLES[0]

def generar_audio(texto, path, voz):
    texto_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\'\"]', '', texto)
    async def _gen():
        c = edge_tts.Communicate(texto_limpio, voz["voz"], rate=voz["velocidad"])
        await c.save(path)
    try:
        asyncio.new_event_loop().run_until_complete(_gen())
        if os.path.exists(path) and os.path.getsize(path) > 100:
            return path
    except Exception as e:
        print(f"⚠️ Error audio: {e}")
    return None

# ================================================================
# 🖼️ IMÁGENES: PEXELS (fallback)
# ================================================================
def buscar_imagen_pexels_horizontal(query, intentos=3):
    if not PEXELS_API_KEY: return None
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    for intento in range(intentos):
        try:
            params = {"query": f"{query} {random.choice(['natural', 'healthy', 'close up', 'cinematic'])}",
                      "orientation": "landscape", "per_page": 6, "page": random.randint(1, 5)}
            r = requests.get(url, headers=headers, params=params, timeout=15)
            if r.status_code == 200 and r.json().get("photos"):
                return random.choice(r.json()["photos"][:4])["src"]["large2x"]
        except Exception: pass
        time.sleep(3)
    return None

def descargar_imagen(url, salida):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content))
    if img.mode != "RGB":
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA", "P"):
            fondo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
            img = fondo
        else:
            img = img.convert("RGB")
    img = ImageOps.fit(img, (ANCHO, ALTO), Image.Resampling.LANCZOS)
    img.save(salida, "JPEG", quality=90)
    return salida

# ================================================================
# 🎨 IMÁGENES DE SEGMENTOS: FLUX CLOUDFLARE → PEXELS
# ================================================================
SEGMENTO_FLUX_SUFFIX = (", ultra vivid saturated colors, dramatic cinematic lighting, high-contrast macro photography, "
                        "lush botanical herbal theme, glossy dew textures, dark vignette edges with bright glowing subject, "
                        "clean negative space in the lower third for text overlay, "
                        "no text, no watermark, no people, widescreen 16:9")

def _flux_cloudflare_imagen(query, salida):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    payload = {
        "prompt": query + SEGMENTO_FLUX_SUFFIX,
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
        im = ImageOps.fit(im.convert("RGB"), (ANCHO, ALTO), Image.Resampling.LANCZOS)
        im.save(salida, "JPEG", quality=90)
    return salida

def buscar_imagen_segmento(query_en, salida):
    if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:
        for intento in range(1, 4):
            try:
                print(f"   🎨 Flux segmento intento {intento}/3...")
                _flux_cloudflare_imagen(query_en, salida)
                print(f"   ✅ Imagen de segmento generada con Flux (Cloudflare)")
                return salida
            except Exception as e:
                print(f"   ⚠️ Flux segmento intento {intento} falló: {e}")
                time.sleep(2)
        print("   ⚠️ Flux falló tras 3 intentos en este segmento. Usando Pexels.")
    else:
        print("   ⚠️ Sin keys de Cloudflare configuradas. Usando Pexels para el segmento.")

    url_img = buscar_imagen_pexels_horizontal(query_en)
    if url_img:
        try:
            return descargar_imagen(url_img, salida)
        except Exception as e:
            print(f"   ⚠️ Pexels falló ({e}). Usando imagen por defecto.")
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
        return img_path
    except Exception as e:
        print(f"⚠️ Error potenciando imagen: {e}")
        return img_path

# ================================================================
# 🖼️ TEXTO QUEMADO ESTILO VIRAL + COMPOSICIÓN DE PRODUCTO
# ================================================================
def quemar_texto_pantalla(img_path, texto, salida, estilo="lower"):
    try:
        fuente = asegurar_fuente_thumbnail()
        with Image.open(img_path) as img:
            img = img.convert("RGBA")
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
            x = (ANCHO - banner.width) // 2
            y = ALTO - banner.height - 150
            capa.paste(banner, (x, y), banner)

        img = Image.alpha_composite(img, capa)
        img.convert("RGB").save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error quemando texto: {e}")
        return img_path

def _cargar_fondo(url_o_ruta):
    if os.path.exists(url_o_ruta):
        return Image.open(url_o_ruta).convert("RGB")
    r = requests.get(url_o_ruta, timeout=20)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")

def componer_producto_horizontal(url_producto, fondo, salida="img_producto_largo.jpg"):
    try:
        fondo_img = ImageOps.fit(_cargar_fondo(fondo), (ANCHO, ALTO), Image.Resampling.LANCZOS)
        rp = requests.get(url_producto, timeout=20, verify=False)
        prod = Image.open(io.BytesIO(rp.content)).convert("RGBA")
        try:
            prod = remove(prod)
            print("   ✂️ Fondo del producto eliminado")
        except Exception as e:
            print(f"   ⚠️ rembg falló ({e}), usando imagen original")
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

def efecto_ken_burns(img_path, duracion, direccion="in"):
    clip = ImageClip(img_path).set_duration(duracion)
    if direccion == "in":
        clip = clip.resize(lambda t: 1.0 + 0.25 * (t / duracion))
    else:
        clip = clip.resize(lambda t: 1.25 - 0.25 * (t / duracion))
    def crop_center(frame):
        h, w = frame.shape[:2]
        target_w, target_h = ANCHO, ALTO
        x1 = max(0, (w - target_w) // 2)
        y1 = max(0, (h - target_h) // 2)
        x2 = min(w, x1 + target_w)
        y2 = min(h, y1 + target_h)
        return frame[y1:y2, x1:x2]
    clip = clip.fl_image(crop_center)
    return clip

def montar_video_largo(segmentos_img, salida="largo_final.mp4"):
    clips_video, clips_audio = [], []
    duraciones_segmentos = []
    
    for i, seg in enumerate(segmentos_img):
        audio = AudioFileClip(seg["audio_path"])
        dur = audio.duration + (PAUSA_ENTRE_SEGMENTOS if i < len(segmentos_img) - 1 else 0)
        duraciones_segmentos.append(dur)
        vc = efecto_ken_burns(seg["img_path"], dur, "in" if i % 2 == 0 else "out")
        clips_video.append(vc)
        clips_audio.append(audio)
        if i < len(segmentos_img) - 1:
            clips_audio.append(AudioClip(lambda t: 0, duration=PAUSA_ENTRE_SEGMENTOS))

    audio_narracion = concatenate_audioclips(clips_audio)
    video = concatenate_videoclips(clips_video, method="compose")
    duracion_total = audio_narracion.duration

    musicas = [f for f in os.listdir(".") if f.lower().endswith(".mp3") and not f.startswith(("seg", "test", "audio")) and os.path.getsize(f) > 100]
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

    clips_overlays = [video]
    aviso = crear_overlay_aviso()
    if aviso:
        av_clip = ImageClip(aviso, transparent=True).set_start(0).set_duration(6)
        clips_overlays.append(av_clip)

    overlay = crear_overlay_cta()
    if overlay:
        cta_clip = ImageClip(overlay, transparent=True).set_start(max(duracion_total - 15, 0)).set_duration(15)
        clips_overlays.append(cta_clip)

    video = CompositeVideoClip(clips_overlays, size=(ANCHO, ALTO))

    print("🎬 Renderizando video largo (puede tardar varios minutos)...")
    video.write_videofile(salida, fps=24, codec="libx264", audio_codec="aac",
                          threads=4, preset="ultrafast", verbose=False, logger=None)
    return salida, duraciones_segmentos, duracion_total

def formatear_timestamp(segundos):
    minutos = int(segundos) // 60
    segs = int(segundos) % 60
    return f"{minutos:02d}:{segs:02d}"

def generar_capitulos_dinamicos(duraciones_segmentos):
    nombres_segmentos = [
        "Introducción",
        "El problema",
        "El ingrediente estrella",
        "Beneficio 1",
        "Beneficio 2",
        "Beneficio 3",
        "El producto recomendado",
        "Cómo conseguirlo",
    ]
    
    capitulos = []
    tiempo_acumulado = 0.0
    
    for i, dur in enumerate(duraciones_segmentos):
        timestamp = formatear_timestamp(tiempo_acumulado)
        nombre = nombres_segmentos[i] if i < len(nombres_segmentos) else f"Capítulo {i+1}"
        capitulos.append(f"{timestamp} {nombre}")
        tiempo_acumulado += dur
    
    return "\n".join(capitulos)

# ================================================================
# 🎨 MOTOR DE FONDOS FLUX PARA MINIATURA
# ================================================================
FLUX_PROMPT_SUFFIX = (", dramatic macro photography, vivid saturated colors, cinematic lighting, "
                      "professional youtube thumbnail background, no text, no watermark, widescreen 16:9")

def _guardar_fondo(bytes_img, salida):
    with open(salida, "wb") as f:
        f.write(bytes_img)
    return salida

def buscar_fondo_flux_cloudflare(query, salida="bg_ia.jpg"):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    payload = {
        "prompt": query + FLUX_PROMPT_SUFFIX,
        "steps": 4
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    b64 = (data.get("result") or {}).get("image")
    if not b64:
        raise ValueError(f"Cloudflare no devolvió imagen: {str(data)[:200]}")
    return _guardar_fondo(base64.b64decode(b64), salida)

def buscar_fondo_flux_huggingface(query, salida="bg_ia.jpg"):
    url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    payload = {"inputs": query + FLUX_PROMPT_SUFFIX}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "")
    if "image" not in ctype or len(r.content) < 20000:
        raise ValueError(f"HF no devolvió imagen válida (ctype={ctype}, bytes={len(r.content)})")
    return _guardar_fondo(r.content, salida)

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
    print("⚠️ Flux falló tras 3 intentos. Usando Pexels como siempre.")
    return None

# ================================================================
# 🖼️ THUMBNAIL ENGINE V3
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
        print("✅ Fuente Anton descargada para miniaturas")
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

def crear_miniatura_larga(img_base, url_producto, ingrediente, problema, titulo_seguro, salida="thumb_largo.jpg"):
    try:
        fuente = asegurar_fuente_thumbnail()
        with Image.open(img_base) as bgf:
            bg = ImageOps.fit(bgf.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
        bg = ImageEnhance.Color(bg).enhance(1.45)
        bg = ImageEnhance.Contrast(bg).enhance(1.22)
        bg = ImageEnhance.Brightness(bg).enhance(1.05)
        bg = bg.convert("RGBA")

        capa = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        for x in range(0, 880):
            d.line([(x, 0), (x, 720)], fill=(0, 0, 0, int(200 * (1 - x / 880))))
        for y in range(540, 720):
            d.line([(0, y), (1280, y)], fill=(0, 0, 0, int(140 * ((y - 540) / 180))))
        bg = Image.alpha_composite(bg, capa)

        bloques = []
        linea1 = (" ".join(ingrediente.split()[:2]) or "REMEDIOS NATURALES").upper()
        try:
            bloques.append(_fit(linea1, fuente, 150, 64, 780, render_texto_gradiente))
        except Exception as e:
            print(f"⚠️ Degradado falló ({e}); usando texto sólido amarillo")
            bloques.append(_fit(linea1, fuente, 150, 64, 780, render_texto_solido, fill=(255, 214, 102)))
        bloques.append(render_texto_solido("PARA", fuente, 56))

        partes = [p.strip() for p in (problema or "").split(",") if p.strip()]
        if not partes:
            palabras = [p for p in re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ]', '', titulo_seguro).split() if len(p) > 3]
            partes = [" ".join(palabras[:4])] if palabras else ["BIENESTAR NATURAL"]
        b1, b2 = [], []
        for p in partes:
            if not b2 and len(" ".join(b1 + [p])) <= 30:
                b1.append(p)
            else:
                b2.append(p)
        bloques.append(_fit(" ".join(b1).upper(), fuente, 74, 40, 740, render_banner, bg=(198, 30, 30)))
        if b2:
            bloques.append(_fit(("Y " + " ".join(b2)).upper(), fuente, 74, 40, 740,
                                render_banner, bg=(20, 90, 40), borde=(255, 255, 255)))

        y = 28
        for img_bloque in bloques:
            try:
                rot = img_bloque.rotate(2, expand=True, resample=Image.BICUBIC)
                bg.paste(rot, (46, y), rot)
                y += rot.height + 8
            except Exception as e:
                print(f"⚠️ Bloque de texto falló: {e}")
            if y > 545:
                break

        try:
            rp = requests.get(url_producto, timeout=20, verify=False)
            prod = Image.open(io.BytesIO(rp.content)).convert("RGBA")
            try:
                prod = remove(prod)
                print("   ✂️ Fondo del producto eliminado para miniatura")
            except Exception:
                pass
            ph = 600
            prod = prod.resize((max(1, int(prod.width * (ph / prod.height))), ph), Image.Resampling.LANCZOS)
            gx = 1280 - prod.width - 30
            gy = (720 - ph) // 2 - 20
            halo = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            ImageDraw.Draw(halo).ellipse([gx - 60, gy + ph * 0.45, gx + prod.width + 60, gy + ph + 80],
                                         fill=(255, 255, 255, 120))
            halo = halo.filter(ImageFilter.GaussianBlur(40))
            bg = Image.alpha_composite(bg, halo)
            bg.paste(prod, (gx, gy), prod)
            print("   ✅ Producto pegado a la derecha de la miniatura")
        except Exception as e:
            print(f"⚠️ Producto en miniatura falló: {e}")

        bar = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        db = ImageDraw.Draw(bar)
        db.rectangle([(0, 648), (1280, 720)], fill=(0, 0, 0, 175))
        db.text((40, 664), titulo_seguro.upper()[:64], font=ImageFont.truetype(fuente, 40), fill=(255, 214, 102, 255))
        bg = Image.alpha_composite(bg, bar)

        bg.convert("RGB").save(salida, "JPEG", quality=93)
        print(f"✅ Miniatura V3 estilo viral creada: {salida}")
        return salida
    except Exception as e:
        print(f"⚠️ Error miniatura V3: {e}")
        return None

# ================================================================
# 📤 SUBIR A YOUTUBE (CON REINTENTOS + VALIDACIÓN DE TAGS)
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
    """Valida y limpia los tags ANTES de enviarlos a YouTube."""
    if not tags_str:
        return "remedios naturales, salud natural, bienestar"
    
    tags_lista = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
    tags_validos = []
    
    for tag in tags_lista:
        # Reglas de YouTube:
        # - Máximo 30 caracteres por tag
        # - Solo letras, números y espacios
        # - Sin caracteres especiales
        tag_limpio = re.sub(r'\s+', ' ', tag).strip()
        
        if len(tag_limpio) > 30:
            # Truncar inteligentemente
            tag_limpio = tag_limpio[:27] + "..."
        
        if len(tag_limpio) < 2:
            continue
            
        if not re.match(r'^[a-záéíóúüñ0-9\s]+$', tag_limpio):
            continue
            
        if tag_limpio not in tags_validos:
            tags_validos.append(tag_limpio)
    
    # Mínimo 3 tags
    if len(tags_validos) < 3:
        tags_validos = ["remedios naturales", "salud natural", "bienestar"]
    
    # Máximo 30 tags y 500 caracteres totales
    resultado = []
    total_chars = 0
    for tag in tags_validos[:30]:
        if total_chars + len(tag) + 1 > 495:
            break
        resultado.append(tag)
        total_chars += len(tag) + 1
    
    return ", ".join(resultado)

def subir_video_largo(video_path, thumb_path, titulo, tags_str, gancho, contexto, ingrediente, problema=None, capitulos_dinamicos=""):
    creds = obtener_credenciales_youtube()
    youtube = build("youtube", "v3", credentials=creds)

    problema_str = f"\n🎯 Útil para: {problema}" if problema else ""
    
    # 🔥 VALIDAR TAGS ANTES DE ENVIAR
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

⏱️ CAPÍTULOS (basados en el audio real del video):
{capitulos_dinamicos}

⚕️ AVISO: Este video es contenido educativo basado en la tradición herbolaria mexicana. No sustituye la consulta médica profesional.

🔍 En este video aprenderás:
• Para qué sirve el {ingrediente} en la herbolaria mexicana
• Beneficios y propiedades tradicionales del {ingrediente}
• Cómo usar el {ingrediente} como remedio natural
• El producto recomendado con {ingrediente} y dónde conseguirlo

#remediosnaturales #remedioscaseros #saludnatural #medicinanatural #herbolaria #hierbasmedicinales #{ingrediente.replace(' ', '')}"""

    if ACTIVAR_DISCLOSURE_IA: descripcion += DISCLOSURE_TEXT

    body = {
        "snippet": {"title": titulo[:100], "description": descripcion[:5000],
                    "tags": [t.strip() for t in tags_validados.split(",") if t.strip()][:30],
                    "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }
    
    video_id = None
    for intento in range(1, 4):
        try:
            print(f"📤 Subiendo video a YouTube (intento {intento}/3)...")
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
            video_id = response["id"]
            print(f"✅ Video largo subido con SEO viral: https://youtu.be/{video_id}")
            break
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
                    raise
            else:
                print(f"❌ Error subiendo a YouTube: {e}")
                raise

    if thumb_path and os.path.exists(thumb_path):
        try:
            mt = MediaFileUpload(thumb_path, chunksize=-1, resumable=True, mimetype="image/jpeg")
            youtube.thumbnails().set(videoId=video_id, media_body=mt).execute()
            print("✅ Miniatura V3 personalizada subida")
        except Exception as e:
            print(f"⚠️ Error miniatura: {e}")

    fijar_comentario_contacto(youtube, video_id)
    return video_id

# ================================================================
# 🚀 MAIN
# ================================================================
def main():
    print("🎬 Bot VIDEOS LARGOS Herbolaria (Horizontal 16:9, ~3-4 min)")
    print("🔥 SEO ELITE + Capítulos dinámicos + Tags VidIQ + Segmentos con Flux")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    estado = cargar_estado()
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)

    producto, ingrediente = seleccionar_producto_e_ingrediente_largo()
    tema_viral = max(TEMAS_VIRALES_SALUD, key=lambda x: x.get("ctr_potencial", 0) * random.uniform(0.8, 1.2))
    problema = producto.get('recomendado_para', '')
    print(f"📦 Producto: {producto['nombre']} | 🌱 Ingrediente: {ingrediente}")
    print(f"🎯 Tema: {tema_viral['tema']} | 💊 Problema: {problema}")

    guion = ia_genera_guion_largo(producto, ingrediente, tema_viral)
    ingrediente_hablado = guion.get("ingrediente_real", ingrediente)
    voz = validar_voz()

    orden = ["hook", "problema", "ingrediente", "beneficio_1", "beneficio_2", "beneficio_3", "producto", "cta"]
    segmentos_img = []

    fondo_producto = buscar_imagen_segmento(
        guion["segmentos"]["producto"].get("query_pexels", f"{ingrediente_hablado} natural"),
        "bg_producto.jpg"
    )

    for i, clave in enumerate(orden):
        seg = guion["segmentos"][clave]
        print(f"\n🎬 Segmento {i+1}/8: {clave}")
        img_path = f"img_largo_{i}.jpg"

        if clave in ("producto", "cta"):
            if not componer_producto_horizontal(producto["imagen_url"], fondo_producto, img_path):
                if os.path.exists(fondo_producto):
                    with Image.open(fondo_producto) as im:
                        ImageOps.fit(im.convert("RGB"), (ANCHO, ALTO), Image.Resampling.LANCZOS).save(img_path, "JPEG", quality=90)
                else:
                    buscar_imagen_segmento(seg.get("query_pexels", f"{ingrediente_hablado} plant natural"), img_path)
        else:
            buscar_imagen_segmento(seg.get("query_pexels", f"{ingrediente_hablado} plant natural"), img_path)

        img_path = potenciar_imagen_segmento(img_path)

        tp = seg.get("texto_pantalla", "")
        if tp:
            img_path = quemar_texto_pantalla(img_path, tp, img_path, estilo="center" if clave == "hook" else "lower")

        audio_path = f"audio_largo_{i}.mp3"
        if not generar_audio(seg["texto"], audio_path, voz):
            print(f"❌ Falló audio del segmento {clave}")
            sys.exit(1)
        segmentos_img.append({"img_path": img_path, "audio_path": audio_path})

    video_path, duraciones_segmentos, duracion_total = montar_video_largo(segmentos_img)
    
    capitulos_dinamicos = generar_capitulos_dinamicos(duraciones_segmentos)
    print(f"\n⏱️ Capítulos generados dinámicamente:")
    print(capitulos_dinamicos)
    print(f"⏱️ Duración total del video: {formatear_timestamp(duracion_total)}")

    base_thumb = buscar_fondo_ia_flux(f"{ingrediente_hablado} plant natural vivid macro")
    if not base_thumb:
        url_bg = buscar_imagen_pexels_horizontal(f"{ingrediente_hablado} plant natural")
        if url_bg:
            base_thumb = descargar_imagen(url_bg, "bg_pexels.jpg")
        else:
            base_thumb = "img_largo_2.jpg"
    thumb = crear_miniatura_larga(base_thumb, producto["imagen_url"], ingrediente_hablado, problema, guion["titulo"])

    video_id = subir_video_largo(
        video_path, thumb, guion["titulo"], guion["tags"],
        guion["gancho_descripcion"], guion["contexto_descripcion"],
        ingrediente_hablado, problema,
        capitulos_dinamicos=capitulos_dinamicos
    )

    guardar_ingrediente_largo_usado(ingrediente, producto["nombre"])
    guardar_titulo(guion["titulo"])
    estado["publicaciones_hoy"] = estado.get("publicaciones_hoy", 0) + 1
    estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
    guardar_estado(estado)

    print(f"\n🎉 VIDEO LARGO PUBLICADO CON SEO ELITE: https://youtu.be/{video_id}")
    print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
    print(f"   📞 Teléfono: {TELEFONO_NUMBER}")
    print(f"   🤖 Telegram: {TELEGRAM_BOT}")
    print(f"   🔑 Contraseña del bot: {TELEGRAM_PASSWORD}")

    for f in os.listdir("."):
        if f.startswith(("img_largo_", "audio_largo_")) or f in ("cta_overlay.png", "aviso_overlay.png", "largo_final.mp4", "thumb_largo.jpg", "bg_ia.jpg", "bg_pexels.jpg", "bg_producto.jpg"):
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

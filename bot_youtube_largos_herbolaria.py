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

WHATSAPP_NUMBER = "+52 3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"
CANAL_LINK = "https://www.youtube.com/@sombrasdemedianocheoficial"
FACEBOOK_LINK = "https://www.facebook.com/profile.php?id=61593237382982"

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

# ⏰ VENTANA DE PUBLICACIÓN (hora CDMX)
HORA_MIN_PUBLICAR = 9
HORA_MAX_PUBLICAR = 17

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ================================================================
# 🛡️ PALABRAS PROHIBIDAS (Política de salud de YouTube - 9 categorías)
# ================================================================
PALABRAS_PROHIBIDAS_TITULO = [
    # 1. Claims de curación
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
    # 2. Claims médicos no verificados
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
    # 3. Reemplazo de tratamiento médico
    "reemplaza", "reemplaza medicamentos", "reemplaza tu tratamiento",
    "sustituye", "sustituye medicamentos", "sustituye tu tratamiento",
    "no necesitas médico", "sin ir al médico", "olvida al doctor",
    "mejor que las pastillas", "mejor que los medicamentos",
    "olvida la medicina", "tira tus pastillas", "deja tu tratamiento",
    "sin fármacos", "sin medicamentos", "sin receta médica",
    "alternativa a medicamentos", "en vez de medicamentos",
    # 4. Promesas de tiempo específico
    "en 24 horas", "en un día", "hoy mismo",
    "en 3 días", "en tres días",
    "en 7 días", "en una semana", "en siete días",
    "en un mes", "en 30 días",
    "esta noche", "mañana mismo",
    "al instante", "inmediatamente", "instantáneo", "instantanea",
    "resultados inmediatos", "efecto inmediato",
    "rápido y fácil", "exprés", "express",
    # 5. Sensacionalismo / miedo
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
    # 6. Transformación extrema / peso
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
    # 7. Clickbait genérico
    "no vas a creer", "no lo vas a creer",
    "te sorprenderá", "te dejará impactado",
    "quedarás impactado", "quedarás asombrado",
    "brutal", "bestial",
    "top", "los 10 mejores", "los 5 peores",
    "lo que nadie dice", "lo que nadie sabe",
    "el mejor del mundo", "el peor del mundo",
    "definitivo", "perfecto",
    # 8. Enfermedades graves
    "cáncer", "cancer", "tumor", "tumores",
    "VIH", "SIDA", "sida",
    "alzheimer", "parkinson", "esclerosis",
    "leucemia", "infarto", "derrame cerebral",
    "ictus", "metástasis",
    # 9. Otros problemáticos
    "solución", "elimina",
    "limpiar tu cuerpo", "limpieza total del cuerpo",
]

# ================================================================
# 🔥 BASE DE DATOS DE KEYWORDS VIRALES (alto volumen de búsqueda)
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
    "#salud", "#natural", "#tradicionmexicana",
]

# ================================================================
# 🌿 TEMAS VIRALES (seguros + keywords de alto volumen)
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "remedios naturales", "para qué sirve"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales de las hierbas", "remedios naturales efectivos"], "ctr_potencial": 9.2},
    {"tema": "remedio_casero", "keywords_cortas": ["remedios caseros", "natural", "tradición", "hierbas medicinales"], "keywords_largas": ["remedios caseros efectivos", "tratamiento natural con hierbas", "remedios de la abuela"], "ctr_potencial": 9.5},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "evidencia"], "keywords_largas": ["estudios sobre hierbas", "evidencia tradicional"], "ctr_potencial": 10.5},
    {"tema": "alivio_natural", "keywords_cortas": ["alivio natural", "bienestar", "medicina natural", "plantas medicinales"], "keywords_largas": ["alivio natural tradicional", "remedios mexicanos para el bienestar", "hierbas que alivian"], "ctr_potencial": 10.8},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "herbolaria mexicana", "tradición"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional mexicana", "herbolaria que pocos conocen"], "ctr_potencial": 9.8},
]

# ================================================================
# 🎤 VOCES
# ================================================================
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

    # ⏰ Solo publicar dentro de la ventana 9:00-17:00 CDMX
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

# ================================================================
# 🌱 SELECCIÓN DE PRODUCTO + INGREDIENTE
# ================================================================
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

# ================================================================
# 📚 CATÁLOGOS
# ================================================================
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

# ================================================================
# 🔥 MOTOR DE KEYWORDS VIRALES + TÍTULOS SEGUROS
# ================================================================
def obtener_keywords_aleatorias_virales(cantidad=5):
    """Selecciona keywords virales ponderadas por peso de búsqueda."""
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
    """Sanitiza palabras prohibidas + inyecta keyword viral de alto volumen."""
    t = re.sub(r'#\w+', '', (titulo_ia or "").strip()).strip()
    lower = t.lower()

    # 1) Si tiene palabras prohibidas → reemplazo total
    if any(p in lower for p in PALABRAS_PROHIBIDAS_TITULO):
        print("🛡️ Título con palabra prohibida → reemplazando por fórmula viral segura...")
        t = ""

    # 2) Si no tiene keyword viral → inyectar patrón de búsqueda al inicio
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
            f"{ingrediente}: hierbas medicinales para tu bienestar",
            f"Medicina natural: el poder del {ingrediente}",
            f"Salud natural: secretos del {ingrediente}",
            f"Plantas medicinales: {ingrediente} y sus beneficios",
            f"Remedios naturales con {ingrediente}: tradición mexicana",
            f"¿Sabías esto del {ingrediente}? Usos y beneficios",
        ]
        if problema:
            patrones.extend([
                f"Remedios naturales con {ingrediente} para {problema}",
                f"{ingrediente}: hierba medicinal para {problema}",
                f"Cómo usar {ingrediente} para {problema} (remedio casero)",
                f"Para qué sirve el {ingrediente} en {problema}",
            ])
        t = random.choice(patrones)
        print(f"🔥 Keyword viral inyectada en título: {t}")
    return t[:70]

def generar_tags_virales(ingrediente, problema=None, tema_viral=None):
    """Genera 20 tags optimizados con keywords de alto volumen."""
    tags = [ingrediente.lower(), f"{ingrediente} beneficios", f"{ingrediente} propiedades"]
    tags.extend(obtener_keywords_aleatorias_virales(6))
    if tema_viral:
        tags.extend(tema_viral.get("keywords_cortas", [])[:3])
        tags.extend(tema_viral.get("keywords_largas", [])[:2])
    if problema:
        tags.append(problema.lower())
        tags.append(f"remedios naturales para {problema.lower()}")
    for ht in HASHTAGS_VIRALES[:6]:
        tags.append(ht.replace("#", ""))
    tags_unicos = []
    for tag in tags:
        tag_limpio = tag.strip().lower()
        if tag_limpio and tag_limpio not in tags_unicos:
            tags_unicos.append(tag_limpio)
    return ", ".join(tags_unicos[:20])

# ================================================================
# 🤖 IA GENERA GUION (SEO viral + políticas seguras)
# ================================================================
def ia_genera_guion_largo(producto, ingrediente, tema_viral):
    info_catalogo = obtener_info_ingrediente_catalogo(ingrediente) or "Sin ficha en catálogo; usa conocimiento general verificado."
    curiosidad = obtener_curiosidad_catalogo(ingrediente) or ""
    problema = producto.get('recomendado_para', '')
    keywords_virales_prompt = obtener_keywords_aleatorias_virales(8)
    prohibidas_str = ", ".join(f'"{p}"' for p in PALABRAS_PROHIBIDAS_TITULO[:40]) + "..."

    prompt = f"""Eres guionista experto en salud natural, SEO para YouTube y herbolaria mexicana. Creas videos LARGOS (5 minutos, horizontal) OPTIMIZADOS para búsquedas virales y 100% SEGUROS ante las políticas de YouTube.

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

🎬 ESTRUCTURA OBLIGATORIA (8 segmentos, ~5 minutos reales):
1. "hook" (45-55 palabras): Pregunta o dato impactante del ingrediente (usa el dato curioso). INCLUYE una keyword viral ("remedios naturales", "hierbas medicinales" o "salud natural").
2. "problema" (85-100 palabras): El problema/síntoma que sufre la audiencia ({problema}).
3. "ingrediente" (130-150 palabras): Presenta el ingrediente estrella, origen e historia. Menciona "herbolaria mexicana" o "medicina natural".
4. "beneficio_1" (90-105 palabras): Primer beneficio según la tradición herbal.
5. "beneficio_2" (90-105 palabras): Segundo beneficio según la tradición herbal.
6. "beneficio_3" (90-105 palabras): Tercer beneficio según la tradición herbal.
7. "producto" (170-195 palabras): Presenta {producto.get('nombre')}, cómo contiene el ingrediente y modo de empleo.
8. "cta" (165-190 palabras): Resumen + DEBE terminar EXACTAMENTE con: "¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

REGLAS GENERALES:
- Si el ingrediente suena a saborizante (ej: "Sabor Piña Natural"), habla del ingrediente REAL ("Piña") manteniendo coherencia con el producto.
- NO digas números de WhatsApp/Telegram en el audio (solo la frase final del cta).
- Tono educativo, cálido y cercano. Sin emojis en el texto hablado.
- Incluye SIEMPRE un disclaimer natural: "esto es información educativa basada en la tradición herbolaria, no sustituye la consulta médica".
- Cada segmento incluye "texto_pantalla" (máx 5 palabras) y "query_pexels" (en inglés, imagen horizontal 16:9 del subtema).

🚨 POLÍTICA DE SALUD DE YOUTUBE (CRÍTICO — ESTO EVITA BANNEO DEL CANAL):
NUNCA uses en TÍTULO, GUION NI DESCRIPCIÓN:
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
- "remedios naturales", "remedios caseros", "hierbas medicinales", "plantas medicinales"
- "¿sabías que...?", "para qué sirve", "beneficios de", "propiedades de"

📝 TÍTULO DEL VIDEO (MUY IMPORTANTE PARA SEO):
DEBE contener al inicio (primeras 3 palabras) una keyword viral:
"For qué sirve"/"Para qué sirve", "Beneficios de", "Remedios naturales", "Remedios caseros",
"Cómo usar", "Propiedades de", "Hierbas medicinales", "Medicina natural",
"Plantas medicinales", "Salud natural", "Herbolaria mexicana"

Ejemplos de TÍTULOS VIRALES Y SEGUROS:
- "Para qué sirve el Aloe Vera en remedios naturales"
- "Beneficios del nopal en la herbolaria mexicana"
- "Remedios caseros con manzanilla: usos tradicionales"
- "Cómo usar la cúrcuma como remedio natural"
- "Propiedades del zacate limón que pocos conocen"

Devuelve ESTRICTAMENTE este JSON:
{{
  "ingrediente_real": "nombre real normalizado del ingrediente para voz y búsqueda de imágenes (ej: Piña)",
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
            print(f"🤖 IA escribiendo guion de 5 min con SEO viral... (intento {intento+1}/5)")
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.8, "max_tokens": 3500, "response_format": {"type": "json_object"}}, timeout=120)
            r.raise_for_status()
            resp = r.json()["choices"][0]["message"]["content"].strip()
            resp = re.sub(r'`json\s*', '', resp).replace('`', '')
            i0, i1 = resp.find('{'), resp.rfind('}')
            data = json.loads(resp[i0:i1+1], strict=False)

            orden = ["hook", "problema", "ingrediente", "beneficio_1", "beneficio_2", "beneficio_3", "producto", "cta"]
            for k in orden:
                if k not in data.get("segmentos", {}) or len(data["segmentos"][k].get("texto", "")) < 40:
                    raise ValueError(f"Segmento {k} faltante o corto")

            cta_txt = data["segmentos"]["cta"]["texto"]
            if "contactos están en la descripción" not in cta_txt.lower():
                data["segmentos"]["cta"]["texto"] = cta_txt.rstrip() + " ¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

            data["ingrediente_real"] = data.get("ingrediente_real") or ingrediente

            # 🔥 SANITIZAR + INYECTAR KEYWORDS VIRALES AL TÍTULO
            data["titulo"] = optimizar_titulo_largo(data.get("titulo"), data["ingrediente_real"], problema)

            # 🔥 GENERAR TAGS VIRALES AUTOMÁTICAMENTE
            data["tags"] = generar_tags_virales(data["ingrediente_real"], problema, tema_viral)

            print(f"✅ Guion listo. Ingrediente real: {data['ingrediente_real']}")
            print(f"🔥 Título SEO: {data.get('titulo')}")
            print(f"🏷️ Tags virales: {data.get('tags')[:90]}...")
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
# 🖼️ IMÁGENES
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

def quemar_texto_pantalla(img_path, texto, salida, estilo="lower"):
    try:
        with Image.open(img_path) as img:
            img = img.convert("RGBA")
            capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(capa)
            font = None
            for size in range(72, 36, -4):
                font = ImageFont.truetype(FUENTE, size)
                if draw.textbbox((0, 0), texto.upper(), font=font)[2] < ANCHO * 0.85: break
            tw = draw.textbbox((0, 0), texto.upper(), font=font)[2]
            th = draw.textbbox((0, 0), texto.upper(), font=font)[3]
            if estilo == "lower":
                y = ALTO - 190
            else:
                y = (ALTO - th) // 2
            draw.rectangle([(ANCHO - tw) // 2 - 30, y - 20, (ANCHO + tw) // 2 + 30, y + th + 25], fill=(0, 0, 0, 170))
            draw.text(((ANCHO - tw) // 2, y), texto.upper(), font=font, fill=(255, 214, 102, 255))
            img = Image.alpha_composite(img, capa).convert("RGB")
            img.save(salida, "JPEG", quality=90)
            return salida
    except Exception as e:
        print(f"⚠️ Error quemando texto: {e}")
        return img_path

def componer_producto_horizontal(url_producto, url_fondo, salida="img_producto_largo.jpg"):
    try:
        r = requests.get(url_fondo, timeout=20)
        fondo = ImageOps.fit(Image.open(io.BytesIO(r.content)).convert("RGB"), (ANCHO, ALTO), Image.Resampling.LANCZOS)
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
        fondo.paste(sombra, (x - 12, y - 12), sombra)
        fondo.paste(prod, (x, y), prod)
        fondo.save(salida, "JPEG", quality=90)
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

# ================================================================
# 🎬 KEN BURNS (COMPATIBLE CON MOVIEPY 1.0.3)
# ================================================================
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

# ================================================================
# 🎥 MONTAR VIDEO
# ================================================================
def montar_video_largo(segmentos_img, salida="largo_final.mp4"):
    clips_video, clips_audio = [], []
    for i, seg in enumerate(segmentos_img):
        audio = AudioFileClip(seg["audio_path"])
        dur = audio.duration + (PAUSA_ENTRE_SEGMENTOS if i < len(segmentos_img) - 1 else 0)
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

    # Overlays: aviso legal (inicio) + CTA (final)
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
    return salida

# ================================================================
# 🖼️ THUMBNAIL ENGINE V3 (estilo viral: texto gigante + banners + producto)
# ================================================================
FONT_THUMB_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_THUMB_LOCAL = "Anton-Regular.ttf"

def asegurar_fuente_thumbnail():
    """Descarga una vez la fuente Anton (gratis, licencia OFL)."""
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
    """Texto GIGANTE con degradado amarillo→naranja y contorno negro."""
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
    grad[:, :, :3] = (np.array(top, float) * (1 - t) + np.array(bottom, float) * t).astype(np.uint8)
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
    """Caja redondeada de color con texto (banner rojo/verde estilo viral)."""
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

def buscar_fondo_ia_pollinations(query, salida="bg_ia.jpg"):
    """Fondo dramático GRATIS sin API key (Pollinations/Flux). Devuelve None si falla."""
    try:
        prompt = urllib.parse.quote(f"{query}, dramatic macro photography, vivid saturated colors, cinematic lighting, professional youtube thumbnail background, no text, no watermark")
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&nologo=true&model=flux"
        r = requests.get(url, timeout=75)
        if r.status_code == 200 and len(r.content) > 20000:
            with open(salida, "wb") as f:
                f.write(r.content)
            print("✅ Fondo IA gratis generado (Pollinations)")
            return salida
    except Exception as e:
        print(f"⚠️ Pollinations falló, usando Pexels: {e}")
    return None

def crear_miniatura_larga(img_base, url_producto, ingrediente, problema, titulo_seguro, salida="thumb_largo.jpg"):
    """Miniatura estilo viral: ingrediente gigante + PARA + banners de beneficio + producto con halo."""
    try:
        fuente = asegurar_fuente_thumbnail()
        with Image.open(img_base) as bgf:
            bg = ImageOps.fit(bgf.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
        bg = ImageEnhance.Color(bg).enhance(1.45)
        bg = ImageEnhance.Contrast(bg).enhance(1.22)
        bg = ImageEnhance.Brightness(bg).enhance(1.05)
        bg = bg.convert("RGBA")

        # Degradado lateral + inferior para que el texto resalte
        capa = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(capa)
        for x in range(0, 880):
            d.line([(x, 0), (x, 720)], fill=(0, 0, 0, int(200 * (1 - x / 880))))
        for y in range(540, 720):
            d.line([(0, y), (1280, y)], fill=(0, 0, 0, int(140 * ((y - 540) / 180))))
        bg = Image.alpha_composite(bg, capa)

        # ---- Bloques de texto ----
        bloques = []
        linea1 = (" ".join(ingrediente.split()[:2]) or "REMEDIOS NATURALES").upper()
        bloques.append(_fit(linea1, fuente, 150, 64, 780, render_texto_gradiente))
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

        # Pegado con inclinación ligera (dinamismo)
        y = 28
        for img_bloque in bloques:
            rot = img_bloque.rotate(2, expand=True, resample=Image.BICUBIC)
            bg.paste(rot, (46, y), rot)
            y += rot.height + 8
            if y > 545:
                break

        # ---- Producto recortado con halo ----
        try:
            rp = requests.get(url_producto, timeout=20, verify=False)
            prod = Image.open(io.BytesIO(rp.content)).convert("RGBA")
            try:
                prod = remove(prod)
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
        except Exception as e:
            print(f"⚠️ Producto en miniatura: {e}")

        # ---- Barra inferior con título seguro ----
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
# 📤 SUBIR A YOUTUBE (SEO viral + token auto-refresh)
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

def subir_video_largo(video_path, thumb_path, titulo, tags_str, gancho, contexto, ingrediente, problema=None):
    creds = obtener_credenciales_youtube()
    youtube = build("youtube", "v3", credentials=creds)

    hashtags_str = " ".join(HASHTAGS_VIRALES[:6])
    problema_str = f"\n🎯 Útil para: {problema}" if problema else ""

    descripcion = f"""{gancho}

{contexto}
{problema_str}

🌿 INGREDIENTE ESTRELLA: {ingrediente}

⏱️ CAPÍTULOS:
00:00 Introducción
00:15 El problema
00:45 El ingrediente estrella
01:30 Beneficio 1
02:00 Beneficio 2
02:30 Beneficio 3
03:00 El producto recomendado
04:00 Cómo conseguirlo

⚕️ AVISO: Este video es contenido educativo basado en la tradición herbolaria mexicana. No sustituye la consulta médica profesional.

📲 ¿QUIERES SABER MÁS O ADQUIRIR ESTE PRODUCTO?
💬 WhatsApp: {WHATSAPP_NUMBER}
🤖 Asistente Inteligente: {TELEGRAM_BOT}

🔗 Canal: {CANAL_LINK}
📘 Facebook: {FACEBOOK_LINK}

🔍 Búsquedas relacionadas: remedios naturales, remedios caseros, salud natural, medicina natural, herbolaria mexicana, hierbas medicinales, plantas medicinales, tips de salud, bienestar natural, tradición mexicana, para qué sirve, beneficios de, propiedades de, cómo usar

{hashtags_str} #{ingrediente.replace(' ', '')}"""

    if ACTIVAR_DISCLOSURE_IA: descripcion += DISCLOSURE_TEXT

    body = {
        "snippet": {"title": titulo[:100], "description": descripcion[:5000],
                    "tags": [t.strip() for t in tags_str.split(",") if t.strip()][:20],
                    "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    video_id = response["id"]
    print(f"✅ Video largo subido con SEO viral: https://youtu.be/{video_id}")

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
    print("🎬 Bot VIDEOS LARGOS Herbolaria (Horizontal 16:9, ~5 min)")
    print("🔥 SEO VIRAL ACTIVO + Miniaturas estilo canal grande + Blindaje anti-baneo")
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
    url_fondo_producto = buscar_imagen_pexels_horizontal(guion["segmentos"]["producto"].get("query_pexels", f"{ingrediente_hablado} natural")) or \
                         "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1920&fit=crop"

    for i, clave in enumerate(orden):
        seg = guion["segmentos"][clave]
        print(f"\n🎬 Segmento {i+1}/8: {clave}")
        img_path = f"img_largo_{i}.jpg"

        if clave in ("producto", "cta"):
            if not componer_producto_horizontal(producto["imagen_url"], url_fondo_producto, img_path):
                descargar_imagen(url_fondo_producto, img_path)
        else:
            url_img = buscar_imagen_pexels_horizontal(seg.get("query_pexels", f"{ingrediente_hablado} plant natural"))
            if not url_img:
                url_img = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1920&fit=crop"
            descargar_imagen(url_img, img_path)

        tp = seg.get("texto_pantalla", "")
        if tp:
            img_path = quemar_texto_pantalla(img_path, tp, img_path, estilo="center" if clave == "hook" else "lower")

        audio_path = f"audio_largo_{i}.mp3"
        if not generar_audio(seg["texto"], audio_path, voz):
            print(f"❌ Falló audio del segmento {clave}")
            sys.exit(1)
        segmentos_img.append({"img_path": img_path, "audio_path": audio_path})

    video_path = montar_video_largo(segmentos_img)

    # 🖼️ Miniatura V3: fondo IA gratis (Pollinations) o fallback Pexels
    base_thumb = buscar_fondo_ia_pollinations(f"{ingrediente_hablado} plant natural vivid") or "img_largo_2.jpg"
    thumb = crear_miniatura_larga(base_thumb, producto["imagen_url"], ingrediente_hablado, problema, guion["titulo"])

    video_id = subir_video_largo(video_path, thumb, guion["titulo"], guion["tags"],
                                 guion["gancho_descripcion"], guion["contexto_descripcion"],
                                 ingrediente_hablado, problema)

    guardar_ingrediente_largo_usado(ingrediente, producto["nombre"])
    guardar_titulo(guion["titulo"])
    estado["publicaciones_hoy"] = estado.get("publicaciones_hoy", 0) + 1
    estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
    guardar_estado(estado)

    print(f"\n🎉 VIDEO LARGO PUBLICADO CON SEO VIRAL: https://youtu.be/{video_id}")

    for f in os.listdir("."):
        if f.startswith(("img_largo_", "audio_largo_")) or f in ("cta_overlay.png", "aviso_overlay.png", "largo_final.mp4", "thumb_largo.jpg", "bg_ia.jpg"):
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

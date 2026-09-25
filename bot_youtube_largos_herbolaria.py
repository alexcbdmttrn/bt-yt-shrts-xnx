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

# 🛡️ LISTA AMPLIADA DE PALABRAS PROHIBIDAS (Política de salud de YouTube)
# Agrupada en 8 categorías para máxima protección contra bans/des-recomendaciones
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

    # ─────────── 3. REEMPLAZO DE TRATAMIENTO MÉDICO (MUY PELIGROSO) ───────────
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

    # ─────────── 8. ENFERMEDADES GRAVES (evitar en títulos) ───────────
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
# 🌿 TEMAS VIRALES (Seguros para políticas de YouTube)
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "natural"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales"], "ctr_potencial": 9.2},
    {"tema": "remedio_casero", "keywords_cortas": ["remedio casero", "natural", "tradicional"], "keywords_largas": ["remedios caseros", "tratamiento natural"], "ctr_potencial": 8.8},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "evidencia"], "keywords_largas": ["estudios sobre hierbas", "evidencia tradicional"], "ctr_potencial": 10.5},
    {"tema": "alivio_natural", "keywords_cortas": ["alivio natural", "bienestar", "tradición"], "keywords_largas": ["alivio natural tradicional", "remedio mexicano"], "ctr_potencial": 10.8},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "tradicional"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional"], "ctr_potencial": 9.8},
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

def sanitizar_titulo(titulo, ingrediente):
    """Si el título trae claims médicos prohibidos, lo reemplaza por una fórmula segura."""
    lower = (titulo or "").lower()
    if any(p in lower for p in PALABRAS_PROHIBIDAS_TITULO):
        # Plantillas 100% seguras — ninguna usa palabras prohibidas
        plantillas = [
            f"{ingrediente}: por qué la tradición herbal lo sigue usando",
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

# ================================================================
# 🤖 IA GENERA GUION
# ================================================================
def ia_genera_guion_largo(producto, ingrediente, tema_viral):
    info_catalogo = obtener_info_ingrediente_catalogo(ingrediente) or "Sin ficha en catálogo; usa conocimiento general verificado."
    curiosidad = obtener_curiosidad_catalogo(ingrediente) or ""

    # Lista de prohibidas formateada para el prompt
    prohibidas_str = ", ".join(f'"{p}"' for p in PALABRAS_PROHIBIDAS_TITULO[:40]) + "..."

    prompt = f"""Eres guionista experto en salud natural y SEO para videos LARGOS de YouTube (5 minutos, horizontal).

📦 PRODUCTO COMPLETO:
NOMBRE: {producto.get('nombre')}
PRESENTACIÓN: {producto.get('presentacion')}
RECOMENDADO PARA: {producto.get('recomendado_para')}
INGREDIENTES CLAVE: {producto.get('ingredientes_clave')}
BENEFICIOS: {producto.get('beneficios')}
MODO DE EMPLEO: {producto.get('MODO DE EMPLEO / DOSIS')}

🌱 INGREDIENTE ESTRELLA OBLIGATORIO (NO lo cambies): {ingrediente}
📚 FICHA DEL CATÁLOGO DEL INGREDIENTE: {info_catalogo}
💡 DATO CURIOSO DEL CATÁLOGO (úsalo en el hook o en un beneficio): {curiosidad}
🎯 TEMA VIRAL DE ESTE VIDEO: {tema_viral['tema'].upper()} (keywords: {', '.join(tema_viral['keywords_cortas'])})

🎬 ESTRUCTURA OBLIGATORIA (8 segmentos, ~5 minutos):
1. "hook" (45-55 palabras): Pregunta o dato impactante del ingrediente (usa el dato curioso si existe).
2. "problema" (85-100 palabras): El problema/síntoma que sufre la audiencia ({producto.get('recomendado_para')}).
3. "ingrediente" (130-150 palabras): Presenta el ingrediente estrella, origen e historia breve.
4. "beneficio_1" (90-105 palabras): Primer beneficio según la tradición herbal.
5. "beneficio_2" (90-105 palabras): Segundo beneficio según la tradición herbal.
6. "beneficio_3" (90-105 palabras): Tercer beneficio según la tradición herbal.
7. "producto" (170-195 palabras): Presenta {producto.get('nombre')}, cómo contiene el ingrediente y modo de empleo.
8. "cta" (165-190 palabras): Resumen + DEBE terminar EXACTAMENTE con: "¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

REGLAS GENERALES:
- Si el ingrediente obligatorio suena a saborizante (ej: "Sabor Piña Natural"), habla del ingrediente REAL ("Piña") pero mantén la coherencia con el producto.
- NO digas números de WhatsApp/Telegram en el audio (solo la frase final del cta).
- Tono educativo, cálido y cercano. Sin emojis en el texto hablado.
- Incluye SIEMPRE un disclaimer natural como "esto es información educativa basada en la tradición herbolaria, no sustituye la consulta médica".
- Cada segmento incluye "texto_pantalla" (máx 5 palabras) y "query_pexels" (en inglés, imagen horizontal 16:9 del subtema).

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
- "Aloe Vera: por qué la tradición lo usa en golpes y moretones"
- "Zacate Limón: 3 usos que la herbolaria mexicana le da"
- "¿Sabías esto del nopal? El aliado de tu abuela"
- "Cúrcuma: el papel que juega en el bienestar tradicional"

Devuelve ESTRICTAMENTE este JSON:
{{
  "ingrediente_real": "nombre real normalizado del ingrediente para voz y búsqueda de imágenes (ej: Piña)",
  "titulo": "Título SEO de video largo (máx 70 chars, sin hashtags, variado y 100% SEGURO según políticas de YouTube)",
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
  "tags": "12-15 tags separados por coma (keywords cortas y largas del tema {tema_viral['tema']}, SIN palabras prohibidas)",
  "gancho_descripcion": "Gancho máx 90 caracteres, sin claims médicos",
  "contexto_descripcion": "1-2 oraciones de contexto educativo"
}}"""

    for intento in range(5):
        try:
            print(f"🤖 IA escribiendo guion de 5 min... (intento {intento+1}/5)")
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
            data["titulo"] = sanitizar_titulo(data.get("titulo"), data["ingrediente_real"])

            # 🛡️ Sanitizar también tags por si la IA mete palabras prohibidas
            if "tags" in data and data["tags"]:
                tags_lista = [t.strip() for t in data["tags"].split(",") if t.strip()]
                tags_limpia = [t for t in tags_lista if not any(p in t.lower() for p in PALABRAS_PROHIBIDAS_TITULO)]
                data["tags"] = ", ".join(tags_limpia[:15])

            print(f"✅ Guion listo. Ingrediente real: {data['ingrediente_real']} | Título: {data.get('titulo')}")
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
# 🎬 KEN BURNS CORREGIDO (COMPATIBLE CON MOVIEPY 1.0.3)
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

    # Overlays (Aviso + CTA)
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
# 🖼️ MINIATURA V2 (Alto CTR)
# ================================================================
def crear_miniatura_larga(img_base, url_producto, texto, salida="thumb_largo.jpg"):
    try:
        with Image.open(img_base) as bg:
            bg = ImageOps.fit(bg.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
            bg = ImageEnhance.Color(bg).enhance(1.35)
            bg = ImageEnhance.Brightness(bg).enhance(1.12)
            bg = ImageEnhance.Contrast(bg).enhance(1.15)
            bg = bg.convert("RGBA")
            capa = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(capa)
            # Degradado lateral
            for x in range(0, 780):
                a = int(215 * (1 - x / 780))
                d.line([(x, 0), (x, 720)], fill=(0, 0, 0, a))
            # Texto corto
            palabras = [p for p in re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ]', '', texto).split() if len(p) > 2][:4]
            frase = " ".join(palabras).upper()
            size = 132
            font = ImageFont.truetype(FUENTE, size)
            while size > 58 and d.textbbox((0, 0), frase, font=font)[2] > 690:
                size -= 6
                font = ImageFont.truetype(FUENTE, size)
            lineas = [frase]
            if d.textbbox((0, 0), frase, font=font)[2] > 690:
                mid = len(frase) // 2
                idx = frase.rfind(' ', 0, mid + 12)
                if idx > 0:
                    lineas = [frase[:idx], frase[idx+1:]]
            y = 300 - (len(lineas) - 1) * int(size * 0.62)
            for ln in lineas:
                d.text((60, y), ln, font=font, fill=(255, 214, 102, 255),
                       stroke_width=7, stroke_fill=(0, 0, 0, 255))
                y += int(size * 1.16)
            # Badge
            fb = ImageFont.truetype(FUENTE, 32)
            badge = "HERBOLARIA TRADICIONAL"
            bw = d.textbbox((0, 0), badge, font=fb)[2]
            d.rounded_rectangle([(60, 606), (60 + bw + 48, 668)], radius=31, fill=(198, 40, 40, 235))
            d.text((84, 620), badge, font=fb, fill=(255, 255, 255, 255))
            bg = Image.alpha_composite(bg, capa)
            # Producto
            try:
                rp = requests.get(url_producto, timeout=20, verify=False)
                prod = Image.open(io.BytesIO(rp.content)).convert("RGBA")
                try: prod = remove(prod)
                except Exception: pass
                ph = 620
                prod = prod.resize((int(prod.width * (ph / prod.height)), ph), Image.Resampling.LANCZOS)
                gx = 1280 - prod.width - 40
                gy = (720 - ph) // 2
                halo = Image.new("RGBA", bg.size, (0, 0, 0, 0))
                hd = ImageDraw.Draw(halo)
                hd.ellipse([gx - 50, gy + ph * 0.5, gx + prod.width + 50, gy + ph + 70], fill=(255, 255, 255, 110))
                halo = halo.filter(ImageFilter.GaussianBlur(35))
                bg = Image.alpha_composite(bg, halo)
                bg.paste(prod, (gx, gy), prod)
            except Exception: pass
            bg.convert("RGB").save(salida, "JPEG", quality=92)
            print(f"✅ Miniatura v2 creada: {salida}")
            return salida
    except Exception as e:
        print(f"⚠️ Error miniatura v2: {e}")
        return None

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

def subir_video_largo(video_path, thumb_path, titulo, tags_str, gancho, contexto, ingrediente):
    creds = obtener_credenciales_youtube()
    youtube = build("youtube", "v3", credentials=creds)

    descripcion = f"""{gancho}

{contexto}

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

#{ingrediente.replace(' ', '')} #SaludNatural #Herbolaria #MedicinaNatural #Bienestar"""

    if ACTIVAR_DISCLOSURE_IA: descripcion += DISCLOSURE_TEXT

    body = {
        "snippet": {"title": titulo[:100], "description": descripcion[:5000],
                    "tags": [t.strip() for t in tags_str.split(",") if t.strip()][:15],
                    "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    video_id = response["id"]
    print(f"✅ Video largo subido: https://youtu.be/{video_id}")

    if thumb_path and os.path.exists(thumb_path):
        try:
            mt = MediaFileUpload(thumb_path, chunksize=-1, resumable=True, mimetype="image/jpeg")
            youtube.thumbnails().set(videoId=video_id, media_body=mt).execute()
            print("✅ Miniatura personalizada subida")
        except Exception as e:
            print(f"⚠️ Error miniatura: {e}")

    fijar_comentario_contacto(youtube, video_id)
    return video_id

# ================================================================
# 🚀 MAIN
# ================================================================
def main():
    print("🎬 Bot VIDEOS LARGOS Herbolaria (Horizontal 16:9, ~5 min)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    estado = cargar_estado()
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)

    producto, ingrediente = seleccionar_producto_e_ingrediente_largo()
    tema_viral = max(TEMAS_VIRALES_SALUD, key=lambda x: x.get("ctr_potencial", 0) * random.uniform(0.8, 1.2))
    print(f"📦 Producto: {producto['nombre']} | 🌱 Ingrediente: {ingrediente} | 🎯 Tema: {tema_viral['tema']}")

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
    thumb = crear_miniatura_larga("img_largo_2.jpg", producto["imagen_url"], guion["titulo"])
    video_id = subir_video_largo(video_path, thumb, guion["titulo"], guion["tags"],
                                 guion["gancho_descripcion"], guion["contexto_descripcion"], ingrediente_hablado)

    guardar_ingrediente_largo_usado(ingrediente, producto["nombre"])
    guardar_titulo(guion["titulo"])
    estado["publicaciones_hoy"] = estado.get("publicaciones_hoy", 0) + 1
    estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
    guardar_estado(estado)

    print(f"\n🎉 VIDEO LARGO PUBLICADO: https://youtu.be/{video_id}")

    for f in os.listdir("."):
        if f.startswith(("img_largo_", "audio_largo_")) or f in ("cta_overlay.png", "aviso_overlay.png", "largo_final.mp4", "thumb_largo.jpg"):
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

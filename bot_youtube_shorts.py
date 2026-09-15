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
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from PIL import Image, ImageFilter
import requests
import edge_tts
import pytz
import urllib3

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
INTERVALO_MIN_HORAS = 4
INTERVALO_MAX_HORAS = 8
RETRASO_MAX_MINUTOS = 45

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ================================================================
# 🌿 TEMAS VIRALES DE SALUD
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "natural"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales comprobadas"], "busquedas": 850000, "ctr_potencial": 9.2, "retencion_objetivo": 78, "tendencia": "creciente"},
    {"tema": "remedio_casero", "keywords_cortas": ["remedio casero", "natural", "tradicional"], "keywords_largas": ["remedios caseros efectivos", "tratamiento natural"], "busquedas": 920000, "ctr_potencial": 8.8, "retencion_objetivo": 75, "tendencia": "estable"},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "comprobado"], "keywords_largas": ["estudios científicos comprobados", "evidencia científica"], "busquedas": 680000, "ctr_potencial": 10.5, "retencion_objetivo": 82, "tendencia": "explosiva"},
    {"tema": "cura_milagrosa", "keywords_cortas": ["cura", "eliminar", "sanar"], "keywords_largas": ["como eliminar naturalmente", "cura natural efectiva"], "busquedas": 1200000, "ctr_potencial": 11.3, "retencion_objetivo": 80, "tendencia": "explosiva"},
    {"tema": "secreto_ancestral", "keywords_cortas": ["secreto", "ancestral", "tradicional"], "keywords_largas": ["secreto de los abuelos", "sabiduría tradicional"], "busquedas": 540000, "ctr_potencial": 9.8, "retencion_objetivo": 77, "tendencia": "creciente"},
]

# ================================================================
# 🎤 VOCES DINÁMICAS OPTIMIZADAS
# ================================================================
VOCES_DISPONIBLES = [
    {"voz": "es-MX-DaliaNeural", "velocidad": "+12%", "tono": "+2Hz"},
    {"voz": "es-MX-JorgeNeural", "velocidad": "+10%", "tono": "0Hz"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+15%", "tono": "+3Hz"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+10%", "tono": "+1Hz"},
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

def seleccionar_producto_e_ingrediente():
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    data_usados = cargar_ingredientes_usados()
    usados = data_usados.get("ingredientes", [])
    df = df[df["ingredientes_clave"].notna() & (df["ingredientes_clave"] != "")]
    df = df[df["imagen_url"].notna() & (df["imagen_url"] != "")]
    
    for _ in range(50):
        producto = df.sample(1).iloc[0].to_dict()
        ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",") if i.strip()]
        if ingredientes:
            ingrediente = random.choice(ingredientes)
            if f"{ingrediente}|{producto['nombre']}" not in usados:
                return producto, ingrediente
    
    print("🔄 Todos los ingredientes usados. Reiniciando historial...")
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump({"ingredientes": [], "fecha_reinicio": datetime.now().date().isoformat()}, f)
    
    producto = df.sample(1).iloc[0].to_dict()
    ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",") if i.strip()]
    return producto, random.choice(ingredientes) if ingredientes else "Hierba natural"

def cargar_titulos():
    try:
        with open(TITULOS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"titulos": []}

def guardar_titulo(titulo):
    data = cargar_titulos()
    if titulo not in data["titulos"]:
        data["titulos"].append(titulo)
        with open(TITULOS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

# ================================================================
# 📝 GENERAR GUION CON SEO ÉLITE
# ================================================================
def generar_guion_herbolaria(producto, ingrediente, tema_viral):
    info_ingrediente = "Ingrediente natural con propiedades medicinales"
    try:
        with open(CATALOGO_INGREDIENTES, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        for item in catalog:
            if ingrediente.lower() in item.get("nombre", "").lower():
                info_ingrediente = f"{item.get('descripcion', '')}"
                break
    except: pass

    prompt = f"""Eres un experto en herbolaria creando contenido VIRAL para YouTube Shorts.
TEMA: {tema_viral['tema'].upper()}
PRODUCTO: {producto['nombre']}
INGREDIENTE: {ingrediente}
INFO INGREDIENTE: {info_ingrediente}
BENEFICIOS PRODUCTO: {producto['beneficios']}

REGLAS ESTRICTAS:
1. SEGMENTO 1 (0-25s): Habla SOLO del ingrediente {ingrediente}. Inicia con pregunta impactante. Menciona 2-3 beneficios. NO menciones el producto ni WhatsApp/Telegram.
2. SEGMENTO 2 (25-45s): Presenta el producto {producto['nombre']}. Di que contiene {ingrediente}. NO menciones WhatsApp/Telegram en el audio.
3. TÍTULO: Formato exacto: "El secreto del {ingrediente} #{ingrediente.replace(' ','')} #saludnatural #herbolaria" (Máx 70 chars).

Devuelve ESTRICTAMENTE este JSON:
{{
    "titulo": "Título viral con hashtags integrados",
    "guion_segmento_1": "Texto de 25s sobre el ingrediente (65-75 palabras). Pregunta inicial + beneficios.",
    "guion_segmento_2": "Texto de 20s presentando el producto (50-60 palabras). Sin mencionar contacto.",
    "tags": "tag1, tag2, tag3 (10-15 tags incluyendo keywords cortas y largas)",
    "descripcion_corta": "Descripción SEO (máx 120 caracteres)",
    "gancho_descripcion": "Gancho inicial (máx 90 caracteres)",
    "contexto_descripcion": "Contexto (1 oración)"
}}"""

    for intento in range(6):
        try:
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], 
                      "temperature": 0.8, "max_tokens": 800, "response_format": {"type": "json_object"}}, timeout=60)
            r.raise_for_status()
            respuesta = r.json()["choices"][0]["message"]["content"].strip()
            respuesta = re.sub(r'`json\s*', '', respuesta).replace('`', '')
            inicio, fin = respuesta.find('{'), respuesta.rfind('}')
            json_str = respuesta[inicio:fin+1] if inicio != -1 and fin != -1 else respuesta
            
            data = json.loads(json_str, strict=False)
            if "guion_segmento_1" not in data or len(data["guion_segmento_1"]) < 50:
                raise ValueError("Texto demasiado corto")
            
            # Forzar formato de título con hashtags si la IA no lo hace bien
            titulo = data.get("titulo", "").strip()
            if "#" not in titulo or len(titulo) > 75:
                hashtags = [f"#{ingrediente.replace(' ', '').lower()}", "#saludnatural", "#herbolaria"]
                titulo_base = random.choice([f"El secreto del {ingrediente}", f"El poder del {ingrediente}", f"¿Conocías el {ingrediente}?"])
                titulo = f"{titulo_base} {' '.join(hashtags[:2])}"
            data["titulo"] = titulo
            
            # Optimizar tags
            tags_list = [t.strip() for t in data.get("tags", "").split(",") if t.strip()][:10]
            for kw in tema_viral.get("keywords_cortas", [])[:2]:
                if kw.lower() not in [t.lower() for t in tags_list]: tags_list.append(kw)
            for kw in tema_viral.get("keywords_largas", [])[:2]:
                if kw.lower() not in [t.lower() for t in tags_list]: tags_list.append(kw)
            for ext in [ingrediente.lower(), "salud natural", "bienestar", "medicina natural"]:
                if ext not in tags_list and len(tags_list) < 15: tags_list.append(ext)
            
            data["tags"] = ", ".join(tags_list[:15])
            return data
        except Exception as e:
            if intento == 5:
                print(f"❌ Todos los intentos de IA fallaron: {e}")
                sys.exit(1)
            time.sleep(5)

# ================================================================
# 🖼️ IMÁGENES Y VIDEO (CORREGIDO Y OPTIMIZADO)
# ================================================================
def buscar_imagen_pexels_salud(query, intentos=3):
    if not PEXELS_API_KEY: return None
    variantes = ["natural", "healthy", "organic", "fresh", "herbal", "medicinal"]
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

def crear_video_con_dos_imagenes(guion, url_ingrediente, url_producto):
    print("🎬 Renderizando video con 2 imágenes (Zoom lento)...")
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
    
    clips_video = []
    
    # 1. IMAGEN DEL INGREDIENTE (Pexels)
    try:
        r = requests.get(url_ingrediente, timeout=15)
        img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((1080, 1920))
        img.save("temp_ingrediente.jpg")
        
        video_ingrediente = ImageClip("temp_ingrediente.jpg").set_duration(duracion_seg1)
        video_ingrediente = video_ingrediente.resize(lambda t: 1 + 0.03 * (t / duracion_seg1))  # Zoom lento
        clips_video.append(video_ingrediente)
        print("✅ Imagen del ingrediente cargada")
    except Exception as e:
        print(f"⚠️ Error con imagen de ingrediente: {e}")
    
    # 2. IMAGEN DEL PRODUCTO (Catálogo)
    try:
        r = requests.get(url_producto, timeout=15, verify=False)
        img = Image.open(io.BytesIO(r.content))
        
        # ✅ CORRECCIÓN CRÍTICA: Convertir RGBA a RGB para evitar error de guardado JPEG
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = img.resize((1080, 1920))
        img.save("temp_producto.jpg")
        
        video_producto = ImageClip("temp_producto.jpg").set_duration(duracion_seg2)
        video_producto = video_producto.resize(lambda t: 1 + 0.03 * (t / duracion_seg2))  # Zoom lento
        clips_video.append(video_producto)
        print("✅ Imagen del producto cargada")
    except Exception as e:
        print(f"⚠️ Error con imagen de producto: {e}")
    
    if not clips_video:
        print("❌ No se pudieron cargar las imágenes")
        return None
    
    # Unir videos
    video_final = concatenate_videoclips(clips_video, method="compose")
    
    # 🛡️ BLINDAJE ANTI-FALLOS DE MÚSICA
    musicas = [f for f in os.listdir(".") if f.endswith(".mp3") and os.path.getsize(f) > 5000 and not f.startswith("seg")]
    musica_aplicada = False
    if musicas:
        for musica_path in musicas:
            try:
                musica = AudioFileClip(musica_path).subclip(0, duracion_seg1 + duracion_seg2).volumex(0.10)
                audio_final = CompositeAudioClip([audio_total, musica])
                video_final = video_final.set_audio(audio_final)
                print("✅ Música de fondo agregada")
                musica_aplicada = True
                break
            except Exception:
                continue
    
    if not musica_aplicada:
        print("⚠️ No se pudo cargar música. El video se publicará solo con la voz.")
        video_final = video_final.set_audio(audio_total)
    
    video_final.write_videofile("short_final.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    
    for f in ["seg1.mp3", "seg2.mp3", "temp_ingrediente.jpg", "temp_producto.jpg"]:
        if os.path.exists(f): os.remove(f)
    
    return "short_final.mp4"

# ================================================================
# 📤 SUBIR A YOUTUBE
# ================================================================
def subir_a_youtube(video_path, titulo, tags_str, descripcion_corta, gancho, contexto, ingrediente):
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None
    
    # ✅ WhatsApp y Telegram SOLO en la descripción
    descripcion = f"""{gancho}

{contexto}

📲 **CONTÁCTANOS PARA MÁS INFORMACIÓN:**
💬 WhatsApp: {WHATSAPP_NUMBER}
🤖 Asistente Inteligente: {TELEGRAM_BOT}

🔗 Canal: {CANAL_LINK}
📘 Facebook: {FACEBOOK_LINK}

📦 Envíos a todo México
💳 Aceptamos todas las formas de pago

#{' #'.join([t.strip() for t in tags_str.split(',')[:5]])} #Shorts #SaludNatural #Herbolaria #{ingrediente.replace(' ', '')}"""
    
    if ACTIVAR_DISCLOSURE_IA: descripcion += DISCLOSURE_TEXT
    
    body = {
        "snippet": {"title": titulo[:100], "description": descripcion[:5000], "tags": [t.strip() for t in tags_str.split(",")][:15], "categoryId": "26", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True},
    }
    
    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True))
        response = request.execute()
        print(f"✅ Short subido: https://youtu.be/{response['id']}")
        return response["id"]
    except Exception as e:
        print(f"❌ Error subiendo a YouTube: {e}")
        return None

# ================================================================
# 🚀 MAIN
# ================================================================
def main():
    print("🌿 Bot Herbolaria ÉLITE - YouTube Shorts")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎤 Voz: {CONFIG_VOZ_ACTUAL['voz']}")
    
    estado = cargar_estado()
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).date().isoformat()
    if estado.get("fecha") != hoy:
        estado["fecha"] = hoy
        estado["publicaciones_hoy"] = 0
    
    if estado.get("publicaciones_hoy", 0) >= MAX_VIDEOS_DIA:
        print("✅ Límite diario alcanzado.")
        sys.exit(0)
        
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encuentra {EXCEL_FILE}")
        sys.exit(1)

    producto, ingrediente = seleccionar_producto_e_ingrediente()
    print(f"📦 Producto: {producto['nombre']}")
    print(f"🌱 Ingrediente: {ingrediente}")
    
    tema_viral = max(TEMAS_VIRALES_SALUD, key=lambda x: x.get("ctr_potencial", 0) * random.uniform(0.8, 1.2))
    guion = generar_guion_herbolaria(producto, ingrediente, tema_viral)
    print(f"📝 Título: {guion['titulo']}")
    
    # Buscar imagen del ingrediente/planta
    url_ingrediente = buscar_imagen_pexels_salud(ingrediente)
    print(f"🔍 Imagen del ingrediente: {url_ingrediente[:80]}...")
    
    # URL del producto del Excel
    url_producto = producto["imagen_url"]
    
    video_path = crear_video_con_dos_imagenes(guion, url_ingrediente, url_producto)
    if not video_path:
        print("❌ Error creando video")
        sys.exit(1)
    
    video_id = subir_a_youtube(video_path, guion["titulo"], guion["tags"], guion["descripcion_corta"], guion["gancho_descripcion"], guion["contexto_descripcion"], ingrediente)
    
    if video_id:
        guardar_ingrediente_usado(ingrediente, producto["nombre"])
        guardar_titulo(guion["titulo"])
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

import asyncio
import json
import os
import random
import re
import sys
import time
import urllib3
from datetime import datetime
import pandas as pd
import requests
import edge_tts
import pytz
from PIL import Image, ImageOps, ImageFilter
from moviepy.editor import (
    AudioFileClip, CompositeAudioClip, ImageClip, 
    concatenate_audioclips, TextClip, CompositeVideoClip
)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = json.loads(os.getenv("YOUTUBE_USER_TOKEN")) if os.getenv("YOUTUBE_USER_TOKEN") else {}

# TU INFORMACIÓN DE CONTACTO
WHATSAPP_NUMBER = "+52 123 456 7890"  # ← CAMBIA ESTO POR TU NÚMERO REAL
TELEGRAM_BOT = "https://t.me/alex_xanax_bot"

ESTADO_FILE = "estado_shorts.json"
TITULOS_FILE = "titulos_shorts_publicados.json"
EXCEL_FILE = "catalogo_xanax.xlsx"

MAX_SHORTS_DIA = 3
INTERVALO_MIN_HORAS = 3
INTERVALO_MAX_HORAS = 6
RETRASO_MAX_MINUTOS = 45

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ================================================================
# VOCES
# ================================================================
VOCES_DISPONIBLES = [
    {"voz": "es-MX-DaliaNeural", "velocidad": "+8%", "tono": "0Hz"},
    {"voz": "es-MX-JorgeNeural", "velocidad": "+8%", "tono": "0Hz"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+8%", "tono": "0Hz"},
]
CONFIG_VOZ_ACTUAL = random.choice(VOCES_DISPONIBLES)

# ================================================================
# ESTADO
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"publicaciones_hoy": 0, "fecha": None, "ultima_publicacion": None, "productos_usados": []}

def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)

def cargar_titulos():
    try:
        with open(TITULOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"titulos": []}

def guardar_titulo(titulo):
    data = cargar_titulos()
    if titulo not in data["titulos"]:
        data["titulos"].append(titulo)
        with open(TITULOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# ================================================================
# LÓGICA DE PUBLICACIÓN
# ================================================================
def deberia_publicar_ahora(estado):
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).date().isoformat()
    if estado.get("fecha") != hoy:
        estado["fecha"] = hoy
        estado["publicaciones_hoy"] = 0
        estado["productos_usados"] = []

    if estado.get("publicaciones_hoy", 0) >= MAX_SHORTS_DIA:
        print(f"✅ Límite de {MAX_SHORTS_DIA} shorts diarios alcanzado.")
        return False

    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff_horas = (datetime.now(pytz.timezone("America/Mexico_City")) - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(INTERVALO_MIN_HORAS, INTERVALO_MAX_HORAS)
        if diff_horas < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h. Han pasado {diff_horas:.1f}h.")
            return False

    retraso = random.randint(0, RETRASO_MAX_MINUTOS * 60)
    if retraso > 0:
        print(f"⏳ Retraso aleatorio: {retraso//60} min {retraso%60} seg...")
        time.sleep(retraso)
    return True

# ================================================================
# LECTURA DEL CATÁLOGO
# ================================================================
def obtener_producto_aleatorio(estado):
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    df = df[df["imagen_url"].notna() & (df["imagen_url"] != "")]
    
    productos_usados = estado.get("productos_usados", [])
    disponibles = df[~df["nombre"].isin(productos_usados)]
    
    if disponibles.empty:
        disponibles = df
    
    producto = disponibles.sample(1).iloc[0].to_dict()
    
    ingredientes = str(producto.get("ingredientes_clave", "")).split(",")
    ingrediente_principal = ingredientes[0].strip() if ingredientes else "Hierba natural"
    
    return producto, ingrediente_principal

# ================================================================
# GENERAR GUION (45 segundos)
# ================================================================
def generar_guion(producto, ingrediente):
    prompt = f"""Crea un guion para YouTube Short de 45 segundos sobre "{producto['nombre']}".

INGREDIENTE PRINCIPAL: {ingrediente}
BENEFICIOS DEL PRODUCTO: {producto['beneficios']}

REGLAS ESTRICTAS:
- SEGMENTO 1 (0-25s): Habla sobre los beneficios científicos/naturales de "{ingrediente}". Sé educativo.
- SEGMENTO 2 (25-45s): Presenta "{producto['nombre']}". Di que contiene {ingrediente} y otros componentes. Termina con: "Escríbenos por WhatsApp para asesorarte y conseguirlo".
- NO uses emojis en el texto hablado.
- Longitud total: 110-130 palabras máximo.

Devuelve SOLO este JSON:
{{
    "titulo": "Título llamativo con el ingrediente (máx 60 caracteres)",
    "guion_segmento_1": "Texto de 25 segundos sobre el ingrediente",
    "guion_segmento_2": "Texto de 20 segundos presentando el producto",
    "tags": "tag1, tag2, tag3, tag4, tag5"
}}"""
    
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 400, "response_format": {"type": "json_object"}}, timeout=60)
        r.raise_for_status()
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"⚠️ Error generando guion: {e}")
        return {
            "titulo": f"Beneficios de {ingrediente} con {producto['nombre']}",
            "guion_segmento_1": f"¿Sabías que {ingrediente} es un poderoso aliado natural? Ayuda a mejorar tu bienestar, reduce la inflamación y fortalece tu cuerpo de manera segura y efectiva.",
            "guion_segmento_2": f"Consigue {producto['nombre']}, formulado con {ingrediente} de alta calidad. Escríbenos por WhatsApp para asesorarte y hacer tu pedido hoy mismo.",
            "tags": f"{ingrediente}, salud natural, bienestar, herbolaria, {producto['nombre']}"
        }

# ================================================================
# BUSCAR FONDO EN PEXELS
# ================================================================
def buscar_fondo_pexels(ingrediente):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": f"{ingrediente} natural healthy background", "orientation": "portrait", "per_page": 5}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200 and r.json().get("photos"):
            return random.choice(r.json()["photos"])["src"]["large2x"]
    except: pass
    return "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop"

# ================================================================
# COMPONER IMAGEN (Producto + Fondo)
# ================================================================
def componer_imagen_final(url_producto, url_fondo, salida="producto_final.jpg"):
    print("🎨 Componiendo imagen del producto sobre el fondo...")
    try:
        r_fondo = requests.get(url_fondo, timeout=15)
        fondo = Image.open(requests.compat.BytesIO(r_fondo.content)).convert("RGB").resize((1080, 1920))
        
        r_prod = requests.get(url_producto, timeout=15, verify=False)
        producto = Image.open(requests.compat.BytesIO(r_prod.content)).convert("RGBA")
        
        target_h = int(1920 * 0.45)
        ratio = target_h / producto.height
        producto = producto.resize((int(producto.width * ratio), target_h), Image.Resampling.LANCZOS)
        
        sombra = producto.copy()
        sombra = ImageOps.expand(sombra, border=20, fill=(0,0,0,0))
        sombra = sombra.filter(ImageFilter.GaussianBlur(radius=25))
        
        x = (1080 - producto.width) // 2
        y = int(1920 * 0.55)
        
        fondo.paste(sombra, (x - 20, y - 20), sombra)
        fondo.paste(producto, (x, y), producto)
        
        fondo.save(salida, "JPEG", quality=90)
        return salida
    except Exception as e:
        print(f"⚠️ Error componiendo imagen: {e}. Usando fondo solo.")
        return url_fondo

# ================================================================
# AUDIO
# ================================================================
async def generar_audio(texto, path):
    texto_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\'\"]', '', texto)
    try:
        communicate = edge_tts.Communicate(texto_limpio, CONFIG_VOZ_ACTUAL["voz"], rate=CONFIG_VOZ_ACTUAL["velocidad"])
        await communicate.save(path)
        return path
    except Exception as e:
        print(f"⚠️ Error audio: {e}")
        return None

# ================================================================
# CREAR VIDEO
# ================================================================
def crear_video(guion, imagen_path):
    print("🎬 Renderizando video...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio1_path = loop.run_until_complete(generar_audio(guion["guion_segmento_1"], "seg1.mp3"))
    audio2_path = loop.run_until_complete(generar_audio(guion["guion_segmento_2"], "seg2.mp3"))
    loop.close()
    
    if not audio1_path or not audio2_path:
        return None
        
    clip1 = AudioFileClip(audio1_path)
    clip2 = AudioFileClip(audio2_path)
    audio_total = concatenate_audioclips([clip1, clip2])
    duracion = audio_total.duration
    
    video_clip = ImageClip(imagen_path).set_duration(duracion)
    video_clip = video_clip.resize(lambda t: 1 + 0.08 * (t / duracion))
    video_clip = video_clip.set_position(('center', 'center'))
    
    musicas = [f for f in os.listdir(".") if f.endswith(".mp3") and not f.startswith("seg")]
    if musicas:
        musica = AudioFileClip(random.choice(musicas)).subclip(0, duracion).volumex(0.10)
        audio_final = CompositeAudioClip([audio_total, musica])
        video_clip = video_clip.set_audio(audio_final)
    else:
        video_clip = video_clip.set_audio(audio_total)
        
    video_clip.write_videofile("short_final.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    
    for f in ["seg1.mp3", "seg2.mp3"]:
        if os.path.exists(f): os.remove(f)
        
    return "short_final.mp4"

# ================================================================
# SUBIR A YOUTUBE
# ================================================================
def subir_a_youtube(video_path, titulo, tags_str):
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None

    descripcion = (
        f"🌿 Descubre los beneficios de este poderoso ingrediente natural.\n\n"
        f"📲 **CONTÁCTANOS PARA PEDIRLO:**\n"
        f"💬 WhatsApp: {WHATSAPP_NUMBER}\n"
        f"🤖 Asesor Inteligente: {TELEGRAM_BOT}\n\n"
        f"📦 Envíos a todo México\n"
        f"💳 Aceptamos todas las formas de pago\n\n"
        f"#{' #'.join([t.strip() for t in tags_str.split(',')[:5]])} #Shorts #SaludNatural #Herbolaria"
    )
    
    if ACTIVAR_DISCLOSURE_IA:
        descripcion += DISCLOSURE_TEXT

    body = {
        "snippet": {
            "title": titulo[:100],
            "description": descripcion[:5000],
            "tags": [t.strip() for t in tags_str.split(",")][:15],
            "categoryId": "24",
            "defaultLanguage": "es",
            "defaultAudioLanguage": "es",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        print(f"✅ Short subido: https://youtu.be/{response['id']}")
        return response["id"]
    except Exception as e:
        print(f"❌ Error subiendo a YouTube: {e}")
        return None

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Bot YouTube Shorts Xanax - Iniciando...")
    estado = cargar_estado()
    
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)
        
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encuentra {EXCEL_FILE}")
        sys.exit(1)

    producto, ingrediente = obtener_producto_aleatorio(estado)
    print(f" Producto seleccionado: {producto['nombre']}")
    print(f"🌱 Ingrediente principal: {ingrediente}")
    
    guion = generar_guion(producto, ingrediente)
    print(f"📝 Título: {guion['titulo']}")
    
    fondo_url = buscar_fondo_pexels(ingrediente)
    imagen_final = componer_imagen_final(producto["imagen_url"], fondo_url)
    
    video_path = crear_video(guion, imagen_final)
    if not video_path:
        print("❌ Falló la creación del video")
        sys.exit(1)
        
    video_id = subir_a_youtube(video_path, guion["titulo"], guion["tags"])
    
    if video_id:
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        estado["productos_usados"].append(producto["nombre"])
        guardar_estado(estado)
        guardar_titulo(guion["titulo"])
        print("🎉 ¡Proceso completado exitosamente!")
        
    if os.path.exists("short_final.mp4"): os.remove("short_final.mp4")
    if os.path.exists("producto_final.jpg"): os.remove("producto_final.jpg")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

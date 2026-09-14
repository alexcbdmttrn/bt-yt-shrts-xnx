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
    concatenate_audioclips
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

# 📞 INFORMACIÓN DE CONTACTO
WHATSAPP_NUMBER = "+52 3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"
CANAL_YOUTUBE = "https://www.youtube.com/@sombrasdemedianocheoficial"
FACEBOOK_LINK = "https://www.facebook.com/profile.php?id=61593237382982"

#  ARCHIVOS
ESTADO_FILE = "estado_herbolaria.json"
INGREDIENTES_USADOS_FILE = "ingredientes_usados.json"
TITULOS_FILE = "titulos_publicados.json"
EXCEL_FILE = "catalogo_xanax.xlsx"

# ⏰ CONFIGURACIÓN DE PUBLICACIÓN (1 video diario, hora aleatoria)
MAX_VIDEOS_DIA = 1
INTERVALO_MIN_HORAS = 4   # Mínimo 4 horas entre publicaciones
INTERVALO_MAX_HORAS = 8   # Máximo 8 horas entre publicaciones
RETRASO_MAX_MINUTOS = 45  # Retraso aleatorio hasta 45 min

# 🤖 DIVULGACIÓN DE IA (OBLIGATORIA EN YOUTUBE)
ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ================================================================
# 🎤 VOCES NEURALES (Femeninas naturales mexicanas)
# ================================================================
VOCES_DISPONIBLES = [
    {"voz": "es-MX-DaliaNeural", "velocidad": "+8%"},
    {"voz": "es-MX-JorgeNeural", "velocidad": "+8%"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+8%"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+8%"},
]
CONFIG_VOZ_ACTUAL = random.choice(VOCES_DISPONIBLES)

# ================================================================
# 🎨 TEMAS VIRALES DE SALUD/HERBOLARIA
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords": ["beneficios", "propiedades", "natural", "medicinal"]},
    {"tema": "remedio_casero", "keywords": ["remedio casero", "natural", "tradicional"]},
    {"tema": "dato_cientifico", "keywords": ["ciencia", "estudio", "comprobado", "evidencia"]},
    {"tema": "secreto_ancestral", "keywords": ["secreto", "ancestral", "milenario", "antiguo"]},
    {"tema": "resultado_inmediato", "keywords": ["elimina", "reduce", "mejora", "transforma"]},
]

# ================================================================
#  FÓRMULAS DE TÍTULOS SEO
# ================================================================
FORMULAS_TITULOS = [
    "¿Sabías que {ingrediente} puede {beneficio}?",
    "Lo que NADIE te dice sobre {ingrediente}",
    "{numero} beneficios de {ingrediente} que ignorabas",
    "El SECRETO de {ingrediente} que las farmacéuticas ocultan",
    "Así {beneficio} con {ingrediente} en 7 días",
    "¿Por qué todos usan {ingrediente} ahora?",
    "Descubrí algo PROHIBIDO sobre {ingrediente}",
    "NO tomes {ingrediente} sin saber esto",
]

# ================================================================
# 📊 ESTADO Y PREVENCIÓN DE DUPLICADOS
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"publicaciones_hoy": 0, "fecha": None, "ultima_publicacion": None}

def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)

def cargar_ingredientes_usados():
    try:
        with open(INGREDIENTES_USADOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"ingredientes": [], "fecha_reinicio": None}

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
#  DECISIÓN DE PUBLICAR (1 video diario, hora aleatoria)
# ================================================================
def deberia_publicar_ahora(estado):
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).date().isoformat()
    
    # Reiniciar contador si es nuevo día
    if estado.get("fecha") != hoy:
        estado["fecha"] = hoy
        estado["publicaciones_hoy"] = 0
        print(f"📅 Nuevo día. Contador reiniciado.")
    
    # Verificar límite de 1 video diario
    if estado.get("publicaciones_hoy", 0) >= MAX_VIDEOS_DIA:
        print(f"✅ Límite de {MAX_VIDEOS_DIA} video diario alcanzado.")
        return False
    
    # Verificar intervalo desde última publicación
    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff_horas = (datetime.now(pytz.timezone("America/Mexico_City")) - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(INTERVALO_MIN_HORAS, INTERVALO_MAX_HORAS)
        
        if diff_horas < intervalo:
            print(f" Esperando {intervalo:.1f}h. Han pasado {diff_horas:.1f}h.")
            return False
        else:
            print(f"✅ Han pasado {diff_horas:.1f}h. Intervalo superado.")
    
    # Retraso aleatorio para hora impredecible
    retraso = random.randint(0, RETRASO_MAX_MINUTOS * 60)
    if retraso > 0:
        print(f"⏳ Retraso aleatorio: {retraso//60}min {retraso%60}s")
        time.sleep(retraso)
    
    print(f"✅ Decisión: Publicar. (Video {estado['publicaciones_hoy'] + 1}/{MAX_VIDEOS_DIA} del día)")
    return True

# ================================================================
# 🎲 SELECCIONAR PRODUCTO E INGREDIENTE ALEATORIO
# ================================================================
def seleccionar_producto_e_ingrediente():
    """Selecciona un producto y UN ingrediente aleatorio de sus ingredientes_clave"""
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    data_usados = cargar_ingredientes_usados()
    usados = data_usados.get("ingredientes", [])
    
    # Filtrar productos con ingredientes válidos
    df = df[df["ingredientes_clave"].notna() & (df["ingredientes_clave"] != "")]
    
    intentos = 0
    while intentos < 50:
        producto = df.sample(1).iloc[0].to_dict()
        ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",")]
        
        if ingredientes:
            #  SELECCIÓN ALEATORIA (no siempre el primero)
            ingrediente = random.choice(ingredientes)
            entry = f"{ingrediente}|{producto['nombre']}"
            
            if entry not in usados:
                print(f"✅ Seleccionado: {ingrediente} de {producto['nombre']}")
                return producto, ingrediente
        
        intentos += 1
    
    # Si todos están usados, reiniciar
    print("🔄 Todos los ingredientes usados. Reiniciando...")
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump({"ingredientes": [], "fecha_reinicio": datetime.now().date().isoformat()}, f)
    
    # Reintentar
    producto = df.sample(1).iloc[0].to_dict()
    ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",")]
    ingrediente = random.choice(ingredientes) if ingredientes else "Hierba natural"
    
    return producto, ingrediente

# ================================================================
# 📝 GENERAR GUION (45 segundos: 25s ingrediente + 20s producto)
# ================================================================
def generar_guion(producto, ingrediente):
    tema_viral = random.choice(TEMAS_VIRALES_SALUD)
    
    prompt = f"""Eres un experto en herbolaria y nutrición creando contenido VIRAL para YouTube Shorts.

PRODUCTO: {producto['nombre']}
INGREDIENTE PRINCIPAL: {ingrediente}
BENEFICIOS DEL PRODUCTO: {producto['beneficios']}
TEMA VIRAL: {tema_viral['tema']}

REGLAS ESTRICTAS:
- Duración total: 45 segundos exactos
- SEGMENTO 1 (0-25s): Educación sobre {ingrediente}
  * Inicia con pregunta impactante
  * 2-3 beneficios científicos concretos
  * Tono educativo pero entretenido
  
- SEGMENTO 2 (25-45s): Presentación del producto
  * Menciona {producto['nombre']}
  * Di que contiene {ingrediente}
  * CTA claro: "Escríbenos al WhatsApp {WHATSAPP_NUMBER} o busca nuestro asistente en Telegram {TELEGRAM_BOT}"

FORMATO JSON:
{{
    "titulo": "Título viral (55-70 caracteres)",
    "guion_segmento_1": "Texto de 25 segundos (65-75 palabras)",
    "guion_segmento_2": "Texto de 20 segundos (50-60 palabras)",
    "tags": "tag1, tag2, tag3 (8-12 tags)",
    "descripcion_corta": "Descripción SEO (máx 120 caracteres)"
}}"""

    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], 
                  "temperature": 0.7, "max_tokens": 400, "response_format": {"type": "json_object"}}, 
            timeout=60)
        r.raise_for_status()
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"️ Error generando guion: {e}")
        return {
            "titulo": f"Beneficios increíbles de {ingrediente}",
            "guion_segmento_1": f"¿Sabías que {ingrediente} tiene propiedades extraordinarias? Este ingrediente natural ayuda a mejorar tu digestión, fortalece tu sistema inmunológico y aporta antioxidantes esenciales. Estudios recientes confirman sus beneficios para la salud.",
            "guion_segmento_2": f"Consigue {producto['nombre']} con {ingrediente} de alta calidad. Escríbenos al WhatsApp {WHATSAPP_NUMBER} o busca nuestro asistente inteligente en Telegram {TELEGRAM_BOT}. ¡Tu salud natural te lo agradecerá!",
            "tags": f"{ingrediente}, salud natural, bienestar, herbolaria, {producto['nombre']}",
            "descripcion_corta": f"Descubre los beneficios de {ingrediente} con {producto['nombre']}"
        }

# ================================================================
# 🖼️ BUSCAR IMAGEN EN PEXELS
# ================================================================
def buscar_imagen_pexels(query, intentos=3):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 10,
        "page": random.randint(1, 5)
    }
    
    for intento in range(intentos):
        try:
            print(f"🔍 Buscando en Pexels: '{query}'...")
            r = requests.get(url, headers=headers, params=params, timeout=25)
            if r.status_code == 200:
                data = r.json()
                if data.get("photos") and len(data["photos"]) > 0:
                    foto = random.choice(data["photos"][:5])
                    return foto["src"]["large2x"]
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(3)
    
    return None

# ================================================================
# 🎨 COMPONER IMAGEN (Producto + Fondo)
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
# 🎙️ GENERAR AUDIO
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
# 🎬 CREAR VIDEO
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
# 📤 SUBIR A YOUTUBE
# ================================================================
def subir_a_youtube(video_path, titulo, tags_str, descripcion_corta):
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None

    descripcion = (
        f"{descripcion_corta}\n\n"
        f"📲 **CONTÁCTANOS PARA PEDIRLO:**\n"
        f"💬 WhatsApp: {WHATSAPP_NUMBER}\n"
        f"🤖 Asistente Inteligente: {TELEGRAM_BOT}\n\n"
        f"🔗 Canal: {CANAL_YOUTUBE}\n"
        f" Facebook: {FACEBOOK_LINK}\n\n"
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
            "categoryId": "26",
            "defaultLanguage": "es",
            "defaultAudioLanguage": "es",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,  # 🔥 DIVULGACIÓN DE IA OBLIGATORIA
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
# 🚀 MAIN
# ================================================================
def main():
    print("🌿 Bot Herbolaria YouTube Shorts - 1 video diario")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎤 Voz: {CONFIG_VOZ_ACTUAL['voz']}")
    
    estado = cargar_estado()
    
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)
        
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ No se encuentra {EXCEL_FILE}")
        sys.exit(1)

    producto, ingrediente = seleccionar_producto_e_ingrediente()
    print(f"📦 Producto: {producto['nombre']}")
    print(f" Ingrediente: {ingrediente}")
    
    guion = generar_guion(producto, ingrediente)
    print(f"📝 Título: {guion['titulo']}")
    
    fondo_url = buscar_imagen_pexels(f"{ingrediente} natural healthy background")
    if not fondo_url:
        fondo_url = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop"
    
    imagen_final = componer_imagen_final(producto["imagen_url"], fondo_url)
    
    video_path = crear_video(guion, imagen_final)
    if not video_path:
        print("❌ Falló la creación del video")
        sys.exit(1)
        
    video_id = subir_a_youtube(video_path, guion["titulo"], guion["tags"], guion["descripcion_corta"])
    
    if video_id:
        guardar_ingrediente_usado(ingrediente, producto["nombre"])
        guardar_titulo(guion["titulo"])
        
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        
        print(f"\n🎉 ¡Publicado exitosamente!")
        print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
        print(f"    Telegram: {TELEGRAM_BOT}")
        print(f"   🔗 URL: https://youtu.be/{video_id}")
        print(f"    Videos hoy: {estado['publicaciones_hoy']}/{MAX_VIDEOS_DIA}")
    
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

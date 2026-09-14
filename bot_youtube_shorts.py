import asyncio
from datetime import datetime, timedelta
import json
import os
import random
import re
import sys
import time
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import (
    AudioFileClip, CompositeAudioClip, ImageClip, 
    concatenate_audioclips, concatenate_videoclips,
    AudioClip, TextClip, CompositeVideoClip
)
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import requests
import edge_tts
import pytz
import urllib3

# Silenciar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
# CONFIGURACIÓN ÉLITE - HERBOLARIA/NUTRICIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
YOUTUBE_USER_TOKEN = (
    json.loads(os.getenv("YOUTUBE_USER_TOKEN"))
    if os.getenv("YOUTUBE_USER_TOKEN")
    else {}
)

CANAL_LINK = "https://www.youtube.com/@sombrasdemedianocheoficial"
FACEBOOK_LINK = "https://www.facebook.com/profile.php?id=61593237382982"
WHATSAPP_NUMBER = "+52 3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"

ESTADO_FILE = "estado_herbolaria.json"
INGREDIENTES_USADOS_FILE = "ingredientes_usados.json"
TITULOS_FILE = "titulos_publicados.json"
ANALYTICS_FILE = "analytics_herbolaria.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"

MAX_SHORTS_DIA = 3
INTERVALO_MIN_HORAS = 4
INTERVALO_MAX_HORAS = 7
RETRASO_MAX_MINUTOS = 30

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ================================================================
# 🌿 TEMAS VIRALES DE SALUD/HERBOLARIA 2024-2025
# ================================================================
TEMAS_VIRALES_SALUD = [
    {
        "tema": "beneficios_ocultos",
        "keywords": ["beneficios", "propiedades", "curativo", "natural", "medicinal"],
        "keywords_larga": ["beneficios que no conocías", "propiedades medicinales", "usos medicinales"],
        "categorias": ["hierbas", "frutas", "verduras", "semillas"],
        "busquedas": 850000,
        "competencia": "media",
        "ctr_potencial": 9.2,
        "retencion_objetivo": 78,
        "duracion_optima": 45,
        "tendencia": "creciente",
        "engagement_rate": 15.3
    },
    {
        "tema": "remedio_casero",
        "keywords": ["remedio casero", "natural", "sin medicamentos", "casero", "tradicional"],
        "keywords_larga": ["remedios caseros efectivos", "como curar naturalmente", "tratamiento natural"],
        "categorias": ["infusiones", "tés", "extractos"],
        "busquedas": 920000,
        "competencia": "alta",
        "ctr_potencial": 8.8,
        "retencion_objetivo": 75,
        "duracion_optima": 50,
        "tendencia": "estable",
        "engagement_rate": 14.7
    },
    {
        "tema": "dato_cientifico",
        "keywords": ["ciencia", "estudio", "investigación", "comprobado", "evidencia"],
        "keywords_larga": ["estudios científicos", "investigación médica", "evidencia científica"],
        "categorias": ["curiosidades", "nutrición", "salud"],
        "busquedas": 680000,
        "competencia": "baja",
        "ctr_potencial": 10.5,
        "retencion_objetivo": 82,
        "duracion_optima": 55,
        "tendencia": "explosiva",
        "engagement_rate": 17.2
    },
    {
        "tema": "cura_milagrosa",
        "keywords": ["cura", "eliminar", "desaparecer", "sanar", "recuperar"],
        "keywords_larga": ["como eliminar naturalmente", "cura natural", "sanación natural"],
        "categorias": ["productos", "tratamientos"],
        "busquedas": 1200000,
        "competencia": "media",
        "ctr_potencial": 11.3,
        "retencion_objetivo": 80,
        "duracion_optima": 48,
        "tendencia": "explosiva",
        "engagement_rate": 18.5
    },
    {
        "tema": "secreto_ancestral",
        "keywords": ["secreto", "ancestral", "tradicional", "milenario", "antiguo"],
        "keywords_larga": ["secreto de los abuelos", "remedio ancestral", "sabiduría ancestral"],
        "categorias": ["hierbas", "plantas medicinales"],
        "busquedas": 540000,
        "competencia": "baja",
        "ctr_potencial": 9.8,
        "retencion_objetivo": 77,
        "duracion_optima": 52,
        "tendencia": "creciente",
        "engagement_rate": 16.1
    }
]

# ================================================================
# 🎯 FÓRMULAS DE TÍTULOS ÉLITE - SALUD
# ================================================================
FORMULAS_TITULOS_SALUD = {
    "pregunta_impacto": [
        "¿Sabías que {ingrediente} puede {beneficio}?",
        "¿Por qué NADIE te cuenta esto sobre {ingrediente}?",
        "¿Qué pasa si tomas {ingrediente} todos los días?",
        "¿Conocías este SECRETO de {ingrediente}?",
    ],
    "numero_especifico": [
        "{numero} beneficios de {ingrediente} que ignorabas",
        "{numero} razones para usar {ingrediente} HOY",
        "{numero} formas de usar {ingrediente} (la {numero} te sorprenderá)",
    ],
    "secreto_revelado": [
        "El SECRETO de {ingrediente} que las farmacéuticas ocultan",
        "Lo que NADIE te dice sobre {ingrediente}",
        "Descubrí algo PROHIBIDO sobre {ingrediente}",
    ],
    "advertencia_salud": [
        "️ NO tomes {ingrediente} sin saber esto",
        "🚨 ALERTA: Esto pasa si usas {ingrediente}",
        "PELIGRO: Error común con {ingrediente}",
    ],
    "resultado_inmediato": [
        "Así {beneficio} con {ingrediente} en 7 días",
        "Elimina {problema} naturalmente con {ingrediente}",
        "Transforma tu salud con {ingrediente}",
    ]
}

# ================================================================
# 🎨 PSICOLOGÍA DEL COLOR - SALUD
# ================================================================
PSICOLOGIA_COLOR_SALUD = {
    "energia": {
        "primario": "#FF6B35",  # Naranja - Energía, vitalidad
        "secundario": "#F7C59F",  # Durazno - Calidez
        "acento": "#2EC4B6",  # Turquesa - Salud
        "contraste_minimo": 4.5
    },
    "naturaleza": {
        "primario": "#2D6A4F",  # Verde oscuro - Naturaleza
        "secundario": "#52B788",  # Verde claro - Frescura
        "acento": "#FFD166",  # Amarillo - Optimismo
        "contraste_minimo": 4.5
    },
    "confianza": {
        "primario": "#118AB2",  # Azul - Confianza
        "secundario": "#073B4C",  # Azul oscuro - Profesionalismo
        "acento": "#FFD166",  # Amarillo - Atención
        "contraste_minimo": 4.5
    },
    "urgencia": {
        "primario": "#E63946",  # Rojo - Urgencia
        "secundario": "#1D3557",  # Azul marino - Contraste
        "acento": "#F1FAEE",  # Blanco - Claridad
        "contraste_minimo": 7.0
    }
}

# ================================================================
# 📊 CALCULAR SCORE DE VIRALIDAD
# ================================================================
def calcular_puntuacion_viralidad(tema):
    factores = {
        "busquedas": tema["busquedas"] / 1000000 * 30,
        "ctr_potencial": tema["ctr_potencial"] * 2.5,
        "retencion": tema["retencion_objetivo"] * 2.0,
        "engagement": tema["engagement_rate"] * 1.5,
        "tendencia": 10 if tema["tendencia"] == "explosiva" else 5,
    }
    score_total = sum(factores.values())
    return {
        "score": score_total,
        "factores": factores,
        "categoria": "Alta" if score_total > 75 else "Media" if score_total > 50 else "Baja"
    }

# ================================================================
#  SELECCIONAR INGREDIENTE ALEATORIO (SIN REPETIR)
# ================================================================
def cargar_ingredientes_usados():
    try:
        with open(INGREDIENTES_USADOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"ingredientes": [], "fecha_reinicio": None}

def guardar_ingrediente_usado(ingrediente, producto):
    data = cargar_ingredientes_usados()
    hoy = datetime.now().date().isoformat()
    
    # Reiniciar si es un nuevo día
    if data.get("fecha_reinicio") != hoy:
        data["ingredientes"] = []
        data["fecha_reinicio"] = hoy
    
    entry = f"{ingrediente}|{producto}"
    if entry not in data["ingredientes"]:
        data["ingredientes"].append(entry)
    
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def seleccionar_producto_e_ingrediente():
    """Selecciona un producto y un ingrediente aleatorio no usado"""
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
# 🎬 GENERAR GUION 45 SEGUNDOS (25s + 20s)
# ================================================================
def generar_guion_herbolaria(producto, ingrediente, tema_viral):
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
# 🎨 CREAR MINIATURA ÉLITE - SALUD
# ================================================================
def crear_miniatura_herbolaria(img_path, texto, producto_nombre, output_path):
    color_scheme = random.choice(list(PSICOLOGIA_COLOR_SALUD.values()))
    
    try:
        with Image.open(img_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img = ImageOps.fit(img, (1080, 1920), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(1.4)
            img = ImageEnhance.Color(img).enhance(1.3)
            img = ImageEnhance.Sharpness(img).enhance(1.8)
            
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Texto principal
            texto_final = texto.upper().strip()
            palabras = texto_final.split()
            if len(palabras) > 3:
                mitad = len(palabras) // 2
                lineas = [" ".join(palabras[:mitad]), " ".join(palabras[mitad:])]
            else:
                lineas = [texto_final]
            
            # Fuente
            font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
            font_size = 100
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
            
            # Posición
            total_height = 0
            for linea in lineas:
                bbox = draw.textbbox((0, 0), linea, font=font)
                total_height += bbox[3] - bbox[1] + 20
            
            y_start = (height - total_height) // 2 + 100
            
            # Fondo semitransparente
            padding = 40
            max_width = max(draw.textbbox((0, 0), linea, font=font)[2] for linea in lineas)
            draw.rectangle(
                [(width - max_width) // 2 - padding, y_start - padding,
                 (width + max_width) // 2 + padding, y_start + total_height + padding],
                fill=(0, 0, 0, 200)
            )
            
            # Texto con contorno
            y_current = y_start
            for linea in lineas:
                bbox = draw.textbbox((0, 0), linea, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                x = (width - w) // 2
                
                # Contorno negro
                for dx in range(-6, 7):
                    for dy in range(-6, 7):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y_current + dy), linea, font=font, fill=(0, 0, 0))
                
                # Texto principal
                draw.text((x, y_current), linea, font=font, fill=color_scheme["acento"])
                y_current += h + 20
            
            # Emoji de salud
            try:
                emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 80)
                draw.text((width - 120, 100), "🌿", font=emoji_font)
            except:
                pass
            
            img.save(output_path, "JPEG", quality=95, optimize=True)
            print(f"✅ Miniatura creada: {output_path}")
            return True
    except Exception as e:
        print(f"❌ Error creando miniatura: {e}")
        return False

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
# 🎬 CREAR VIDEO SHORT
# ================================================================
def crear_video_short(guion, ingrediente, producto, output_path="short_final.mp4"):
    print("🎬 Creando video Short...")
    
    # Buscar imagen del ingrediente
    query = f"{ingrediente} natural healthy close-up"
    img_url = buscar_imagen_pexels(query)
    
    if not img_url:
        # Fallback: crear imagen placeholder
        img = Image.new("RGB", (1080, 1920), (46, 106, 79))
        img_path = "temp_ingrediente.jpg"
        img.save(img_path)
    else:
        # Descargar imagen
        r = requests.get(img_url, timeout=30)
        img_path = "temp_ingrediente.jpg"
        with open(img_path, "wb") as f:
            f.write(r.content)
    
    # Ajustar imagen
    with Image.open(img_path) as img:
        img = ImageOps.fit(img, (1080, 1920), Image.Resampling.LANCZOS)
        img.save(img_path)
    
    # Generar audio segmento 1
    async def generar_audio_seg1():
        communicate = edge_tts.Communicate(guion["guion_segmento_1"], "es-MX-DaliaNeural", rate="+8%")
        await communicate.save("seg1.mp3")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generar_audio_seg1())
    loop.close()
    
    # Generar audio segmento 2
    async def generar_audio_seg2():
        communicate = edge_tts.Communicate(guion["guion_segmento_2"], "es-MX-DaliaNeural", rate="+8%")
        await communicate.save("seg2.mp3")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generar_audio_seg2())
    loop.close()
    
    # Cargar audios
    audio1 = AudioFileClip("seg1.mp3")
    audio2 = AudioFileClip("seg2.mp3")
    audio_total = concatenate_audioclips([audio1, audio2])
    duracion = audio_total.duration
    
    # Crear video con zoom
    video_clip = ImageClip(img_path).set_duration(duracion)
    video_clip = video_clip.resize(lambda t: 1 + 0.08 * (t / duracion))
    video_clip = video_clip.set_position(('center', 'center'))
    
    # Música de fondo (si existe)
    musicas = [f for f in os.listdir(".") if f.endswith(".mp3") and not f.startswith("seg")]
    if musicas:
        musica = AudioFileClip(random.choice(musicas)).subclip(0, duracion).volumex(0.10)
        audio_final = CompositeAudioClip([audio_total, musica])
        video_clip = video_clip.set_audio(audio_final)
    else:
        video_clip = video_clip.set_audio(audio_total)
    
    # Exportar
    video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    
    # Limpieza
    for f in ["seg1.mp3", "seg2.mp3", "temp_ingrediente.jpg"]:
        if os.path.exists(f):
            os.remove(f)
    
    print(f"✅ Video creado: {output_path} ({duracion:.1f}s)")
    return output_path

# ================================================================
#  SUBIR A YOUTUBE
# ================================================================
def subir_a_youtube(video_path, titulo, tags_str, descripcion):
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando: {e}")
        return None
    
    tags = [t.strip() for t in tags_str.split(",") if t.strip()][:15]
    
    descripcion_completa = f"""{descripcion}

📲 **CONTÁCTANOS:**
💬 WhatsApp: {WHATSAPP_NUMBER}
🤖 Asistente Inteligente: {TELEGRAM_BOT}

🔗 Canal: {CANAL_LINK}
📘 Facebook: {FACEBOOK_LINK}

{tags_str}"""

    if ACTIVAR_DISCLOSURE_IA:
        descripcion_completa += DISCLOSURE_TEXT

    body = {
        "snippet": {
            "title": titulo[:100],
            "description": descripcion_completa[:5000],
            "tags": tags,
            "categoryId": "26",  # Howto & Style / Salud
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
        video_id = response["id"]
        print(f"✅ Short subido: https://youtu.be/{video_id}")
        return video_id
    except Exception as e:
        print(f"❌ Error subiendo: {e}")
        return None

# ================================================================
# 🎯 DECISIÓN DE PUBLICAR
# ================================================================
def deberia_publicar_ahora(estado):
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).date().isoformat()
    
    if estado.get("fecha") != hoy:
        estado["fecha"] = hoy
        estado["publicaciones_hoy"] = 0
    
    if estado.get("publicaciones_hoy", 0) >= MAX_SHORTS_DIA:
        print(f"✅ Límite de {MAX_SHORTS_DIA} shorts alcanzado")
        return False
    
    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff_horas = (datetime.now(pytz.timezone("America/Mexico_City")) - datetime.fromisoformat(ultima)).total_seconds() / 3600
        intervalo = random.uniform(INTERVALO_MIN_HORAS, INTERVALO_MAX_HORAS)
        
        if diff_horas < intervalo:
            print(f"⏳ Esperando {intervalo:.1f}h. Han pasado {diff_horas:.1f}h")
            return False
    
    retraso = random.randint(0, RETRASO_MAX_MINUTOS * 60)
    if retraso > 0:
        print(f"⏳ Retraso aleatorio: {retraso//60}min {retraso%60}s")
        time.sleep(retraso)
    
    return True

# ================================================================
# 📊 CARGAR/GUARDAR ESTADO
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

# ================================================================
# 🚀 MAIN
# ================================================================
def main():
    print("🌿 Bot Herbolaria ÉLITE - YouTube Shorts")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    estado = cargar_estado()
    
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)
    
    # Seleccionar producto e ingrediente aleatorio
    producto, ingrediente = seleccionar_producto_e_ingrediente()
    print(f"📦 Producto: {producto['nombre']}")
    print(f" Ingrediente: {ingrediente}")
    
    # Seleccionar tema viral
    tema_viral = random.choice(TEMAS_VIRALES_SALUD)
    print(f"🔥 Tema viral: {tema_viral['tema']}")
    
    # Generar guion
    guion = generar_guion_herbolaria(producto, ingrediente, tema_viral)
    print(f"📝 Título: {guion['titulo']}")
    
    # Crear video
    video_path = crear_video_short(guion, ingrediente, producto)
    
    if not video_path:
        print("❌ Error creando video")
        sys.exit(1)
    
    # Subir a YouTube
    video_id = subir_a_youtube(
        video_path=video_path,
        titulo=guion["titulo"],
        tags_str=guion["tags"],
        descripcion=guion["descripcion_corta"]
    )
    
    if video_id:
        # Guardar ingrediente usado
        guardar_ingrediente_usado(ingrediente, producto["nombre"])
        
        # Actualizar estado
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        
        print(f"\n🎉 ¡Publicado exitosamente!")
        print(f"   📱 WhatsApp: {WHATSAPP_NUMBER}")
        print(f"   🤖 Telegram: {TELEGRAM_BOT}")
        print(f"   🔗 URL: https://youtu.be/{video_id}")
        print(f"   📊 Publicaciones hoy: {estado['publicaciones_hoy']}/{MAX_SHORTS_DIA}")
    
    # Limpieza final
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

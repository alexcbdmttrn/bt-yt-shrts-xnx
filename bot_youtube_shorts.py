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
)
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
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
ANALYTICS_FILE = "analytics_herbolaria.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"

MAX_VIDEOS_DIA = 1
INTERVALO_MIN_HORAS = 4
INTERVALO_MAX_HORAS = 8
RETRASO_MAX_MINUTOS = 45

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ================================================================
# 🌿 TEMAS VIRALES DE SALUD (ADAPTADOS DEL ANÁLISIS ÉLITE)
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords": ["beneficios", "propiedades", "natural", "medicinal"], "busquedas": 850000, "ctr_potencial": 9.2, "retencion_objetivo": 78, "tendencia": "creciente"},
    {"tema": "remedio_casero", "keywords": ["remedio casero", "natural", "sin medicamentos", "tradicional"], "busquedas": 920000, "ctr_potencial": 8.8, "retencion_objetivo": 75, "tendencia": "estable"},
    {"tema": "dato_cientifico", "keywords": ["ciencia", "estudio", "investigación", "comprobado"], "busquedas": 680000, "ctr_potencial": 10.5, "retencion_objetivo": 82, "tendencia": "explosiva"},
    {"tema": "cura_milagrosa", "keywords": ["cura", "eliminar", "desaparecer", "sanar"], "busquedas": 1200000, "ctr_potencial": 11.3, "retencion_objetivo": 80, "tendencia": "explosiva"},
    {"tema": "secreto_ancestral", "keywords": ["secreto", "ancestral", "tradicional", "milenario"], "busquedas": 540000, "ctr_potencial": 9.8, "retencion_objetivo": 77, "tendencia": "creciente"},
]

# ================================================================
# 🎯 FÓRMULAS DE TÍTULOS ÉLITE (NEURO-MARKETING PARA SALUD)
# ================================================================
FORMULAS_TITULOS_SALUD = {
    "pregunta_impacto": ["¿Sabías que {ingrediente} puede {beneficio}?", "¿Por qué NADIE te cuenta esto sobre {ingrediente}?", "¿Qué pasa si tomas {ingrediente} todos los días?"],
    "numero_especifico": ["{numero} beneficios de {ingrediente} que ignorabas", "{numero} razones para usar {ingrediente} HOY"],
    "secreto_revelado": ["El SECRETO de {ingrediente} que las farmacéuticas ocultan", "Lo que NADIE te dice sobre {ingrediente}"],
    "advertencia_salud": ["⚠️ NO tomes {ingrediente} sin saber esto", "🚨 ALERTA: Esto pasa si usas {ingrediente}"],
    "resultado_inmediato": ["Así {beneficio} con {ingrediente} en 7 días", "Elimina {problema} naturalmente con {ingrediente}"],
}

PSICOLOGIA_COLOR_SALUD = {
    "energia": {"acento": "#2EC4B6"}, "naturaleza": {"acento": "#FFD166"},
    "confianza": {"acento": "#FFD166"}, "urgencia": {"acento": "#F1FAEE"}, "bienestar": {"acento": "#FFD166"}
}

# ================================================================
# 📊 ALGORITMO DE PREDICCIÓN DE VIRALIDAD (DEL BOT DE TERROR, ADAPTADO)
# ================================================================
def calcular_puntuacion_viralidad(tema):
    factores = {
        "busquedas": tema["busquedas"] / 1000000 * 30,
        "ctr_potencial": tema["ctr_potencial"] * 2.5,
        "retencion": tema["retencion_objetivo"] * 2.0,
        "tendencia": 10 if tema["tendencia"] == "explosiva" else 5,
    }
    score_total = sum(factores.values())
    return {"score": score_total, "categoria": "Alta" if score_total > 75 else "Media"}

def calcular_score_titulo_salud(titulo):
    score = 50
    if 55 <= len(titulo) <= 70: score += 15
    elif 40 <= len(titulo) <= 80: score += 8
    palabras_poder = ["SECRETO", "COMPROBADO", "CIENTÍFICO", "REAL", "VERDAD", "NADIE", "NUNCA", "EFECTIVO"]
    if any(p in titulo.upper() for p in palabras_poder): score += 12
    if any(c.isdigit() for c in titulo): score += 8
    if "?" in titulo: score += 10
    if sum(1 for c in titulo if c.isupper()) > 3: score += 5
    return min(score, 100)

def generar_titulo_ab_testing(keywords, ingrediente, producto, tema_viral):
    categorias = list(FORMULAS_TITULOS_SALUD.keys())
    if tema_viral in ["dato_cientifico"]: categoria_principal = "pregunta_impacto"
    elif tema_viral in ["advertencia_salud"]: categoria_principal = "advertencia_salud"
    else: categoria_principal = random.choice(categorias)
    
    formulas = FORMULAS_TITULOS_SALUD[categoria_principal]
    variantes = []
    for _ in range(3):
        formula = random.choice(formulas)
        titulo = formula.replace("{ingrediente}", ingrediente).replace("{producto}", producto)
        titulo = titulo.replace("{beneficio}", "mejorar tu salud").replace("{problema}", "malestares")
        palabras = titulo.split()
        for j, palabra in enumerate(palabras):
            if palabra.upper() in ["SECRETO", "NADIE", "PROHIBIDO", "ALERTA", "PELIGRO", "REAL", "VERDAD", "COMPROBADO"]:
                palabras[j] = palabra.upper()
        titulo = " ".join(palabras)
        if len(titulo) > 70: titulo = titulo[:67] + "..."
        variantes.append({"titulo": titulo, "score_predicho": calcular_score_titulo_salud(titulo)})
    
    variantes.sort(key=lambda x: x["score_predicho"], reverse=True)
    return variantes

def predecir_rendimiento_salud(tema, titulo, hora_publicacion):
    score_tema = next((t["ctr_potencial"] for t in TEMAS_VIRALES_SALUD if t["tema"] == tema), 7.0)
    score_titulo = calcular_score_titulo_salud(titulo)
    horario_optimo = ["07", "12", "19"]
    score_horario = 1.0 if hora_publicacion[:2] in horario_optimo else 0.8
    vistas_predichas = int((score_tema * score_titulo * score_horario) * 1000)
    return {
        "vistas_predichas": vistas_predichas,
        "ctr_predicho": round(score_tema * (score_titulo / 100), 2),
        "retencion_predicha": round(70 + (score_titulo / 10), 1),
        "confianza": "Alta" if vistas_predichas > 50000 else "Media"
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
            ingrediente = random.choice(ingredientes) # ✅ SELECCIÓN ALEATORIA
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
                info_ingrediente = f"{item.get('descripcion', '')} - {item.get('caracteristicas_visuales', '')}"
                break
    except: pass

    prompt = f"""Eres un experto en herbolaria y nutrición creando contenido VIRAL para YouTube Shorts.
TEMA VIRAL: {tema_viral['tema'].upper()}
PRODUCTO: {producto['nombre']}
INGREDIENTE PRINCIPAL: {ingrediente}
INFO INGREDIENTE: {info_ingrediente}
BENEFICIOS DEL PRODUCTO: {producto['beneficios']}

REGLAS ESTRICTAS:
- Duración total: 45 segundos exactos
- SEGMENTO 1 (0-25s): Educación sobre {ingrediente}. Inicia con pregunta impactante o dato sorprendente. 2-3 beneficios científicos concretos.
- SEGMENTO 2 (25-45s): Presentación del producto. Menciona {producto['nombre']}. Di que contiene {ingrediente}. CTA claro: "Escríbenos al WhatsApp {WHATSAPP_NUMBER} o busca nuestro asistente en Telegram {TELEGRAM_BOT}".
- Sin emojis en el texto hablado.

Devuelve ESTRICTAMENTE este JSON:
{{
    "titulo": "Título viral (55-70 caracteres)",
    "guion_segmento_1": "Texto de 25 segundos (65-75 palabras)",
    "guion_segmento_2": "Texto de 20 segundos (50-60 palabras)",
    "tags": "tag1, tag2, tag3 (10-15 tags separados por coma)",
    "descripcion_corta": "Descripción SEO (máx 120 caracteres)",
    "gancho_descripcion": "Gancho inicial (máx 90 caracteres)",
    "contexto_descripcion": "Contexto (1 oración)"
}}"""

    for intento in range(6):
        try:
            r = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], 
                      "temperature": 0.75, "max_tokens": 800, "response_format": {"type": "json_object"}}, timeout=60)
            r.raise_for_status()
            respuesta = r.json()["choices"][0]["message"]["content"].strip()
            respuesta = re.sub(r'`json\s*', '', respuesta).replace('`', '')
            inicio, fin = respuesta.find('{'), respuesta.rfind('}')
            json_str = respuesta[inicio:fin+1] if inicio != -1 and fin != -1 else respuesta
            
            data = json.loads(json_str, strict=False)
            if "guion_segmento_1" not in data or len(data["guion_segmento_1"]) < 50:
                raise ValueError("Texto demasiado corto")
            
            titulo = data.get("titulo", "").strip()
            if len(titulo) < 35 or len(titulo) > 75:
                variantes = generar_titulo_ab_testing(data.get("tags", "").split(",")[:3], ingrediente, producto["nombre"], tema_viral["tema"])
                titulo = variantes[0]["titulo"]
            data["titulo"] = titulo
            
            tags_list = [t.strip() for t in data.get("tags", "").split(",") if t.strip()][:12]
            for kw in tema_viral["keywords"][:2]:
                if kw.lower() not in [t.lower() for t in tags_list]: tags_list.append(kw)
            for ext in ["salud natural", "bienestar", "herbolaria", "medicina natural"]:
                if ext not in tags_list and len(tags_list) < 15: tags_list.append(ext)
            
            data["tags"] = ", ".join(tags_list)
            data["hashtags_descripcion"] = f"#Shorts #{tema_viral['tema'].capitalize()} #{ingrediente.replace(' ', '')} #SaludNatural"
            return data
        except Exception as e:
            if intento == 5:
                print(f"❌ Todos los intentos de IA fallaron: {e}")
                sys.exit(1)
            time.sleep(5)

# ================================================================
# 🖼️ IMÁGENES Y VIDEO (CON BLINDAJE ANTI-FALLOS)
# ================================================================
def buscar_imagen_pexels_salud(query, intentos=3):
    if not PEXELS_API_KEY: return None
    variantes = ["natural", "healthy", "organic", "fresh", "herbal"]
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

def componer_imagen_final(url_producto, url_fondo, salida="producto_final.jpg"):
    try:
        r_fondo = requests.get(url_fondo, timeout=15)
        fondo = Image.open(io.BytesIO(r_fondo.content)).convert("RGB").resize((1080, 1920))
        r_prod = requests.get(url_producto, timeout=15, verify=False)
        producto = Image.open(io.BytesIO(r_prod.content)).convert("RGBA")
        
        target_h = int(1920 * 0.45)
        producto = producto.resize((int(producto.width * (target_h / producto.height)), target_h), Image.Resampling.LANCZOS)
        
        sombra = producto.copy().filter(ImageFilter.GaussianBlur(radius=20))
        x, y = (1080 - producto.width) // 2, int(1920 * 0.55)
        
        fondo.paste(sombra, (x - 10, y - 10), sombra)
        fondo.paste(producto, (x, y), producto)
        fondo.save(salida, "JPEG", quality=85)
        return salida
    except Exception as e:
        print(f"⚠️ Error componiendo imagen: {e}. Usando fondo solo.")
        return url_fondo

VOCES_DISPONIBLES = [{"voz": "es-MX-DaliaNeural", "velocidad": "+8%"}, {"voz": "es-MX-JorgeNeural", "velocidad": "+8%"}, {"voz": "es-ES-ElviraNeural", "velocidad": "+8%"}]
CONFIG_VOZ_ACTUAL = random.choice(VOCES_DISPONIBLES)

async def generar_audio(texto, path):
    texto_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\'\"]', '', texto)
    try:
        await edge_tts.Communicate(texto_limpio, CONFIG_VOZ_ACTUAL["voz"], rate=CONFIG_VOZ_ACTUAL["velocidad"]).save(path)
        return path
    except Exception as e:
        print(f"⚠️ Error audio: {e}")
        return None

def crear_video(guion, imagen_path):
    print("🎬 Renderizando video...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    audio1 = loop.run_until_complete(generar_audio(guion["guion_segmento_1"], "seg1.mp3"))
    audio2 = loop.run_until_complete(generar_audio(guion["guion_segmento_2"], "seg2.mp3"))
    loop.close()
    
    if not audio1 or not audio2: return None
    
    clip1, clip2 = AudioFileClip(audio1), AudioFileClip(audio2)
    audio_total = concatenate_audioclips([clip1, clip2])
    duracion = audio_total.duration
    
    video_clip = ImageClip(imagen_path).set_duration(duracion)
    video_clip = video_clip.resize(lambda t: 1 + 0.05 * (t / duracion))
    
    # 🛡️ BLINDAJE ANTI-FALLOS DE MÚSICA
    musicas = [f for f in os.listdir(".") if f.endswith(".mp3") and os.path.getsize(f) > 5000 and not f.startswith("seg")]
    musica_aplicada = False
    if musicas:
        for musica_path in musicas:
            try:
                musica = AudioFileClip(musica_path).subclip(0, duracion).volumex(0.10)
                video_clip = video_clip.set_audio(CompositeAudioClip([audio_total, musica]))
                print("✅ Música de fondo agregada exitosamente")
                musica_aplicada = True
                break
            except Exception:
                continue
    
    if not musica_aplicada:
        print("⚠️ No se pudo cargar música válida. El video se publicará solo con la voz.")
        video_clip = video_clip.set_audio(audio_total)
    
    video_clip.write_videofile("short_final.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    for f in ["seg1.mp3", "seg2.mp3"]:
        if os.path.exists(f): os.remove(f)
    return "short_final.mp4"

# ================================================================
# 📤 SUBIR A YOUTUBE
# ================================================================
def subir_a_youtube(video_path, titulo, tags_str, descripcion_corta, gancho, contexto):
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando YouTube: {e}")
        return None
    
    descripcion = f"{gancho}\n\n{contexto}\n\n📲 **CONTÁCTANOS:**\n💬 WhatsApp: {WHATSAPP_NUMBER}\n🤖 Asistente: {TELEGRAM_BOT}\n\n📦 Envíos a todo México\n#{' #'.join([t.strip() for t in tags_str.split(',')[:5]])} #Shorts #SaludNatural"
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
    print(f"📦 Producto: {producto['nombre']} | 🌱 Ingrediente: {ingrediente}")
    
    tema_viral = max(TEMAS_VIRALES_SALUD, key=lambda x: x.get("ctr_potencial", 0) * random.uniform(0.8, 1.2))
    guion = generar_guion_herbolaria(producto, ingrediente, tema_viral)
    print(f"📝 Título: {guion['titulo']}")
    
    fondo_url = buscar_imagen_pexels_salud(ingrediente)
    imagen_final = componer_imagen_final(producto["imagen_url"], fondo_url)
    
    video_path = crear_video(guion, imagen_final)
    if not video_path:
        print("❌ Error creando video")
        sys.exit(1)
    
    prediccion = predecir_rendimiento_salud(tema_viral["tema"], guion["titulo"], datetime.now(pytz.timezone("America/Mexico_City")).strftime("%H:%M"))
    print(f"\n📊 PREDICCIÓN DE RENDIMIENTO: 👁️ {prediccion['vistas_predichas']:,} vistas | 🎯 CTR: {prediccion['ctr_predicho']}%")
    
    video_id = subir_a_youtube(video_path, guion["titulo"], guion["tags"], guion["descripcion_corta"], guion["gancho_descripcion"], guion["contexto_descripcion"])
    
    if video_id:
        guardar_ingrediente_usado(ingrediente, producto["nombre"])
        guardar_titulo(guion["titulo"])
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        print(f"🎉 ¡Publicado! WhatsApp: {WHATSAPP_NUMBER} | URL: https://youtu.be/{video_id}")
    
    for f in ["short_final.mp4", "producto_final.jpg"]:
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

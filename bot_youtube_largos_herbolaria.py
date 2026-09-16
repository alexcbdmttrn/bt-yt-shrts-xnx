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
    AudioFileClip, CompositeAudioClip, ImageClip,
    concatenate_audioclips, concatenate_videoclips, AudioClip,
    CompositeVideoClip,  # ✅ CORREGIDO: faltaba este import
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

# ================================================================
# 🌿 TEMAS VIRALES
# ================================================================
TEMAS_VIRALES_SALUD = [
    {"tema": "beneficios_ocultos", "keywords_cortas": ["beneficios", "propiedades", "natural"], "keywords_largas": ["beneficios que no conocías", "propiedades medicinales comprobadas"], "ctr_potencial": 9.2},
    {"tema": "remedio_casero", "keywords_cortas": ["remedio casero", "natural", "tradicional"], "keywords_largas": ["remedios caseros efectivos", "tratamiento natural"], "ctr_potencial": 8.8},
    {"tema": "dato_cientifico", "keywords_cortas": ["ciencia", "estudio", "comprobado"], "keywords_largas": ["estudios científicos comprobados", "evidencia científica"], "ctr_potencial": 10.5},
    {"tema": "cura_milagrosa", "keywords_cortas": ["cura", "eliminar", "sanar"], "keywords_largas": ["como eliminar naturalmente", "cura natural efectiva"], "ctr_potencial": 11.3},
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
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).date().isoformat()
    if estado.get("fecha") != hoy:
        estado["fecha"] = hoy
        estado["publicaciones_hoy"] = 0
    if estado.get("publicaciones_hoy", 0) >= MAX_LARGOS_DIA:
        print("✅ Límite diario de videos largos alcanzado.")
        return False
    ultima = estado.get("ultima_publicacion")
    if ultima:
        diff = (datetime.now(pytz.timezone("America/Mexico_City")) - datetime.fromisoformat(ultima)).total_seconds() / 3600
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
# 🤖 IA GENERA GUION
# ================================================================
def ia_genera_guion_largo(producto, ingrediente, tema_viral):
    info_catalogo = obtener_info_ingrediente_catalogo(ingrediente) or "Sin ficha en catálogo; usa conocimiento general verificado."
    curiosidad = obtener_curiosidad_catalogo(ingrediente) or ""

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
1. "hook" (15s, 35-45 palabras): Pregunta o dato impactante del ingrediente (usa el dato curioso si existe).
2. "problema" (30s, 70-85 palabras): El problema/síntoma que sufre la audiencia ({producto.get('recomendado_para')}).
3. "ingrediente" (45s, 105-125 palabras): Presenta el ingrediente estrella, origen e historia breve.
4. "beneficio_1" (30s, 70-85 palabras): Primer beneficio científico concreto.
5. "beneficio_2" (30s, 70-85 palabras): Segundo beneficio científico concreto.
6. "beneficio_3" (30s, 70-85 palabras): Tercer beneficio científico concreto.
7. "producto" (60s, 140-165 palabras): Presenta {producto.get('nombre')}, cómo contiene el ingrediente y modo de empleo.
8. "cta" (60s, 140-165 palabras): Resumen + DEBE terminar EXACTAMENTE con: "¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

REGLAS:
- Si el ingrediente obligatorio suena a saborizante (ej: "Sabor Piña Natural"), habla del ingrediente REAL ("Piña") pero mantén la coherencia con el producto.
- NO digas números de WhatsApp/Telegram en el audio (solo la frase final del cta).
- Tono educativo, cálido y cercano. Sin emojis en el texto hablado.
- Cada segmento incluye "texto_pantalla" (máx 5 palabras) y "query_pexels" (en inglés, imagen horizontal 16:9 del subtema).

Devuelve ESTRICTAMENTE este JSON:
{{
  "ingrediente_real": "nombre real normalizado del ingrediente para voz y búsqueda de imágenes (ej: Piña)",
  "titulo": "Título SEO de video largo (máx 70 chars, sin hashtags, variado: pregunta, número, secreto, cómo, verdad...)",
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
  "tags": "12-15 tags separados por coma (keywords cortas y largas del tema {tema_viral['tema']})",
  "gancho_descripcion": "Gancho máx 90 caracteres",
  "contexto_descripcion": "1-2 oraciones de contexto"
}}"""

    for intento in range(5):
        try:
            print(f"🤖 IA escribiendo guion de 5 min... (intento {intento+1}/5)")
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
                if k not in data.get("segmentos", {}) or len(data["segmentos"][k].get("texto", "")) < 40:
                    raise ValueError(f"Segmento {k} faltante o corto")

            cta_txt = data["segmentos"]["cta"]["texto"]
            if "contactos están en la descripción" not in cta_txt.lower():
                data["segmentos"]["cta"]["texto"] = cta_txt.rstrip() + " ¿Quieres saber más o adquirir este producto? Contáctanos por WhatsApp o a nuestro asesor por Telegram, los contactos están en la descripción."

            data["ingrediente_real"] = data.get("ingrediente_real") or ingrediente
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
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
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
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
        tw = draw.textbbox((0, 0), texto, font=font)[2]
        draw.text(((ANCHO - tw) // 2, ALTO - 122), texto, font=font, fill=(255, 214, 102, 255))
        img.save(salida)
        return salida
    except Exception as e:
        print(f"⚠️ Error overlay CTA: {e}")
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

    # ✅ CompositeVideoClip ya está importado correctamente
    overlay = crear_overlay_cta()
    if overlay:
        cta_clip = ImageClip(overlay, transparent=True).set_start(max(duracion_total - 15, 0)).set_duration(15)
        video = CompositeVideoClip([video, cta_clip], size=(ANCHO, ALTO))

    print("🎬 Renderizando video largo (puede tardar varios minutos)...")
    video.write_videofile(salida, fps=24, codec="libx264", audio_codec="aac",
                          threads=4, preset="ultrafast", verbose=False, logger=None)
    return salida

# ================================================================
# 🖼️ MINIATURA
# ================================================================
def crear_miniatura_larga(img_base, url_producto, texto, salida="thumb_largo.jpg"):
    try:
        with Image.open(img_base) as bg:
            bg = ImageOps.fit(bg.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
            bg = ImageEnhance.Contrast(bg).enhance(1.25).convert("RGBA")
            capa = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(capa)
            d.rectangle([(0, 0), (760, 720)], fill=(0, 0, 0, 150))
            palabras = texto.upper().split()
            lineas, actual = [], ""
            for p in palabras:
                if len(actual + " " + p) > 22: lineas.append(actual); actual = p
                else: actual = (actual + " " + p).strip()
            if actual: lineas.append(actual)
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
            y = 180
            for ln in lineas[:3]:
                d.text((60, y), ln, font=font, fill=(255, 214, 102, 255))
                y += 86
            bg = Image.alpha_composite(bg, capa)
            try:
                rp = requests.get(url_producto, timeout=20, verify=False)
                prod = Image.open(io.BytesIO(rp.content)).convert("RGBA")
                try: prod = remove(prod)
                except Exception: pass
                ph = 560
                prod = prod.resize((int(prod.width * (ph / prod.height)), ph), Image.Resampling.LANCZOS)
                bg.paste(prod, (1280 - prod.width - 60, (720 - ph) // 2), prod)
            except Exception: pass
            bg.convert("RGB").save(salida, "JPEG", quality=92)
            print(f"✅ Miniatura larga creada: {salida}")
            return salida
    except Exception as e:
        print(f"⚠️ Error miniatura larga: {e}")
        return None

# ================================================================
# 📤 SUBIR A YOUTUBE
# ================================================================
def subir_video_largo(video_path, thumb_path, titulo, tags_str, gancho, contexto, ingrediente):
    creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
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
        if f.startswith(("img_largo_", "audio_largo_")) or f in ("cta_overlay.png", "largo_final.mp4", "thumb_largo.jpg"):
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

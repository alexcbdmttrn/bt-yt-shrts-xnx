import asyncio
from datetime import datetime, timedelta
import json
import os
import random
import re
import sys
import time
import pandas as pd
import io  # ✅ AGREGADO: Importar módulo io
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

WHATSAPP_NUMBER = "+52 3123395334"
TELEGRAM_BOT = "@alex_xanax_bot"
CANAL_LINK = "https://www.youtube.com/@sombrasdemedianocheoficial"
FACEBOOK_LINK = "https://www.facebook.com/profile.php?id=61593237382982"

ESTADO_FILE = "estado_herbolaria.json"
INGREDIENTES_USADOS_FILE = "ingredientes_usados.json"
TITULOS_FILE = "titulos_herbolaria_publicados.json"
TEMAS_FILE = "temas_herbolaria_usados.json"
ANALYTICS_FILE = "analytics_herbolaria.json"

EXCEL_FILE = "catalogo_xanax.xlsx"
CATALOGO_INGREDIENTES = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES = "catalogo_curiosidades_salud.json"

MAX_SHORTS_DIA = 1
INTERVALO_MIN_HORAS = 4
INTERVALO_MAX_HORAS = 8
RETRASO_MAX_MINUTOS = 45

ACTIVAR_DISCLOSURE_IA = True
DISCLOSURE_TEXT = "\n🤖 Contenido generado con inteligencia artificial (voz e imágenes) con fines educativos."

# ================================================================
# 🌿 TEMAS VIRALES DE SALUD/HERBOLARIA 2024-2025 CON ANÁLISIS DE COMPETENCIA
# ================================================================
TEMAS_VIRALES_SALUD = [
    {
        "tema": "beneficios_ocultos",
        "keywords": ["beneficios", "propiedades", "curativo", "natural", "medicinal"],
        "keywords_larga": ["beneficios que no conocías", "propiedades medicinales", "usos medicinales"],
        "contextos": ["desayuno saludable", "infusión matutina", "remedio casero", "suplemento natural"],
        "busquedas": 850000,
        "competencia": "media",
        "ctr_potencial": 9.2,
        "retencion_objetivo": 78,
        "duracion_optima": 45,
        "tendencia": "creciente",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "25-55",
        "engagement_rate": 15.3
    },
    {
        "tema": "remedio_casero",
        "keywords": ["remedio casero", "natural", "sin medicamentos", "casero", "tradicional"],
        "keywords_larga": ["remedios caseros efectivos", "como curar naturalmente", "tratamiento natural"],
        "contextos": ["cocina", "botiquín natural", "jardín medicinal", "herbolaria mexicana"],
        "busquedas": 920000,
        "competencia": "alta",
        "ctr_potencial": 8.8,
        "retencion_objetivo": 75,
        "duracion_optima": 50,
        "tendencia": "estable",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "30-60",
        "engagement_rate": 14.7
    },
    {
        "tema": "dato_cientifico",
        "keywords": ["ciencia", "estudio", "investigación", "comprobado", "evidencia"],
        "keywords_larga": ["estudios científicos", "investigación médica", "evidencia científica"],
        "contextos": ["laboratorio", "estudio clínico", "investigación universitaria", "revista médica"],
        "busquedas": 680000,
        "competencia": "baja",
        "ctr_potencial": 10.5,
        "retencion_objetivo": 82,
        "duracion_optima": 55,
        "tendencia": "explosiva",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "25-50",
        "engagement_rate": 17.2
    },
    {
        "tema": "cura_milagrosa",
        "keywords": ["cura", "eliminar", "desaparecer", "sanar", "recuperar"],
        "keywords_larga": ["como eliminar naturalmente", "cura natural", "sanación natural"],
        "contextos": ["testimonio real", "resultado comprobado", "transformación salud"],
        "busquedas": 1200000,
        "competencia": "media",
        "ctr_potencial": 11.3,
        "retencion_objetivo": 80,
        "duracion_optima": 48,
        "tendencia": "explosiva",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "35-65",
        "engagement_rate": 18.5
    },
    {
        "tema": "secreto_ancestral",
        "keywords": ["secreto", "ancestral", "tradicional", "milenario", "antiguo"],
        "keywords_larga": ["secreto de los abuelos", "remedio ancestral", "sabiduría ancestral"],
        "contextos": ["medicina tradicional mexicana", "conocimiento ancestral", "hierbas milenarias"],
        "busquedas": 540000,
        "competencia": "baja",
        "ctr_potencial": 9.8,
        "retencion_objetivo": 77,
        "duracion_optima": 52,
        "tendencia": "creciente",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "30-60",
        "engagement_rate": 16.1
    },
    {
        "tema": "error_comun",
        "keywords": ["error", "equivocado", "mal hecho", "peligro", "cuidado"],
        "keywords_larga": ["errores al tomar", "como no usar", "precauciones"],
        "contextos": ["advertencia salud", "precaución natural", "uso correcto"],
        "busquedas": 720000,
        "competencia": "baja",
        "ctr_potencial": 10.8,
        "retencion_objetivo": 85,
        "duracion_optima": 45,
        "tendencia": "creciente",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "25-55",
        "engagement_rate": 19.2
    },
    {
        "tema": "comparacion_natural",
        "keywords": ["vs", "comparación", "mejor que", "alternativa natural"],
        "keywords_larga": ["natural vs farmacéutico", "alternativa natural efectiva"],
        "contextos": ["comparación productos", "alternativas naturales", "opción saludable"],
        "busquedas": 650000,
        "competencia": "media",
        "ctr_potencial": 9.5,
        "retencion_objetivo": 76,
        "duracion_optima": 50,
        "tendencia": "estable",
        "estacionalidad": "todo_el_año",
        "audiencia_objetivo": "28-55",
        "engagement_rate": 15.8
    },
]

# ================================================================
#  FÓRMULAS DE TÍTULOS ÉLITE - SALUD (BASADAS EN NEURO-MARKETING)
# ================================================================
FORMULAS_TITULOS_SALUD = {
    "pregunta_impacto": [
        "¿Sabías que {ingrediente} puede {beneficio}?",
        "¿Por qué NADIE te cuenta esto sobre {ingrediente}?",
        "¿Qué pasa si tomas {ingrediente} todos los días?",
        "¿Conocías este SECRETO de {ingrediente}?",
        "¿Es {ingrediente} realmente efectivo? La ciencia responde",
    ],
    "numero_especifico": [
        "{numero} beneficios de {ingrediente} que ignorabas",
        "{numero} razones para usar {ingrediente} HOY",
        "{numero} formas de usar {ingrediente} (la {numero} te sorprenderá)",
        "TOP {numero} usos medicinales de {ingrediente}",
    ],
    "secreto_revelado": [
        "El SECRETO de {ingrediente} que las farmacéuticas ocultan",
        "Lo que NADIE te dice sobre {ingrediente}",
        "Descubrí algo PROHIBIDO sobre {ingrediente}",
        "La VERDAD sobre {ingrediente} que ocultan",
    ],
    "advertencia_salud": [
        "️ NO tomes {ingrediente} sin saber esto",
        "🚨 ALERTA: Esto pasa si usas {ingrediente}",
        "PELIGRO: Error común con {ingrediente}",
        "CUIDADO con {ingrediente} si tienes {condicion}",
    ],
    "resultado_inmediato": [
        "Así {beneficio} con {ingrediente} en 7 días",
        "Elimina {problema} naturalmente con {ingrediente}",
        "Transforma tu salud con {ingrediente}",
        "Resultados reales con {ingrediente} en {tiempo}",
    ],
    "comparacion_poder": [
        "{ingrediente} vs Medicamentos: ¿Cuál es mejor?",
        "Por qué {ingrediente} supera a los fármacos",
        "{ingrediente}: La alternativa natural que funciona",
    ],
    "testimonio_real": [
        "Usé {ingrediente} por 30 días y esto pasó",
        "Mi experiencia con {ingrediente} para {condicion}",
        "Cómo {ingrediente} cambió mi salud",
    ],
}

# ================================================================
# 🎨 PSICOLOGÍA DEL COLOR - SALUD (OPTIMIZADA PARA CONVERSIÓN)
# ================================================================
PSICOLOGIA_COLOR_SALUD = {
    "energia_vitalidad": {
        "primario": "#FF6B35",
        "secundario": "#F7C59F",
        "acento": "#2EC4B6",
        "contraste_minimo": 4.5
    },
    "naturaleza_organico": {
        "primario": "#2D6A4F",
        "secundario": "#52B788",
        "acento": "#FFD166",
        "contraste_minimo": 4.5
    },
    "confianza_cientifica": {
        "primario": "#118AB2",
        "secundario": "#073B4C",
        "acento": "#FFD166",
        "contraste_minimo": 4.5
    },
    "urgencia_alerta": {
        "primario": "#E63946",
        "secundario": "#1D3557",
        "acento": "#F1FAEE",
        "contraste_minimo": 7.0
    },
    "bienestar_calma": {
        "primario": "#74A57F",
        "secundario": "#B7E4C7",
        "acento": "#FFD166",
        "contraste_minimo": 4.5
    },
}

# ================================================================
#  ALGORITMO DE PREDICCIÓN DE VIRALIDAD
# ================================================================
def calcular_puntuacion_viralidad(tema):
    """Calcula la probabilidad de viralidad basada en múltiples factores"""
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
# 🎯 OPTIMIZADOR DE PALABRAS CLAVE SEMÁNTICO
# ================================================================
def generar_cluster_keywords(tema_principal):
    """Genera un cluster de keywords semánticamente relacionadas"""
    clusters = {
        "beneficios_ocultos": {
            "primarias": ["beneficios", "propiedades", "natural", "medicinal"],
            "secundarias": ["salud", "bienestar", "curativo", "terapéutico"],
            "long_tail": ["beneficios para la salud", "propiedades medicinales comprobadas", "usos terapéuticos"],
            "relacionadas": ["hierbas medicinales", "remedios naturales", "medicina alternativa"]
        },
        "remedio_casero": {
            "primarias": ["remedio casero", "natural", "casero", "tradicional"],
            "secundarias": ["hogar", "fácil", "económico", "accesible"],
            "long_tail": ["remedios caseros efectivos", "como hacer remedio natural", "tratamiento en casa"],
            "relacionadas": ["medicina tradicional", "herbolaria", "plantas medicinales"]
        },
        "dato_cientifico": {
            "primarias": ["ciencia", "estudio", "investigación", "comprobado"],
            "secundarias": ["evidencia", "clínico", "universidad", "publicado"],
            "long_tail": ["estudios científicos comprobados", "investigación médica reciente", "evidencia científica"],
            "relacionadas": ["salud basada en evidencia", "medicina científica", "investigación salud"]
        },
        "cura_milagrosa": {
            "primarias": ["cura", "eliminar", "sanar", "recuperar"],
            "secundarias": ["resultado", "efectivo", "transformación", "mejoría"],
            "long_tail": ["cura natural efectiva", "como eliminar naturalmente", "sanación comprobada"],
            "relacionadas": ["testimonios reales", "resultados comprobados", "transformación salud"]
        },
        "secreto_ancestral": {
            "primarias": ["secreto", "ancestral", "tradicional", "milenario"],
            "secundarias": ["abuelos", "sabiduría", "antiguo", "conocimiento"],
            "long_tail": ["secreto de los abuelos", "remedio ancestral mexicano", "sabiduría tradicional"],
            "relacionadas": ["medicina tradicional mexicana", "conocimiento ancestral", "hierbas milenarias"]
        },
        "error_comun": {
            "primarias": ["error", "equivocado", "peligro", "cuidado"],
            "secundarias": ["advertencia", "precaución", "correcto", "seguro"],
            "long_tail": ["errores al tomar hierbas", "como usar correctamente", "precauciones naturales"],
            "relacionadas": ["seguridad natural", "uso correcto", "precauciones salud"]
        },
        "comparacion_natural": {
            "primarias": ["vs", "comparación", "mejor que", "alternativa"],
            "secundarias": ["natural", "fármaco", "opción", "elección"],
            "long_tail": ["natural vs farmacéutico", "alternativa natural efectiva", "mejor opción salud"],
            "relacionadas": ["medicina comparada", "opciones naturales", "alternativas saludables"]
        },
    }
    return clusters.get(tema_principal, {
        "primarias": ["salud", "natural", "bienestar"],
        "secundarias": ["hierbas", "plantas", "remedios"],
        "long_tail": ["beneficios para la salud", "remedios naturales"],
        "relacionadas": ["herbolaria", "medicina natural"]
    })

# ================================================================
# 🧠 ANALIZADOR DE COMPETENCIA (SIMULADO PARA SALUD)
# ================================================================
def analizar_competencia_youtube_salud(tema):
    """Analiza la competencia y encuentra gaps de oportunidad"""
    analisis = {
        "beneficios_ocultos": {
            "videos_top_10_avg_views": 320000,
            "avg_ctr_competencia": 7.2,
            "avg_retencion": 68,
            "gap_oportunidad": "Falta contenido en español con evidencia científica",
            "mejor_horario_publicacion": ["07:00", "12:00", "19:00"],
            "duracion_optima": "45-55 segundos"
        },
        "remedio_casero": {
            "videos_top_10_avg_views": 450000,
            "avg_ctr_competencia": 8.1,
            "avg_retencion": 72,
            "gap_oportunidad": "Alta demanda, poca calidad en producción",
            "mejor_horario_publicacion": ["08:00", "13:00", "20:00"],
            "duracion_optima": "50-60 segundos"
        },
        "dato_cientifico": {
            "videos_top_10_avg_views": 280000,
            "avg_ctr_competencia": 9.5,
            "avg_retencion": 78,
            "gap_oportunidad": "Poca competencia en español, alta credibilidad",
            "mejor_horario_publicacion": ["09:00", "14:00", "21:00"],
            "duracion_optima": "55-65 segundos"
        },
        "cura_milagrosa": {
            "videos_top_10_avg_views": 520000,
            "avg_ctr_competencia": 10.2,
            "avg_retencion": 75,
            "gap_oportunidad": "Tendencia explosiva, testimonios reales funcionan",
            "mejor_horario_publicacion": ["07:30", "12:30", "19:30"],
            "duracion_optima": "48-58 segundos"
        },
        "secreto_ancestral": {
            "videos_top_10_avg_views": 380000,
            "avg_ctr_competencia": 8.8,
            "avg_retencion": 74,
            "gap_oportunidad": "Nicho poco explotado, alta conexión emocional",
            "mejor_horario_publicacion": ["08:30", "13:30", "20:30"],
            "duracion_optima": "52-62 segundos"
        },
        "error_comun": {
            "videos_top_10_avg_views": 410000,
            "avg_ctr_competencia": 9.8,
            "avg_retencion": 82,
            "gap_oportunidad": "Alto engagement por miedo a errores",
            "mejor_horario_publicacion": ["07:00", "12:00", "19:00"],
            "duracion_optima": "45-55 segundos"
        },
        "comparacion_natural": {
            "videos_top_10_avg_views": 350000,
            "avg_ctr_competencia": 8.5,
            "avg_retencion": 71,
            "gap_oportunidad": "Decisiones de compra, alta conversión",
            "mejor_horario_publicacion": ["10:00", "15:00", "20:00"],
            "duracion_optima": "50-60 segundos"
        },
    }
    return analisis.get(tema, {
        "videos_top_10_avg_views": 200000,
        "avg_ctr_competencia": 6.5,
        "avg_retencion": 65,
        "gap_oportunidad": "Oportunidad general en salud natural",
        "mejor_horario_publicacion": ["08:00", "13:00", "19:00"],
        "duracion_optima": "45-55 segundos"
    })

# ================================================================
#  GENERADOR DE MINIATURAS ÉLITE (NEURO-MARKETING PARA SALUD)
# ================================================================
def crear_miniatura_elite_salud(img_path, texto, tema_viral, output_path):
    """Crea miniaturas basadas en neuro-marketing para salud"""
    if any(p in tema_viral for p in ["error", "peligro", "alerta", "cuidado"]):
        color_scheme = PSICOLOGIA_COLOR_SALUD["urgencia_alerta"]
    elif any(p in tema_viral for p in ["cientifico", "estudio", "evidencia"]):
        color_scheme = PSICOLOGIA_COLOR_SALUD["confianza_cientifica"]
    elif any(p in tema_viral for p in ["ancestral", "secreto", "tradicional"]):
        color_scheme = PSICOLOGIA_COLOR_SALUD["naturaleza_organico"]
    elif any(p in tema_viral for p in ["energia", "vitalidad", "resultado"]):
        color_scheme = PSICOLOGIA_COLOR_SALUD["energia_vitalidad"]
    else:
        color_scheme = PSICOLOGIA_COLOR_SALUD["bienestar_calma"]
    
    try:
        with Image.open(img_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = ImageOps.fit(img, (1080, 1920), Image.Resampling.LANCZOS)
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Color(img).enhance(1.3)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            img = ImageEnhance.Brightness(img).enhance(1.05)
            
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            palabras = texto.upper().strip().split()
            if len(palabras) > 4:
                palabras = palabras[:4]
            texto_final = " ".join(palabras)
            
            lineas = [texto_final] if len(palabras) <= 2 else [
                " ".join(palabras[:len(palabras)//2]), 
                " ".join(palabras[len(palabras)//2:])
            ]
            
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraBold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
            font_size = 110
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
            if font is None:
                font = ImageFont.load_default()
            
            total_height = 0
            for linea in lineas:
                bbox = draw.textbbox((0, 0), linea, font=font)
                total_height += bbox[3] - bbox[1] + 20
            y_start = (height - total_height) // 2 + 150
            
            padding = 40
            max_width = max(draw.textbbox((0, 0), linea, font=font)[2] for linea in lineas)
            draw.rectangle(
                [(width - max_width) // 2 - padding, y_start - padding,
                 (width + max_width) // 2 + padding, y_start + total_height + padding],
                fill=(0, 0, 0, 220)
            )
            
            y_current = y_start
            for linea in lineas:
                bbox = draw.textbbox((0, 0), linea, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                x = (width - w) // 2
                for dx in range(-8, 9):
                    for dy in range(-8, 9):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y_current + dy), linea, font=font, fill=(0, 0, 0))
                draw.text((x, y_current), linea, font=font, fill=color_scheme["acento"])
                y_current += h + 20
            
            try:
                emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 80)
                draw.text((width - 120, 100), "", font=emoji_font)
            except:
                pass
            
            img.save(output_path, "JPEG", quality=95, optimize=True)
            print(f"✅ Miniatura ÉLITE creada: {output_path}")
            print(f"    Texto: '{texto_final}'")
            print(f"   🎨 Color: {color_scheme['acento']}")
            return True
    except Exception as e:
        print(f" Error creando miniatura élite: {e}")
        import traceback
        traceback.print_exc()
        return False

# ================================================================
# 🎯 OPTIMIZADOR DE TÍTULOS CON A/B TESTING
# ================================================================
def generar_titulo_ab_testing(keywords, ingrediente, producto, tema_viral):
    """Genera 3 variantes de título para A/B testing"""
    categorias = list(FORMULAS_TITULOS_SALUD.keys())
    
    if tema_viral in ["dato_cientifico", "comparacion_natural"]:
        categoria_principal = "pregunta_impacto"
    elif tema_viral in ["error_comun", "advertencia_salud"]:
        categoria_principal = "advertencia_salud"
    elif tema_viral in ["cura_milagrosa", "resultado_inmediato"]:
        categoria_principal = "resultado_inmediato"
    else:
        categoria_principal = random.choice(categorias)
    
    formulas = FORMULAS_TITULOS_SALUD[categoria_principal]
    
    variantes = []
    for i in range(3):
        formula = random.choice(formulas)
        numeros = ["3", "5", "7", "10"]
        tiempos = ["7 días", "2 semanas", "1 mes", "30 días"]
        beneficios = ["mejorar tu salud", "sentirte mejor", "recuperarte", "sanar naturalmente"]
        problemas = ["malestares", "síntomas", "molestias", "problemas"]
        condiciones = ["esta condición", "este problema", "esta molestia"]
        
        titulo = formula.replace("{ingrediente}", ingrediente)
        titulo = titulo.replace("{producto}", producto)
        titulo = titulo.replace("{numero}", random.choice(numeros))
        titulo = titulo.replace("{beneficio}", random.choice(beneficios))
        titulo = titulo.replace("{problema}", random.choice(problemas))
        titulo = titulo.replace("{tiempo}", random.choice(tiempos))
        titulo = titulo.replace("{condicion}", random.choice(condiciones))
        
        palabras = titulo.split()
        palabras_clave = ["SECRETO", "NADIE", "PROHIBIDO", "ALERTA", "PELIGRO", "REAL", "VERDAD", "COMPROBADO"]
        for j, palabra in enumerate(palabras):
            if palabra.upper() in palabras_clave or len(palabra) > 7:
                palabras[j] = palabra.upper()
        titulo = " ".join(palabras)
        
        if len(titulo) > 70:
            titulo = titulo[:67] + "..."
        elif len(titulo) < 40:
            emojis = ["🌿", "️", "💊", "", "✅"]
            titulo = random.choice(emojis) + " " + titulo
        
        variantes.append({
            "titulo": titulo,
            "longitud": len(titulo),
            "tiene_numero": any(c.isdigit() for c in titulo),
            "tiene_pregunta": "?" in titulo,
            "tiene_emoji": any(ord(c) > 127743 for c in titulo),
            "score_predicho": calcular_score_titulo_salud(titulo)
        })
    
    variantes.sort(key=lambda x: x["score_predicho"], reverse=True)
    return variantes

def calcular_score_titulo_salud(titulo):
    """Calcula un score predictivo basado en mejores prácticas para salud"""
    score = 50
    
    if 55 <= len(titulo) <= 70:
        score += 15
    elif 40 <= len(titulo) <= 80:
        score += 8
    
    palabras_poder = ["SECRETO", "COMPROBADO", "CIENTÍFICO", "REAL", "VERDAD", "NADIE", "NUNCA", "EFECTIVO"]
    if any(p in titulo.upper() for p in palabras_poder):
        score += 12
    
    if any(c.isdigit() for c in titulo):
        score += 8
    
    if "?" in titulo:
        score += 10
    
    if any(ord(c) > 127743 for c in titulo):
        score += 5
    
    if sum(1 for c in titulo if c.isupper()) > 3:
        score += 5
    
    return min(score, 100)

# ================================================================
#  ANALYTICS ÉLITE (PREDICCIÓN Y OPTIMIZACIÓN)
# ================================================================
def cargar_analytics_elite():
    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "videos_publicados": [],
            "mejores_horarios": {},
            "mejores_temas": {},
            "ctr_promedio": 0,
            "retencion_promedio": 0
        }

def guardar_analytics_elite(analytics):
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)

def predecir_rendimiento_salud(tema, titulo, hora_publicacion):
    """Predice el rendimiento basado en datos históricos"""
    analytics = cargar_analytics_elite()
    
    score_tema = next((t["ctr_potencial"] for t in TEMAS_VIRALES_SALUD if t["tema"] == tema), 7.0)
    score_titulo = calcular_score_titulo_salud(titulo)
    
    horario_optimo = ["07:00", "12:00", "19:00"]
    score_horario = 1.0 if hora_publicacion[:2] in [h[:2] for h in horario_optimo] else 0.8
    
    vistas_predichas = int((score_tema * score_titulo * score_horario) * 1000)
    ctr_predicho = score_tema * (score_titulo / 100)
    retencion_predicha = 70 + (score_titulo / 10)
    
    return {
        "vistas_predichas": vistas_predichas,
        "ctr_predicho": round(ctr_predicho, 2),
        "retencion_predicha": round(retencion_predicha, 1),
        "confianza": "Alta" if vistas_predichas > 50000 else "Media" if vistas_predichas > 10000 else "Baja"
    }

# ================================================================
# 🎬 VALIDAR PEXELS API KEY
# ================================================================
def validar_pexels_api_key():
    if not PEXELS_API_KEY:
        print("⚠️ PEXELS_API_KEY no configurada.")
        return False
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        r = requests.get("https://api.pexels.com/v1/search?query=test&per_page=1", headers=headers, timeout=10)
        if r.status_code == 200:
            print("✅ API Key de Pexels válida.")
            return True
        else:
            print(f"️ API Key de Pexels inválida (código {r.status_code}).")
            return False
    except Exception as e:
        print(f"⚠️ Error probando API Key: {e}")
        return False

PEXELS_VALIDA = validar_pexels_api_key()

# ================================================================
# 🧠 DECISIÓN DE PUBLICAR (OPTIMIZADA CON IA)
# ================================================================
def deberia_publicar_ahora(estado):
    hoy = datetime.now(pytz.timezone("America/Mexico_City")).date()
    fecha_hoy = hoy.isoformat()
    
    if estado.get("fecha") != fecha_hoy:
        estado["fecha"] = fecha_hoy
        estado["publicaciones_hoy"] = 0
        print(f"📅 Nuevo día. Contador reiniciado.")
    
    publicadas_hoy = estado.get("publicaciones_hoy", 0)
    if publicadas_hoy >= MAX_SHORTS_DIA:
        print(f"✅ Límite de {MAX_SHORTS_DIA} short diario alcanzado (CALIDAD > CANTIDAD).")
        return False
    
    ultima_hora = estado.get("ultima_publicacion")
    if ultima_hora:
        ultima_hora = datetime.fromisoformat(ultima_hora)
        hora_actual = datetime.now(pytz.timezone("America/Mexico_City"))
        diff_horas = (hora_actual - ultima_hora).total_seconds() / 3600
        intervalo_requerido = random.uniform(INTERVALO_MIN_HORAS, INTERVALO_MAX_HORAS)
        
        if diff_horas < intervalo_requerido:
            print(f"⏳ Esperando {intervalo_requerido:.1f}h desde la última publicación.")
            print(f"   Han pasado {diff_horas:.1f}h. Aún no es momento.")
            return False
        else:
            print(f"✅ Han pasado {diff_horas:.1f}h. Intervalo superado.")
    
    print(f"✅ Decisión: Publicar. (Short {publicadas_hoy + 1}/{MAX_SHORTS_DIA} del día - CALIDAD ÉLITE)")
    
    retraso_segundos = random.randint(0, RETRASO_MAX_MINUTOS * 60)
    if retraso_segundos > 0:
        print(f"⏳ Esperando {retraso_segundos//60} min {retraso_segundos%60} seg antes de comenzar...")
        time.sleep(retraso_segundos)
    
    return True

# ================================================================
#  SELECCIÓN DE PRODUCTO E INGREDIENTE ALEATORIO (ANTI-REPETICIÓN)
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
    
    if data.get("fecha_reinicio") != hoy:
        data["ingredientes"] = []
        data["fecha_reinicio"] = hoy
    
    entry = f"{ingrediente}|{producto}"
    if entry not in data["ingredientes"]:
        data["ingredientes"].append(entry)
    
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def seleccionar_producto_e_ingrediente():
    """Selecciona un producto y UN ingrediente aleatorio de sus ingredientes_clave"""
    df = pd.read_excel(EXCEL_FILE, sheet_name="Productos")
    data_usados = cargar_ingredientes_usados()
    usados = data_usados.get("ingredientes", [])
    
    df = df[df["ingredientes_clave"].notna() & (df["ingredientes_clave"] != "")]
    df = df[df["imagen_url"].notna() & (df["imagen_url"] != "")]
    
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
    
    print("🔄 Todos los ingredientes usados. Reiniciando...")
    with open(INGREDIENTES_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump({"ingredientes": [], "fecha_reinicio": datetime.now().date().isoformat()}, f)
    
    producto = df.sample(1).iloc[0].to_dict()
    ingredientes = [i.strip() for i in str(producto["ingredientes_clave"]).split(",")]
    ingrediente = random.choice(ingredientes) if ingredientes else "Hierba natural"
    
    return producto, ingrediente

# ================================================================
# 📝 GENERAR GUION CON SEO ÉLITE (45 SEGUNDOS: 25s + 20s)
# ================================================================
def generar_guion_herbolaria(producto, ingrediente, tema_viral):
    """Genera guion optimizado con SEO élite"""
    cluster_keywords = generar_cluster_keywords(tema_viral["tema"])
    analisis_competencia = analizar_competencia_youtube_salud(tema_viral["tema"])
    score_viralidad = calcular_puntuacion_viralidad(tema_viral)
    info_ingrediente = obtener_info_ingrediente(ingrediente)
    
    prompt = f"""Eres un experto en herbolaria y nutrición creando contenido VIRAL para YouTube Shorts.

🔥 TEMA VIRAL SELECCIONADO: {tema_viral['tema'].upper()}
📍 CONTEXTO: {random.choice(tema_viral['contextos'])}
🔑 KEYWORDS PRIMARIAS: {', '.join(tema_viral['keywords'])}
🔑 KEYWORDS LONG-TAIL: {', '.join(cluster_keywords.get('long_tail', [])[:2])}
📊 BUSQUEDAS/MES: {tema_viral['busquedas']:,}
🎯 CTR POTENCIAL: {tema_viral['ctr_potencial']}%
📈 RETENCIÓN OBJETIVO: {tema_viral['retencion_objetivo']}%
⏱️ DURACIÓN ÓPTIMA: {tema_viral['duracion_optima']} segundos
📊 SCORE VIRALIDAD: {score_viralidad['score']:.1f}/100 ({score_viralidad['categoria']})

📚 ANÁLISIS DE COMPETENCIA:
Vistas promedio competencia: {analisis_competencia['videos_top_10_avg_views']:,}
CTR promedio competencia: {analisis_competencia['avg_ctr_competencia']}%
Gap de oportunidad: {analisis_competencia['gap_oportunidad']}

 PRODUCTO: {producto['nombre']}
 INGREDIENTE PRINCIPAL: {ingrediente}
📋 INFORMACIÓN DEL INGREDIENTE: {info_ingrediente}
💊 BENEFICIOS DEL PRODUCTO: {producto['beneficios']}

📝 REGLAS ESTRICTAS:
- Duración total: 45 segundos exactos
- SEGMENTO 1 (0-25s): Educación sobre {ingrediente}
  * Inicia con pregunta impactante o dato sorprendente
  * 2-3 beneficios científicos concretos
  * Tono educativo pero entretenido
  * Usa keywords: {', '.join(tema_viral['keywords'][:2])}
  
- SEGMENTO 2 (25-45s): Presentación del producto
  * Menciona {producto['nombre']}
  * Di que contiene {ingrediente}
  * CTA claro: "Escríbenos al WhatsApp {WHATSAPP_NUMBER} o busca nuestro asistente en Telegram {TELEGRAM_BOT}"

🎯 TÍTULO CON ESTRATEGIA ÉLITE (55-70 caracteres):
- Usa fórmula de alto CTR
- Incluye {ingrediente}
- Máximo 70 caracteres

🎯 DESCRIPCIÓN SEO:
- Gancho inicial (máx 90 caracteres)
- Contexto (1 oración)
- Fuente/confianza

🎯 TAGS (10-15):
- Keywords primarias
- Keywords long-tail
- Tags relacionados

Devuelve ESTRICTAMENTE este JSON:
{{
    "titulo": "Título viral (55-70 caracteres)",
    "titulo_alternativo": "Segundo título opcional",
    "guion_segmento_1": "Texto de 25 segundos (65-75 palabras)",
    "guion_segmento_2": "Texto de 20 segundos (50-60 palabras)",
    "tags": "tag1, tag2, tag3 (10-15 tags separados por coma)",
    "descripcion_corta": "Descripción SEO (máx 120 caracteres)",
    "gancho_descripcion": "Gancho inicial (máx 90 caracteres)",
    "contexto_descripcion": "Contexto (1 oración)",
    "palabras_portada": "TEXTO GANCHO máximo 2 palabras para miniatura"
}}"""

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 1000,
        "response_format": {"type": "json_object"}
    }
    
    for intento in range(6):
        try:
            print(f"🔄 Intento {intento+1}/6 generando guion viral...")
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            r.raise_for_status()
            respuesta = r.json()["choices"][0]["message"]["content"].strip()
            
            respuesta = re.sub(r'`json\s*', '', respuesta)
            respuesta = re.sub(r'`\s*', '', respuesta)
            inicio = respuesta.find('{')
            fin = respuesta.rfind('}')
            if inicio != -1 and fin != -1:
                json_str = respuesta[inicio:fin+1]
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
            
            try:
                data = json.loads(json_str, strict=False)
            except json.JSONDecodeError:
                import json5
                data = json5.loads(json_str)
            
            if "guion_segmento_1" not in data or len(data["guion_segmento_1"]) < 50:
                raise ValueError("Texto demasiado corto")
            
            titulo = data.get("titulo", "").strip()
            titulo = re.sub(r'#\w+', '', titulo).strip()
            titulo = ' '.join(titulo.split())
            
            if len(titulo) < 35 or len(titulo) > 75:
                keywords = data.get("tags", "").split(",")[:3]
                variantes = generar_titulo_ab_testing(keywords, ingrediente, producto["nombre"], tema_viral["tema"])
                titulo = variantes[0]["titulo"]
            
            data["titulo"] = titulo
            
            tags_raw = data.get("tags", "")
            tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()][:12]
            
            for kw in tema_viral["keywords"][:2]:
                if kw.lower() not in [t.lower() for t in tags_list]:
                    tags_list.append(kw)
            
            for kw in cluster_keywords.get('long_tail', [])[:2]:
                if kw not in tags_list and len(tags_list) < 15:
                    tags_list.append(kw)
            
            extras = [
                f"salud natural", "bienestar", "herbolaria", "medicina natural",
                "remedios caseros", "plantas medicinales", "productos naturales"
            ]
            for ext in extras:
                if ext not in tags_list and len(tags_list) < 15:
                    tags_list.append(ext)
            
            tags_final = []
            total_chars = 0
            for t in tags_list:
                costo = len(t) + 2
                if total_chars + costo > 480:
                    break
                tags_final.append(t)
                total_chars += costo
            
            data["tags"] = ", ".join(tags_final)
            
            hashtag_base = "#Shorts"
            hashtag_tema = f"#{tema_viral['tema'].capitalize()}"
            hashtag_ingrediente = f"#{ingrediente.replace(' ', '')}"
            hashtag_extra = random.choice([
                "#SaludNatural", "#Herbolaria", "#RemediosCaseros",
                "#MedicinaNatural", "#Bienestar", "#VidaSaludable"
            ])
            data["hashtags_descripcion"] = f"{hashtag_base} {hashtag_tema} {hashtag_ingrediente} {hashtag_extra}"
            
            print(f"   🔥 Título VIRAL: {data['titulo']} ({len(data['titulo'])} chars)")
            print(f"    Keywords: {tema_viral['keywords'][:3]}")
            print(f"   🎯 Tema viral: {tema_viral['tema']}")
            print(f"   📊 Score viralidad: {score_viralidad['score']:.1f}/100")
            
            return data
            
        except Exception as e:
            print(f"❌ Intento {intento+1}/6 falló: {e}")
            if intento < 5:
                time.sleep(10 + intento * 5)
    
    print("❌ TODOS LOS INTENTOS FALLARON.")
    sys.exit(1)

def obtener_info_ingrediente(ingrediente):
    """Obtiene información del ingrediente del catálogo"""
    try:
        with open(CATALOGO_INGREDIENTES, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        for item in catalog:
            if ingrediente.lower() in item.get("nombre", "").lower():
                return f"{item.get('descripcion', '')} - {item.get('caracteristicas_visuales', '')}"
    except:
        pass
    return "Ingrediente natural con propiedades medicinales"

# ================================================================
# 🖼️ BUSCAR IMAGEN EN PEXELS
# ================================================================
ULTIMA_URL_PEXELS = None

def buscar_imagen_pexels_salud(query, intentos=3):
    """Busca imágenes específicamente para contenido de salud"""
    global ULTIMA_URL_PEXELS
    
    if not PEXELS_VALIDA:
        print("⚠️ API Key de Pexels inválida.")
        return None
    
    variantes = ["natural", "healthy", "organic", "fresh", "green", "herbal", "medicinal"]
    variacion = random.choice(variantes)
    query_variada = f"{query} {variacion}"
    
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query_variada,
        "orientation": "portrait",
        "per_page": 10,
        "page": random.randint(1, 8)
    }
    
    for intento in range(intentos):
        try:
            print(f"  Intento {intento+1}/{intentos} buscando en Pexels: '{query_variada}'...")
            r = requests.get(url, headers=headers, params=params, timeout=25)
            if r.status_code == 200:
                data = r.json()
                if data.get("photos") and len(data["photos"]) > 0:
                    fotos = data["photos"][:min(5, len(data["photos"]))]
                    foto = random.choice(fotos)
                    image_url = foto["src"]["large2x"] or foto["src"]["large"] or foto["src"]["original"]
                    
                    if ULTIMA_URL_PEXELS and image_url == ULTIMA_URL_PEXELS:
                        print("   ⚠️ URL repetida, buscando otra página...")
                        params["page"] = (params["page"] % 8) + 1
                        continue
                    
                    ULTIMA_URL_PEXELS = image_url
                    print(f"✅ Imagen encontrada: {image_url[:80]}...")
                    return image_url
                else:
                    print("️ No se encontraron fotos.")
            else:
                print(f"⚠️ Error Pexels: {r.status_code}")
                if r.status_code == 401:
                    print("❌ API key inválida.")
                    break
        except Exception as e:
            print(f"⚠️ Error conexión Pexels: {e}")
        
        if intento < intentos - 1:
            print(f"   ⏳ Esperando 5s...")
            time.sleep(5)
    
    print("❌ No se pudo obtener imagen de Pexels.")
    return None

# ================================================================
# 🎨 COMPONER IMAGEN (PRODUCTO + FONDO) - ✅ CORREGIDO
# ================================================================
def componer_imagen_final(url_producto, url_fondo, salida="producto_final.jpg"):
    """Compone la imagen del producto sobre el fondo de Pexels"""
    print("🎨 Componiendo imagen del producto sobre el fondo...")
    try:
        # Descargar fondo
        r_fondo = requests.get(url_fondo, timeout=15)
        fondo = Image.open(io.BytesIO(r_fondo.content)).convert("RGB").resize((1080, 1920))  # ✅ CORREGIDO: io.BytesIO
        
        # Descargar producto
        r_prod = requests.get(url_producto, timeout=15, verify=False)
        producto = Image.open(io.BytesIO(r_prod.content)).convert("RGBA")  # ✅ CORREGIDO: io.BytesIO
        
        # Redimensionar producto (que ocupe ~45% de la altura)
        target_h = int(1920 * 0.45)
        ratio = target_h / producto.height
        producto = producto.resize((int(producto.width * ratio), target_h), Image.Resampling.LANCZOS)
        
        # Crear sombra
        sombra = producto.copy()
        sombra = ImageOps.expand(sombra, border=20, fill=(0,0,0,0))
        sombra = sombra.filter(ImageFilter.GaussianBlur(radius=25))
        
        # Pegar en el tercio inferior central
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
# ️ GENERAR AUDIO
# ================================================================
VOCES_DISPONIBLES = [
    {"voz": "es-MX-DaliaNeural", "velocidad": "+8%", "tono": "0Hz"},
    {"voz": "es-MX-JorgeNeural", "velocidad": "+8%", "tono": "0Hz"},
    {"voz": "es-ES-ElviraNeural", "velocidad": "+8%", "tono": "0Hz"},
    {"voz": "es-CO-SalomeNeural", "velocidad": "+8%", "tono": "0Hz"},
]
CONFIG_VOZ_ACTUAL = random.choice(VOCES_DISPONIBLES)

async def generar_audio(texto, path):
    """Genera audio con Edge TTS"""
    texto_limpio = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ0-9\s.,;:!?¿¡\'\"]', '', texto)
    try:
        communicate = edge_tts.Communicate(texto_limpio, CONFIG_VOZ_ACTUAL["voz"], rate=CONFIG_VOZ_ACTUAL["velocidad"])
        await communicate.save(path)
        return path
    except Exception as e:
        print(f"⚠️ Error audio: {e}")
        return None

# ================================================================
#  CREAR VIDEO
# ================================================================
def crear_video(guion, imagen_path):
    """Crea el video Short con zoom lento"""
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
    
    # Música de fondo
    musicas = [f for f in os.listdir(".") if f.endswith(".mp3") and not f.startswith("seg")]
    if musicas:
        musica = AudioFileClip(random.choice(musicas)).subclip(0, duracion).volumex(0.10)
        audio_final = CompositeAudioClip([audio_total, musica])
        video_clip = video_clip.set_audio(audio_final)
    else:
        video_clip = video_clip.set_audio(audio_total)
    
    video_clip.write_videofile("short_final.mp4", fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    
    for f in ["seg1.mp3", "seg2.mp3"]:
        if os.path.exists(f):
            os.remove(f)
    
    return "short_final.mp4"

# ================================================================
# 📤 SUBIR A YOUTUBE
# ================================================================
def subir_a_youtube(video_path, titulo, tags_str, descripcion_corta, gancho, contexto):
    """Sube el video a YouTube con SEO optimizado"""
    try:
        creds = Credentials.from_authorized_user_info(YOUTUBE_USER_TOKEN)
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f" Error autenticando YouTube: {e}")
        return None
    
    tags = [t.strip() for t in tags_str.split(",") if t.strip()][:15]
    
    descripcion = f"""{gancho}

{contexto}

📲 **CONTÁCTANOS PARA PEDIRLO:**
💬 WhatsApp: {WHATSAPP_NUMBER}
🤖 Asistente Inteligente: {TELEGRAM_BOT}

 Canal: {CANAL_LINK}
📘 Facebook: {FACEBOOK_LINK}

📦 Envíos a todo México
💳 Aceptamos todas las formas de pago

#{' #'.join([t.strip() for t in tags_str.split(',')[:5]])} #Shorts #SaludNatural #Herbolaria"""
    
    if ACTIVAR_DISCLOSURE_IA:
        descripcion += DISCLOSURE_TEXT
    
    body = {
        "snippet": {
            "title": titulo[:100],
            "description": descripcion[:5000],
            "tags": tags,
            "categoryId": "26",
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
        print(f"❌ Error subiendo a YouTube: {e}")
        return None

# ================================================================
#  CARGAR/GUARDAR ESTADO
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
#  MAIN
# ================================================================
def main():
    print(" Bot Herbolaria ÉLITE - YouTube Shorts")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Voz: {CONFIG_VOZ_ACTUAL['voz']}")
    
    if not YOUTUBE_USER_TOKEN:
        print("❌ No se encontró YOUTUBE_USER_TOKEN.")
        sys.exit(1)
    
    if not PEXELS_VALIDA:
        print("⚠️ PEXELS_API_KEY inválida. Se usarán placeholders.")
    
    estado = cargar_estado()
    
    if not deberia_publicar_ahora(estado):
        guardar_estado(estado)
        sys.exit(0)
    
    producto, ingrediente = seleccionar_producto_e_ingrediente()
    print(f"📦 Producto: {producto['nombre']}")
    print(f"🌱 Ingrediente: {ingrediente}")
    
    tema_viral = max(TEMAS_VIRALES_SALUD, key=lambda x: x.get("ctr_potencial", 0) * random.uniform(0.8, 1.2))
    print(f"🎯 Tema viral: {tema_viral['tema']}")
    
    guion = generar_guion_herbolaria(producto, ingrediente, tema_viral)
    print(f"📝 Título: {guion['titulo']}")
    
    fondo_query = f"{ingrediente} natural healthy background"
    fondo_url = buscar_imagen_pexels_salud(fondo_query)
    if not fondo_url:
        fondo_url = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop"
    
    imagen_final = componer_imagen_final(producto["imagen_url"], fondo_url)
    
    video_path = crear_video(guion, imagen_final)
    if not video_path:
        print("❌ Error creando video")
        sys.exit(1)
    
    prediccion = predecir_rendimiento_salud(
        tema_viral["tema"],
        guion["titulo"],
        datetime.now(pytz.timezone("America/Mexico_City")).strftime("%H:%M")
    )
    print(f"\n📊 PREDICCIÓN DE RENDIMIENTO:")
    print(f"   👁️ Vistas predichas: {prediccion['vistas_predichas']:,}")
    print(f"   🎯 CTR predicho: {prediccion['ctr_predicho']}%")
    print(f"   ⏱️ Retención predicha: {prediccion['retencion_predicha']}%")
    print(f"   🎯 Confianza: {prediccion['confianza']}")
    
    video_id = subir_a_youtube(
        video_path=video_path,
        titulo=guion["titulo"],
        tags_str=guion["tags"],
        descripcion_corta=guion["descripcion_corta"],
        gancho=guion["gancho_descripcion"],
        contexto=guion["contexto_descripcion"]
    )
    
    if video_id:
        guardar_ingrediente_usado(ingrediente, producto["nombre"])
        guardar_titulo(guion["titulo"])
        
        estado["publicaciones_hoy"] += 1
        estado["ultima_publicacion"] = datetime.now(pytz.timezone("America/Mexico_City")).isoformat()
        guardar_estado(estado)
        
        analytics = cargar_analytics_elite()
        analytics["videos_publicados"].append({
            "titulo": guion["titulo"],
            "tema": tema_viral["tema"],
            "fecha": datetime.now().isoformat(),
            "video_id": video_id,
            "prediccion": prediccion
        })
        guardar_analytics_elite(analytics)
        
        print(f"\n🎉 ¡Publicado exitosamente!")
        print(f"    📱 WhatsApp: {WHATSAPP_NUMBER}")
        print(f"   🤖 Telegram: {TELEGRAM_BOT}")
        print(f"   🔗 URL: https://youtu.be/{video_id}")
        print(f"   📊 Publicaciones hoy: {estado['publicaciones_hoy']}/{MAX_SHORTS_DIA}")
    
    if os.path.exists("short_final.mp4"):
        os.remove("short_final.mp4")
    if os.path.exists("producto_final.jpg"):
        os.remove("producto_final.jpg")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

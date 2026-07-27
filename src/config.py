"""Configuración central del proyecto.

Lee las variables de entorno desde un archivo .env en desarrollo local, o
directamente del entorno cuando corre en Hugging Face Spaces (donde las claves
se definen como Secrets del Space).

El proyecto funciona con dos proveedores de modelos. Si no se declara uno de
forma explícita, se elige según la clave que esté disponible, dando prioridad a
Google porque su nivel gratuito no exige tarjeta de crédito.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent

load_dotenv(RAIZ / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

PROVEEDORES = ("google", "openai")

# Modelos por defecto de cada proveedor. Ambos necesitan soportar visión, ya
# que las pruebas escaneadas y las fotos se procesan como imágenes.
MODELOS_POR_DEFECTO = {
    "google": {"vision": "gemini-2.5-flash", "razonamiento": "gemini-2.5-flash"},
    "openai": {"vision": "gpt-4.1-mini", "razonamiento": "gpt-4.1"},
}


def _resolver_proveedor() -> str:
    """Determina qué proveedor usar según la configuración disponible."""
    declarado = os.getenv("PROVEEDOR", "").strip().lower()

    if declarado in PROVEEDORES:
        return declarado

    if GOOGLE_API_KEY:
        return "google"

    return "openai"


PROVEEDOR = _resolver_proveedor()

# Modelo con capacidad de visión: transcribe fotos y PDF escaneados.
MODELO_VISION = (
    os.getenv("MODELO_VISION", "").strip()
    or MODELOS_POR_DEFECTO[PROVEEDOR]["vision"]
)

# Modelo de razonamiento: corrige ejercicios y genera variantes.
MODELO_RAZONAMIENTO = (
    os.getenv("MODELO_RAZONAMIENTO", "").strip()
    or MODELOS_POR_DEFECTO[PROVEEDOR]["razonamiento"]
)

# Límites para controlar costo y tiempo de respuesta.
MAX_PAGINAS = int(os.getenv("MAX_PAGINAS", "8"))
MAX_LADO_IMAGEN = int(os.getenv("MAX_LADO_IMAGEN", "1600"))
DPI_RENDER_PDF = int(os.getenv("DPI_RENDER_PDF", "180"))
MAX_HILOS = int(os.getenv("MAX_HILOS", "6"))

EJEMPLOS = RAIZ / "ejemplos"

EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_VALIDAS = EXTENSIONES_IMAGEN | EXTENSIONES_PDF


def clave_activa() -> str:
    """Devuelve la clave del proveedor seleccionado."""
    return GOOGLE_API_KEY if PROVEEDOR == "google" else OPENAI_API_KEY


def hay_credenciales() -> bool:
    """Indica si el proveedor seleccionado tiene una clave configurada."""
    return bool(clave_activa())


def nombre_proveedor() -> str:
    """Nombre legible del proveedor, para mostrarlo en la interfaz."""
    return "Google Gemini" if PROVEEDOR == "google" else "OpenAI"

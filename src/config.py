"""Configuración central del proyecto.

Lee las variables de entorno desde un archivo .env en desarrollo local, o
directamente del entorno cuando corre en Hugging Face Spaces (donde la clave
se define como Secret del Space).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent

load_dotenv(RAIZ / ".env")

# Clave de OpenAI. En Hugging Face Spaces se define en Settings > Secrets.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Modelo con capacidad de visión: transcribe fotos y PDF escaneados.
MODELO_VISION = os.getenv("MODELO_VISION", "gpt-4o-mini")

# Modelo de razonamiento: corrige ejercicios y genera variantes.
MODELO_RAZONAMIENTO = os.getenv("MODELO_RAZONAMIENTO", "gpt-4o")

# Límites para controlar costo y tiempo de respuesta.
MAX_PAGINAS = int(os.getenv("MAX_PAGINAS", "8"))
MAX_LADO_IMAGEN = int(os.getenv("MAX_LADO_IMAGEN", "1600"))
DPI_RENDER_PDF = int(os.getenv("DPI_RENDER_PDF", "180"))
MAX_HILOS = int(os.getenv("MAX_HILOS", "6"))

EJEMPLOS = RAIZ / "ejemplos"

EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_VALIDAS = EXTENSIONES_IMAGEN | EXTENSIONES_PDF


def hay_credenciales() -> bool:
    """Indica si existe una clave de API configurada."""
    return bool(OPENAI_API_KEY)

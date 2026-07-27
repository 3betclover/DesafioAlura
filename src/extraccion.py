"""Extracción de contenido desde PDF e imágenes.

El objetivo de este módulo es dejar cualquier archivo de entrada en un formato
único que el modelo pueda leer: una lista de páginas, cada una con su imagen
codificada en base64 y, cuando existe, la capa de texto del PDF.

Se envía siempre la imagen porque las pruebas suelen mezclar enunciado impreso
con desarrollo manuscrito, y ese manuscrito no aparece en la capa de texto. El
texto extraído se adjunta como apoyo: mejora la transcripción de enunciados
largos y reduce errores en símbolos poco legibles.
"""

import base64
import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.config import (
    DPI_RENDER_PDF,
    EXTENSIONES_IMAGEN,
    EXTENSIONES_PDF,
    EXTENSIONES_VALIDAS,
    MAX_LADO_IMAGEN,
    MAX_PAGINAS,
)

try:  # PyMuPDF cambió el nombre del paquete en la versión 1.24.3
    import pymupdf
except ImportError:  # pragma: no cover - respaldo para versiones antiguas
    import fitz as pymupdf


class ArchivoNoSoportado(Exception):
    """Se intentó procesar un archivo con una extensión que no manejamos."""


@dataclass
class Pagina:
    """Una página del documento, lista para enviarse al modelo."""

    numero: int
    imagen_b64: str
    texto: str = ""

    @property
    def tiene_texto_util(self) -> bool:
        """Indica si la capa de texto aporta información aprovechable."""
        return len(self.texto.strip()) >= 40


def _optimizar(datos: bytes) -> str:
    """Reduce la imagen a un tamaño razonable y la codifica en base64.

    Las fotos de celular llegan con resoluciones de varios miles de píxeles.
    Enviarlas completas encarece la llamada sin mejorar la lectura, así que se
    limita el lado mayor y se comprime como JPEG.
    """
    imagen = Image.open(io.BytesIO(datos))

    if imagen.mode not in ("RGB", "L"):
        imagen = imagen.convert("RGB")

    if max(imagen.size) > MAX_LADO_IMAGEN:
        imagen.thumbnail((MAX_LADO_IMAGEN, MAX_LADO_IMAGEN), Image.LANCZOS)

    destino = io.BytesIO()
    imagen.save(destino, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(destino.getvalue()).decode("utf-8")


def _paginas_de_pdf(ruta: Path) -> list[Pagina]:
    """Renderiza cada página del PDF como imagen y recupera su capa de texto."""
    paginas: list[Pagina] = []

    with pymupdf.open(ruta) as documento:
        total = min(len(documento), MAX_PAGINAS)

        for indice in range(total):
            hoja = documento[indice]
            pixmap = hoja.get_pixmap(dpi=DPI_RENDER_PDF)
            paginas.append(
                Pagina(
                    numero=indice + 1,
                    imagen_b64=_optimizar(pixmap.tobytes("png")),
                    texto=hoja.get_text().strip(),
                )
            )

    return paginas


def _paginas_de_imagen(ruta: Path) -> list[Pagina]:
    """Trata una imagen suelta como un documento de una sola página."""
    return [Pagina(numero=1, imagen_b64=_optimizar(ruta.read_bytes()))]


def extraer_paginas(ruta: str | Path) -> list[Pagina]:
    """Convierte un archivo de entrada en una lista de páginas procesables.

    Args:
        ruta: Ubicación del PDF o la imagen que subió la persona usuaria.

    Returns:
        Las páginas del documento, limitadas por `MAX_PAGINAS`.

    Raises:
        FileNotFoundError: Si la ruta no existe.
        ArchivoNoSoportado: Si la extensión no es un PDF ni una imagen conocida.
    """
    ruta = Path(ruta)

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    extension = ruta.suffix.lower()

    if extension not in EXTENSIONES_VALIDAS:
        soportadas = ", ".join(sorted(EXTENSIONES_VALIDAS))
        raise ArchivoNoSoportado(
            f"La extensión '{extension}' no está soportada. Formatos válidos: {soportadas}."
        )

    if extension in EXTENSIONES_PDF:
        return _paginas_de_pdf(ruta)

    if extension in EXTENSIONES_IMAGEN:
        return _paginas_de_imagen(ruta)

    raise ArchivoNoSoportado(f"No se pudo procesar el archivo: {ruta.name}")

"""Genera las pruebas de ejemplo que acompañan a la demo.

Produce dos archivos en la carpeta `ejemplos/`:

- `prueba_matematica_en_blanco.pdf`: sirve para probar el modo Profesor.
- `prueba_matematica_resuelta.pdf`: incluye respuestas simuladas de un
  estudiante, con una mezcla deliberada de aciertos y de errores frecuentes,
  para probar el modo Alumno.

Uso:
    python scripts/generar_prueba_ejemplo.py
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from src.exportar import FUENTE, FUENTE_NEGRITA  # noqa: E402

# Cada ítem define su enunciado, sus alternativas y lo que "escribió" el
# estudiante. Los errores están elegidos a propósito: son los que más aparecen
# en pruebas reales de primero medio.
ITEMS = [
    {
        "enunciado": "Resuelve la ecuación 2x + 5 = 17. Muestra tu desarrollo.",
        "alternativas": [],
        "desarrollo": "2x = 17 - 5<br/>2x = 12<br/>x = 12 / 2",
        "respuesta": "x = 6",
        "puntaje": 2,
    },
    {
        "enunciado": "¿Cuál es el valor de 3<super>4</super>?",
        "alternativas": ["A) 7", "B) 12", "C) 64", "D) 81"],
        "desarrollo": "3 · 4 = 12",
        "respuesta": "B",
        "puntaje": 1,
    },
    {
        "enunciado": "Resuelve la ecuación cuadrática x<super>2</super> − 5x + 6 = 0.",
        "alternativas": [],
        "desarrollo": "(x - 2)(x - 3) = 0",
        "respuesta": "x = 2 y x = 3",
        "puntaje": 3,
    },
    {
        "enunciado": (
            "Un triángulo tiene una base de 12 cm y una altura de 7 cm. "
            "Calcula su área."
        ),
        "alternativas": [],
        "desarrollo": "A = base · altura<br/>A = 12 · 7",
        "respuesta": "84 cm²",
        "puntaje": 2,
    },
    {
        "enunciado": "¿Cuál es el resultado de 3/4 + 1/6?",
        "alternativas": ["A) 4/10", "B) 11/12", "C) 2/5", "D) 4/24"],
        "desarrollo": "3 + 1 = 4 y 4 + 6 = 10",
        "respuesta": "A",
        "puntaje": 1,
    },
    {
        "enunciado": "Calcula el 15% de 240.",
        "alternativas": [],
        "desarrollo": "240 · 0,15",
        "respuesta": "36",
        "puntaje": 2,
    },
    {
        "enunciado": (
            "Un triángulo rectángulo tiene catetos de 6 cm y 8 cm. "
            "¿Cuánto mide su hipotenusa?"
        ),
        "alternativas": [],
        "desarrollo": "h = 6 + 8",
        "respuesta": "14 cm",
        "puntaje": 3,
    },
    {
        "enunciado": (
            "Simplifica la expresión algebraica "
            "(4x<super>2</super>y) / (2xy)."
        ),
        "alternativas": [],
        "desarrollo": "4/2 = 2, x²/x = x, y/y = 1",
        "respuesta": "2x",
        "puntaje": 2,
    },
]


def _estilos() -> dict:
    """Estilos del documento, incluyendo el que simula la letra del estudiante."""
    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "Titulo",
            parent=base["Title"],
            fontName=FUENTE_NEGRITA,
            fontSize=16,
            spaceAfter=2,
        ),
        "subtitulo": ParagraphStyle(
            "Subtitulo",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=12,
        ),
        "datos": ParagraphStyle(
            "Datos",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10,
            leading=20,
            spaceAfter=8,
        ),
        "enunciado": ParagraphStyle(
            "Enunciado",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10.5,
            leading=15,
            spaceBefore=11,
            spaceAfter=3,
        ),
        "alternativa": ParagraphStyle(
            "Alternativa",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10.5,
            leading=14,
            leftIndent=1.1 * cm,
        ),
        # Azul e inclinado para que se distinga del enunciado impreso, tal como
        # se vería una respuesta escrita a mano sobre la hoja.
        "manuscrito": ParagraphStyle(
            "Manuscrito",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=11,
            leading=16,
            leftIndent=1.1 * cm,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=3,
        ),
    }


def construir(ruta: Path, con_respuestas: bool) -> Path:
    """Escribe una de las dos versiones de la prueba de ejemplo."""
    estilos = _estilos()
    elementos: list = []

    elementos.append(Paragraph("Evaluación de Matemática", estilos["titulo"]))
    elementos.append(
        Paragraph("1° medio · Unidad: Álgebra y geometría básica", estilos["subtitulo"])
    )

    nombre = "Camila Rojas Fuentes" if con_respuestas else "_" * 34
    curso = "1° medio B" if con_respuestas else "_" * 12
    elementos.append(
        Paragraph(
            f"Nombre: {nombre}    Curso: {curso}    Puntaje total: 16 puntos",
            estilos["datos"],
        )
    )
    elementos.append(HRFlowable(width="100%", color=colors.HexColor("#CBD5E0")))

    for numero, item in enumerate(ITEMS, start=1):
        elementos.append(
            Paragraph(
                f"<b>{numero}.</b> {item['enunciado']} "
                f"<font size=9 color='#718096'>({item['puntaje']} pts)</font>",
                estilos["enunciado"],
            )
        )

        for alternativa in item["alternativas"]:
            elementos.append(Paragraph(alternativa, estilos["alternativa"]))

        if con_respuestas:
            if item["desarrollo"]:
                elementos.append(Paragraph(item["desarrollo"], estilos["manuscrito"]))
            elementos.append(
                Paragraph(
                    f"Respuesta: {item['respuesta']}",
                    estilos["manuscrito"],
                )
            )
        elif not item["alternativas"]:
            elementos.append(Spacer(1, 2.1 * cm))

    documento = SimpleDocTemplate(
        str(ruta),
        pagesize=A4,
        title="Evaluación de Matemática",
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    documento.build(elementos)

    return ruta


def main() -> None:
    destino = RAIZ / "ejemplos"
    destino.mkdir(exist_ok=True)

    en_blanco = construir(destino / "prueba_matematica_en_blanco.pdf", False)
    resuelta = construir(destino / "prueba_matematica_resuelta.pdf", True)

    for archivo in (en_blanco, resuelta):
        print(f"Generado: {archivo.relative_to(RAIZ)} ({archivo.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

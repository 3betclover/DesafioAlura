"""Genera la prueba de ejemplo que acompaña a la demo.

Produce `ejemplos/prueba_matematica.pdf`, una evaluación de 1° medio **sin
resolver**. Se entrega en blanco a propósito: el trabajo de resolver los
ejercicios le corresponde al agente, no al documento.

El mismo archivo sirve para los dos modos de la aplicación. En el modo
estudiante el agente lo resuelve paso a paso, y en el modo docente genera
versiones equivalentes de cada ítem.

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

# Ítems de la evaluación. Cubren álgebra, geometría y proporcionalidad, que es
# el temario habitual de la primera unidad de 1° medio.
ITEMS = [
    {
        "enunciado": "Resuelve la ecuación 2x + 5 = 17. Muestra tu desarrollo.",
        "alternativas": [],
        "puntaje": 2,
    },
    {
        "enunciado": "¿Cuál es el valor de 3<super>4</super>?",
        "alternativas": ["A) 7", "B) 12", "C) 64", "D) 81"],
        "puntaje": 1,
    },
    {
        "enunciado": "Resuelve la ecuación cuadrática x<super>2</super> − 5x + 6 = 0.",
        "alternativas": [],
        "puntaje": 3,
    },
    {
        "enunciado": (
            "Un triángulo tiene una base de 12 cm y una altura de 7 cm. "
            "Calcula su área."
        ),
        "alternativas": [],
        "puntaje": 2,
    },
    {
        "enunciado": "¿Cuál es el resultado de 3/4 + 1/6?",
        "alternativas": ["A) 4/10", "B) 11/12", "C) 2/5", "D) 4/24"],
        "puntaje": 1,
    },
    {
        "enunciado": "Calcula el 15% de 240.",
        "alternativas": [],
        "puntaje": 2,
    },
    {
        "enunciado": (
            "Un triángulo rectángulo tiene catetos de 6 cm y 8 cm. "
            "¿Cuánto mide su hipotenusa?"
        ),
        "alternativas": [],
        "puntaje": 3,
    },
    {
        "enunciado": (
            "Simplifica la expresión algebraica "
            "(4x<super>2</super>y) / (2xy)."
        ),
        "alternativas": [],
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
    }


def construir(ruta: Path) -> Path:
    """Escribe la prueba de ejemplo, sin resolver."""
    estilos = _estilos()
    elementos: list = []

    elementos.append(Paragraph("Evaluación de Matemática", estilos["titulo"]))
    elementos.append(
        Paragraph("1° medio · Unidad: Álgebra y geometría básica", estilos["subtitulo"])
    )
    elementos.append(
        Paragraph(
            f"Nombre: {'_' * 34}    Curso: {'_' * 12}    Puntaje total: 16 puntos",
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

        # Espacio en blanco para que el estudiante desarrolle a mano.
        if not item["alternativas"]:
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

    archivo = construir(destino / "prueba_matematica.pdf")
    print(f"Generado: {archivo.relative_to(RAIZ)} ({archivo.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

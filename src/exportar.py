"""Exportación de las pruebas generadas a un PDF listo para imprimir.

A partir de las variantes creadas por el agente se arman varias *formas* de la
misma evaluación: la Forma A toma la primera variante de cada ítem, la Forma B
la segunda, y así sucesivamente. Todas miden lo mismo, pero ningún estudiante
sentado al lado tiene la misma hoja.

El archivo resultante incluye al final la pauta de corrección de cada forma.
"""

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from src.modelos import ItemConVariantes

LETRAS_FORMA = "ABCDEFGH"

# Símbolos LaTeX más frecuentes en pruebas escolares y su equivalente legible.
SIMBOLOS = {
    r"\cdot": "·",
    r"\times": "×",
    r"\div": "÷",
    r"\pm": "±",
    r"\mp": "∓",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\neq": "≠",
    r"\approx": "≈",
    r"\infty": "∞",
    r"\pi": "π",
    r"\alpha": "α",
    r"\beta": "β",
    r"\theta": "θ",
    r"\Delta": "Δ",
    r"\degree": "°",
    r"\circ": "°",
    r"\rightarrow": "→",
    r"\Rightarrow": "⇒",
    r"\left": "",
    r"\right": "",
    r"\,": " ",
    r"\;": " ",
    r"\!": "",
}


def _registrar_fuente() -> str:
    """Registra una fuente con cobertura de símbolos matemáticos.

    ReportLab incluye la familia Bitstream Vera, que cubre griego y operadores
    matemáticos. Helvetica no los cubre, así que solo se usa como último
    recurso.
    """
    try:
        carpeta = Path(pdfmetrics.__file__).resolve().parent.parent / "fonts"
        pdfmetrics.registerFont(TTFont("Vera", carpeta / "Vera.ttf"))
        pdfmetrics.registerFont(TTFont("Vera-Bold", carpeta / "VeraBd.ttf"))
        pdfmetrics.registerFontFamily("Vera", normal="Vera", bold="Vera-Bold")
        return "Vera"
    except Exception:  # pragma: no cover - depende de la instalación
        return "Helvetica"


FUENTE = _registrar_fuente()
FUENTE_NEGRITA = "Vera-Bold" if FUENTE == "Vera" else "Helvetica-Bold"


def latex_a_texto(texto: str) -> str:
    """Convierte LaTeX simple en texto con marcado de ReportLab.

    No pretende ser un renderizador completo de LaTeX: cubre las construcciones
    que aparecen en pruebas de enseñanza básica y media, que es el 95% de los
    casos reales.
    """
    if not texto:
        return ""

    resultado = escape(texto)

    # Las fracciones se aplanan a la forma (numerador)/(denominador).
    patron_fraccion = re.compile(r"\\d?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
    while patron_fraccion.search(resultado):
        resultado = patron_fraccion.sub(r"(\1)/(\2)", resultado)

    resultado = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"√(\1)", resultado)
    resultado = re.sub(r"\\text\s*\{([^{}]*)\}", r"\1", resultado)

    for comando, simbolo in SIMBOLOS.items():
        resultado = resultado.replace(comando, simbolo)

    # Exponentes y subíndices se traducen al marcado propio de ReportLab.
    resultado = re.sub(r"\^\s*\{([^{}]*)\}", r"<super>\1</super>", resultado)
    resultado = re.sub(r"\^(\w)", r"<super>\1</super>", resultado)
    resultado = re.sub(r"_\s*\{([^{}]*)\}", r"<sub>\1</sub>", resultado)
    resultado = re.sub(r"_(\w)", r"<sub>\1</sub>", resultado)

    resultado = resultado.replace("$", "").replace("\\", "")
    return resultado.strip()


def _estilos() -> dict:
    """Define los estilos de párrafo usados en el documento."""
    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "TituloPrueba",
            parent=base["Title"],
            fontName=FUENTE_NEGRITA,
            fontSize=17,
            leading=21,
            spaceAfter=4,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloPrueba",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10.5,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=14,
        ),
        "seccion": ParagraphStyle(
            "Seccion",
            parent=base["Heading2"],
            fontName=FUENTE_NEGRITA,
            fontSize=13,
            leading=17,
            spaceBefore=10,
            spaceAfter=10,
            textColor=colors.HexColor("#1A365D"),
        ),
        "enunciado": ParagraphStyle(
            "Enunciado",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10.5,
            leading=15,
            spaceBefore=9,
            spaceAfter=4,
        ),
        "alternativa": ParagraphStyle(
            "Alternativa",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10.5,
            leading=14,
            leftIndent=1.1 * cm,
            spaceAfter=2,
        ),
        "paso": ParagraphStyle(
            "Paso",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=9.5,
            leading=13,
            leftIndent=0.9 * cm,
            textColor=colors.HexColor("#2D3748"),
            spaceAfter=2,
        ),
        "datos": ParagraphStyle(
            "Datos",
            parent=base["Normal"],
            fontName=FUENTE,
            fontSize=10,
            leading=22,
            spaceAfter=10,
        ),
    }


def _encabezado(elementos: list, estilos: dict, titulo: str, subtitulo: str) -> None:
    """Agrega el título y la línea de datos del estudiante."""
    elementos.append(Paragraph(latex_a_texto(titulo), estilos["titulo"]))
    elementos.append(Paragraph(subtitulo, estilos["subtitulo"]))
    elementos.append(
        Paragraph(
            "Nombre: ______________________________________  "
            "Curso: ______________  Fecha: ____________",
            estilos["datos"],
        )
    )
    elementos.append(HRFlowable(width="100%", color=colors.HexColor("#CBD5E0")))


def _cuerpo_forma(
    elementos: list,
    estilos: dict,
    resultados: list[ItemConVariantes],
    indice: int,
) -> None:
    """Escribe los ítems de una forma de la prueba."""
    numero_visible = 0

    for resultado in resultados:
        if indice >= len(resultado.variantes):
            continue

        numero_visible += 1
        variante = resultado.variantes[indice]

        elementos.append(
            Paragraph(
                f"<b>{numero_visible}.</b> {latex_a_texto(variante.enunciado)}",
                estilos["enunciado"],
            )
        )

        if variante.alternativas:
            for alternativa in variante.alternativas:
                elementos.append(
                    Paragraph(
                        f"{escape(alternativa.letra)}) {latex_a_texto(alternativa.texto)}",
                        estilos["alternativa"],
                    )
                )
        else:
            elementos.append(Spacer(1, 2.6 * cm))


def _pauta(
    elementos: list,
    estilos: dict,
    resultados: list[ItemConVariantes],
    indice: int,
    letra: str,
) -> None:
    """Escribe la pauta de corrección de una forma."""
    elementos.append(Paragraph(f"Pauta de corrección — Forma {letra}", estilos["seccion"]))

    numero_visible = 0

    for resultado in resultados:
        if indice >= len(resultado.variantes):
            continue

        numero_visible += 1
        variante = resultado.variantes[indice]

        elementos.append(
            Paragraph(
                f"<b>{numero_visible}.</b> Respuesta: "
                f"<b>{latex_a_texto(variante.respuesta_correcta)}</b>"
                f"<br/><i>{escape(resultado.concepto)}</i>",
                estilos["enunciado"],
            )
        )
        for posicion, paso in enumerate(variante.solucion, start=1):
            elementos.append(
                Paragraph(f"{posicion}. {latex_a_texto(paso)}", estilos["paso"])
            )


def exportar_pdf(
    resultados: list[ItemConVariantes],
    ruta_salida: str | Path,
    titulo: str = "Evaluación",
    asignatura: str = "Matemática",
    nivel: str = "",
) -> Path:
    """Genera el PDF con todas las formas de la prueba y sus pautas.

    Args:
        resultados: Variantes generadas por el agente para cada ítem.
        ruta_salida: Dónde escribir el archivo.
        titulo: Título que encabeza cada forma.
        asignatura: Asignatura mostrada en el subtítulo.
        nivel: Curso al que se aplica la evaluación.

    Returns:
        La ruta del PDF generado.

    Raises:
        ValueError: Si no se recibió ninguna variante que exportar.
    """
    if not resultados:
        raise ValueError("No hay variantes generadas para exportar.")

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    total_formas = min(
        len(LETRAS_FORMA), max(len(r.variantes) for r in resultados)
    )

    estilos = _estilos()
    elementos: list = []

    for indice in range(total_formas):
        letra = LETRAS_FORMA[indice]
        subtitulo = " · ".join(filter(None, [asignatura, nivel, f"Forma {letra}"]))

        if indice > 0:
            elementos.append(PageBreak())

        _encabezado(elementos, estilos, titulo, subtitulo)
        _cuerpo_forma(elementos, estilos, resultados, indice)

    for indice in range(total_formas):
        elementos.append(PageBreak())
        _pauta(elementos, estilos, resultados, indice, LETRAS_FORMA[indice])

    documento = SimpleDocTemplate(
        str(ruta_salida),
        pagesize=A4,
        title=titulo,
        author="Te educo a palos",
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    documento.build(elementos)

    return ruta_salida

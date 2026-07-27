"""Te educo a palos — interfaz web del agente.

Punto de entrada de la aplicación, tanto en local como en Hugging Face Spaces.
Expone dos flujos sobre el mismo motor de extracción:

- Modo Alumno: sube su prueba resuelta y recibe retroalimentación por ítem.
- Modo Profesor: sube una prueba y obtiene varias formas equivalentes, con
  pauta, listas para imprimir.
"""

import tempfile
import traceback
from pathlib import Path

import gradio as gr

from src.agente import (
    FaltaClaveAPI,
    corregir_prueba,
    generar_variantes_prueba,
    transcribir_prueba,
)
from src.config import (
    EJEMPLOS,
    MODELO_RAZONAMIENTO,
    MODELO_VISION,
    hay_credenciales,
    nombre_proveedor,
)
from src.exportar import exportar_pdf
from src.extraccion import ArchivoNoSoportado, extraer_paginas
from src.presentacion import formato_correcciones, formato_variantes, resumen_prueba

LATEX = [
    {"left": "$$", "right": "$$", "display": True},
    {"left": "$", "right": "$", "display": False},
]

DIFICULTADES = {
    "Igual que el original": "equivalente al original",
    "Un poco más fácil": "levemente inferior al original",
    "Un poco más difícil": "levemente superior al original",
}

AVISO_SIN_CLAVE = """\
### Falta configurar la clave del modelo

La aplicación necesita una clave de API para funcionar. Sirve cualquiera de
las dos:

- `GOOGLE_API_KEY`, que se obtiene gratis en
  [Google AI Studio](https://aistudio.google.com/apikey).
- `OPENAI_API_KEY`, que requiere una cuenta con saldo.

**En local:** copia `.env.example` como `.env` y completa la clave.
**En Hugging Face Spaces:** ve a *Settings → Variables and secrets* y agrégala
como secreto.
"""


def _mensaje_error(error: Exception) -> str:
    """Convierte una excepción en un mensaje comprensible para la interfaz."""
    if isinstance(error, FaltaClaveAPI):
        return AVISO_SIN_CLAVE

    if isinstance(error, ArchivoNoSoportado):
        return f"### Archivo no soportado\n\n{error}"

    if isinstance(error, FileNotFoundError):
        return "### No se encontró el archivo\n\nVuelve a subirlo e intenta de nuevo."

    traceback.print_exc()
    return (
        "### Ocurrió un error al procesar la prueba\n\n"
        f"```\n{type(error).__name__}: {error}\n```\n\n"
        "Si el documento es una foto, revisa que se lea con nitidez y que no "
        "esté cortada. Si el problema persiste, prueba con menos páginas."
    )


def _leer_prueba(archivo, progreso: gr.Progress):
    """Extrae y transcribe la prueba desde el archivo subido."""
    progreso(0.1, desc="Leyendo el documento")
    paginas = extraer_paginas(archivo)

    progreso(0.35, desc=f"Transcribiendo {len(paginas)} página(s)")
    return transcribir_prueba(paginas)


def revisar_prueba(archivo, progreso=gr.Progress()):
    """Modo Alumno: corrige la prueba y entrega retroalimentación por ítem."""
    if not archivo:
        return "Sube primero tu prueba en PDF o como foto."

    try:
        prueba = _leer_prueba(archivo, progreso)

        if not prueba.items:
            return (
                "### No se detectaron preguntas\n\n"
                "Revisa que el documento contenga los ejercicios y que la imagen "
                "se lea con claridad."
            )

        progreso(0.6, desc=f"Corrigiendo {len(prueba.items)} ítems")
        correcciones = corregir_prueba(prueba)

        progreso(1.0, desc="Listo")
        return formato_correcciones(prueba, correcciones)

    except Exception as error:  # noqa: BLE001 - la interfaz nunca debe caerse
        return _mensaje_error(error)


def crear_variantes(archivo, cantidad, dificultad, progreso=gr.Progress()):
    """Modo Profesor: genera formas equivalentes de la prueba y su PDF."""
    if not archivo:
        return "Sube primero la prueba que quieres reformular.", None

    try:
        prueba = _leer_prueba(archivo, progreso)

        if not prueba.items:
            return (
                "### No se detectaron preguntas\n\n"
                "Revisa que el documento contenga los ejercicios y que la imagen "
                "se lea con claridad."
            ), None

        progreso(0.6, desc=f"Generando {cantidad} formas de {len(prueba.items)} ítems")
        resultados = generar_variantes_prueba(
            prueba,
            cantidad=int(cantidad),
            dificultad=DIFICULTADES.get(dificultad, "equivalente al original"),
        )

        progreso(0.9, desc="Armando el PDF")
        destino = Path(tempfile.gettempdir()) / "te_educo_a_palos_variantes.pdf"
        exportar_pdf(
            resultados,
            destino,
            titulo=prueba.titulo,
            asignatura=prueba.asignatura,
            nivel=prueba.nivel,
        )

        progreso(1.0, desc="Listo")
        vista = f"{resumen_prueba(prueba)}\n\n{formato_variantes(prueba, resultados)}"
        return vista, str(destino)

    except Exception as error:  # noqa: BLE001 - la interfaz nunca debe caerse
        return _mensaje_error(error), None


def _ejemplos(nombre: str) -> list[list[str]]:
    """Devuelve el ejemplo indicado si el archivo existe en el repositorio."""
    ruta = EJEMPLOS / nombre
    return [[str(ruta)]] if ruta.exists() else []


CSS = """
.contenedor-principal { max-width: 1100px; margin: 0 auto; }
footer { display: none !important; }
"""

TEMA = gr.themes.Soft(primary_hue="emerald", secondary_hue="slate")

with gr.Blocks(title="Te educo a palos") as demo:
    with gr.Column(elem_classes="contenedor-principal"):
        gr.Markdown(
            """
            # 🪵 Te educo a palos

            Agente de IA que lee una prueba —en PDF o como foto— separa sus
            preguntas y trabaja sobre ellas.

            **Estudiantes:** suben su prueba resuelta y reciben el paso a paso de
            cada ejercicio, con el punto exacto donde se equivocaron.
            **Docentes:** suben una prueba y obtienen varias formas equivalentes
            con distintos números y contextos, para que no se copien entre filas.
            """
        )

        if not hay_credenciales():
            gr.Markdown(AVISO_SIN_CLAVE)

        with gr.Tabs():
            with gr.Tab("🎒 Soy estudiante"):
                gr.Markdown(
                    "Sube tu prueba **ya respondida**. Funciona con el PDF "
                    "original o con una foto de la hoja escrita a mano."
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        archivo_alumno = gr.File(
                            label="Tu prueba resuelta",
                            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"],
                            type="filepath",
                        )
                        boton_revisar = gr.Button(
                            "Revisar mi prueba", variant="primary", size="lg"
                        )

                        ejemplos_alumno = _ejemplos("prueba_matematica_resuelta.pdf")
                        if ejemplos_alumno:
                            gr.Examples(
                                examples=ejemplos_alumno,
                                inputs=archivo_alumno,
                                label="Prueba de ejemplo",
                            )

                    with gr.Column(scale=2):
                        salida_alumno = gr.Markdown(
                            "El resultado de la corrección aparecerá aquí.",
                            latex_delimiters=LATEX,
                        )

            with gr.Tab("👩‍🏫 Soy docente"):
                gr.Markdown(
                    "Sube una prueba, en blanco o resuelta. El agente identifica "
                    "qué evalúa cada ítem y crea ejercicios nuevos equivalentes."
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        archivo_docente = gr.File(
                            label="Prueba base",
                            file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp"],
                            type="filepath",
                        )
                        cantidad_formas = gr.Slider(
                            minimum=2,
                            maximum=5,
                            value=3,
                            step=1,
                            label="Formas distintas a generar",
                            info="Una forma por fila de la sala.",
                        )
                        nivel_dificultad = gr.Radio(
                            choices=list(DIFICULTADES),
                            value="Igual que el original",
                            label="Dificultad",
                        )
                        boton_generar = gr.Button(
                            "Generar variantes", variant="primary", size="lg"
                        )
                        descarga = gr.File(label="Prueba y pauta en PDF", visible=True)

                        ejemplos_docente = _ejemplos("prueba_matematica_en_blanco.pdf")
                        if ejemplos_docente:
                            gr.Examples(
                                examples=ejemplos_docente,
                                inputs=archivo_docente,
                                label="Prueba de ejemplo",
                            )

                    with gr.Column(scale=2):
                        salida_docente = gr.Markdown(
                            "Las variantes generadas aparecerán aquí.",
                            latex_delimiters=LATEX,
                        )

        gr.Markdown(
            f"""
            ---
            Lectura de documentos con PyMuPDF y pypdf · Agente construido con
            LangChain · {nombre_proveedor()} · Visión `{MODELO_VISION}` ·
            Razonamiento `{MODELO_RAZONAMIENTO}`

            *La nota estimada y la corrección son una ayuda, no reemplazan la
            revisión de un docente.*
            """
        )

    boton_revisar.click(
        fn=revisar_prueba,
        inputs=archivo_alumno,
        outputs=salida_alumno,
    )

    boton_generar.click(
        fn=crear_variantes,
        inputs=[archivo_docente, cantidad_formas, nivel_dificultad],
        outputs=[salida_docente, descarga],
    )


if __name__ == "__main__":
    # Desde Gradio 6 el tema y el CSS se declaran al lanzar, no al construir.
    demo.launch(theme=TEMA, css=CSS)

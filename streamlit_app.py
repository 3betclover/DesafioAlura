"""Te educo a palos: interfaz Streamlit, usada para el despliegue en la nube.

Es una segunda vista sobre el mismo motor que usa `app.py`. Toda la lógica del
agente vive en `src/`, así que ambas interfaces se comportan igual y ninguna
duplica reglas de negocio.

Se mantienen las dos porque Gradio resulta más cómodo para desarrollar en
local, mientras que Streamlit Community Cloud ofrece alojamiento público
gratuito sin exigir tarjeta de crédito.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st

# Los secretos de Streamlit se copian al entorno antes de importar `src`,
# porque `src.config` lee las variables en el momento de cargarse.
for _clave in (
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "PROVEEDOR",
    "MODELO_VISION",
    "MODELO_RAZONAMIENTO",
    "RPM",
):
    try:
        _valor = st.secrets[_clave]
    except Exception:  # noqa: BLE001 - en local puede no existir el archivo
        continue
    if _valor:
        os.environ[_clave] = str(_valor)

from src.agente import (  # noqa: E402
    CuotaAgotada,
    FaltaClaveAPI,
    corregir_prueba,
    generar_variantes_prueba,
    transcribir_prueba,
)
from src.config import (  # noqa: E402
    EJEMPLOS,
    MODELO_RAZONAMIENTO,
    MODELO_VISION,
    hay_credenciales,
    nombre_proveedor,
)
from src.exportar import exportar_pdf  # noqa: E402
from src.extraccion import ArchivoNoSoportado, extraer_paginas  # noqa: E402
from src.presentacion import (  # noqa: E402
    formato_correcciones,
    formato_variantes,
    resumen_prueba,
)

TIPOS = ["pdf", "png", "jpg", "jpeg", "webp"]

DIFICULTADES = {
    "Igual que el original": "equivalente al original",
    "Un poco más fácil": "levemente inferior al original",
    "Un poco más difícil": "levemente superior al original",
}

AVISO_SIN_CLAVE = """
**Falta configurar la clave del modelo.**

Sirve cualquiera de las dos: `GOOGLE_API_KEY`, gratuita en
[Google AI Studio](https://aistudio.google.com/apikey), u `OPENAI_API_KEY`.

En local se define en el archivo `.env`. En Streamlit Community Cloud se agrega
en *Settings → Secrets*.
"""

st.set_page_config(page_title="Te educo a palos", page_icon="🪵", layout="wide")


def guardar_temporal(archivo) -> Path:
    """Deja el archivo subido en disco, que es lo que espera la extracción."""
    destino = Path(tempfile.gettempdir()) / f"tep_{archivo.name}"
    destino.write_bytes(archivo.getbuffer())
    return destino


def mostrar_error(error: Exception) -> None:
    """Traduce la excepción a un mensaje entendible en pantalla."""
    if isinstance(error, FaltaClaveAPI):
        st.error(AVISO_SIN_CLAVE)
    elif isinstance(error, CuotaAgotada):
        st.warning(f"**Límite de peticiones alcanzado.** {error}")
    elif isinstance(error, ArchivoNoSoportado):
        st.error(f"**Archivo no soportado.** {error}")
    else:
        st.error(f"**Ocurrió un error al procesar la prueba.**\n\n`{error}`")
        st.caption(
            "Si el documento es una foto, revisa que se lea con nitidez y que "
            "no esté cortada. Si el problema persiste, prueba con menos páginas."
        )


def leer_prueba(ruta: Path):
    """Extrae las páginas del documento y las transcribe a ítems."""
    paginas = extraer_paginas(ruta)
    st.write(f"Documento leído: {len(paginas)} página(s).")
    return transcribir_prueba(paginas)


def bloque_ejemplo(nombre: str, etiqueta: str) -> None:
    """Ofrece la descarga de una prueba de ejemplo, si está en el repositorio."""
    ruta = EJEMPLOS / nombre
    if ruta.exists():
        st.download_button(
            etiqueta,
            data=ruta.read_bytes(),
            file_name=nombre,
            mime="application/pdf",
            use_container_width=True,
        )


st.title("🪵 Te educo a palos")
st.markdown(
    "Agente de IA que lee una prueba, en PDF o como foto, separa sus preguntas "
    "y trabaja sobre ellas."
)

if not hay_credenciales():
    st.error(AVISO_SIN_CLAVE)

pestana_alumno, pestana_docente = st.tabs(["🎒 Soy estudiante", "👩‍🏫 Soy docente"])


with pestana_alumno:
    st.markdown(
        "Sube tu prueba **ya respondida**. Funciona con el PDF original o con "
        "una foto de la hoja escrita a mano."
    )

    columna_entrada, columna_salida = st.columns([1, 2], gap="large")

    with columna_entrada:
        archivo_alumno = st.file_uploader(
            "Tu prueba resuelta", type=TIPOS, key="archivo_alumno"
        )
        revisar = st.button(
            "Revisar mi prueba",
            type="primary",
            use_container_width=True,
            disabled=archivo_alumno is None,
        )
        st.caption("¿No tienes una a mano?")
        bloque_ejemplo("prueba_matematica_resuelta.pdf", "Descargar prueba de ejemplo")

    with columna_salida:
        if revisar and archivo_alumno is not None:
            try:
                with st.status("Procesando la prueba", expanded=True) as estado:
                    st.write("Leyendo y transcribiendo el documento...")
                    prueba = leer_prueba(guardar_temporal(archivo_alumno))

                    if not prueba.items:
                        estado.update(label="Sin preguntas detectadas", state="error")
                        st.warning(
                            "No se detectaron preguntas. Revisa que el documento "
                            "contenga los ejercicios y que la imagen se lea bien."
                        )
                    else:
                        st.write(
                            f"Corrigiendo {len(prueba.items)} ítems. En el nivel "
                            "gratuito esto toma un par de minutos."
                        )
                        correcciones = corregir_prueba(prueba)
                        estado.update(label="Corrección lista", state="complete")
                        st.session_state["informe"] = formato_correcciones(
                            prueba, correcciones
                        )
            except Exception as error:  # noqa: BLE001 - la vista no debe caerse
                mostrar_error(error)

        if st.session_state.get("informe"):
            st.markdown(st.session_state["informe"])
        else:
            st.info("El resultado de la corrección aparecerá aquí.")


with pestana_docente:
    st.markdown(
        "Sube una prueba, en blanco o resuelta. El agente identifica qué evalúa "
        "cada ítem y crea ejercicios nuevos equivalentes."
    )

    columna_entrada, columna_salida = st.columns([1, 2], gap="large")

    with columna_entrada:
        archivo_docente = st.file_uploader(
            "Prueba base", type=TIPOS, key="archivo_docente"
        )
        cantidad = st.slider(
            "Formas distintas a generar",
            min_value=2,
            max_value=5,
            value=3,
            help="Una forma por fila de la sala.",
        )
        dificultad = st.radio("Dificultad", list(DIFICULTADES), index=0)
        generar = st.button(
            "Generar variantes",
            type="primary",
            use_container_width=True,
            disabled=archivo_docente is None,
        )
        st.caption("¿No tienes una a mano?")
        bloque_ejemplo("prueba_matematica_en_blanco.pdf", "Descargar prueba de ejemplo")

    with columna_salida:
        if generar and archivo_docente is not None:
            try:
                with st.status("Procesando la prueba", expanded=True) as estado:
                    st.write("Leyendo y transcribiendo el documento...")
                    prueba = leer_prueba(guardar_temporal(archivo_docente))

                    if not prueba.items:
                        estado.update(label="Sin preguntas detectadas", state="error")
                        st.warning(
                            "No se detectaron preguntas. Revisa que el documento "
                            "contenga los ejercicios y que la imagen se lea bien."
                        )
                    else:
                        st.write(
                            f"Generando {cantidad} formas a partir de "
                            f"{len(prueba.items)} ítems..."
                        )
                        resultados = generar_variantes_prueba(
                            prueba,
                            cantidad=cantidad,
                            dificultad=DIFICULTADES[dificultad],
                        )

                        st.write("Armando el PDF...")
                        destino = Path(tempfile.gettempdir()) / "te_educo_variantes.pdf"
                        exportar_pdf(
                            resultados,
                            destino,
                            titulo=prueba.titulo,
                            asignatura=prueba.asignatura,
                            nivel=prueba.nivel,
                        )

                        estado.update(label="Variantes listas", state="complete")
                        st.session_state["variantes"] = (
                            f"{resumen_prueba(prueba)}\n\n"
                            f"{formato_variantes(prueba, resultados)}"
                        )
                        st.session_state["pdf"] = destino.read_bytes()
            except Exception as error:  # noqa: BLE001 - la vista no debe caerse
                mostrar_error(error)

        if st.session_state.get("pdf"):
            st.download_button(
                "Descargar prueba y pauta en PDF",
                data=st.session_state["pdf"],
                file_name="te-educo-a-palos-variantes.pdf",
                mime="application/pdf",
                type="primary",
            )

        if st.session_state.get("variantes"):
            st.markdown(st.session_state["variantes"])
        else:
            st.info("Las variantes generadas aparecerán aquí.")


st.divider()
st.caption(
    f"Lectura de documentos con PyMuPDF y pypdf · Agente construido con "
    f"LangChain · {nombre_proveedor()} · Visión `{MODELO_VISION}` · "
    f"Razonamiento `{MODELO_RAZONAMIENTO}`"
)
st.caption(
    "La nota estimada y la corrección son una ayuda, no reemplazan la revisión "
    "de un docente."
)

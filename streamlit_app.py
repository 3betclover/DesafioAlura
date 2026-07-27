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
import time
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
    RPM,
    hay_credenciales,
    nombre_proveedor,
)
from src.estilos import CSS, PORTADA  # noqa: E402
from src.exportar import exportar_pdf  # noqa: E402
from src.extraccion import ArchivoNoSoportado, extraer_paginas  # noqa: E402
from src.modelos import Correccion, Item, ItemConVariantes, Prueba  # noqa: E402
from src.presentacion import ETIQUETAS_ERROR, calcular_nota  # noqa: E402

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

st.set_page_config(
    page_title="Te educo a palos",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Utilidades de pantalla
# --------------------------------------------------------------------------- #


def numero(valor: float) -> str:
    """Formatea un número sin decimales innecesarios."""
    return f"{valor:g}"


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


def panel(titulo: str, descripcion: str) -> None:
    """Encabezado de la columna de carga."""
    st.markdown(
        f'<div class="panel"><h4>{titulo}</h4><p>{descripcion}</p></div>',
        unsafe_allow_html=True,
    )


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


class Cronometro:
    """Muestra el avance real de una etapa: qué se está haciendo y hace cuánto.

    Se prefiere esto a un mensaje fijo del estilo "esto toma un par de minutos",
    porque cuando el proveedor limita las peticiones la espera se alarga y sin
    un contador visible la aplicación parece congelada.
    """

    def __init__(self, contenedor) -> None:
        self.barra = contenedor.progress(0.0, text="Preparando...")
        self.inicio = time.time()

    @property
    def transcurrido(self) -> int:
        return int(time.time() - self.inicio)

    def etapa(self, texto: str, avance: float = 0.0) -> None:
        self.barra.progress(avance, text=f"{texto} · {self.transcurrido} s")

    def por_item(self, verbo: str, desde: float, hasta: float):
        """Devuelve el callback de avance que espera el agente."""

        def avanzar(hechos: int, total: int) -> None:
            fraccion = desde + (hasta - desde) * (hechos / total)
            self.barra.progress(
                fraccion,
                text=f"{verbo} {hechos} de {total} · {self.transcurrido} s",
            )

        return avanzar

    def terminar(self, texto: str) -> None:
        self.barra.progress(1.0, text=f"{texto} · {self.transcurrido} s en total")


def leer_prueba(ruta: Path, cronometro: Cronometro) -> Prueba:
    """Extrae las páginas del documento y las transcribe a ítems."""
    cronometro.etapa("Leyendo el documento", 0.04)
    paginas = extraer_paginas(ruta)

    cronometro.etapa(f"Transcribiendo {len(paginas)} página(s)", 0.1)
    return transcribir_prueba(paginas)


# --------------------------------------------------------------------------- #
# Vistas de resultado
# --------------------------------------------------------------------------- #


def vista_resumen(prueba: Prueba, correcciones: list[Correccion]) -> None:
    """Encabezado con el puntaje total y la nota estimada."""
    obtenido = sum(c.puntaje_obtenido for c in correcciones)
    total = sum(c.puntaje_total for c in correcciones)
    aciertos = sum(1 for c in correcciones if c.es_correcta)
    logro = (obtenido / total * 100) if total else 0.0

    st.markdown(f"### {prueba.titulo}")
    st.caption(f"{prueba.asignatura} · {prueba.nivel}")

    columnas = st.columns(4)
    columnas[0].metric("Correctas", f"{aciertos} de {len(correcciones)}")
    columnas[1].metric("Puntaje", f"{numero(obtenido)} / {numero(total)}")
    columnas[2].metric("Logro", f"{logro:.0f}%")
    columnas[3].metric("Nota estimada", f"{calcular_nota(obtenido, total):.1f}")

    st.caption(
        "La nota usa 60% de exigencia y es solo una referencia. La corrección "
        "es una ayuda, no reemplaza la revisión de un docente."
    )


def vista_correccion(item: Item, correccion: Correccion) -> None:
    """Tarjeta con la retroalimentación de un ítem."""
    bien = correccion.es_correcta
    marca = "bien" if bien else "mal"
    icono = "✅" if bien else "❌"
    etiqueta = ETIQUETAS_ERROR.get(correccion.tipo_error, correccion.tipo_error)

    with st.container(border=True):
        st.markdown(
            f'<span class="marca {marca}">{icono} {etiqueta}</span>'
            f'&nbsp;&nbsp;<strong>Ítem {item.numero}</strong>',
            unsafe_allow_html=True,
        )

        # El enunciado va como cita de Markdown y no dentro de un div propio:
        # Streamlit solo renderiza LaTeX en su propio pipeline de Markdown, así
        # que el contenido nunca debe pasar por HTML crudo.
        st.markdown(f"> {item.enunciado}")

        datos = st.columns(3)
        with datos[0]:
            st.markdown('<div class="dato">Tu respuesta</div>', unsafe_allow_html=True)
            st.markdown(f"**{correccion.respuesta_alumno}**")
        with datos[1]:
            st.markdown(
                '<div class="dato">Respuesta correcta</div>', unsafe_allow_html=True
            )
            st.markdown(f"**{correccion.respuesta_correcta}**")
        with datos[2]:
            st.markdown('<div class="dato">Puntaje</div>', unsafe_allow_html=True)
            st.markdown(
                f"**{numero(correccion.puntaje_obtenido)} / "
                f"{numero(correccion.puntaje_total)}**"
            )

        if not bien and correccion.donde_se_equivoco:
            st.markdown(f"**Dónde se quebró:** {correccion.donde_se_equivoco}")

        st.markdown(correccion.explicacion)

        with st.expander("Ver el desarrollo paso a paso", expanded=not bien):
            for posicion, paso in enumerate(correccion.resolucion_propia, start=1):
                st.markdown(f"**{posicion}.** {paso}")

        if correccion.consejo:
            st.info(correccion.consejo, icon="💡")


def vista_variantes(resultado: ItemConVariantes) -> None:
    """Tarjeta con las versiones generadas a partir de un ítem."""
    with st.container(border=True):
        st.markdown(f"**Ítem {resultado.numero_original}**")
        st.caption(f"Evalúa: {resultado.concepto}")

        # Las formas se listan una tras otra en lugar de usar pestañas
        # anidadas: Streamlit ya tiene pestañas en el nivel superior y anidarlas
        # dentro de una columna genera errores de composición.
        for indice, variante in enumerate(resultado.variantes):
            st.markdown(f'<span class="forma">Forma {chr(ord("A") + indice)}</span>',
                        unsafe_allow_html=True)
            st.markdown(f"> {variante.enunciado}")

            for alternativa in variante.alternativas:
                st.markdown(f"&nbsp;&nbsp;&nbsp;{alternativa.letra}) {alternativa.texto}")

            st.markdown(f"✔️ **Respuesta:** {variante.respuesta_correcta}")

            with st.expander("Ver la pauta de corrección"):
                for posicion, paso in enumerate(variante.solucion, start=1):
                    st.markdown(f"**{posicion}.** {paso}")


# --------------------------------------------------------------------------- #
# Pantalla
# --------------------------------------------------------------------------- #

st.markdown(PORTADA, unsafe_allow_html=True)

if not hay_credenciales():
    st.error(AVISO_SIN_CLAVE)

pestana_alumno, pestana_docente = st.tabs(["🎒 Soy estudiante", "👩‍🏫 Soy docente"])


with pestana_alumno:
    columna_entrada, columna_salida = st.columns([1, 2], gap="large")

    with columna_entrada:
        panel(
            "Corregir mi prueba",
            "Sube tu prueba ya respondida. Funciona con el PDF original o con "
            "una fotografía de la hoja escrita a mano.",
        )
        archivo_alumno = st.file_uploader(
            "Tu prueba resuelta",
            type=TIPOS,
            key="archivo_alumno",
            label_visibility="collapsed",
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
            st.session_state.pop("correccion", None)
            cronometro = Cronometro(st.empty())
            try:
                prueba = leer_prueba(guardar_temporal(archivo_alumno), cronometro)

                if not prueba.items:
                    cronometro.terminar("Sin preguntas detectadas")
                    st.warning(
                        "No se detectaron preguntas. Revisa que el documento "
                        "contenga los ejercicios y que la imagen se lea bien."
                    )
                else:
                    cronometro.etapa(f"Corrigiendo {len(prueba.items)} ítems", 0.3)
                    correcciones = corregir_prueba(
                        prueba, al_avanzar=cronometro.por_item("Corregido el ítem", 0.3, 1.0)
                    )
                    cronometro.terminar("Corrección lista")
                    st.session_state["correccion"] = (prueba, correcciones)
            except Exception as error:  # noqa: BLE001 - la vista no debe caerse
                cronometro.terminar("Proceso interrumpido")
                mostrar_error(error)

        if st.session_state.get("correccion"):
            prueba, correcciones = st.session_state["correccion"]
            vista_resumen(prueba, correcciones)
            st.write("")
            for item, correccion in zip(prueba.items, correcciones):
                vista_correccion(item, correccion)
        elif not revisar:
            st.info(
                "El resultado de la corrección aparecerá aquí: puntaje por ítem, "
                "el punto exacto donde se quebró el razonamiento y el desarrollo "
                "correcto paso a paso.",
                icon="🎒",
            )


with pestana_docente:
    columna_entrada, columna_salida = st.columns([1, 2], gap="large")

    with columna_entrada:
        panel(
            "Generar variantes",
            "Sube una prueba, en blanco o resuelta. El agente identifica qué "
            "evalúa cada ítem y crea ejercicios nuevos equivalentes.",
        )
        archivo_docente = st.file_uploader(
            "Prueba base",
            type=TIPOS,
            key="archivo_docente",
            label_visibility="collapsed",
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
            st.session_state.pop("variantes", None)
            st.session_state.pop("pdf", None)
            cronometro = Cronometro(st.empty())
            try:
                prueba = leer_prueba(guardar_temporal(archivo_docente), cronometro)

                if not prueba.items:
                    cronometro.terminar("Sin preguntas detectadas")
                    st.warning(
                        "No se detectaron preguntas. Revisa que el documento "
                        "contenga los ejercicios y que la imagen se lea bien."
                    )
                else:
                    cronometro.etapa(
                        f"Generando {cantidad} formas de {len(prueba.items)} ítems", 0.3
                    )
                    resultados = generar_variantes_prueba(
                        prueba,
                        cantidad=cantidad,
                        dificultad=DIFICULTADES[dificultad],
                        al_avanzar=cronometro.por_item(
                            "Reformulado el ítem", 0.3, 0.95
                        ),
                    )

                    cronometro.etapa("Armando el PDF", 0.95)
                    destino = Path(tempfile.gettempdir()) / "te_educo_variantes.pdf"
                    exportar_pdf(
                        resultados,
                        destino,
                        titulo=prueba.titulo,
                        asignatura=prueba.asignatura,
                        nivel=prueba.nivel,
                    )

                    cronometro.terminar("Variantes listas")
                    st.session_state["variantes"] = (prueba, resultados)
                    st.session_state["pdf"] = destino.read_bytes()
            except Exception as error:  # noqa: BLE001 - la vista no debe caerse
                cronometro.terminar("Proceso interrumpido")
                mostrar_error(error)

        if st.session_state.get("variantes"):
            prueba, resultados = st.session_state["variantes"]
            formas = max(len(r.variantes) for r in resultados)

            st.markdown(f"### {prueba.titulo}")
            st.caption(
                f"{prueba.asignatura} · {prueba.nivel} · "
                f"{len(resultados)} ítems × {formas} formas"
            )

            if st.session_state.get("pdf"):
                st.download_button(
                    "Descargar las formas y la pauta en PDF",
                    data=st.session_state["pdf"],
                    file_name="te-educo-a-palos-variantes.pdf",
                    mime="application/pdf",
                    type="primary",
                )

            st.write("")
            for resultado in resultados:
                vista_variantes(resultado)
        elif not generar:
            st.info(
                "Las variantes aparecerán aquí, agrupadas por ítem, junto con un "
                "PDF descargable que trae cada forma completa y su pauta de "
                "corrección resuelta.",
                icon="👩‍🏫",
            )


st.markdown(
    f"""
    <div class="pie">
        Lectura de documentos con PyMuPDF y pypdf · Agente construido con
        LangChain · {nombre_proveedor()} · Visión <code>{MODELO_VISION}</code> ·
        Razonamiento <code>{MODELO_RAZONAMIENTO}</code> · Límite de
        <code>{RPM}</code> peticiones por minuto
    </div>
    """,
    unsafe_allow_html=True,
)

"""Agente de IA que transcribe, corrige y reformula pruebas.

El módulo expone tres capacidades, todas construidas sobre LangChain con salida
estructurada mediante Pydantic:

1. `transcribir_prueba`  — lee el documento y separa los ítems.
2. `corregir_prueba`     — resuelve cada ítem y retroalimenta al estudiante.
3. `generar_variantes`   — crea ejercicios equivalentes para el docente.

Las etapas 2 y 3 se ejecutan un ítem por llamada y en paralelo. Aislar cada
ejercicio evita que el modelo arrastre el contexto de una pregunta a la
siguiente, que es la causa más común de correcciones inconsistentes cuando se
manda la prueba completa en un solo prompt.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import (
    MAX_HILOS,
    MODELO_RAZONAMIENTO,
    MODELO_VISION,
    PROVEEDOR,
    clave_activa,
    hay_credenciales,
)
from src.extraccion import Pagina
from src.modelos import Correccion, Item, ItemConVariantes, Prueba


class FaltaClaveAPI(Exception):
    """No hay una clave de API configurada en el entorno."""


def _crear_modelo(nombre: str, esquema, temperatura: float = 0.0):
    """Devuelve un modelo de chat que responde según el esquema Pydantic dado.

    La elección del proveedor se resuelve en `config`, de modo que el resto del
    módulo no necesita saber con cuál se está trabajando.
    """
    if not hay_credenciales():
        variable = "GOOGLE_API_KEY" if PROVEEDOR == "google" else "OPENAI_API_KEY"
        raise FaltaClaveAPI(
            f"Falta la variable {variable}. Defínela en el archivo .env en "
            "local, o como Secret del Space en Hugging Face."
        )

    if PROVEEDOR == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        modelo = ChatGoogleGenerativeAI(
            model=nombre,
            temperature=temperatura,
            google_api_key=clave_activa(),
            timeout=120,
            max_retries=2,
        )
    else:
        from langchain_openai import ChatOpenAI

        modelo = ChatOpenAI(
            model=nombre,
            temperature=temperatura,
            api_key=clave_activa(),
            timeout=120,
            max_retries=2,
        )

    return modelo.with_structured_output(esquema)


def _bloque_imagen(imagen_b64: str) -> dict:
    """Construye el bloque de imagen en el formato estándar de LangChain.

    Desde LangChain 1.0 existe un formato único de bloques de contenido que
    cada integración traduce al dialecto de su proveedor. Usarlo evita tener
    que mantener una variante del mensaje por cada modelo soportado.
    """
    return {
        "type": "image",
        "base64": imagen_b64,
        "mime_type": "image/jpeg",
    }


# --------------------------------------------------------------------------- #
# Etapa 1: transcripción y segmentación
# --------------------------------------------------------------------------- #

INSTRUCCION_TRANSCRIPCION = """\
Eres un asistente docente que digitaliza evaluaciones escolares.

Recibirás las páginas de una prueba como imágenes. Tu tarea es transcribirla y
separarla en ítems individuales.

Reglas:
- Transcribe los enunciados de forma literal, sin corregir la redacción ni la
  ortografía del documento original.
- Escribe toda expresión matemática en LaTeX entre signos de dólar. Por ejemplo:
  $x^2 + 3x - 4 = 0$, $\\frac{2}{5}$, $\\sqrt{16}$.
- Si la prueba está respondida a mano, transcribe la respuesta del estudiante
  tal como está, conservando sus errores. No la corrijas ni la completes.
- Si un ítem no fue respondido, deja `respuesta_alumno` en null.
- Si el documento está en blanco, marca `esta_respondida` como false y deja
  todas las respuestas en null.
- Ignora encabezados, instrucciones generales, líneas para el nombre y pies de
  página. Solo interesan las preguntas.
- No inventes ítems que no aparecen en las imágenes.
"""


def transcribir_prueba(paginas: list[Pagina]) -> Prueba:
    """Convierte las páginas de un documento en una prueba estructurada.

    Args:
        paginas: Páginas obtenidas con `extraccion.extraer_paginas`.

    Returns:
        La prueba con sus ítems separados.
    """
    contenido: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Estas son las {len(paginas)} página(s) de la prueba. "
                "Transcríbela y sepárala en ítems."
            ),
        }
    ]

    for pagina in paginas:
        contenido.append(_bloque_imagen(pagina.imagen_b64))
        if pagina.tiene_texto_util:
            contenido.append(
                {
                    "type": "text",
                    "text": (
                        f"Capa de texto de la página {pagina.numero}, útil para "
                        f"precisar el enunciado impreso:\n{pagina.texto}"
                    ),
                }
            )

    modelo = _crear_modelo(MODELO_VISION, Prueba)
    return modelo.invoke(
        [
            SystemMessage(content=INSTRUCCION_TRANSCRIPCION),
            HumanMessage(content=contenido),
        ]
    )


# --------------------------------------------------------------------------- #
# Etapa 2: corrección con retroalimentación
# --------------------------------------------------------------------------- #

INSTRUCCION_CORRECCION = """\
Eres un profesor de {asignatura} que corrige una evaluación de {nivel}.

Sigue este orden de trabajo, sin saltarte ningún paso:

1. Resuelve el ejercicio por tu cuenta, desde cero, como si la hoja del
   estudiante estuviera en blanco. Escribe ese desarrollo en
   `resolucion_propia` y su resultado en `respuesta_correcta`.
2. Recién entonces compara tu resultado con lo que respondió el estudiante.
3. Marca `es_correcta` como true solo si ambas respuestas son equivalentes.
   Acepta formas distintas de escribir lo mismo: $0{,}5$ y $\\frac{{1}}{{2}}$
   son la misma respuesta, igual que $2x+1$ y $1+2x$.

Sobre la retroalimentación:
- Escribe en segunda persona, dirigiéndote al estudiante.
- Señala el punto exacto donde se quebró el razonamiento, no solo que el
  resultado está mal.
- Explica el procedimiento correcto de forma que sirva para el próximo
  ejercicio, no solo para este.
- Sé directo pero respetuoso. Nunca ridiculices al estudiante.
- Si el ítem quedó sin responder, explica igualmente cómo se resuelve.

Sobre el puntaje:
- Otorga crédito parcial cuando el procedimiento es correcto y el error es
  puramente aritmético.
- Si no hay desarrollo visible y la respuesta es incorrecta, el puntaje es 0.
- Usa {puntaje} como puntaje total del ítem.
"""


def _describir_item(item: Item) -> str:
    """Arma la descripción textual de un ítem para el prompt de corrección."""
    partes = [f"Ítem {item.numero}", f"Enunciado: {item.enunciado}"]

    if item.alternativas:
        opciones = "\n".join(f"  {a.letra}) {a.texto}" for a in item.alternativas)
        partes.append(f"Alternativas:\n{opciones}")

    partes.append(f"Respuesta del estudiante: {item.respuesta_alumno or 'Sin responder'}")

    if item.desarrollo_alumno:
        partes.append(f"Desarrollo manuscrito del estudiante:\n{item.desarrollo_alumno}")
    else:
        partes.append("Desarrollo manuscrito del estudiante: no presenta.")

    return "\n".join(partes)


def corregir_item(item: Item, asignatura: str, nivel: str) -> Correccion:
    """Corrige un ítem y genera su retroalimentación."""
    instruccion = INSTRUCCION_CORRECCION.format(
        asignatura=asignatura,
        nivel=nivel,
        puntaje=item.puntaje if item.puntaje else 1.0,
    )

    modelo = _crear_modelo(MODELO_RAZONAMIENTO, Correccion)
    return modelo.invoke(
        [
            SystemMessage(content=instruccion),
            HumanMessage(content=_describir_item(item)),
        ]
    )


def corregir_prueba(prueba: Prueba) -> list[Correccion]:
    """Corrige todos los ítems de una prueba en paralelo.

    Returns:
        Las correcciones en el mismo orden de los ítems originales.
    """
    if not prueba.items:
        return []

    with ThreadPoolExecutor(max_workers=MAX_HILOS) as ejecutor:
        return list(
            ejecutor.map(
                lambda item: corregir_item(item, prueba.asignatura, prueba.nivel),
                prueba.items,
            )
        )


# --------------------------------------------------------------------------- #
# Etapa 3: generación de variantes para el docente
# --------------------------------------------------------------------------- #

INSTRUCCION_VARIANTES = """\
Eres un profesor de {asignatura} que prepara distintas formas de una misma
evaluación de {nivel}, para que estudiantes sentados juntos no puedan copiarse.

A partir del ítem original, genera {cantidad} ejercicios nuevos.

Cada ejercicio debe:
- Evaluar exactamente la misma habilidad que el original. Identifícala primero
  y déjala escrita en el campo `concepto`.
- Usar números, nombres y contexto distintos. No basta con reordenar la
  pregunta ni con cambiar un solo dato.
- Mantener un nivel de dificultad {dificultad}.
- Tener solución exacta y verificable. Elige los datos de modo que el resultado
  no quede con decimales interminables, salvo que el original también los tenga.
- Conservar el formato del original: si era de alternativas, genera cuatro
  opciones plausibles donde los distractores reflejen errores típicos; si era
  de desarrollo, no incluyas alternativas.

Además, resuelve cada ejercicio paso a paso en el campo `solucion`. Ese
desarrollo es la pauta de corrección del docente, así que debe ser completo y
correcto.
"""


def generar_variantes(
    item: Item,
    asignatura: str,
    nivel: str,
    cantidad: int = 3,
    dificultad: str = "equivalente al original",
) -> ItemConVariantes:
    """Genera ejercicios equivalentes a partir de un ítem."""
    instruccion = INSTRUCCION_VARIANTES.format(
        asignatura=asignatura,
        nivel=nivel,
        cantidad=cantidad,
        dificultad=dificultad,
    )

    detalle = [f"Ítem original número {item.numero}", f"Enunciado: {item.enunciado}"]
    if item.alternativas:
        opciones = "\n".join(f"  {a.letra}) {a.texto}" for a in item.alternativas)
        detalle.append(f"Alternativas:\n{opciones}")

    # Temperatura alta: aquí sí queremos variedad entre las versiones generadas.
    modelo = _crear_modelo(MODELO_RAZONAMIENTO, ItemConVariantes, temperatura=0.8)
    return modelo.invoke(
        [
            SystemMessage(content=instruccion),
            HumanMessage(content="\n".join(detalle)),
        ]
    )


def generar_variantes_prueba(
    prueba: Prueba,
    cantidad: int = 3,
    dificultad: str = "equivalente al original",
    items_elegidos: Optional[list[int]] = None,
) -> list[ItemConVariantes]:
    """Genera variantes para varios ítems de la prueba, en paralelo.

    Args:
        prueba: Prueba ya transcrita.
        cantidad: Cuántas versiones nuevas crear por ítem.
        dificultad: Ajuste de dificultad pedido por el docente.
        items_elegidos: Números de ítem a reformular. Si es None, se usan todos.
    """
    seleccion = prueba.items
    if items_elegidos:
        seleccion = [i for i in prueba.items if i.numero in items_elegidos]

    if not seleccion:
        return []

    with ThreadPoolExecutor(max_workers=MAX_HILOS) as ejecutor:
        return list(
            ejecutor.map(
                lambda item: generar_variantes(
                    item, prueba.asignatura, prueba.nivel, cantidad, dificultad
                ),
                seleccion,
            )
        )

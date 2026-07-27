"""Esquemas de datos que estructuran la salida del modelo de lenguaje.

Cada esquema se entrega a LangChain mediante `with_structured_output`, lo que
obliga al modelo a responder con un JSON válido y verificable en lugar de texto
libre. El orden de los campos importa: el modelo los genera de arriba hacia
abajo, así que un campo declarado antes condiciona a los que vienen después.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Alternativa(BaseModel):
    """Una opción de una pregunta de selección múltiple."""

    letra: str = Field(description="Letra de la alternativa, por ejemplo 'A'.")
    texto: str = Field(description="Contenido de la alternativa.")


class Item(BaseModel):
    """Una pregunta individual extraída de la prueba."""

    numero: int = Field(description="Número del ítem dentro de la prueba.")
    enunciado: str = Field(
        description=(
            "Enunciado completo del ejercicio, transcrito literalmente. "
            "Las expresiones matemáticas se escriben en LaTeX entre signos $."
        )
    )
    tipo: Literal["desarrollo", "alternativas", "verdadero_falso"] = Field(
        description="Formato de la pregunta."
    )
    alternativas: list[Alternativa] = Field(
        default_factory=list,
        description="Opciones disponibles. Lista vacía si el ítem es de desarrollo.",
    )
    respuesta_alumno: Optional[str] = Field(
        default=None,
        description=(
            "Respuesta final escrita por el estudiante. Debe ser null si la "
            "prueba está en blanco o si el ítem no fue respondido."
        ),
    )
    desarrollo_alumno: Optional[str] = Field(
        default=None,
        description=(
            "Procedimiento manuscrito del estudiante, transcrito tal como está, "
            "incluyendo los errores. Null si no hay desarrollo visible."
        ),
    )
    puntaje: Optional[float] = Field(
        default=None, description="Puntaje asignado al ítem, si la prueba lo indica."
    )


class Prueba(BaseModel):
    """Prueba completa transcrita desde el archivo cargado."""

    titulo: str = Field(description="Título de la evaluación.")
    asignatura: str = Field(description="Asignatura, por ejemplo 'Matemática'.")
    nivel: str = Field(
        description="Nivel o curso al que apunta, por ejemplo '1° medio'."
    )
    esta_respondida: bool = Field(
        description="True si el documento contiene respuestas del estudiante."
    )
    items: list[Item] = Field(description="Todos los ítems detectados, en orden.")


class Correccion(BaseModel):
    """Corrección de un ítem con retroalimentación paso a paso.

    El orden de los campos fuerza al modelo a resolver el ejercicio por su
    cuenta antes de mirar lo que respondió el estudiante. Si se evaluara
    primero, el modelo tiende a dar por válido el desarrollo que ya está
    escrito en la hoja.
    """

    resolucion_propia: list[str] = Field(
        description=(
            "Resolución del ejercicio hecha desde cero, ignorando por completo "
            "lo que respondió el estudiante. Un paso por elemento de la lista."
        )
    )
    respuesta_correcta: str = Field(
        description="Resultado final al que se llegó en la resolución propia."
    )
    respuesta_alumno: str = Field(
        description="Respuesta del estudiante, o 'Sin responder' si está vacía."
    )
    es_correcta: bool = Field(
        description="True solo si la respuesta del estudiante equivale a la correcta."
    )
    tipo_error: Literal[
        "ninguno",
        "sin_responder",
        "error_de_calculo",
        "error_de_concepto",
        "error_de_procedimiento",
        "error_de_signo",
        "respuesta_incompleta",
        "error_de_interpretacion",
    ] = Field(description="Categoría del error cometido.")
    donde_se_equivoco: str = Field(
        description=(
            "Punto exacto del desarrollo donde aparece el error, citando el paso. "
            "Cadena vacía si la respuesta es correcta."
        )
    )
    explicacion: str = Field(
        description=(
            "Explicación pedagógica dirigida al estudiante, en segunda persona, "
            "clara y sin humillar. Máximo 4 oraciones."
        )
    )
    consejo: str = Field(
        description="Recomendación concreta para no repetir el error. Una oración."
    )
    puntaje_obtenido: float = Field(
        description="Puntaje logrado, considerando crédito parcial por el desarrollo."
    )
    puntaje_total: float = Field(description="Puntaje máximo del ítem.")


class Variante(BaseModel):
    """Ejercicio nuevo que evalúa el mismo concepto que un ítem original."""

    enunciado: str = Field(
        description=(
            "Enunciado del ejercicio nuevo, con datos y contexto distintos al "
            "original. Expresiones matemáticas en LaTeX entre signos $."
        )
    )
    alternativas: list[Alternativa] = Field(
        default_factory=list,
        description="Opciones si el ítem original era de selección múltiple.",
    )
    respuesta_correcta: str = Field(description="Respuesta correcta del ejercicio.")
    solucion: list[str] = Field(
        description="Desarrollo paso a paso de la solución, para la pauta del docente."
    )


class ItemConVariantes(BaseModel):
    """Conjunto de variantes generadas a partir de un ítem original."""

    numero_original: int = Field(description="Número del ítem que sirvió de base.")
    concepto: str = Field(
        description=(
            "Habilidad u objetivo de aprendizaje que evalúa el ítem, "
            "por ejemplo 'resolución de ecuaciones de segundo grado'."
        )
    )
    variantes: list[Variante] = Field(description="Ejercicios equivalentes generados.")

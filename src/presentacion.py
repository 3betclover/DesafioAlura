"""Traduce los resultados del agente a Markdown para mostrarlos en la interfaz.

Se mantiene separado de `app.py` para que la lógica de presentación pueda
probarse sin levantar Gradio, y para que la interfaz quede reducida a conectar
componentes.
"""

from src.modelos import Correccion, ItemConVariantes, Prueba

# Exigencia habitual del sistema escolar chileno: el 60% del puntaje
# corresponde a la nota 4,0.
EXIGENCIA = 0.6
NOTA_MINIMA = 1.0
NOTA_APROBACION = 4.0
NOTA_MAXIMA = 7.0

ETIQUETAS_ERROR = {
    "ninguno": "Correcto",
    "sin_responder": "Sin responder",
    "error_de_calculo": "Error de cálculo",
    "error_de_concepto": "Error de concepto",
    "error_de_procedimiento": "Error de procedimiento",
    "error_de_signo": "Error de signo",
    "respuesta_incompleta": "Respuesta incompleta",
    "error_de_interpretacion": "Error de interpretación",
}


def calcular_nota(obtenido: float, total: float) -> float:
    """Convierte un puntaje a la escala de notas de 1,0 a 7,0.

    Usa una escala lineal de dos tramos con 60% de exigencia, que es la fórmula
    estándar en los establecimientos chilenos.
    """
    if total <= 0:
        return NOTA_MINIMA

    corte = EXIGENCIA * total

    if obtenido < corte:
        nota = NOTA_MINIMA + (NOTA_APROBACION - NOTA_MINIMA) * (obtenido / corte)
    else:
        restante = total - corte
        avance = (obtenido - corte) / restante if restante else 1.0
        nota = NOTA_APROBACION + (NOTA_MAXIMA - NOTA_APROBACION) * avance

    return round(min(max(nota, NOTA_MINIMA), NOTA_MAXIMA), 1)


def _numero(valor: float) -> str:
    """Formatea un número sin decimales innecesarios."""
    return f"{valor:g}"


def formato_correcciones(prueba: Prueba, correcciones: list[Correccion]) -> str:
    """Arma el informe de retroalimentación para el estudiante."""
    if not correcciones:
        return "No se detectaron ítems en el documento."

    obtenido = sum(c.puntaje_obtenido for c in correcciones)
    total = sum(c.puntaje_total for c in correcciones)
    aciertos = sum(1 for c in correcciones if c.es_correcta)
    porcentaje = (obtenido / total * 100) if total else 0.0
    nota = calcular_nota(obtenido, total)

    lineas = [
        f"# {prueba.titulo}",
        f"**{prueba.asignatura}** · {prueba.nivel}",
        "",
        "| Correctas | Puntaje | Logro | Nota estimada |",
        "|---|---|---|---|",
        f"| {aciertos} de {len(correcciones)} "
        f"| {_numero(obtenido)} / {_numero(total)} "
        f"| {porcentaje:.0f}% "
        f"| **{nota:.1f}** |",
        "",
        "> La nota se calcula con 60% de exigencia y es solo una referencia.",
        "",
        "---",
        "",
    ]

    for item, correccion in zip(prueba.items, correcciones):
        icono = "✅" if correccion.es_correcta else "❌"
        etiqueta = ETIQUETAS_ERROR.get(correccion.tipo_error, correccion.tipo_error)

        lineas.append(f"## {icono} Ítem {item.numero} · {etiqueta}")
        lineas.append("")
        lineas.append(f"*{item.enunciado}*")
        lineas.append("")
        lineas.append(
            f"- **Tu respuesta:** {correccion.respuesta_alumno}"
        )
        lineas.append(
            f"- **Respuesta correcta:** {correccion.respuesta_correcta}"
        )
        lineas.append(
            f"- **Puntaje:** {_numero(correccion.puntaje_obtenido)} / "
            f"{_numero(correccion.puntaje_total)}"
        )
        lineas.append("")

        if not correccion.es_correcta and correccion.donde_se_equivoco:
            lineas.append(f"**Dónde se quebró:** {correccion.donde_se_equivoco}")
            lineas.append("")

        lineas.append(correccion.explicacion)
        lineas.append("")
        lineas.append("**Paso a paso:**")
        lineas.append("")
        for posicion, paso in enumerate(correccion.resolucion_propia, start=1):
            lineas.append(f"{posicion}. {paso}")
        lineas.append("")

        if correccion.consejo:
            lineas.append(f"💡 *{correccion.consejo}*")
            lineas.append("")

        lineas.append("---")
        lineas.append("")

    return "\n".join(lineas)


def formato_variantes(prueba: Prueba, resultados: list[ItemConVariantes]) -> str:
    """Arma la vista previa de las formas generadas para el docente."""
    if not resultados:
        return "No se generaron variantes."

    total_formas = max(len(r.variantes) for r in resultados)

    lineas = [
        f"# Variantes generadas · {prueba.titulo}",
        f"**{prueba.asignatura}** · {prueba.nivel} · "
        f"{len(resultados)} ítems × {total_formas} formas",
        "",
        "Cada forma toma una variante distinta de cada ítem. "
        "Descarga el PDF para obtener todas las formas con su pauta.",
        "",
        "---",
        "",
    ]

    for resultado in resultados:
        lineas.append(f"## Ítem {resultado.numero_original}")
        lineas.append(f"*Evalúa: {resultado.concepto}*")
        lineas.append("")

        for indice, variante in enumerate(resultado.variantes):
            letra = chr(ord("A") + indice)
            lineas.append(f"**Forma {letra}.** {variante.enunciado}")
            lineas.append("")

            for alternativa in variante.alternativas:
                lineas.append(f"   {alternativa.letra}) {alternativa.texto}")
            if variante.alternativas:
                lineas.append("")

            lineas.append(f"   ✔️ **Respuesta:** {variante.respuesta_correcta}")
            lineas.append("")

        lineas.append("---")
        lineas.append("")

    return "\n".join(lineas)


def resumen_prueba(prueba: Prueba) -> str:
    """Descripción corta de lo que se detectó en el documento."""
    estado = "con respuestas del estudiante" if prueba.esta_respondida else "en blanco"
    return (
        f"Se detectaron **{len(prueba.items)} ítems** en «{prueba.titulo}» "
        f"({prueba.asignatura}, {prueba.nivel}), {estado}."
    )

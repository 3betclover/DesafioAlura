"""Traduce los resultados del agente a Markdown para mostrarlos en la interfaz.

Se mantiene separado de `app.py` para que la lógica de presentación pueda
probarse sin levantar Gradio, y para que la interfaz quede reducida a conectar
componentes.
"""

from src.modelos import Correccion, ItemConVariantes, Prueba

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


def formato_correcciones(prueba: Prueba, correcciones: list[Correccion]) -> str:
    """Arma el informe de retroalimentación para el estudiante."""
    if not correcciones:
        return "No se detectaron ítems en el documento."

    aciertos = sum(1 for c in correcciones if c.es_correcta)
    porcentaje = (aciertos / len(correcciones) * 100) if correcciones else 0.0

    lineas = [
        f"# {prueba.titulo}",
        f"**{prueba.asignatura}** · {prueba.nivel}",
        "",
        "| Correctas | Con errores | Logro |",
        "|---|---|---|",
        f"| {aciertos} "
        f"| {len(correcciones) - aciertos} "
        f"| {porcentaje:.0f}% de los ítems |",
        "",
        "> El agente identifica aciertos y errores. La calificación le "
        "corresponde al docente.",
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

"""Hoja de estilos de la interfaz Streamlit.

Se mantiene aparte de `streamlit_app.py` para que el archivo de la aplicación
conserve solo el flujo de la pantalla y no quede sepultado bajo un bloque de
CSS.

La paleta gira en torno a un ámbar amaderado, que acompaña el nombre del
proyecto, con neutros cálidos de apoyo y los verdes y rojos reservados
exclusivamente para señalar acierto y error en las correcciones.
"""

CSS = """
<style>
:root {
    --tinta: #1C1917;
    --tinta-suave: #57534E;
    --borde: #E7E2DC;
    --papel: #FBF9F7;
    --madera: #B45309;
    --madera-oscura: #7C2D12;
    --acierto: #15803D;
    --error: #B91C1C;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Encabezado ------------------------------------------------------------ */

.portada {
    background: linear-gradient(135deg, var(--madera-oscura) 0%, #9A3412 45%, var(--madera) 100%);
    color: #FFF7ED;
    padding: 1.75rem 2rem;
    border-radius: 18px;
    margin-bottom: 1.75rem;
    box-shadow: 0 10px 30px -12px rgba(124, 45, 18, 0.55);
}

.portada h1 {
    margin: 0;
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #FFF7ED;
}

.portada p {
    margin: 0.5rem 0 0;
    font-size: 1.02rem;
    line-height: 1.5;
    color: rgba(255, 247, 237, 0.9);
    max-width: 60ch;
}

.portada .etiquetas {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}

.portada .etiquetas span {
    background: rgba(255, 247, 237, 0.16);
    border: 1px solid rgba(255, 247, 237, 0.28);
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    font-size: 0.78rem;
    letter-spacing: 0.01em;
}

/* Pestañas -------------------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid var(--borde);
}

.stTabs [data-baseweb="tab"] {
    height: 3rem;
    padding: 0 1.25rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--tinta-suave);
}

.stTabs [aria-selected="true"] {
    color: var(--madera) !important;
}

/* Panel lateral de carga ------------------------------------------------ */

.panel {
    background: var(--papel);
    border: 1px solid var(--borde);
    border-radius: 14px;
    padding: 1.1rem 1.15rem 0.4rem;
    margin-bottom: 1rem;
}

.panel h4 {
    margin: 0 0 0.35rem;
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--madera);
}

.panel p {
    margin: 0 0 0.8rem;
    font-size: 0.9rem;
    line-height: 1.45;
    color: var(--tinta-suave);
}

/* Botones --------------------------------------------------------------- */

.stButton > button,
.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.55rem 1rem;
}

/* Tarjetas de resultado ------------------------------------------------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px;
}

.marca {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding: 0.18rem 0.6rem;
    border-radius: 6px;
}

.marca.bien {
    background: #DCFCE7;
    color: var(--acierto);
}

.marca.mal {
    background: #FEE2E2;
    color: var(--error);
}

.forma {
    display: inline-block;
    margin-top: 0.9rem;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--madera);
}

/* Los enunciados se escriben como cita de Markdown, para que Streamlit
   renderice el LaTeX que contienen. */
[data-testid="stVerticalBlockBorderWrapper"] blockquote {
    background: var(--papel);
    border-left: 3px solid var(--madera);
    border-radius: 0 8px 8px 0;
    padding: 0.6rem 0.9rem;
    margin: 0.7rem 0 1rem;
    color: var(--tinta);
    font-size: 0.95rem;
}

.dato {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--tinta-suave);
    margin-bottom: 0.1rem;
}

.dato + div {
    font-size: 1.02rem;
    font-weight: 600;
}

/* Métricas -------------------------------------------------------------- */

[data-testid="stMetric"] {
    background: var(--papel);
    border: 1px solid var(--borde);
    border-radius: 12px;
    padding: 0.85rem 1rem;
}

[data-testid="stMetricLabel"] {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--tinta-suave);
}

/* Pie ------------------------------------------------------------------- */

.pie {
    margin-top: 2.5rem;
    padding-top: 1.1rem;
    border-top: 1px solid var(--borde);
    font-size: 0.82rem;
    line-height: 1.6;
    color: var(--tinta-suave);
}

.pie code {
    background: var(--papel);
    border: 1px solid var(--borde);
    border-radius: 5px;
    padding: 0.05rem 0.35rem;
    font-size: 0.78rem;
}
</style>
"""

PORTADA = """
<div class="portada">
    <h1>Te educo a palos</h1>
    <p>
        Agente de inteligencia artificial que lee una prueba, en PDF o como
        fotografía, separa sus preguntas y trabaja sobre ellas: corrige con
        retroalimentación paso a paso, o genera versiones equivalentes para
        que nadie se copie.
    </p>
    <div class="etiquetas">
        <span>PDF y fotografías</span>
        <span>Letra manuscrita</span>
        <span>Retroalimentación por ítem</span>
        <span>Varias formas de una misma prueba</span>
    </div>
</div>
"""

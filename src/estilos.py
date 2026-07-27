"""Hoja de estilos de la interfaz Streamlit.

Se mantiene aparte de `streamlit_app.py` para que el archivo de la aplicación
conserve solo el flujo de la pantalla y no quede sepultado bajo un bloque de
CSS.

La dirección visual es editorial: papel crema, títulos en Playfair Display con
serifas de alto contraste, texto en Lora, filetes finos en lugar de sombras y
antetítulos en versalitas. La idea es que una prueba corregida se lea como un
artículo de revista y no como el volcado de un formulario.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap');

:root {
    --papel: #FAF6EC;
    --papel-hondo: #F3ECDC;
    --tinta: #211C16;
    --tinta-suave: #6B6154;
    --filete: #DDD2BC;
    --filete-tenue: #EAE1CE;
    --sello: #7B2D26;
    --acierto: #2F6B4F;
    --error: #9B2C2C;
}

/* Tipografía --------------------------------------------------------------- */

/* La tipografía se declara solo en la raíz y se deja heredar. Aplicarla
   elemento por elemento pisaba la fuente de los íconos de Streamlit, que son
   ligaduras: la palabra "upload" se dibuja como símbolo, y con una serifa
   encima quedaba escrita tal cual sobre el botón. */
html, body,
[data-testid="stAppViewContainer"] {
    font-family: 'Lora', Georgia, 'Times New Roman', serif;
}

/* Restitución explícita para los íconos, por si algún ancestro los alcanza. */
[data-testid="stIconMaterial"],
.material-icons,
.material-symbols-rounded,
.material-symbols-outlined {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    font-weight: normal !important;
    letter-spacing: normal !important;
}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    font-family: 'Playfair Display', Georgia, serif;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--tinta);
}

code, pre, kbd, [data-testid="stCode"] * {
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace !important;
}

.block-container {
    max-width: 1140px;
    padding-top: 2.4rem;
    padding-bottom: 5rem;
}

/* Cabecera ----------------------------------------------------------------- */

.masthead {
    border-top: 2px solid var(--tinta);
    border-bottom: 1px solid var(--filete);
    padding: 1.4rem 0 1.5rem;
    margin-bottom: 0.4rem;
    text-align: center;
}

.masthead .antetitulo {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.24em;
    color: var(--sello);
    margin-bottom: 0.7rem;
}

.masthead h1 {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 3.15rem;
    font-weight: 700;
    line-height: 1.06;
    margin: 0;
    color: var(--tinta);
}

.masthead .bajada {
    font-family: 'Lora', Georgia, serif;
    font-style: italic;
    font-size: 1.06rem;
    line-height: 1.62;
    color: var(--tinta-suave);
    max-width: 62ch;
    margin: 0.9rem auto 0;
}

.sumario {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0 2.1rem;
    border-bottom: 3px double var(--filete);
    padding-bottom: 1rem;
    margin-bottom: 2.1rem;
    font-size: 0.73rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--tinta-suave);
}

/* Pestañas ----------------------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    border-bottom: 1px solid var(--filete);
}

.stTabs [data-baseweb="tab"] {
    height: 2.9rem;
    padding: 0 0.2rem;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 1.12rem;
    font-weight: 600;
    color: var(--tinta-suave);
}

.stTabs [aria-selected="true"] {
    color: var(--sello) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--sello);
}

/* Columna de carga --------------------------------------------------------- */

.pliego {
    border-top: 1px solid var(--tinta);
    padding-top: 0.9rem;
    margin-bottom: 1.1rem;
}

.pliego h4 {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.28rem;
    margin: 0 0 0.4rem;
}

.pliego p {
    font-size: 0.92rem;
    line-height: 1.6;
    color: var(--tinta-suave);
    margin: 0;
}

/* Controles ---------------------------------------------------------------- */

.stButton > button,
.stDownloadButton > button {
    border-radius: 2px;
    font-weight: 600;
    letter-spacing: 0.03em;
    padding: 0.6rem 1rem;
    border: 1px solid var(--sello);
}

/* Zona de carga --------------------------------------------------------- */

[data-testid="stFileUploaderDropzone"] {
    background: var(--papel-hondo);
    border: 1px dashed var(--sello);
    border-radius: 3px;
    padding: 1.4rem 1.1rem;
    transition: background 0.15s ease;
}

[data-testid="stFileUploaderDropzone"]:hover {
    background: #EDE3CE;
}

/* El botón de la zona de carga es secundario frente al de acción: se deja
   discreto para que la mirada vaya primero al área donde se suelta el archivo. */
[data-testid="stFileUploaderDropzone"] button {
    border: 1px solid var(--filete);
    background: transparent;
    color: var(--sello);
    font-size: 0.85rem;
    padding: 0.4rem 0.9rem;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    color: var(--tinta-suave);
}

/* Tarjetas de resultado ---------------------------------------------------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 3px;
    border-color: var(--filete) !important;
    background: rgba(255, 253, 248, 0.6);
}

[data-testid="stVerticalBlockBorderWrapper"] blockquote {
    background: var(--papel-hondo);
    border-left: 2px solid var(--sello);
    border-radius: 0;
    padding: 0.75rem 1rem;
    margin: 0.8rem 0 1.1rem;
    font-size: 1rem;
    line-height: 1.6;
    color: var(--tinta);
}

.marca {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    padding: 0.16rem 0;
    border-bottom: 1px solid currentColor;
}

.marca.bien { color: var(--acierto); }
.marca.mal { color: var(--error); }
.marca.neutra { color: var(--sello); }

.folio {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.22rem;
    font-weight: 600;
    color: var(--tinta);
}

.dato {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--tinta-suave);
    margin-bottom: 0.15rem;
}

.forma {
    display: inline-block;
    margin-top: 1.1rem;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--sello);
    border-bottom: 1px solid var(--filete);
    padding-bottom: 0.15rem;
}

/* Métricas ----------------------------------------------------------------- */

[data-testid="stMetric"] {
    background: transparent;
    border: none;
    border-top: 1px solid var(--filete);
    border-radius: 0;
    padding: 0.7rem 0 0;
}

[data-testid="stMetricLabel"] {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--tinta-suave);
}

[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 600;
    color: var(--tinta);
}

/* Titulillo de sección ----------------------------------------------------- */

.titulillo {
    border-bottom: 3px double var(--filete);
    padding-bottom: 0.6rem;
    margin-bottom: 1.3rem;
}

.titulillo h3 {
    font-size: 1.85rem;
    margin: 0;
}

.titulillo .credito {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--tinta-suave);
    margin-top: 0.35rem;
}

/* Pie ---------------------------------------------------------------------- */

.colofon {
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 3px double var(--filete);
    font-size: 0.8rem;
    line-height: 1.75;
    color: var(--tinta-suave);
    text-align: center;
}

.colofon code {
    background: var(--papel-hondo);
    border-radius: 2px;
    padding: 0.05rem 0.35rem;
    font-size: 0.75rem;
}
</style>
"""

MASTHEAD = """
<div class="masthead">
    <div class="antetitulo">Challenge Alura Agente</div>
    <h1>Te educo a palos</h1>
    <p class="bajada">
        Un agente de inteligencia artificial que lee una prueba, en PDF o como
        fotografía, separa sus preguntas y trabaja sobre ellas: las resuelve
        paso a paso, corrige lo que escribió el estudiante, o escribe versiones
        equivalentes para que nadie se copie.
    </p>
</div>
<div class="sumario">
    <span>PDF y fotografías</span>
    <span>Letra manuscrita</span>
    <span>Retroalimentación por ítem</span>
    <span>Varias formas de una prueba</span>
</div>
"""

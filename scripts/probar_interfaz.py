"""Comprueba que la interfaz Streamlit se renderiza sin errores.

Streamlit muestra las excepciones en el navegador y no en la salida del
servidor, así que levantar la aplicación y revisar el log no basta para saber
si funciona. `AppTest` ejecuta el script completo en memoria, construye todos
los componentes y deja las excepciones al alcance de la prueba.

Detecta, entre otras cosas, los identificadores de elemento duplicados, que
aparecen cuando dos componentes iguales se declaran sin una clave que los
distinga.

No realiza ninguna llamada al modelo: solo verifica el estado inicial de la
pantalla.

Uso:
    python scripts/probar_interfaz.py
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from streamlit.testing.v1 import AppTest  # noqa: E402

ESPERADO = {
    "pestañas": 2,
    "botones": 2,
    "descargas": 2,
    "cargadores": 2,
}


def main() -> int:
    prueba = AppTest.from_file(str(RAIZ / "streamlit_app.py"), default_timeout=90)
    prueba.run()

    if prueba.exception:
        print(f"FALLA: la interfaz lanzó {len(prueba.exception)} excepción(es).\n")
        for excepcion in prueba.exception:
            print(f"  {excepcion.value}\n")
        return 1

    obtenido = {
        "pestañas": len(prueba.tabs),
        "botones": len(prueba.button),
        "descargas": len(prueba.get("download_button")),
        "cargadores": len(prueba.get("file_uploader")),
    }

    problemas = [
        f"  {nombre}: se esperaban {cantidad}, hay {obtenido[nombre]}"
        for nombre, cantidad in ESPERADO.items()
        if obtenido[nombre] != cantidad
    ]

    if problemas:
        print("FALLA: la pantalla no tiene los componentes esperados.")
        print("\n".join(problemas))
        return 1

    print("La interfaz se renderiza sin errores.")
    for nombre, cantidad in obtenido.items():
        print(f"  {nombre}: {cantidad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

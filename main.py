"""Mundo Libro: sistema de gestión de la Biblioteca Comunitaria.

Corte 1 (archivos de registros de longitud fija) y Corte 2 (árbol genérico
que clasifica el catálogo), integrados en una sola consola.

Ejecutar:   python main.py
Opciones:   --simple   texto plano, sin color ni limpieza de pantalla
            --ayuda    muestra esta ayuda

Los datos se guardan en la carpeta datos/. Con la variable de entorno
MUNDO_LIBRO_DATOS se puede usar otra carpeta (útil para pruebas).
"""
import os
import sys

from interfaz import estilo
from interfaz.menus import App

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_DATOS = os.environ.get("MUNDO_LIBRO_DATOS") or os.path.join(BASE, "datos")


def main(argumentos=None) -> int:
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    if "--ayuda" in argumentos or "-h" in argumentos:
        print(__doc__)
        return 0
    estilo.iniciar(simple="--simple" in argumentos)
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    ruta_libros = os.path.join(CARPETA_DATOS, "libros.dat")
    ruta_arbol = os.path.join(CARPETA_DATOS, "arbol_catalogo.txt")
    try:
        App(ruta_libros, ruta_arbol).ejecutar()
    except ValueError as error:
        estilo.error(f"El archivo arbol_catalogo.txt no tiene un formato válido: {error}")
        estilo.info("Corrígelo con un editor de texto o bórralo para empezar con un árbol nuevo.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

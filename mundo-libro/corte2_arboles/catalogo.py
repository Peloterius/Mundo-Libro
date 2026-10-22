"""Datos de ejemplo y generación inicial del catálogo (Corte 2)."""
import os
from corte1_archivos.archivo_libros import ArchivoLibros
from corte1_archivos.registro import Libro
from .arbol import Arbol

# (categoría, subcategoría, id, título, autor)
EJEMPLO = [
    ("Literatura", "Novela", 1001, "Cien años de soledad", "Gabriel García Márquez"),
    ("Literatura", "Novela", 1002, "Crónica de una muerte anunciada", "Gabriel García Márquez"),
    ("Literatura", "Cuento", 1003, "Ficciones", "Jorge Luis Borges"),
    ("Literatura", "Poesía", 1004, "Veinte poemas de amor", "Pablo Neruda"),
    ("Ciencias", "Matemáticas", 1005, "Álgebra", "Aurelio Baldor"),
    ("Ciencias", "Informática", 1006, "Fundamentos de bases de datos", "Silberschatz"),
    ("Ciencias", "Informática", 1007, "Introducción a los algoritmos", "Cormen"),
    ("Infantil", "Cuentos ilustrados", 1008, "El principito", "Antoine de Saint-Exupéry"),
    ("Historia", "Historia de Colombia", 1009, "Breve historia de Colombia", "Varios autores"),
]


def crear_datos_ejemplo(ruta_libros: str, ruta_arbol: str) -> None:
    """Genera libros.dat y arbol_catalogo.txt con el catálogo de ejemplo."""
    if os.path.exists(ruta_libros):
        os.remove(ruta_libros)
    archivo = ArchivoLibros(ruta_libros)
    arbol = Arbol()
    vistas = set()
    for cat, sub, idl, titulo, autor in EJEMPLO:
        if cat not in vistas:
            arbol.insertar("Biblioteca Mundo Libro", cat); vistas.add(cat)
        if (cat, sub) not in vistas:
            arbol.insertar(cat, sub); vistas.add((cat, sub))
        archivo.agregar(Libro(idl, titulo, autor))
        arbol.insertar(sub, f"{idl}|{titulo}")
    arbol.guardar(ruta_arbol)

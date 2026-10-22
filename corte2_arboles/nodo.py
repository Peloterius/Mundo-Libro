"""Nodo del árbol genérico del catálogo (Corte 2)."""


class Nodo:
    """dato: nombre de la categoría/subcategoría; en las hojas, «ID|título».
    hijos: lista de nodos hijos (vacía en las hojas)."""

    def __init__(self, dato: str):
        self.dato = dato
        self.hijos = []

    def es_hoja(self) -> bool:
        return not self.hijos

    def coincide(self, buscado: str) -> bool:
        """Un nodo coincide por su dato exacto o, si es un libro, por su ID o su título."""
        if self.dato == buscado:
            return True
        if "|" in self.dato:
            id_libro, titulo = self.dato.split("|", 1)
            return buscado == id_libro or buscado.lower() == titulo.lower()
        return False

    def __repr__(self) -> str:
        return f"Nodo({self.dato!r}, hijos={len(self.hijos)})"

"""Operaciones básicas sobre el archivo de libros (Corte 1)."""
import os
from .registro import Libro, TAMANO


class ArchivoLibros:
    def __init__(self, ruta: str):
        self.ruta = ruta
        if not os.path.exists(ruta):          # si no existe, se crea (modo w+b)
            with open(ruta, "w+b"):
                pass

    # ---- operaciones básicas ----
    def total(self) -> int:
        return os.path.getsize(self.ruta) // TAMANO

    def agregar(self, libro: Libro) -> int:
        """Escribe el registro al final y devuelve su número de orden (desde 1)."""
        with open(self.ruta, "r+b") as f:
            f.seek(0, os.SEEK_END)
            f.write(libro.a_bytes())
        return self.total()

    def modificar(self, n: int, libro: Libro) -> None:
        """Reescribe el registro n en su misma posición."""
        self._validar(n)
        with open(self.ruta, "r+b") as f:
            f.seek((n - 1) * TAMANO)
            f.write(libro.a_bytes())

    # ---- acceso directo ----
    def leer_directo(self, n: int) -> Libro:
        """Acceso directo: desplazamiento = (n - 1) * 173."""
        self._validar(n)
        with open(self.ruta, "rb") as f:
            f.seek((n - 1) * TAMANO)
            return Libro.desde_bytes(f.read(TAMANO))

    # ---- acceso secuencial ----
    def recorrer(self):
        """Genera (n, libro) leyendo desde el inicio, registro por registro."""
        with open(self.ruta, "rb") as f:
            n = 0
            while True:
                datos = f.read(TAMANO)
                if len(datos) < TAMANO:
                    return
                n += 1
                yield n, Libro.desde_bytes(datos)

    def buscar_secuencial(self, id_libro: int):
        """Devuelve (n, libro) o None si el ID no existe."""
        for n, libro in self.recorrer():
            if libro.id_libro == id_libro:
                return n, libro
        return None

    def cambiar_estado(self, id_libro: int, disponible: bool, id_lector=0, nombre="", f_prestamo="", f_devolucion=""):
        hallado = self.buscar_secuencial(id_libro)
        if hallado is None:
            return False
        n, libro = hallado
        libro.disponible = disponible
        libro.id_lector, libro.nombre_lector = (id_lector, nombre) if not disponible else (0, "")
        libro.fecha_prestamo, libro.fecha_devolucion = (f_prestamo, f_devolucion) if not disponible else ("", "")
        self.modificar(n, libro)
        return True

    def _validar(self, n: int) -> None:
        if n < 1 or n > self.total():
            raise IndexError(f"Registro {n} fuera de rango (1..{self.total()})")

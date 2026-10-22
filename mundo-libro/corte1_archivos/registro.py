"""Registro de longitud fija de un libro (Corte 1).

Diseño (coincide con la tabla «Diseño del archivo» del documento):
    ID libro 4 | Título 50 | Autor 40 | Estado 1 | ID lector 4 |
    Nombre lector 50 | Fecha P 12 | Fecha D 12  ->  173 bytes
"""
import struct
from dataclasses import dataclass

FORMATO = "<i50s40sBi50s12s12s"
TAMANO = struct.calcsize(FORMATO)  # 173 bytes
assert TAMANO == 173


def _a_bytes(texto: str, ancho: int) -> bytes:
    """Codifica el texto en UTF-8, lo recorta a `ancho` bytes y rellena con espacios."""
    datos = texto.encode("utf-8")[:ancho]
    return datos.ljust(ancho, b" ")


def _a_texto(datos: bytes) -> str:
    return datos.decode("utf-8", errors="ignore").rstrip()


@dataclass
class Libro:
    id_libro: int
    titulo: str
    autor: str
    disponible: bool = True          # Estado: 1 disponible / 0 prestado
    id_lector: int = 0
    nombre_lector: str = ""
    fecha_prestamo: str = ""         # AAAA-MM-DD
    fecha_devolucion: str = ""

    def a_bytes(self) -> bytes:
        return struct.pack(
            FORMATO,
            self.id_libro,
            _a_bytes(self.titulo, 50),
            _a_bytes(self.autor, 40),
            1 if self.disponible else 0,
            self.id_lector,
            _a_bytes(self.nombre_lector, 50),
            _a_bytes(self.fecha_prestamo, 12),
            _a_bytes(self.fecha_devolucion, 12),
        )

    @staticmethod
    def desde_bytes(datos: bytes) -> "Libro":
        (idl, tit, aut, est, idlec, nom, fp, fd) = struct.unpack(FORMATO, datos)
        return Libro(idl, _a_texto(tit), _a_texto(aut), bool(est), idlec,
                     _a_texto(nom), _a_texto(fp), _a_texto(fd))

    def __str__(self) -> str:
        estado = "disponible" if self.disponible else f"prestado a {self.nombre_lector} (hasta {self.fecha_devolucion})"
        return f"[{self.id_libro}] {self.titulo} - {self.autor} ({estado})"

import os, tempfile, unittest, random
from corte1_archivos.archivo_libros import ArchivoLibros
from corte1_archivos.registro import Libro, TAMANO
from corte1_archivos.ordenacion import ordenar_por_busqueda, ordenar_mezcla_directa


class PruebasArchivo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.ruta = os.path.join(self.dir, "libros.dat")
        self.arch = ArchivoLibros(self.ruta)
        for i in (5, 3, 9, 1, 7, 2, 8):
            self.arch.agregar(Libro(1000 + i, f"Libro {i}", "Autor"))

    def test_tamano_registro(self):
        self.assertEqual(TAMANO, 173)
        self.assertEqual(os.path.getsize(self.ruta), 7 * 173)

    def test_acceso_directo(self):
        self.assertEqual(self.arch.leer_directo(3).id_libro, 1009)

    def test_acceso_directo_fuera_de_rango(self):
        with self.assertRaises(IndexError):
            self.arch.leer_directo(99)

    def test_busqueda_secuencial(self):
        self.assertEqual(self.arch.buscar_secuencial(1001)[0], 4)
        self.assertIsNone(self.arch.buscar_secuencial(5555))

    def test_modificar_estado(self):
        self.assertTrue(self.arch.cambiar_estado(1003, False, 7, "Ana", "2026-10-01", "2026-10-16"))
        self.assertFalse(self.arch.buscar_secuencial(1003)[1].disponible)

    def test_ordenacion_externa(self):
        salida = self.ruta + ".ord"
        ordenar_por_busqueda(self.ruta, salida)
        ids = [l.id_libro for _, l in ArchivoLibros(salida).recorrer()]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), 7)

    def test_mezcla_directa(self):
        pasadas = ordenar_mezcla_directa(self.ruta)
        ids = [l.id_libro for _, l in self.arch.recorrer()]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(pasadas, 3)

    def test_mezcla_directa_aleatoria(self):
        ruta = os.path.join(self.dir, "r.dat"); a = ArchivoLibros(ruta)
        ids = random.sample(range(1, 200), 53)
        for i in ids: a.agregar(Libro(i, "t", "a"))
        ordenar_mezcla_directa(ruta)
        self.assertEqual([l.id_libro for _, l in a.recorrer()], sorted(ids))


if __name__ == "__main__":
    unittest.main()

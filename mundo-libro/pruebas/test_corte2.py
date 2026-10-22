import os, tempfile, unittest
from corte1_archivos.archivo_libros import ArchivoLibros
from corte2_arboles.arbol import Arbol
from corte2_arboles.catalogo import crear_datos_ejemplo


class PruebasArbol(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.libros = os.path.join(self.dir, "libros.dat")
        self.txt = os.path.join(self.dir, "arbol_catalogo.txt")
        crear_datos_ejemplo(self.libros, self.txt)
        self.arbol = Arbol.cargar(self.txt)

    def test_medidas(self):
        self.assertEqual(self.arbol.medidas(), (3, 21, 9))

    def test_insertar(self):
        self.assertTrue(self.arbol.insertar("Novela", "2001|Pedro Páramo"))
        self.assertEqual(self.arbol.medidas(), (3, 22, 10))

    def test_insertar_padre_inexistente(self):
        self.assertFalse(self.arbol.insertar("Deportes", "x"))
        self.assertEqual(self.arbol.medidas(), (3, 21, 9))

    def test_preorden(self):
        pre = [d for _, d in self.arbol.preorden()]
        self.assertEqual(pre[:6], ["Biblioteca Mundo Libro", "Literatura", "Novela",
                                   "1001|Cien años de soledad", "1002|Crónica de una muerte anunciada", "Cuento"])
        self.assertEqual(len(pre), 21)

    def test_posorden(self):
        pos = self.arbol.posorden()
        self.assertEqual(pos[-1], "Biblioteca Mundo Libro")
        self.assertEqual(pos[0], "1001|Cien años de soledad")

    def test_buscar(self):
        self.assertEqual(self.arbol.buscar("Informática").dato, "Informática")
        self.assertEqual(self.arbol.buscar("1008").dato, "1008|El principito")
        self.assertEqual(self.arbol.buscar("el principito").dato, "1008|El principito")
        self.assertIsNone(self.arbol.buscar("Deportes"))

    def test_eliminar_con_descendencia(self):
        self.assertTrue(self.arbol.eliminar("Ciencias"))
        self.assertEqual(self.arbol.medidas(), (3, 15, 6))
        self.assertIsNone(self.arbol.buscar("Informática"))

    def test_eliminar_inexistente(self):
        self.assertFalse(self.arbol.eliminar("Deportes"))

    def test_buscar_con_traza(self):
        nodo, camino, visitados = self.arbol.buscar_con_traza("Informática")
        self.assertEqual(nodo.dato, "Informática")
        self.assertEqual(camino, ["Biblioteca Mundo Libro", "Ciencias", "Informática"])
        self.assertEqual(visitados, 13)           # posición de Informática en el preorden
        nodo, camino, visitados = self.arbol.buscar_con_traza("Deportes")
        self.assertIsNone(nodo)
        self.assertEqual((camino, visitados), ([], 21))

    def test_guardar_y_reconstruir(self):
        self.arbol.insertar("Poesía", "2002|Sonetos")
        copia = os.path.join(self.dir, "copia.txt")
        self.arbol.guardar(copia)
        nuevo = Arbol.cargar(copia)
        self.assertEqual(nuevo.preorden(), self.arbol.preorden())
        self.assertEqual(nuevo.medidas(), self.arbol.medidas())

    def test_archivo_texto(self):
        with open(self.txt, encoding="utf-8") as f:
            lineas = f.read().splitlines()
        self.assertEqual(lineas[0], "0|Biblioteca Mundo Libro")
        self.assertEqual(lineas[3], "3|1001|Cien años de soledad")
        self.assertEqual(len(lineas), 21)

    def test_enlace_con_archivo(self):
        for nivel, dato in self.arbol.preorden():
            if nivel == 3:
                self.assertIsNotNone(ArchivoLibros(self.libros).buscar_secuencial(int(dato.split("|")[0])))


if __name__ == "__main__":
    unittest.main()

import os, re, subprocess, sys, tempfile, unittest

from interfaz import estilo
from interfaz.menus import es_libro, id_de, titulo_de

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class PruebasEstilo(unittest.TestCase):
    def setUp(self):
        self.antes = (estilo.CONFIG.color, estilo.CONFIG.unicode, estilo.CONFIG.ancho)
        estilo.CONFIG.ancho = 70

    def tearDown(self):
        estilo.CONFIG.color, estilo.CONFIG.unicode, estilo.CONFIG.ancho = self.antes

    def test_caja_con_ancho_uniforme(self):
        for color in (False, True):
            for unicode_ in (False, True):
                estilo.CONFIG.color, estilo.CONFIG.unicode = color, unicode_
                caja = estilo.armar_caja([estilo.c("hola", "ok"), "texto " * 30], titulo="Título")
                anchos = {estilo.largo(linea) for linea in caja.splitlines()}
                self.assertEqual(anchos, {70})

    def test_recortar_conserva_largo_visible(self):
        estilo.CONFIG.color = True
        texto = estilo.c("abcdefghij", "ok") + " klm"
        recortado = estilo.recortar(texto, 8)
        self.assertEqual(estilo.largo(recortado), 8)
        self.assertEqual(estilo.recortar("corto", 8), "corto")

    def test_tabla_cabe_en_la_caja(self):
        estilo.CONFIG.color = False
        columnas = [("ID", 6), ("Título", 40), ("Autor", 40), ("Estado", 12)]
        filas = [["1001", "T" * 60, "A" * 60, "disponible"]]
        for linea in estilo.tabla(columnas, filas):
            self.assertLessEqual(estilo.largo(linea), estilo.CONFIG.ancho - 4)

    def test_es_libro(self):
        self.assertTrue(es_libro("1001|Cien años de soledad"))
        self.assertFalse(es_libro("Informática"))
        self.assertFalse(es_libro("Arte|Moderno"))
        self.assertEqual(id_de("1001|Título | con barra"), 1001)
        self.assertEqual(titulo_de("1001|Título | con barra"), "Título | con barra")


def ejecutar(entradas, carpeta):
    """Ejecuta main.py en modo simple con respuestas simuladas."""
    entorno = dict(os.environ, MUNDO_LIBRO_DATOS=carpeta)
    return subprocess.run([sys.executable, "main.py", "--simple"], cwd=RAIZ, env=entorno,
                          input="\n".join(entradas) + "\n", capture_output=True, text=True, encoding="utf-8")


class PruebasFlujo(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.mkdtemp()

    def test_primera_ejecucion_crea_datos_y_sale(self):
        r = ejecutar(["0"], self.carpeta)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Primera ejecución", r.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "libros.dat")))
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "arbol_catalogo.txt")))

    def test_sin_codigos_de_color_en_modo_simple(self):
        r = ejecutar(["1", "1", "0", "0"], self.carpeta)
        self.assertEqual(ANSI.sub("", r.stdout), r.stdout)
        self.assertIn("Biblioteca Mundo Libro", r.stdout)

    def test_insertar_guardar_y_reconstruir(self):
        r = ejecutar(["1", "4", "raíz", "Arte", "4", "arte", "Pintura",
                      "5", "2001", "Pedro Páramo", "Autor", "pintura",
                      "9", "0", "0"], self.carpeta)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.carpeta, "arbol_catalogo.txt"), encoding="utf-8") as f:
            lineas = f.read().splitlines()
        self.assertEqual(len(lineas), 24)
        self.assertEqual(lineas[-3:], ["1|Arte", "2|Pintura", "3|2001|Pedro Páramo"])
        r2 = ejecutar(["1", "7", "0", "0"], self.carpeta)
        self.assertIn("24", r2.stdout)

    def test_eliminar_pide_confirmacion(self):
        r = ejecutar(["1", "6", "Ciencias", "n", "7", "0", "0"], self.carpeta)
        self.assertIn("Operación cancelada", r.stdout)
        with open(os.path.join(self.carpeta, "arbol_catalogo.txt"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 21)

    def test_eliminar_con_confirmacion(self):
        r = ejecutar(["1", "6", "Ciencias", "s", "0", "0"], self.carpeta)
        self.assertIn("21", r.stdout)
        with open(os.path.join(self.carpeta, "arbol_catalogo.txt"), encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 15)

    def test_prestamo_y_devolucion(self):
        r = ejecutar(["2", "5", "1001", "7", "Ana", "7", "6", "1001", "0", "0"], self.carpeta)
        self.assertIn("Préstamo registrado", r.stdout)
        self.assertIn("devuelto por Ana", r.stdout)

    def test_tildes_y_enie_se_guardan_y_se_leen(self):
        ejecutar(["1", "4", "raíz", "Niñez y juventud", "9", "0", "0"], self.carpeta)
        with open(os.path.join(self.carpeta, "arbol_catalogo.txt"), encoding="utf-8") as f:
            self.assertIn("1|Niñez y juventud", f.read().splitlines())
        r = ejecutar(["1", "3", "NIÑEZ Y JUVENTUD", "0", "0"], self.carpeta)
        self.assertIn("Niñez y juventud", r.stdout)
        self.assertNotIn("\ufffd", r.stdout)

    def test_entradas_invalidas_no_rompen(self):
        r = ejecutar(["x", "9", "1", "99", "abc", "5", "0", "0"], self.carpeta)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_archivo_de_arbol_danado(self):
        ejecutar(["0"], self.carpeta)
        with open(os.path.join(self.carpeta, "arbol_catalogo.txt"), "w", encoding="utf-8") as f:
            f.write("esto no es un árbol\n")
        r = ejecutar(["0"], self.carpeta)
        self.assertEqual(r.returncode, 1)
        self.assertIn("formato válido", r.stdout)

    def test_arbol_ausente_no_borra_los_libros(self):
        ejecutar(["0"], self.carpeta)
        os.remove(os.path.join(self.carpeta, "arbol_catalogo.txt"))
        r = ejecutar(["1", "1", "0", "0"], self.carpeta)
        self.assertIn("Sin clasificar: 9", r.stdout)


if __name__ == "__main__":
    unittest.main()

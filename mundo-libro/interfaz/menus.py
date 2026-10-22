"""Pantallas y menús de Mundo Libro.

Solo presentación: la lógica vive en corte1_archivos (archivo de registros de
longitud fija) y corte2_arboles (árbol genérico del catálogo).
"""
import os
from datetime import date, timedelta

from corte1_archivos.archivo_libros import ArchivoLibros
from corte1_archivos.registro import Libro, TAMANO
from corte1_archivos.ordenacion import ordenar_por_busqueda, ordenar_mezcla_directa
from corte2_arboles.arbol import Arbol
from corte2_arboles.catalogo import crear_datos_ejemplo
from . import estilo as e

DIAS_PRESTAMO = 15
ID_RAIZ_ALIAS = ("raiz", "raíz")


# ---------------------------------------------------------------- utilidades del árbol
def es_libro(dato: str) -> bool:
    """Las hojas de libro guardan «ID|título»; las categorías no llevan «|»."""
    cabeza, separador, _ = dato.partition("|")
    return bool(separador) and cabeza.isdigit()


def id_de(dato: str) -> int:
    return int(dato.split("|", 1)[0])


def titulo_de(dato: str) -> str:
    return dato.split("|", 1)[1]


def recorrer(nodo, camino=()):
    """Genera (camino, nodo) en preorden; el camino incluye al propio nodo."""
    camino = camino + (nodo.dato,)
    yield camino, nodo
    for hijo in nodo.hijos:
        yield from recorrer(hijo, camino)


def tipo_nodo(camino, nodo) -> str:
    if len(camino) == 1:
        return "raíz"
    if es_libro(nodo.dato):
        return "libro (hoja)"
    return "categoría" if len(camino) == 2 else "subcategoría"


def nombre_corto(dato: str) -> str:
    return f"{id_de(dato)}  {titulo_de(dato)}" if es_libro(dato) else dato


def ruta_texto(camino) -> str:
    sep = f" {e.g('flecha')} "
    return sep.join(nombre_corto(d) if i else d for i, d in enumerate(camino))


class App:
    def __init__(self, ruta_libros: str, ruta_arbol: str):
        self.ruta_libros = ruta_libros
        self.ruta_arbol = ruta_arbol
        self.aviso_inicial = self._preparar_datos()
        self.archivo = ArchivoLibros(ruta_libros)
        self.arbol = Arbol.cargar(ruta_arbol)

    # ------------------------------------------------------------ datos iniciales
    def _preparar_datos(self):
        hay_libros = os.path.exists(self.ruta_libros)
        hay_arbol = os.path.exists(self.ruta_arbol)
        if not hay_libros and not hay_arbol:
            crear_datos_ejemplo(self.ruta_libros, self.ruta_arbol)
            return "Primera ejecución: se crearon 9 libros de ejemplo y su árbol en la carpeta datos/."
        if hay_libros and not hay_arbol:
            Arbol().guardar(self.ruta_arbol)
            return "No había árbol guardado: se creó uno vacío. Los libros del archivo aparecen sin clasificar."
        if hay_arbol and not hay_libros:
            return "No se encontró libros.dat: se creó vacío. Las hojas del árbol aún no tienen registro."
        return None

    # ------------------------------------------------------------ consultas comunes
    def registros(self) -> dict:
        """ID -> (n.º de registro, Libro), en el orden del archivo."""
        return {libro.id_libro: (n, libro) for n, libro in self.archivo.recorrer()}

    def hay_cambios(self) -> bool:
        try:
            return Arbol.cargar(self.ruta_arbol).preorden() != self.arbol.preorden()
        except (OSError, ValueError):
            return True

    def ids_clasificados(self) -> set:
        return {id_de(n.dato) for _, n in recorrer(self.arbol.raiz) if es_libro(n.dato)}

    def buscar_flexible(self, texto: str):
        """Busca por dato, ID o título (sin distinguir mayúsculas). «raíz» devuelve la raíz."""
        if texto.casefold() in ID_RAIZ_ALIAS:
            return self.arbol.raiz
        nodo = self.arbol.buscar(texto)
        if nodo is not None:
            return nodo
        for _, n in recorrer(self.arbol.raiz):
            if n.dato.casefold() == texto.casefold():
                return n
        return None

    def pedir_nodo(self, etiqueta: str, solo_contenedores: bool = False):
        while True:
            texto = e.pedir(etiqueta)
            nodo = self.buscar_flexible(texto)
            if nodo is None:
                e.error(f"No hay ningún nodo «{texto}». No distingue mayúsculas; revisa el nombre.")
            elif solo_contenedores and es_libro(nodo.dato):
                e.error("Eso es un libro (una hoja) y no puede contener otros nodos.")
            else:
                return nodo

    def resumen(self) -> str:
        regs = self.registros()
        prestados = sum(1 for _, (_, libro) in regs.items() if not libro.disponible)
        altura, nodos, _ = self.arbol.medidas()
        estado = e.c("guardado", "ok") if not self.hay_cambios() else e.c("sin guardar", "aviso")
        punto = f"  {e.g('punto')}  "
        return (f"{len(regs)} libros{punto}{prestados} prestados{punto}"
                f"árbol: {nodos} nodos, altura {altura}{punto}{estado}")

    def encabezado(self, *ruta: str) -> None:
        e.limpiar()
        e.actualizar_ancho()
        migas = f" {e.g('flecha')} ".join(ruta)
        e.caja([e.c(migas, "negrita"), self.resumen()], titulo="Mundo Libro", borde="marca")

    def ejecutar_accion(self, ruta, accion) -> None:
        self.encabezado(*ruta)
        try:
            accion()
        except e.Cancelado:
            e.aviso("Operación cancelada. No se modificó nada.")
        e.pausa()

    def submenu(self, titulo: str, acciones) -> None:
        while True:
            self.encabezado(titulo)
            opcion = e.menu([(t, d) for t, d, _ in acciones])
            if opcion == 0:
                return
            texto, _, accion = acciones[opcion - 1]
            self.ejecutar_accion((titulo, texto), accion)

    # ------------------------------------------------------------ menú principal
    def ejecutar(self) -> None:
        try:
            while True:
                self.encabezado("Inicio")
                if self.aviso_inicial:
                    e.info(self.aviso_inicial)
                    self.aviso_inicial = None
                estado = "activadas" if e.CONFIG.explicar else "desactivadas"
                opcion = e.menu(
                    [("Catálogo en árbol", "categorías, subcategorías y libros"),
                     ("Libros y préstamos", "archivo de registros fijos"),
                     (f"Explicaciones: {estado}", "qué pasa en la estructura")],
                    salida="Salir y guardar el árbol")
                if opcion == 1:
                    self.submenu("Catálogo en árbol", self.acciones_catalogo())
                elif opcion == 2:
                    self.submenu("Libros y préstamos", self.acciones_libros())
                elif opcion == 3:
                    e.CONFIG.explicar = not e.CONFIG.explicar
                elif opcion == 0:
                    break
        except (KeyboardInterrupt, EOFError):
            print()
        self.guardar_al_salir()

    def guardar_al_salir(self) -> None:
        self.arbol.guardar(self.ruta_arbol)
        e.ok(f"Árbol guardado en {os.path.basename(self.ruta_arbol)}. Hasta pronto.")

    # ============================================================ CATÁLOGO EN ÁRBOL
    def acciones_catalogo(self):
        return [
            ("Ver catálogo completo", "recorrido en preorden", self.ver_catalogo),
            ("Ver los libros de una categoría", "hojas de un subárbol", self.libros_de_categoria),
            ("Buscar un dato", "por nombre, ID o título", self.buscar_dato),
            ("Agregar categoría o subcategoría", "inserción de un nodo", self.agregar_categoria),
            ("Agregar libro al catálogo", "archivo + árbol", self.agregar_libro),
            ("Eliminar categoría o libro", "con toda su descendencia", self.eliminar_nodo),
            ("Medidas del árbol", "altura, nodos y hojas", self.medidas),
            ("Ver recorrido en posorden", "hijos antes que el padre", self.ver_posorden),
            ("Guardar el árbol en el archivo", "arbol_catalogo.txt", self.guardar_arbol),
            ("Reconstruir el árbol desde el archivo", "descarta lo no guardado", self.reconstruir_arbol),
        ]

    def estado_libro(self, id_libro: int, regs: dict) -> str:
        if id_libro not in regs:
            return e.c("sin registro", "aviso")
        if regs[id_libro][1].disponible:
            return e.c(f"{e.g('lleno')} disponible", "ok")
        return e.c(f"{e.g('hueco')} prestado", "error")

    def lineas_arbol(self, regs: dict) -> list:
        lineas, contador = [], [0]
        cuerpo = e.CONFIG.ancho - 4

        def rec(nodo, nivel, prefijo, ultimo):
            contador[0] += 1
            if nivel == 0:
                rama, extension = "", ""
            else:
                rama = e.g("fin") if ultimo else e.g("rama")
                extension = e.g("vacio") if ultimo else e.g("tronco")
            margen = e.c(f"{contador[0]:>3}  N{nivel}  ", "tenue") + e.c(prefijo + rama, "tenue")
            derecha = ""
            if nivel == 0:
                etiqueta = e.c(nodo.dato, "negrita", "acento")
            elif es_libro(nodo.dato):
                etiqueta = f"{e.c(id_de(nodo.dato), 'acento')}  {titulo_de(nodo.dato)}"
                derecha = self.estado_libro(id_de(nodo.dato), regs)
            else:
                etiqueta = e.c(nodo.dato, "negrita", "marca") if nivel == 1 else e.c(nodo.dato, "suave")
                if not nodo.hijos:
                    etiqueta += e.c("  (vacía)", "tenue")
            izquierda = margen + etiqueta
            if derecha:
                sitio = cuerpo - e.largo(derecha) - 2
                izquierda = e.recortar(izquierda, sitio)
                izquierda += " " * (cuerpo - e.largo(izquierda) - e.largo(derecha))
            lineas.append(izquierda + derecha)
            for i, hijo in enumerate(nodo.hijos):
                rec(hijo, nivel + 1, prefijo + extension, i == len(nodo.hijos) - 1)

        rec(self.arbol.raiz, 0, "", True)
        return lineas

    def ver_catalogo(self) -> None:
        regs = self.registros()
        encabezado = e.c("ord  niv  catálogo", "tenue")
        e.caja_paginada([encabezado] + self.lineas_arbol(regs), "Catálogo en preorden", por_pagina=18)
        clasificados = self.ids_clasificados()
        sin = [libro for id_libro, (_, libro) in regs.items() if id_libro not in clasificados]
        if sin:
            lineas = [f"{e.c(libro.id_libro, 'acento')}  {libro.titulo}  {e.c(libro.autor, 'tenue')}" for libro in sin]
            e.caja_paginada(lineas, f"Sin clasificar: {len(sin)} en el archivo, no en el árbol", por_pagina=10)
            e.info("Clasifícalos con «Agregar libro al catálogo» escribiendo su ID.")
        e.nota("Qué pasó en el árbol",
               "El preorden visita cada nodo antes que sus hijos, de izquierda a derecha; por eso cada "
               "categoría aparece sobre lo que contiene. «Orden» es la posición de la visita y «N» el nivel, "
               "la distancia a la raíz (N0). Las hojas son los libros, y su estado se lee del archivo libros.dat.")

    def pista_categorias(self) -> None:
        lineas = []
        for nivel_1 in self.arbol.raiz.hijos:
            hijos = [h.dato for h in nivel_1.hijos if not es_libro(h.dato)]
            lineas.append(e.c(nivel_1.dato, "negrita", "marca")
                          + (f" {e.g('flecha')} " + ", ".join(hijos) if hijos else e.c("  (sin subcategorías)", "tenue")))
        if lineas:
            e.caja(lineas, "Categorías disponibles")

    def libros_de_categoria(self) -> None:
        self.pista_categorias()
        nodo = self.pedir_nodo("Categoría o subcategoría")
        libros = [n for _, n in recorrer(nodo) if es_libro(n.dato)]
        if not libros:
            e.aviso(f"«{nodo.dato}» no tiene libros clasificados.")
            return
        regs = self.registros()
        filas = []
        for n in libros:
            id_libro = id_de(n.dato)
            autor = regs[id_libro][1].autor if id_libro in regs else ""
            filas.append([str(id_libro), titulo_de(n.dato), autor, self.estado_libro(id_libro, regs)])
        columnas = [("ID", 6), ("Título", 34), ("Autor", 22), ("Estado", 12)]
        e.caja_paginada(e.tabla(columnas, filas), f"{len(libros)} libro(s) en {nodo.dato}", por_pagina=16)
        e.nota("Qué pasó en el árbol",
               f"Se ubicó el nodo «{nodo.dato}» y se recorrió solo su subárbol, sin mirar el resto del catálogo. "
               "Los libros son las hojas de ese subárbol; el autor y el estado se leen del archivo por su ID.")

    def buscar_dato(self) -> None:
        texto = e.pedir("Nombre, ID o título a buscar")
        nodo, camino, visitados = self.arbol.buscar_con_traza(texto)
        if nodo is None:
            nodo = self.buscar_flexible(texto)
            if nodo is not None:
                nodo, camino, visitados = self.arbol.buscar_con_traza(nodo.dato)
        total = self.arbol.medidas()[1]
        if nodo is None:
            e.error(f"No existe «{texto}» en el catálogo. El árbol no cambió.")
            e.nota("Qué pasó en el árbol",
                   f"La búsqueda recorrió los {visitados} nodos del árbol sin hallar coincidencias y devolvió nulo. "
                   "En un árbol genérico no hay orden entre los datos, por eso hay que revisar cada rama.")
            return
        libros_dentro = sum(1 for _, n in recorrer(nodo) if es_libro(n.dato))
        pares = [("Dato", e.c(nombre_corto(nodo.dato), "negrita")),
                 ("Tipo", tipo_nodo(camino, nodo)),
                 ("Nivel", str(len(camino) - 1)),
                 ("Camino", ruta_texto(camino)),
                 ("Hijos", str(len(nodo.hijos)))]
        if es_libro(nodo.dato):
            regs = self.registros()
            id_libro = id_de(nodo.dato)
            if id_libro in regs:
                n, libro = regs[id_libro]
                pares += [("Autor", libro.autor), ("Estado", self.estado_libro(id_libro, regs)),
                          ("Registro", f"n.º {n} en libros.dat")]
        else:
            pares.append(("Libros dentro", str(libros_dentro)))
        e.ficha(pares, "Encontrado")
        e.nota("Qué pasó en el árbol",
               f"La búsqueda es recursiva: compara cada nodo con lo buscado (caso base) y, si no coincide, "
               f"sigue por sus hijos (caso recursivo). Visitó {visitados} de {total} nodos hasta encontrarlo "
               f"y devolvió el primero que coincidió.")

    def agregar_categoria(self) -> None:
        self.pista_categorias()
        e.info("Para una categoría general escribe «raíz» como padre.")
        padre = self.pedir_nodo("Dentro de (nombre del padre)", solo_contenedores=True)
        if any(es_libro(h.dato) for h in padre.hijos):
            e.error(f"«{padre.dato}» ya contiene libros: guarda libros o subcategorías, no ambos.")
            return

        def validar(texto):
            if "|" in texto:
                return "El nombre no puede llevar «|» (es el separador del archivo)."
            if texto.isdigit():
                return "El nombre no puede ser solo un número: se confundiría con el ID de un libro."
            if self.buscar_flexible(texto) is not None:
                return f"Ya existe un nodo llamado «{texto}»."
            return None

        nombre = e.pedir_texto("Nombre nuevo", validar=validar)
        antes = self.arbol.medidas()
        self.arbol.insertar(padre.dato, nombre)
        despues = self.arbol.medidas()
        e.ok(f"«{nombre}» creada dentro de «{padre.dato}».")
        e.ficha([("Nodos", f"{antes[1]} {e.g('flecha')} {despues[1]}"),
                 ("Altura", f"{antes[0]} {e.g('flecha')} {despues[0]}")], "Cambio en el árbol")
        e.nota("Qué pasó en el árbol",
               f"insertar() busca el padre de forma recursiva. Caso base: el nodo actual es «{padre.dato}», "
               f"así que se crea un Nodo y se agrega a su lista de hijos. Caso recursivo: si no lo es, "
               f"se intenta en cada hijo.",
               "El cambio está solo en memoria: usa «Guardar el árbol en el archivo» para conservarlo.")

    def contenedores_de_libros(self):
        """Subcategorías donde pueden colgar libros: sin otras categorías dentro."""
        res = []
        for camino, nodo in recorrer(self.arbol.raiz):
            if len(camino) == 1 or es_libro(nodo.dato):
                continue
            if all(es_libro(h.dato) for h in nodo.hijos):
                res.append((camino, nodo))
        return res

    def elegir_subcategoria(self):
        candidatas = self.contenedores_de_libros()
        if not candidatas:
            e.error("No hay subcategorías donde clasificar. Crea una con «Agregar categoría o subcategoría».")
            raise e.Cancelado()
        filas = [[str(i), f" {e.g('flecha')} ".join(camino[1:])] for i, (camino, _) in enumerate(candidatas, 1)]
        e.caja_paginada(e.tabla([("N.º", 4), ("Subcategoría", 60)], filas), "Dónde clasificarlo", por_pagina=14)
        while True:
            respuesta = e.pedir("Número o nombre de la subcategoría")
            if respuesta.isdigit() and 1 <= int(respuesta) <= len(candidatas):
                return candidatas[int(respuesta) - 1][1]
            nodo = self.buscar_flexible(respuesta)
            for _, candidata in candidatas:
                if candidata is nodo:
                    return nodo
            e.error("Elige un número de la lista o el nombre exacto de una subcategoría.")

    def agregar_libro(self) -> None:
        id_libro = e.pedir_entero("ID del libro")
        existente = self.archivo.buscar_secuencial(id_libro)
        if id_libro in self.ids_clasificados():
            camino = self.arbol.buscar_con_traza(str(id_libro))[1]
            e.error(f"El libro {id_libro} ya está clasificado en {ruta_texto(camino[:-1])}.")
            return
        if existente:
            libro = existente[1]
            e.info(f"El libro {id_libro} («{libro.titulo}») ya está en el archivo y falta clasificarlo.")
            titulo, nuevo = libro.titulo, False
        else:
            titulo = e.pedir_texto("Título", max_bytes=50, validar=lambda t: "El título no puede llevar «|»." if "|" in t else None)
            autor = e.pedir_texto("Autor", max_bytes=40)
            nuevo = True
        sub = self.elegir_subcategoria()
        if nuevo:
            posicion = self.archivo.agregar(Libro(id_libro, titulo, autor))
        self.arbol.insertar(sub.dato, f"{id_libro}|{titulo}")
        camino = self.arbol.buscar_con_traza(str(id_libro))[1]
        if nuevo:
            e.ok(f"Libro guardado en libros.dat (registro n.º {posicion}) y clasificado en el árbol.")
        else:
            e.ok("Libro clasificado en el árbol; su registro en libros.dat no cambió.")
        e.ficha([("Libro", f"{id_libro}  {titulo}"), ("Ubicación", ruta_texto(camino[:-1])),
                 ("Nivel de la hoja", str(len(camino) - 1))], "Clasificado")
        e.nota("Qué pasó en el archivo y en el árbol",
               ("Se escribió un registro de 173 bytes al final de libros.dat. " if nuevo else
                "El registro ya existía, así que el archivo no se tocó. ")
               + f"En el árbol se insertó la hoja «{id_libro}|{titulo}» como hijo de «{sub.dato}»: "
               "el ID de la hoja es el enlace con su registro.",
               "El árbol cambió solo en memoria; guárdalo para persistirlo.")

    def eliminar_nodo(self) -> None:
        nodo = self.pedir_nodo("Nombre, ID o título a eliminar")
        if nodo is self.arbol.raiz:
            e.error("La raíz no se puede eliminar.")
            return
        _, camino, _ = self.arbol.buscar_con_traza(nodo.dato)
        padre = camino[-2]
        subarbol = list(recorrer(nodo))
        libros = sum(1 for _, n in subarbol if es_libro(n.dato))
        lineas = []
        for ruta, n in subarbol[:12]:
            sangria = "  " * (len(ruta) - 1)
            lineas.append(sangria + (e.c(nombre_corto(n.dato), "acento") if len(ruta) == 1 else nombre_corto(n.dato)))
        if len(subarbol) > 12:
            lineas.append(e.c(f"{e.g('elipsis')} y {len(subarbol) - 12} nodo(s) más", "tenue"))
        e.caja(lineas, "Se eliminará esta rama", borde="aviso")
        e.aviso(f"Son {len(subarbol)} nodo(s), con {libros} libro(s). Los registros siguen en libros.dat.")
        if not e.confirmar("¿Eliminar la rama completa?"):
            e.info("Operación cancelada. No se modificó nada.")
            return
        antes = self.arbol.medidas()
        self.arbol.eliminar(nodo.dato)
        despues = self.arbol.medidas()
        e.ok(f"Se eliminó «{nombre_corto(nodo.dato)}» con su descendencia.")
        e.ficha([("Nodos", f"{antes[1]} {e.g('flecha')} {despues[1]}"),
                 ("Hojas", f"{antes[2]} {e.g('flecha')} {despues[2]}"),
                 ("Altura", f"{antes[0]} {e.g('flecha')} {despues[0]}")], "Cambio en el árbol")
        e.nota("Qué pasó en el árbol",
               f"eliminar() revisa los hijos de cada nodo. Cuando uno coincide, lo quita de la lista de hijos "
               f"de su padre («{padre}»). Al perderse esa referencia también se pierde todo su subárbol "
               f"({len(subarbol)} nodos): no hace falta borrarlos uno a uno.",
               "El cambio está solo en memoria; guárdalo para persistirlo.")

    def medidas(self) -> None:
        altura, nodos, hojas = self.arbol.medidas()
        por_nivel = {}
        libros = 0
        for camino, n in recorrer(self.arbol.raiz):
            por_nivel[len(camino) - 1] = por_nivel.get(len(camino) - 1, 0) + 1
            libros += es_libro(n.dato)
        e.ficha([("Raíz", self.arbol.raiz.dato), ("Altura", str(altura)),
                 ("Niveles", f"{altura + 1} (de 0 a {altura})"), ("Nodos", str(nodos)),
                 ("Hojas", f"{hojas} (nodos sin hijos)"), ("Libros", str(libros))], "Medidas del árbol")
        mayor = max(por_nivel.values())
        lineas = []
        for nivel in sorted(por_nivel):
            barra = e.g("barra") * max(1, round(por_nivel[nivel] * 28 / mayor))
            lineas.append(f"{e.c('N' + str(nivel), 'tenue')}  {e.c(barra, 'marca')} {por_nivel[nivel]}")
        e.caja(lineas, "Nodos por nivel")
        e.nota("Qué pasó en el árbol",
               "Las tres medidas salen de una sola recursión. Caso base: un nodo nulo tiene altura -1 y un nodo "
               "sin hijos es una hoja de altura 0. Caso recursivo: altura = 1 + la mayor altura de sus hijos; "
               "nodos = 1 + la suma de los nodos de cada hijo; hojas = la suma de las hojas de cada hijo.")

    def ver_posorden(self) -> None:
        regs = self.registros()
        lineas = []
        for i, dato in enumerate(self.arbol.posorden(), 1):
            estilo = ("negrita", "acento") if dato == self.arbol.raiz.dato else (() if es_libro(dato) else ("marca",))
            lineas.append(f"{e.c(str(i).rjust(3), 'tenue')}  {e.c(nombre_corto(dato), *estilo)}")
        e.caja_paginada(lineas, "Catálogo en posorden", por_pagina=18)
        e.nota("Qué pasó en el árbol",
               "El posorden visita primero todos los hijos y al final el nodo: los libros salen antes que su "
               "subcategoría y la raíz es lo último. Sirve cuando hay que procesar los descendientes antes "
               "que el padre.")

    def guardar_arbol(self) -> None:
        self.arbol.guardar(self.ruta_arbol)
        with open(self.ruta_arbol, encoding="utf-8") as f:
            lineas = f.read().splitlines()
        vista = [e.c(linea, "suave") if linea[0] != "3" else linea for linea in lineas[:9]]
        if len(lineas) > 9:
            vista.append(e.c(f"{e.g('elipsis')} ({len(lineas) - 9} líneas más)", "tenue"))
        e.ok(f"Árbol guardado: {len(lineas)} líneas en {os.path.basename(self.ruta_arbol)}.")
        e.caja(vista, os.path.basename(self.ruta_arbol))
        e.nota("Qué pasó en el archivo",
               "El guardado recorre el árbol en preorden y escribe una línea «nivel|dato» por nodo. Las "
               "referencias entre objetos no se pueden guardar, pero el orden de las líneas y su nivel "
               "contienen toda la jerarquía. En las hojas el dato es «ID|título».")

    def reconstruir_arbol(self) -> None:
        if self.hay_cambios():
            e.aviso("Hay cambios en memoria que no están guardados; se perderían.")
            if not e.confirmar("¿Reconstruir de todos modos?"):
                e.info("Operación cancelada. No se modificó nada.")
                return
        try:
            nuevo = Arbol.cargar(self.ruta_arbol)
        except (OSError, ValueError) as error:
            e.error(f"No se pudo leer el archivo: {error}")
            return
        self.arbol = nuevo
        altura, nodos, hojas = nuevo.medidas()
        e.ok("Árbol reconstruido desde el archivo.")
        e.ficha([("Nodos", str(nodos)), ("Hojas", str(hojas)), ("Altura", str(altura))], "Árbol cargado")
        e.nota("Qué pasó en el archivo y en el árbol",
               "Se leyó cada línea y se separó su nivel y su dato. La línea de nivel 0 crea la raíz; las demás "
               "se agregan como hijo del último nodo de la pila cuyo nivel es una unidad menor, desapilando "
               "los nodos que ya no pueden ser padres.")

    # ============================================================ LIBROS Y PRÉSTAMOS
    def acciones_libros(self):
        return [
            ("Listar los libros", "acceso secuencial", self.listar),
            ("Consultar por n.º de registro", "acceso directo", self.consultar_directo),
            ("Buscar un libro por ID", "acceso secuencial", self.buscar_id),
            ("Registrar un libro nuevo", "se agrega al final", self.registrar),
            ("Prestar un libro", f"por {DIAS_PRESTAMO} días", self.prestar),
            ("Devolver un libro", "libera el registro", self.devolver),
            ("Préstamos activos y atrasados", "control de devoluciones", self.prestamos),
            ("Editar título o autor", "modifica en su posición", self.editar),
            ("Ordenar por ID: búsqueda externa", "archivo auxiliar", self.ordenar_busqueda),
            ("Ordenar por ID: mezcla directa", "dos archivos auxiliares", self.ordenar_mezcla),
        ]

    def fila_libro(self, n: int, libro: Libro) -> list:
        estado = e.c(f"{e.g('lleno')} disponible", "ok") if libro.disponible else e.c(f"{e.g('hueco')} prestado", "error")
        return [str(n), str(libro.id_libro), libro.titulo, libro.autor, estado]

    COLUMNAS_LIBROS = [("N.º", 4), ("ID", 6), ("Título", 30), ("Autor", 22), ("Estado", 12)]

    def listar(self) -> None:
        filas = [self.fila_libro(n, libro) for n, libro in self.archivo.recorrer()]
        if not filas:
            e.aviso("El archivo no tiene libros todavía.")
            return
        e.caja_paginada(e.tabla(self.COLUMNAS_LIBROS, filas), f"{len(filas)} registros de {TAMANO} bytes", por_pagina=16)
        e.nota("Qué pasó en el archivo",
               f"El acceso secuencial abre libros.dat y lee registro por registro desde el inicio, de {TAMANO} "
               "bytes cada uno, hasta llegar al final.")

    def consultar_directo(self) -> None:
        total = self.archivo.total()
        if total == 0:
            e.aviso("El archivo no tiene libros todavía.")
            return
        n = e.pedir_entero(f"N.º de registro (1 a {total})", maximo=total)
        libro = self.archivo.leer_directo(n)
        desplazamiento = (n - 1) * TAMANO
        e.ficha([("Registro", f"n.º {n}"), ("Desplazamiento", f"({n} - 1) x {TAMANO} = {desplazamiento} bytes"),
                 ("Libro", f"{libro.id_libro}  {libro.titulo}"), ("Autor", libro.autor),
                 ("Estado", "disponible" if libro.disponible else f"prestado a {libro.nombre_lector} hasta {libro.fecha_devolucion}")],
                "Acceso directo")
        e.nota("Qué pasó en el archivo",
               f"Como todos los registros miden {TAMANO} bytes, la posición se calcula sin leer los anteriores: "
               f"el programa hizo seek({desplazamiento}) y leyó un solo registro.")

    def buscar_id(self) -> None:
        id_libro = e.pedir_entero("ID a buscar")
        hallado = self.archivo.buscar_secuencial(id_libro)
        total = self.archivo.total()
        if hallado is None:
            e.error(f"No existe un libro con ID {id_libro}.")
            e.nota("Qué pasó en el archivo", f"Se leyeron los {total} registros desde el inicio y ninguno coincidió.")
            return
        n, libro = hallado
        e.caja_paginada(e.tabla(self.COLUMNAS_LIBROS, [self.fila_libro(n, libro)]), "Encontrado")
        e.nota("Qué pasó en el archivo",
               f"El acceso secuencial leyó {n} de {total} registros, en orden, hasta hallar el ID {id_libro}.")

    def registrar(self) -> None:
        id_libro = e.pedir_entero("ID del libro")
        if self.archivo.buscar_secuencial(id_libro):
            e.error(f"Ya existe un libro con ID {id_libro}.")
            return
        titulo = e.pedir_texto("Título", max_bytes=50, validar=lambda t: "El título no puede llevar «|»." if "|" in t else None)
        autor = e.pedir_texto("Autor", max_bytes=40)
        n = self.archivo.agregar(Libro(id_libro, titulo, autor))
        e.ok(f"Libro registrado en la posición {n} del archivo.")
        e.info("Aún no está en el catálogo: clasifícalo en Catálogo en árbol › Agregar libro al catálogo.")
        e.nota("Qué pasó en el archivo",
               f"El registro se escribió al final de libros.dat; el archivo creció {TAMANO} bytes.")

    def prestar(self) -> None:
        id_libro = e.pedir_entero("ID del libro")
        hallado = self.archivo.buscar_secuencial(id_libro)
        if hallado is None:
            e.error(f"No existe un libro con ID {id_libro}.")
            return
        libro = hallado[1]
        if not libro.disponible:
            e.error(f"«{libro.titulo}» ya está prestado a {libro.nombre_lector} hasta {libro.fecha_devolucion}.")
            return
        e.info(f"Libro: {libro.titulo}")
        id_lector = e.pedir_entero("ID del lector")
        nombre = e.pedir_texto("Nombre del lector", max_bytes=50)
        hoy = date.today()
        vence = hoy + timedelta(days=DIAS_PRESTAMO)
        self.archivo.cambiar_estado(id_libro, False, id_lector, nombre, hoy.isoformat(), vence.isoformat())
        e.ok("Préstamo registrado.")
        e.ficha([("Libro", libro.titulo), ("Lector", f"{nombre} ({id_lector})"),
                 ("Préstamo", hoy.isoformat()), ("Devolución", f"{vence.isoformat()} ({DIAS_PRESTAMO} días)")], "Préstamo")
        e.nota("Qué pasó en el archivo",
               "El registro se reescribió en su misma posición con el estado «prestado» y los datos del lector. "
               "El árbol no cambia: la hoja del libro sigue en su categoría y consulta su estado en el archivo.")

    def devolver(self) -> None:
        id_libro = e.pedir_entero("ID del libro")
        hallado = self.archivo.buscar_secuencial(id_libro)
        if hallado is None:
            e.error(f"No existe un libro con ID {id_libro}.")
            return
        libro = hallado[1]
        if libro.disponible:
            e.aviso(f"«{libro.titulo}» ya estaba disponible.")
            return
        atraso = self.dias_de_atraso(libro)
        self.archivo.cambiar_estado(id_libro, True)
        e.ok(f"«{libro.titulo}» devuelto por {libro.nombre_lector}.")
        if atraso > 0:
            e.aviso(f"Se devolvió con {atraso} día(s) de atraso.")
        e.nota("Qué pasó en el archivo",
               "El registro se reescribió en su posición con el estado «disponible» y los campos del préstamo vacíos.")

    @staticmethod
    def dias_de_atraso(libro: Libro) -> int:
        try:
            return (date.today() - date.fromisoformat(libro.fecha_devolucion)).days
        except ValueError:
            return 0

    def prestamos(self) -> None:
        filas, atrasados = [], 0
        for n, libro in self.archivo.recorrer():
            if libro.disponible:
                continue
            atraso = self.dias_de_atraso(libro)
            if atraso > 0:
                atrasados += 1
                estado = e.c(f"atrasado {atraso} d", "error")
            else:
                estado = e.c("al día", "ok")
            filas.append([str(libro.id_libro), libro.titulo, libro.nombre_lector, libro.fecha_devolucion, estado])
        if not filas:
            e.ok("No hay libros prestados.")
            return
        columnas = [("ID", 6), ("Título", 26), ("Lector", 18), ("Devuelve", 10), ("Estado", 14)]
        e.caja_paginada(e.tabla(columnas, filas), f"{len(filas)} préstamo(s), {atrasados} atrasado(s)", por_pagina=16)

    def editar(self) -> None:
        id_libro = e.pedir_entero("ID del libro a editar")
        hallado = self.archivo.buscar_secuencial(id_libro)
        if hallado is None:
            e.error(f"No existe un libro con ID {id_libro}.")
            return
        n, libro = hallado
        sin_barra = lambda t: "El título no puede llevar «|»." if "|" in t else None
        titulo = e.pedir_texto("Título", max_bytes=50, defecto=libro.titulo, validar=sin_barra)
        autor = e.pedir_texto("Autor", max_bytes=40, defecto=libro.autor)
        if (titulo, autor) == (libro.titulo, libro.autor):
            e.info("No hubo cambios.")
            return
        libro.titulo, libro.autor = titulo, autor
        self.archivo.modificar(n, libro)
        e.ok(f"Registro n.º {n} actualizado.")
        for _, nodo in recorrer(self.arbol.raiz):
            if es_libro(nodo.dato) and id_de(nodo.dato) == id_libro:
                nodo.dato = f"{id_libro}|{titulo}"
                e.info("También se actualizó el título de su hoja en el árbol; guarda el árbol para persistirlo.")
        e.nota("Qué pasó en el archivo",
               f"El registro se reescribió en su misma posición, a {(n - 1) * TAMANO} bytes del inicio.")

    def ordenar_busqueda(self) -> None:
        if self.archivo.total() < 2:
            e.aviso("Hace falta al menos 2 libros para ordenar.")
            return
        antes = [libro.id_libro for _, libro in self.archivo.recorrer()]
        destino = self.ruta_libros + ".ordenado"
        ordenar_por_busqueda(self.ruta_libros, destino)
        os.replace(destino, self.ruta_libros)
        self.mostrar_orden(antes)
        e.nota("Qué pasó en el archivo",
               "En cada pasada se recorrió el archivo de entrada para hallar el menor ID aún no copiado, se escribió "
               "en el archivo de salida y se marcó como copiado. Los registros nunca se cargaron en memoria; "
               "se reemplazó libros.dat por el archivo ordenado.")

    def ordenar_mezcla(self) -> None:
        if self.archivo.total() < 2:
            e.aviso("Hace falta al menos 2 libros para ordenar.")
            return
        antes = [libro.id_libro for _, libro in self.archivo.recorrer()]
        pasadas = ordenar_mezcla_directa(self.ruta_libros)
        self.mostrar_orden(antes)
        e.nota("Qué pasó en el archivo",
               f"Se hicieron {pasadas} pasada(s). En cada una se repartieron bloques entre dos archivos auxiliares "
               "y se mezclaron los pares de bloques en orden de ID; el tamaño del bloque se duplicó hasta cubrir "
               "todo el archivo.")

    def mostrar_orden(self, antes) -> None:
        def resumen(ids):
            return " ".join(str(i) for i in ids[:10]) + (" " + e.g("elipsis") if len(ids) > 10 else "")
        despues = [libro.id_libro for _, libro in self.archivo.recorrer()]
        e.ok("Archivo ordenado por ID.")
        e.ficha([("Antes", resumen(antes)), ("Después", resumen(despues))], "Orden de los IDs")

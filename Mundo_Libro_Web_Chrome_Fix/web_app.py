"""Mundo Libro Web: frontend local compatible con el archivo binario original.

Se puede ejecutar en la raíz del repositorio o desde una subcarpeta que esté
adentro del repositorio. No requiere paquetes externos.
"""
from __future__ import annotations
import json
import os
import struct
import tempfile
import threading
import webbrowser
from dataclasses import dataclass
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent

def find_project_root() -> Path | None:
    """Busca el repositorio real hacia arriba para compartir su carpeta datos/."""
    for candidate in (BASE_DIR, *BASE_DIR.parents):
        if ((candidate / "main.py").is_file()
            and (candidate / "corte1_archivos" / "archivo_libros.py").is_file()
            and (candidate / "corte2_arboles" / "arbol.py").is_file()):
            return candidate
    return None

PROJECT_ROOT = find_project_root()
# Si se extrae dentro del repo, usa sus datos. Si se extrae por separado,
# funciona en modo independiente y crea una carpeta datos/ junto a esta app.
APP_DATA_ROOT = PROJECT_ROOT if PROJECT_ROOT else BASE_DIR
DATA_DIR = Path(os.environ.get("MUNDO_LIBRO_DATOS", APP_DATA_ROOT / "datos")).resolve()
BOOKS_FILE = DATA_DIR / "libros.dat"
TREE_FILE = DATA_DIR / "arbol_catalogo.txt"
WEB_DIR = BASE_DIR / "web"
HOST = "127.0.0.1"
START_PORT = int(os.environ.get("MUNDO_LIBRO_WEB_PORT", "8000"))

# El formato binario es idéntico al del proyecto original (173 bytes).
FORMAT = struct.Struct("<i50s40sBi50s12s12s")
RECORD_SIZE = FORMAT.size
assert RECORD_SIZE == 173


def encode_fixed(text: str, width: int) -> bytes:
    raw = str(text).encode("utf-8")[:width]
    return raw.ljust(width, b" ")


def decode_fixed(raw: bytes) -> str:
    return raw.decode("utf-8", errors="ignore").rstrip()

@dataclass
class Libro:
    id_libro: int
    titulo: str
    autor: str
    disponible: bool = True
    id_lector: int = 0
    nombre_lector: str = ""
    fecha_prestamo: str = ""
    fecha_devolucion: str = ""

    def to_bytes(self) -> bytes:
        return FORMAT.pack(
            int(self.id_libro), encode_fixed(self.titulo, 50), encode_fixed(self.autor, 40),
            1 if self.disponible else 0, int(self.id_lector), encode_fixed(self.nombre_lector, 50),
            encode_fixed(self.fecha_prestamo, 12), encode_fixed(self.fecha_devolucion, 12),
        )

    @staticmethod
    def from_bytes(data: bytes) -> "Libro":
        if len(data) != RECORD_SIZE:
            raise ValueError(f"Registro incompleto: se esperaban {RECORD_SIZE} bytes y llegaron {len(data)}.")
        idl, title, author, status, reader_id, reader_name, loan_date, due_date = FORMAT.unpack(data)
        return Libro(idl, decode_fixed(title), decode_fixed(author), bool(status), reader_id,
                     decode_fixed(reader_name), decode_fixed(loan_date), decode_fixed(due_date))

class ArchivoLibros:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_bytes(b"")

    def total(self) -> int:
        size = self.path.stat().st_size
        if size % RECORD_SIZE:
            raise ValueError(f"libros.dat no tiene un múltiplo de {RECORD_SIZE} bytes (tamaño actual: {size}).")
        return size // RECORD_SIZE

    def recorrer(self):
        with self.path.open("rb") as stream:
            number = 0
            while True:
                block = stream.read(RECORD_SIZE)
                if not block:
                    return
                if len(block) != RECORD_SIZE:
                    raise ValueError(f"El archivo {self.path.name} contiene un registro incompleto al final.")
                number += 1
                yield number, Libro.from_bytes(block)

    def agregar(self, book: Libro) -> int:
        with self.path.open("ab") as stream:
            stream.write(book.to_bytes())
        return self.total()

    def modificar(self, number: int, book: Libro) -> None:
        if number < 1 or number > self.total():
            raise IndexError(f"Registro {number} fuera de rango (1..{self.total()}).")
        with self.path.open("r+b") as stream:
            stream.seek((number - 1) * RECORD_SIZE)
            stream.write(book.to_bytes())

    def buscar_secuencial(self, book_id: int):
        for number, book in self.recorrer():
            if book.id_libro == int(book_id):
                return number, book
        return None

    def cambiar_estado(self, book_id: int, available: bool, reader_id=0, reader_name="", loan_date="", due_date="") -> bool:
        found = self.buscar_secuencial(book_id)
        if found is None:
            return False
        number, book = found
        book.disponible = bool(available)
        if available:
            book.id_lector, book.nombre_lector = 0, ""
            book.fecha_prestamo, book.fecha_devolucion = "", ""
        else:
            book.id_lector, book.nombre_lector = int(reader_id), str(reader_name)
            book.fecha_prestamo, book.fecha_devolucion = str(loan_date), str(due_date)
        self.modificar(number, book)
        return True

class Nodo:
    def __init__(self, dato: str):
        self.dato = dato
        self.hijos: list[Nodo] = []

    def coincide(self, searched: str) -> bool:
        if self.dato == searched:
            return True
        if "|" in self.dato:
            book_id, title = self.dato.split("|", 1)
            return searched == book_id or searched.casefold() == title.casefold()
        return False

    def es_hoja(self) -> bool:
        return not self.hijos

class Arbol:
    def __init__(self, dato_raiz: str = "Biblioteca Mundo Libro"):
        self.raiz = Nodo(dato_raiz)

    def insertar(self, parent: str, data: str) -> bool:
        return self._insertar(self.raiz, parent, data)

    def _insertar(self, node: Nodo, parent: str, data: str) -> bool:
        if node.coincide(parent):
            node.hijos.append(Nodo(data))
            return True
        for child in node.hijos:
            if self._insertar(child, parent, data):
                return True
        return False

    def buscar(self, data: str):
        def walk(node: Nodo):
            if node.coincide(data):
                return node
            for child in node.hijos:
                result = walk(child)
                if result is not None:
                    return result
            return None
        return walk(self.raiz)

    def preorden(self):
        rows = []
        def walk(node: Nodo, level: int):
            rows.append((level, node.dato))
            for child in node.hijos:
                walk(child, level + 1)
        walk(self.raiz, 0)
        return rows

    def medidas(self):
        def walk(node):
            if node is None:
                return -1, 0, 0
            if node.es_hoja():
                return 0, 1, 1
            height, nodes, leaves = 0, 1, 0
            for child in node.hijos:
                h, n, l = walk(child)
                height = max(height, h + 1)
                nodes += n
                leaves += l
            return height, nodes, leaves
        return walk(self.raiz)

    def eliminar(self, data: str) -> bool:
        def walk(node: Nodo):
            for child in node.hijos:
                if child.coincide(data):
                    node.hijos.remove(child)
                    return True
            for child in node.hijos:
                if walk(child):
                    return True
            return False
        return walk(self.raiz)

    def guardar(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
            for level, data in self.preorden():
                stream.write(f"{level}|{data}\n")

    @staticmethod
    def cargar(path: str | Path) -> "Arbol":
        tree = None
        stack: list[tuple[int, Nodo]] = []
        with Path(path).open(encoding="utf-8") as stream:
            for raw_line in stream:
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue
                try:
                    level_text, data = line.split("|", 1)
                    level = int(level_text)
                except (ValueError, TypeError):
                    raise ValueError(f"Línea inválida en arbol_catalogo.txt: {line}")
                if level == 0:
                    tree = Arbol(data)
                    stack = [(0, tree.raiz)]
                    continue
                while stack and stack[-1][0] >= level:
                    stack.pop()
                if not stack:
                    raise ValueError(f"Línea sin padre: {line}")
                node = Nodo(data)
                stack[-1][1].hijos.append(node)
                stack.append((level, node))
        if tree is None:
            raise ValueError("El archivo arbol_catalogo.txt no contiene una raíz nivel 0.")
        return tree

EXAMPLE = [
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

def create_example_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archive = ArchivoLibros(BOOKS_FILE)
    tree = Arbol()
    seen = set()
    for cat, subcat, book_id, title, author in EXAMPLE:
        if cat not in seen:
            tree.insertar(tree.raiz.dato, cat)
            seen.add(cat)
        if (cat, subcat) not in seen:
            tree.insertar(cat, subcat)
            seen.add((cat, subcat))
        archive.agregar(Libro(book_id, title, author))
        tree.insertar(subcat, f"{book_id}|{title}")
    tree.guardar(TREE_FILE)

def ensure_data() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    books_exists, tree_exists = BOOKS_FILE.exists(), TREE_FILE.exists()
    if not books_exists and not tree_exists:
        create_example_data()
    elif not books_exists:
        BOOKS_FILE.write_bytes(b"")
    elif not tree_exists:
        tree = Arbol()
        books = [book for _, book in ArchivoLibros(BOOKS_FILE).recorrer()]
        if books:
            tree.insertar(tree.raiz.dato, "Sin clasificar")
            for book in books:
                tree.insertar("Sin clasificar", f"{book.id_libro}|{book.titulo}")
        tree.guardar(TREE_FILE)

def load_tree() -> Arbol:
    ensure_data()
    return Arbol.cargar(TREE_FILE)

def load_archive() -> ArchivoLibros:
    ensure_data()
    return ArchivoLibros(BOOKS_FILE)

def all_books() -> list[Libro]:
    return [book for _, book in load_archive().recorrer()]

def category_map(tree: Arbol) -> dict[str, dict[str, str]]:
    result = {}
    for category in tree.raiz.hijos:
        for subcategory in category.hijos:
            for leaf in subcategory.hijos:
                if "|" in leaf.dato:
                    book_id, _ = leaf.dato.split("|", 1)
                    result[book_id.strip()] = {"category": category.dato, "subcategory": subcategory.dato}
    return result

def nested_tree(node: Nodo, books: dict[str, Libro] | None = None) -> dict:
    payload = {"name": node.dato, "children": [nested_tree(child, books) for child in node.hijos]}
    if "|" in node.dato:
        book_id, title = node.dato.split("|", 1)
        payload.update(type="book", id=book_id.strip(), title=title.strip())
        book = (books or {}).get(book_id.strip())
        if book:
            payload.update(author=book.autor, available=bool(book.disponible))
    elif not node.hijos:
        payload["type"] = "leaf"
    elif node.dato == "Biblioteca Mundo Libro":
        payload["type"] = "root"
    else:
        payload["type"] = "category"
    return payload

def serialize_book(book: Libro, cats: dict[str, dict[str, str]]) -> dict:
    cat = cats.get(str(book.id_libro), {})
    return {"id": book.id_libro, "title": book.titulo, "author": book.autor,
            "available": bool(book.disponible), "reader_id": book.id_lector,
            "reader_name": book.nombre_lector, "loan_date": book.fecha_prestamo,
            "due_date": book.fecha_devolucion, "category": cat.get("category", "Sin clasificar"),
            "subcategory": cat.get("subcategory", "Sin clasificar")}

def state_payload() -> dict:
    tree, archive = load_tree(), load_archive()
    books = [book for _, book in archive.recorrer()]
    cats = category_map(tree)
    height, nodes, leaves = tree.medidas()
    categories = [node.dato for node in tree.raiz.hijos]
    lent = sum(not book.disponible for book in books)
    lines = TREE_FILE.read_text(encoding="utf-8").splitlines() if TREE_FILE.exists() else []
    return {"ok": True, "books": [serialize_book(b, cats) for b in books],
            "tree": nested_tree(tree.raiz, {str(b.id_libro): b for b in books}),
            "stats": {"total_books": len(books), "available": len(books)-lent, "lent": lent,
                      "categories": len(categories), "height": height, "nodes": nodes, "leaves": leaves},
            "categories": categories,
            "subcategories": {n.dato: [c.dato for c in n.hijos] for n in tree.raiz.hijos},
            "files": {"books_name": BOOKS_FILE.name, "books_bytes": BOOKS_FILE.stat().st_size if BOOKS_FILE.exists() else 0,
                      "tree_name": TREE_FILE.name, "tree_lines": len(lines), "tree_preview": lines[:16],
                      "data_dir": str(DATA_DIR)}}

def write_books_without(remove_ids: set[str]) -> None:
    archive = load_archive()
    fd, temp_name = tempfile.mkstemp(prefix="libros_", suffix=".dat", dir=str(DATA_DIR))
    os.close(fd)
    try:
        replacement = ArchivoLibros(temp_name)
        for _, book in archive.recorrer():
            if str(book.id_libro) not in remove_ids:
                replacement.agregar(book)
        os.replace(temp_name, BOOKS_FILE)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

class Handler(BaseHTTPRequestHandler):
    server_version = "MundoLibroWeb/1.1"

    def log_message(self, fmt, *args):
        print("[Mundo Libro Web] " + fmt % args)

    def send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, status: int, payload: dict) -> None:
        self.send_bytes(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def error(self, message: str, status: int = 400) -> None:
        self.json_response(status, {"ok": False, "error": message})

    def do_GET(self):
        path = urlparse(self.path).path
        static = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/index.html": ("index.html", "text/html; charset=utf-8"),
                  "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if path in static:
            filename, content_type = static[path]
            try:
                self.send_bytes(200, (WEB_DIR / filename).read_bytes(), content_type)
            except FileNotFoundError:
                self.error(f"Falta {WEB_DIR / filename}. Extrae la carpeta web completa junto a web_app.py.", 404)
        elif path == "/api/state":
            try:
                self.json_response(200, state_payload())
            except Exception as exc:
                self.error(f"No se pudo cargar el proyecto: {exc}. Revisa que libros.dat tenga registros completos de 173 bytes y que arbol_catalogo.txt sea válido.", 500)
        elif path == "/api/health":
            self.json_response(200, {"ok": True, "message": "Mundo Libro Web está activo", "project_root": str(PROJECT_ROOT or BASE_DIR), "data_dir": str(DATA_DIR)})
        else:
            self.error("Ruta no encontrada", 404)

    def do_POST(self):
        try:
            body = self.body()
            path = urlparse(self.path).path
            if path == "/api/books":
                self.add_book(body)
            elif path == "/api/loans":
                self.make_loan(body)
            elif path == "/api/returns":
                self.return_book(body)
            elif path == "/api/categories":
                self.add_category(body)
            elif path == "/api/tree/delete":
                self.delete_branch(body)
            elif path == "/api/persist/save":
                tree = load_tree(); tree.guardar(TREE_FILE)
                self.json_response(200, {"ok": True, "message": "Árbol guardado en arbol_catalogo.txt"})
            elif path == "/api/persist/reload":
                tree = Arbol.cargar(TREE_FILE); height, nodes, leaves = tree.medidas()
                self.json_response(200, {"ok": True, "message": f"Árbol reconstruido: {nodes} nodos, altura {height} y {leaves} hojas"})
            else:
                self.error("Ruta no encontrada", 404)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self.error(str(exc) or "Datos no válidos")
        except Exception as exc:
            self.error(f"Error al procesar la operación: {exc}", 500)

    def add_book(self, body: dict):
        try:
            book_id = int(body.get("id", ""))
        except (TypeError, ValueError):
            raise ValueError("El ID del libro debe ser un número entero.")
        title, author = str(body.get("title", "")).strip(), str(body.get("author", "")).strip()
        category, subcategory = str(body.get("category", "")).strip(), str(body.get("subcategory", "")).strip()
        if book_id <= 0 or not title or not author or not category or not subcategory:
            raise ValueError("Completa ID, título, autor, categoría y subcategoría.")
        if len(title.encode("utf-8")) > 50 or len(author.encode("utf-8")) > 40:
            raise ValueError("El título admite hasta 50 bytes y el autor hasta 40 bytes UTF-8.")
        archive = load_archive()
        if archive.buscar_secuencial(book_id) is not None:
            raise ValueError(f"Ya existe un libro con el ID {book_id}.")
        tree = load_tree()
        category_node = tree.buscar(category)
        if category_node is None:
            tree.insertar(tree.raiz.dato, category); category_node = tree.buscar(category)
        if category_node is None:
            raise ValueError("No se pudo crear la categoría seleccionada.")
        if not any(child.dato == subcategory for child in category_node.hijos):
            if tree.buscar(subcategory) is not None:
                raise ValueError("Ya existe una subcategoría con ese nombre en otra rama. Usa otro nombre.")
            if not tree.insertar(category, subcategory):
                raise ValueError("No fue posible crear la subcategoría seleccionada.")
        if not tree.insertar(subcategory, f"{book_id}|{title}"):
            raise ValueError("No fue posible insertar el libro en la categoría elegida.")
        archive.agregar(Libro(book_id, title, author))
        tree.guardar(TREE_FILE)
        self.json_response(200, {"ok": True, "message": f"Libro {title} agregado correctamente al catálogo."})

    def make_loan(self, body: dict):
        try:
            book_id, reader_id = int(body.get("id", "")), int(body.get("reader_id", ""))
        except (TypeError, ValueError):
            raise ValueError("El ID del libro y el del lector deben ser números.")
        reader_name = str(body.get("reader_name", "")).strip()
        loan_date = str(body.get("loan_date", date.today().isoformat())).strip()
        due_date = str(body.get("due_date", "")).strip()
        if not reader_name or reader_id <= 0 or not due_date:
            raise ValueError("Completa el ID del lector, el nombre y la fecha de devolución.")
        try:
            date.fromisoformat(loan_date); date.fromisoformat(due_date)
        except ValueError:
            raise ValueError("Las fechas deben tener formato AAAA-MM-DD.")
        if len(reader_name.encode("utf-8")) > 50:
            raise ValueError("El nombre del lector admite hasta 50 bytes UTF-8.")
        archive = load_archive(); found = archive.buscar_secuencial(book_id)
        if found is None:
            raise ValueError("No existe un libro con ese ID.")
        _, book = found
        if not book.disponible:
            raise ValueError("Ese libro ya está prestado.")
        if not archive.cambiar_estado(book_id, False, reader_id, reader_name, loan_date, due_date):
            raise ValueError("No se pudo registrar el préstamo.")
        self.json_response(200, {"ok": True, "message": f"Préstamo registrado para «{book.titulo}»."})

    def return_book(self, body: dict):
        try: book_id = int(body.get("id", ""))
        except (TypeError, ValueError): raise ValueError("Escribe un ID de libro válido.")
        archive = load_archive(); found = archive.buscar_secuencial(book_id)
        if found is None: raise ValueError("No existe un libro con ese ID.")
        _, book = found
        if book.disponible: raise ValueError("Ese libro ya figura como disponible.")
        if not archive.cambiar_estado(book_id, True): raise ValueError("No se pudo registrar la devolución.")
        self.json_response(200, {"ok": True, "message": f"Devolución registrada: «{book.titulo}»."})

    def add_category(self, body: dict):
        name = str(body.get("name", "")).strip()
        parent = str(body.get("parent", "Biblioteca Mundo Libro")).strip()
        if not name or "|" in name:
            raise ValueError("Escribe un nombre de categoría válido, sin el carácter |.")
        tree = load_tree()
        if tree.buscar(parent) is None: raise ValueError("No se encontró la categoría superior seleccionada.")
        if tree.buscar(name) is not None: raise ValueError("Ya existe un nodo con ese nombre en el catálogo.")
        if not tree.insertar(parent, name): raise ValueError("No se pudo agregar la categoría.")
        tree.guardar(TREE_FILE)
        self.json_response(200, {"ok": True, "message": f"«{name}» se agregó dentro de «{parent}»."})

    def delete_branch(self, body: dict):
        name = str(body.get("name", "")).strip()
        if not name or name == "Biblioteca Mundo Libro": raise ValueError("Selecciona un nodo que no sea la raíz.")
        tree = load_tree(); target = tree.buscar(name)
        if target is None: raise ValueError("No se encontró ese dato en el árbol.")
        remove_ids: set[str] = set()
        def collect(node):
            if "|" in node.dato: remove_ids.add(node.dato.split("|", 1)[0].strip())
            for child in node.hijos: collect(child)
        collect(target)
        if not tree.eliminar(name): raise ValueError("No se pudo eliminar el nodo seleccionado.")
        if remove_ids: write_books_without(remove_ids)
        tree.guardar(TREE_FILE)
        detail = f" y {len(remove_ids)} registro(s) de libro" if remove_ids else ""
        self.json_response(200, {"ok": True, "message": f"Se eliminó «{name}»{detail}."})

def main() -> None:
    ensure_data()
    last_error = None
    server = None
    for port in range(START_PORT, START_PORT + 11):
        try:
            server = ThreadingHTTPServer((HOST, port), Handler)
            break
        except OSError as exc:
            last_error = exc
    if server is None:
        raise RuntimeError(f"No hay puertos libres entre {START_PORT} y {START_PORT+10}. Cierra otra instancia de Mundo Libro o cambia MUNDO_LIBRO_WEB_PORT. Detalle: {last_error}")
    url = f"http://{HOST}:{server.server_port}"
    mode = "repositorio existente" if PROJECT_ROOT else "modo independiente con datos de ejemplo"
    print("\nMUNDO LIBRO WEB")
    print(f"Modo: {mode}")
    print(f"Carpeta de datos: {DATA_DIR}")
    print(f"Abre en Chrome: {url}")
    print("Deja esta ventana abierta. Para detener el servidor, presiona Ctrl+C.\n")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado. Los datos guardados permanecen en la carpeta datos/.")
    finally:
        server.server_close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nNO SE PUDO INICIAR MUNDO LIBRO WEB")
        print(f"Detalle: {exc}")
        print("Comprueba que el ZIP se haya extraído completo y que tengas Python 3.10 o superior.")
        input("Presiona Enter para cerrar esta ventana...")

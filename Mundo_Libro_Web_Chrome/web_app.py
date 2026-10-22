"""Interfaz web local para Mundo Libro.

Coloca este archivo en la raíz del repositorio Peloterius/Mundo-Libro y ejecuta:
    python web_app.py
La interfaz usa las clases originales de los cortes 1 y 2, y conserva los
archivos datos/libros.dat y datos/arbol_catalogo.txt.
"""
from __future__ import annotations

import json
import os
import tempfile
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from corte1_archivos.archivo_libros import ArchivoLibros
from corte1_archivos.registro import Libro
from corte2_arboles.arbol import Arbol
from corte2_arboles.catalogo import crear_datos_ejemplo

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("MUNDO_LIBRO_DATOS", BASE_DIR / "datos"))
BOOKS_FILE = DATA_DIR / "libros.dat"
TREE_FILE = DATA_DIR / "arbol_catalogo.txt"
WEB_DIR = BASE_DIR / "web"
HOST = "127.0.0.1"
PORT = int(os.environ.get("MUNDO_LIBRO_WEB_PORT", "8000"))


def ensure_data() -> None:
    """Prepara almacenamiento sin reemplazar datos existentes."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not BOOKS_FILE.exists() and not TREE_FILE.exists():
        crear_datos_ejemplo(str(BOOKS_FILE), str(TREE_FILE))
        return
    if not BOOKS_FILE.exists():
        ArchivoLibros(str(BOOKS_FILE))
    if not TREE_FILE.exists():
        tree = Arbol()
        archive = ArchivoLibros(str(BOOKS_FILE))
        books = [book for _, book in archive.recorrer()]
        if books:
            tree.insertar(tree.raiz.dato, "Sin clasificar")
            for book in books:
                tree.insertar("Sin clasificar", f"{book.id_libro}|{book.titulo}")
        tree.guardar(str(TREE_FILE))


def load_tree() -> Arbol:
    ensure_data()
    return Arbol.cargar(str(TREE_FILE))


def load_archive() -> ArchivoLibros:
    ensure_data()
    return ArchivoLibros(str(BOOKS_FILE))


def all_books() -> list[Libro]:
    archive = load_archive()
    return [book for _, book in archive.recorrer()]


def book_map() -> dict[str, Libro]:
    return {str(book.id_libro): book for book in all_books()}


def category_map(tree: Arbol) -> dict[str, dict[str, str]]:
    """Relaciona cada hoja ID|título con su categoría y subcategoría."""
    result: dict[str, dict[str, str]] = {}
    for category in tree.raiz.hijos:
        for subcategory in category.hijos:
            for leaf in subcategory.hijos:
                if "|" in leaf.dato:
                    book_id, _ = leaf.dato.split("|", 1)
                    result[book_id.strip()] = {
                        "category": category.dato,
                        "subcategory": subcategory.dato,
                    }
    return result


def nested_tree(node, books: dict[str, Libro] | None = None) -> dict:
    payload = {"name": node.dato, "children": [nested_tree(child, books) for child in node.hijos]}
    if "|" in node.dato:
        book_id, title = node.dato.split("|", 1)
        payload["type"] = "book"
        payload["id"] = book_id.strip()
        payload["title"] = title.strip()
        found = (books or {}).get(book_id.strip())
        if found:
            payload["author"] = found.autor
            payload["available"] = bool(found.disponible)
    elif node is not None and not node.hijos:
        payload["type"] = "leaf"
    elif node.dato == "Biblioteca Mundo Libro":
        payload["type"] = "root"
    else:
        payload["type"] = "category"
    return payload


def serialize_book(book: Libro, cats: dict[str, dict[str, str]]) -> dict:
    cat = cats.get(str(book.id_libro), {})
    return {
        "id": book.id_libro,
        "title": book.titulo,
        "author": book.autor,
        "available": bool(book.disponible),
        "reader_id": book.id_lector,
        "reader_name": book.nombre_lector,
        "loan_date": book.fecha_prestamo,
        "due_date": book.fecha_devolucion,
        "category": cat.get("category", "Sin clasificar"),
        "subcategory": cat.get("subcategory", "Sin clasificar"),
    }


def state_payload() -> dict:
    tree = load_tree()
    archive = load_archive()
    books = [book for _, book in archive.recorrer()]
    cats = category_map(tree)
    height, nodes, leaves = tree.medidas()
    categories = [node.dato for node in tree.raiz.hijos]
    all_subcategories = [child.dato for parent in tree.raiz.hijos for child in parent.hijos]
    lent = sum(not book.disponible for book in books)
    tree_lines = TREE_FILE.read_text(encoding="utf-8").splitlines() if TREE_FILE.exists() else []
    return {
        "ok": True,
        "books": [serialize_book(book, cats) for book in books],
        "tree": nested_tree(tree.raiz, {str(b.id_libro): b for b in books}),
        "stats": {
            "total_books": len(books),
            "available": len(books) - lent,
            "lent": lent,
            "categories": len(categories),
            "height": height,
            "nodes": nodes,
            "leaves": leaves,
        },
        "categories": categories,
        "subcategories": {
            node.dato: [child.dato for child in node.hijos]
            for node in tree.raiz.hijos
        },
        "files": {
            "books_name": BOOKS_FILE.name,
            "books_bytes": BOOKS_FILE.stat().st_size if BOOKS_FILE.exists() else 0,
            "tree_name": TREE_FILE.name,
            "tree_lines": len(tree_lines),
            "tree_preview": tree_lines[:16],
            "data_dir": str(DATA_DIR),
        },
    }


def write_books_without(remove_ids: set[str]) -> None:
    """Reescribe libros.dat excluyendo IDs, con archivo temporal y reemplazo."""
    archive = load_archive()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="libros_", suffix=".dat", dir=str(DATA_DIR))
    os.close(fd)
    try:
        new_archive = ArchivoLibros(temp_name)
        for _, book in archive.recorrer():
            if str(book.id_libro) not in remove_ids:
                new_archive.agregar(book)
        os.replace(temp_name, BOOKS_FILE)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)


class Handler(BaseHTTPRequestHandler):
    server_version = "MundoLibroWeb/1.0"

    def log_message(self, fmt, *args):
        print("[Mundo Libro Web] " + fmt % args)

    def _send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, data, "application/json; charset=utf-8")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _error(self, message: str, status: int = 400) -> None:
        self._json(status, {"ok": False, "error": message})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/index.html":
            file_path = WEB_DIR / "index.html"
            content_type = "text/html; charset=utf-8"
        elif path == "/styles.css":
            file_path = WEB_DIR / "styles.css"
            content_type = "text/css; charset=utf-8"
        elif path == "/app.js":
            file_path = WEB_DIR / "app.js"
            content_type = "text/javascript; charset=utf-8"
        elif path == "/api/state":
            try:
                self._json(200, state_payload())
            except Exception as exc:
                self._error(f"No se pudo cargar Mundo Libro: {exc}", 500)
            return
        elif path == "/api/health":
            self._json(200, {"ok": True, "message": "Mundo Libro Web está activo"})
            return
        else:
            self._error("Ruta no encontrada", 404)
            return
        try:
            self._send_bytes(200, file_path.read_bytes(), content_type)
        except FileNotFoundError:
            self._error(f"No se encontró el archivo de interfaz: {file_path}", 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._body()
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
                tree = load_tree()
                tree.guardar(str(TREE_FILE))
                self._json(200, {"ok": True, "message": "Árbol guardado en arbol_catalogo.txt"})
            elif path == "/api/persist/reload":
                tree = Arbol.cargar(str(TREE_FILE))
                height, nodes, leaves = tree.medidas()
                self._json(200, {"ok": True, "message": f"Árbol reconstruido: {nodes} nodos, altura {height} y {leaves} hojas"})
            else:
                self._error("Ruta no encontrada", 404)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self._error(str(exc) or "Datos no válidos")
        except Exception as exc:
            self._error(f"Ocurrió un error al procesar la operación: {exc}", 500)

    def add_book(self, body: dict):
        try:
            book_id = int(body.get("id", ""))
        except (TypeError, ValueError):
            raise ValueError("El ID del libro debe ser un número entero.")
        title = str(body.get("title", "")).strip()
        author = str(body.get("author", "")).strip()
        category = str(body.get("category", "")).strip()
        subcategory = str(body.get("subcategory", "")).strip()
        if book_id <= 0 or not title or not author or not category or not subcategory:
            raise ValueError("Completa ID, título, autor, categoría y subcategoría.")
        archive = load_archive()
        if archive.buscar_secuencial(book_id) is not None:
            raise ValueError(f"Ya existe un libro con el ID {book_id}.")
        tree = load_tree()
        category_node = tree.buscar(category)
        if category_node is None:
            tree.insertar(tree.raiz.dato, category)
            category_node = tree.buscar(category)
        if category_node is None:
            raise ValueError("No se pudo crear la categoría seleccionada.")
        subcategory_node = next((child for child in category_node.hijos if child.dato == subcategory), None)
        if subcategory_node is None:
            existing_subcategory = tree.buscar(subcategory)
            if existing_subcategory is not None:
                raise ValueError("Ya existe una subcategoría con ese nombre en otra rama. Usa un nombre diferente para evitar ambigüedades en la búsqueda recursiva.")
            if not tree.insertar(category, subcategory):
                raise ValueError("No fue posible crear la subcategoría seleccionada.")
        if not tree.insertar(subcategory, f"{book_id}|{title}"):
            raise ValueError("No fue posible insertar el libro en la categoría elegida.")
        archive.agregar(Libro(book_id, title, author))
        tree.guardar(str(TREE_FILE))
        self._json(200, {"ok": True, "message": f"Libro {title} agregado correctamente al catálogo."})

    def make_loan(self, body: dict):
        try:
            book_id = int(body.get("id", ""))
            reader_id = int(body.get("reader_id", ""))
        except (TypeError, ValueError):
            raise ValueError("El ID del libro y el del lector deben ser números.")
        reader_name = str(body.get("reader_name", "")).strip()
        loan_date = str(body.get("loan_date", date.today().isoformat())).strip()
        due_date = str(body.get("due_date", "")).strip()
        if not reader_name or reader_id <= 0 or not due_date:
            raise ValueError("Completa el ID del lector, el nombre y la fecha de devolución.")
        try:
            date.fromisoformat(loan_date)
            date.fromisoformat(due_date)
        except ValueError:
            raise ValueError("Las fechas deben tener el formato AAAA-MM-DD.")
        archive = load_archive()
        found = archive.buscar_secuencial(book_id)
        if found is None:
            raise ValueError("No existe un libro con ese ID.")
        _, book = found
        if not book.disponible:
            raise ValueError("Ese libro ya está prestado.")
        ok = archive.cambiar_estado(book_id, False, reader_id, reader_name, loan_date, due_date)
        if not ok:
            raise ValueError("No se pudo registrar el préstamo.")
        self._json(200, {"ok": True, "message": f"Préstamo registrado para «{book.titulo}»."})

    def return_book(self, body: dict):
        try:
            book_id = int(body.get("id", ""))
        except (TypeError, ValueError):
            raise ValueError("Escribe un ID de libro válido.")
        archive = load_archive()
        found = archive.buscar_secuencial(book_id)
        if found is None:
            raise ValueError("No existe un libro con ese ID.")
        _, book = found
        if book.disponible:
            raise ValueError("Ese libro ya figura como disponible.")
        if not archive.cambiar_estado(book_id, True):
            raise ValueError("No se pudo registrar la devolución.")
        self._json(200, {"ok": True, "message": f"Devolución registrada: «{book.titulo}»."})

    def add_category(self, body: dict):
        name = str(body.get("name", "")).strip()
        parent = str(body.get("parent", "Biblioteca Mundo Libro")).strip()
        if not name or "|" in name:
            raise ValueError("Escribe un nombre de categoría válido, sin el carácter |.")
        tree = load_tree()
        parent_node = tree.buscar(parent)
        if parent_node is None:
            raise ValueError("No se encontró la categoría superior seleccionada.")
        if tree.buscar(name) is not None:
            raise ValueError("Ya existe un nodo con ese nombre en el catálogo.")
        if not tree.insertar(parent, name):
            raise ValueError("No se pudo agregar la categoría.")
        tree.guardar(str(TREE_FILE))
        self._json(200, {"ok": True, "message": f"«{name}» se agregó dentro de «{parent}»."})

    def delete_branch(self, body: dict):
        name = str(body.get("name", "")).strip()
        if not name or name == "Biblioteca Mundo Libro":
            raise ValueError("Selecciona una categoría, subcategoría o libro; la raíz no se puede eliminar.")
        tree = load_tree()
        target = tree.buscar(name)
        if target is None:
            raise ValueError("No se encontró ese dato en el árbol.")
        remove_ids: set[str] = set()
        def collect(node):
            if "|" in node.dato:
                remove_ids.add(node.dato.split("|", 1)[0].strip())
            for child in node.hijos:
                collect(child)
        collect(target)
        if not tree.eliminar(name):
            raise ValueError("No se pudo eliminar el nodo seleccionado.")
        if remove_ids:
            write_books_without(remove_ids)
        tree.guardar(str(TREE_FILE))
        removed_count = len(remove_ids)
        detail = f" y {removed_count} registro(s) de libro" if removed_count else ""
        self._json(200, {"ok": True, "message": f"Se eliminó «{name}»{detail}."})


def main() -> None:
    ensure_data()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print("\nMundo Libro ya está disponible en el navegador.")
    print(f"Dirección: {url}")
    print("Para cerrar el servidor, vuelve a esta terminal y presiona Ctrl+C.\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor de Mundo Libro cerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

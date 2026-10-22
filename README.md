# Mundo Libro

Sistema de gestión para la Biblioteca Comunitaria Mundo Libro.
Proyecto de Estructuras de Datos II · Fundación Universitaria Compensar · Ingeniería de Software.

- **Corte 1 (archivos):** registros de longitud fija (173 bytes), acceso secuencial y directo, ordenación externa por búsqueda y mezcla directa.
- **Corte 2 (árboles):** árbol genérico que clasifica el catálogo (biblioteca → categoría → subcategoría → libro), con inserción, recorridos en preorden y posorden, búsqueda, altura y conteo, eliminación y persistencia en `arbol_catalogo.txt`.

Ambas partes trabajan integradas: cada hoja del árbol guarda el ID de su libro, y ese ID enlaza con el registro de `libros.dat` (autor, estado y préstamo).

## Cómo ejecutarlo

Requiere Python 3.10 o superior. No tiene dependencias externas.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

En la primera ejecución se crean datos de ejemplo en `datos/` (9 libros y el árbol del catálogo).
Para ver bien los cuadros y colores usa una terminal de al menos 80 columnas (Windows Terminal, VS Code o la terminal de Codespaces).

| Opción de arranque | Efecto |
|---|---|
| `python main.py --simple` | Texto plano, sin color ni limpieza de pantalla (útil para capturas o para redirigir la salida). |
| `python main.py --ayuda` | Muestra la ayuda. |

## Navegación

Todos los menús se manejan escribiendo el número de la opción; `0` vuelve o sale. Una respuesta vacía cancela la operación en curso sin modificar nada. El encabezado muestra siempre dónde estás y el estado del sistema (libros, préstamos, nodos, altura y si el árbol está guardado).

```
Inicio
├─ 1  Catálogo en árbol
│    1 Ver catálogo completo (preorden)      6 Eliminar categoría o libro
│    2 Ver los libros de una categoría       7 Medidas del árbol
│    3 Buscar un dato                        8 Ver recorrido en posorden
│    4 Agregar categoría o subcategoría      9 Guardar el árbol en el archivo
│    5 Agregar libro al catálogo            10 Reconstruir el árbol desde el archivo
├─ 2  Libros y préstamos
│    1 Listar los libros                     6 Devolver un libro
│    2 Consultar por n.º de registro         7 Préstamos activos y atrasados
│    3 Buscar un libro por ID                8 Editar título o autor
│    4 Registrar un libro nuevo              9 Ordenar por ID: búsqueda externa
│    5 Prestar un libro                     10 Ordenar por ID: mezcla directa
└─ 3  Explicaciones en pantalla (activar o desactivar)
```

Con las explicaciones activadas, cada operación termina con un cuadro **«Qué pasó en el árbol»** (o **«en el archivo»**) que describe el caso base, el caso recursivo y el cambio en la estructura. Así se puede explicar en vivo lo que ocurre mientras se ejecuta.

El árbol cambia en memoria y se guarda en `arbol_catalogo.txt` al elegir «Guardar el árbol en el archivo» o al salir. El encabezado indica «sin guardar» mientras haya cambios pendientes.

## Estructura

```
mundo-libro/
├── main.py                 # punto de entrada
├── requirements.txt        # sin dependencias externas
├── corte1_archivos/        # registro.py, archivo_libros.py, ordenacion.py
├── corte2_arboles/         # nodo.py, arbol.py, catalogo.py
├── interfaz/               # estilo.py (cuadros, color, tablas) y menus.py (pantallas)
├── pruebas/                # pruebas unitarias y de flujo de ambos cortes
└── datos/                  # libros.dat y arbol_catalogo.txt (se generan al iniciar)
```

La lógica de los cortes vive en `corte1_archivos/` y `corte2_arboles/`; `interfaz/` solo se ocupa de la presentación.

## Pruebas

```bash
python -m unittest discover -s pruebas -t . -v
```

## Formato de los archivos

- `libros.dat`: registros binarios de 173 bytes: ID libro (4), título (50), autor (40), estado (1), ID lector (4), nombre lector (50), fecha de préstamo (12), fecha de devolución (12).
- `arbol_catalogo.txt`: una línea `nivel|dato` por nodo, en preorden. En las hojas el dato es `ID|título`, y el ID enlaza con el registro de `libros.dat`.

Los archivos de `datos/` se generan al ejecutar y no se versionan (ver `.gitignore`).

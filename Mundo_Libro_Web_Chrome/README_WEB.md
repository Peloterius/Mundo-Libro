# Mundo Libro — Interfaz web local

Esta carpeta agrega una interfaz web para Chrome/Edge al proyecto de consola existente. Usa las clases originales `ArchivoLibros`, `Libro` y `Arbol`, así que trabaja con los mismos archivos `datos/libros.dat` y `datos/arbol_catalogo.txt`.

## Instalar en tu repositorio

1. Descarga y descomprime `Mundo_Libro_Web_UI.zip`.
2. Copia `web_app.py` en la raíz del repositorio `Mundo-Libro`, al lado de `main.py`.
3. Copia la carpeta `web` completa en la raíz, al mismo nivel que `main.py`.
4. Abre la carpeta del proyecto con Visual Studio Code.
5. Abre la terminal integrada y ejecuta:

   ```bash
   python web_app.py
   ```

6. Se abrirá `http://127.0.0.1:8000` en el navegador. Si no se abre, copia esa dirección en Chrome.
7. Para detener el servidor, ve a la terminal y pulsa `Ctrl+C`.

## Qué incluye

- Panel inicial con resumen de libros y préstamos.
- Catálogo con búsqueda y filtros.
- Registro de libros.
- Registro de préstamos y devoluciones.
- Visualización del árbol genérico, categorías y subcategorías.
- Altura, nodos y hojas calculados con la clase `Arbol` existente.
- Guardado y reconstrucción del árbol desde `arbol_catalogo.txt`.
- Eliminación de categoría/libro con confirmación y actualización coordinada de los archivos.

## Notas

- Requiere Python 3.10 o superior, igual que el proyecto, y no añade dependencias externas.
- El servidor solo escucha en `127.0.0.1` (tu computador); no publica la biblioteca en Internet.
- La interfaz web usa los archivos en la carpeta `datos` del proyecto. No borres esa carpeta si contiene tus datos reales.
- La interfaz de navegador es un complemento nuevo; `python main.py` sigue abriendo la interfaz de terminal original.
- Los mockups del video son una propuesta visual; esta interfaz contiene interacciones funcionales conectadas al modelo original, pero no pretende sustituir las validaciones docentes ni la revisión del código.

# Mundo Libro Web — paquete corregido

## Forma recomendada
1. Descarga y extrae este ZIP.
2. Copia `web_app.py`, `Abrir_Mundo_Libro_Web.bat` y la carpeta `web` a la raíz de tu repositorio `Mundo-Libro` (la carpeta donde está `main.py`). Si Windows pregunta si quieres reemplazar archivos, no reemplaces `main.py` ni ningún archivo original; estos archivos son nuevos.
3. Haz doble clic en `Abrir_Mundo_Libro_Web.bat`.
4. Deja abierta la consola. El navegador debería abrirse en una dirección `http://127.0.0.1:8000` (si ese puerto está ocupado, el programa intentará del 8001 al 8010). También verás la dirección exacta en consola.

Puedes extraer y ejecutar el ZIP en una carpeta independiente para probarlo con 9 libros de ejemplo; en ese modo no modificará la carpeta datos/ del repositorio original. Para integrar la interfaz con tus registros actuales, copia los tres elementos a la raíz del repositorio original tal como se indica arriba.

## Si no abre
- Asegúrate de tener Python 3.10 o superior (`py -3 --version` en una terminal).
- No cierres la consola después de que abra Chrome: esa ventana mantiene activo el servidor.
- Copia la dirección exacta que se imprime en la consola; puede ser 8000, 8001, etc.
- Si aparece un mensaje de error, copia el texto completo. No borres `datos/libros.dat` ni `datos/arbol_catalogo.txt`.

## Compatibilidad
El backend usa el formato binario original `libros.dat` (registros de 173 bytes) y el formato de árbol `nivel|dato` de `arbol_catalogo.txt`, sin instalar dependencias externas. Si se coloca dentro de la raíz del repositorio, busca la carpeta de datos de ese proyecto. El ZIP por sí solo también puede ejecutarse con datos de demostración.

Las operaciones de préstamo, devolución, catálogo y árbol escriben en esos archivos cuando la aplicación está integrada con el repositorio. Antes de probarla con datos importantes, guarda una copia de `datos/`.

"""Estilo de la consola de Mundo Libro.

Reúne color, cajas, tablas y lectura segura de datos. No contiene lógica del
catálogo: solo presentación. Si la terminal no admite color o Unicode, se usan
alternativas simples (ASCII y sin color).
"""
import os
import re
import shutil
import sys
import textwrap

_ANSI = re.compile(r"\x1b\[[0-9;]*m")

ESTILOS = {
    "negrita": "1",
    "marca": "38;5;37",     # verde azulado: títulos y categorías
    "acento": "38;5;214",   # ámbar: números, IDs y raíz
    "suave": "38;5;110",    # azul suave: subcategorías
    "ok": "38;5;78",
    "error": "38;5;203",
    "aviso": "38;5;221",
    "tenue": "38;5;244",
}

_UNI = {
    "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│",
    "rama": "├─ ", "fin": "└─ ", "tronco": "│  ", "vacio": "   ",
    "ok": "✔", "error": "✖", "aviso": "▲", "info": "•",
    "lleno": "●", "hueco": "○", "barra": "█", "flecha": "›", "punto": "·",
    "elipsis": "…",
}
_ASC = {
    "tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|",
    "rama": "|- ", "fin": "`- ", "tronco": "|  ", "vacio": "   ",
    "ok": "[ok]", "error": "[x]", "aviso": "[!]", "info": "-",
    "lleno": "*", "hueco": "o", "barra": "#", "flecha": ">", "punto": "-",
    "elipsis": "~",
}


class _Config:
    color = False
    interactivo = False     # limpia pantalla, pausa y pagina
    unicode = True
    explicar = True         # muestra «qué pasó en la estructura»
    ancho = 80


CONFIG = _Config()


class Cancelado(Exception):
    """El usuario dejó una respuesta vacía para cancelar la operación."""


def g(nombre: str) -> str:
    return (_UNI if CONFIG.unicode else _ASC)[nombre]


def iniciar(simple: bool = False) -> None:
    """Detecta las capacidades de la terminal. `simple` fuerza texto plano."""
    for flujo in (sys.stdout, sys.stdin):
        try:
            utf8 = (flujo.encoding or "").lower().replace("-", "") == "utf8"
            if not utf8 and not flujo.isatty():
                flujo.reconfigure(encoding="utf-8", errors="replace")
            else:
                flujo.reconfigure(errors="replace")   # nunca falla por un carácter raro
        except Exception:
            pass
    tty = sys.stdout.isatty() and sys.stdin.isatty()
    if os.name == "nt":
        os.system("")  # activa las secuencias ANSI en la consola de Windows
        if (sys.stdout.encoding or "").lower().replace("-", "") != "utf8" and sys.stdout.isatty():
            os.system("chcp 65001 >nul")   # consola antigua: pasa a UTF-8 para ver tildes y ñ
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    CONFIG.color = (not simple and sys.stdout.isatty()
                    and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb")
    CONFIG.interactivo = not simple and tty
    codificacion = (sys.stdout.encoding or "").lower().replace("-", "").replace("_", "")
    CONFIG.unicode = codificacion == "utf8" and not simple
    actualizar_ancho()


def actualizar_ancho() -> None:
    columnas = shutil.get_terminal_size((80, 24)).columns
    CONFIG.ancho = min(max(columnas - 2, 60), 90)


# ---------------------------------------------------------------- texto
def c(texto, *estilos) -> str:
    texto = str(texto)
    if not CONFIG.color or not estilos:
        return texto
    return f"\x1b[{';'.join(ESTILOS[s] for s in estilos)}m{texto}\x1b[0m"


def largo(texto: str) -> int:
    return len(_ANSI.sub("", texto))


def recortar(texto: str, n: int) -> str:
    """Recorta a `n` caracteres visibles conservando las secuencias de color."""
    if largo(texto) <= n:
        return texto
    salida, visibles = [], 0
    limite = max(n - 1, 0)
    for trozo in re.split(r"(\x1b\[[0-9;]*m)", texto):
        if _ANSI.fullmatch(trozo):
            salida.append(trozo)
            continue
        cabe = limite - visibles
        if cabe <= 0:
            break
        salida.append(trozo[:cabe])
        visibles += min(len(trozo), cabe)
        if len(trozo) > cabe:
            break
    fin = "\x1b[0m" if CONFIG.color else ""
    return "".join(salida) + fin + g("elipsis")


def parrafo(texto: str, ancho: int = None) -> list:
    ancho = ancho or CONFIG.ancho - 4
    return textwrap.wrap(texto, ancho) or [""]


# ---------------------------------------------------------------- cajas
def armar_caja(lineas, titulo: str = "", borde: str = "tenue", ancho: int = None) -> str:
    ancho = ancho or CONFIG.ancho
    cuerpo = ancho - 4
    h = g("h")
    if titulo:
        titulo = recortar(titulo, ancho - 8)
        resto = ancho - len(titulo) - 5
        sup = (c(g("tl") + h, borde) + c(f" {titulo} ", "negrita", "marca")
               + c(h * resto + g("tr"), borde))
    else:
        sup = c(g("tl") + h * (ancho - 2) + g("tr"), borde)
    inf = c(g("bl") + h * (ancho - 2) + g("br"), borde)
    v = c(g("v"), borde)
    filas = [sup]
    for linea in lineas:
        linea = recortar(linea, cuerpo)
        filas.append(f"{v} {linea}{' ' * (cuerpo - largo(linea))} {v}")
    filas.append(inf)
    return "\n".join(filas)


def caja(lineas, titulo: str = "", borde: str = "tenue") -> None:
    print(armar_caja(lineas, titulo, borde))


def caja_paginada(lineas, titulo: str, por_pagina: int = 16) -> None:
    """Imprime una caja; en modo interactivo la divide en páginas."""
    if not CONFIG.interactivo or len(lineas) <= por_pagina:
        caja(lineas, titulo)
        return
    paginas = [lineas[i:i + por_pagina] for i in range(0, len(lineas), por_pagina)]
    for i, pagina in enumerate(paginas, 1):
        caja(pagina, f"{titulo} ({i}/{len(paginas)})")
        if i < len(paginas):
            if pedir_crudo("Enter para ver más, 0 para terminar") == "0":
                return


def ficha(pares, titulo: str = "") -> None:
    """Caja con pares «etiqueta  valor» alineados."""
    ancho_et = max(len(p[0]) for p in pares)
    sitio = CONFIG.ancho - 4 - ancho_et - 2
    lineas = []
    for et, val in pares:
        trozos = parrafo(val, sitio) if "\x1b" not in val and len(val) > sitio else [val]
        for i, trozo in enumerate(trozos):
            lineas.append(f"{c(et.ljust(ancho_et), 'tenue') if i == 0 else ' ' * ancho_et}  {trozo}")
    caja(lineas, titulo)


def nota(titulo: str, *parrafos) -> None:
    """Explicación de lo ocurrido en la estructura (se puede desactivar)."""
    if not CONFIG.explicar:
        return
    lineas = []
    for i, p in enumerate(parrafos):
        if i:
            lineas.append("")
        lineas.extend(parrafo(p))
    caja(lineas, titulo, borde="marca")


def tabla(columnas, filas) -> list:
    """columnas: [(título, ancho_máximo)]. Devuelve las líneas de la tabla."""
    anchos = []
    for i, (titulo, maximo) in enumerate(columnas):
        mayor = max([len(titulo)] + [largo(f[i]) for f in filas])
        anchos.append(min(mayor, maximo))
    union = "  "
    disponible = CONFIG.ancho - 4
    while sum(anchos) + len(union) * (len(anchos) - 1) > disponible:
        ancha = max(range(len(anchos)), key=lambda k: anchos[k])
        if anchos[ancha] <= 8:
            break
        anchos[ancha] -= 1

    def fila(celdas, estilo=None):
        partes = []
        for celda, ancho in zip(celdas, anchos):
            celda = recortar(celda, ancho)
            partes.append(celda + " " * (ancho - largo(celda)))
        texto = union.join(partes).rstrip()
        return c(texto, estilo) if estilo else texto

    lineas = [fila([t for t, _ in columnas], "tenue")]
    lineas.append(c(g("h") * min(sum(anchos) + len(union) * (len(anchos) - 1), disponible), "tenue"))
    lineas.extend(fila(f) for f in filas)
    return lineas


# ---------------------------------------------------------------- mensajes
def ok(texto: str) -> None:
    print(f"  {c(g('ok'), 'ok')} {texto}")


def error(texto: str) -> None:
    print(f"  {c(g('error'), 'error')} {texto}")


def aviso(texto: str) -> None:
    print(f"  {c(g('aviso'), 'aviso')} {texto}")


def info(texto: str) -> None:
    print(f"  {c(g('info'), 'marca')} {texto}")


def limpiar() -> None:
    if CONFIG.interactivo:
        print("\x1b[2J\x1b[H", end="")


def pausa() -> None:
    if CONFIG.interactivo:
        print()
        pedir_crudo("Enter para volver al menú")


# ---------------------------------------------------------------- entrada
def pedir_crudo(etiqueta: str) -> str:
    print(f"\n  {c(etiqueta, 'acento')} {c(g('flecha'), 'acento')} ", end="", flush=True)
    return input().strip()


def menu(opciones, salida: str = "Volver") -> int:
    """Muestra opciones numeradas y devuelve la elegida (0 = salida)."""
    ancho_num = len(str(len(opciones)))
    ancho_texto = max(len(t) for t, _ in opciones)
    lineas = []
    for i, (texto, detalle) in enumerate(opciones, 1):
        fila = f"{c(str(i).rjust(ancho_num), 'negrita', 'acento')}  {texto.ljust(ancho_texto)}"
        if detalle:
            fila += f"   {c(detalle, 'tenue')}"
        lineas.append(fila)
    lineas.append(f"{c('0'.rjust(ancho_num), 'negrita', 'acento')}  {c(salida, 'tenue')}")
    caja(lineas)
    while True:
        respuesta = pedir_crudo("Elige una opción")
        if respuesta.isdigit() and int(respuesta) <= len(opciones):
            return int(respuesta)
        error(f"Escribe un número entre 0 y {len(opciones)}.")


def pedir(etiqueta: str) -> str:
    """Pide un texto; la respuesta vacía cancela la operación."""
    respuesta = pedir_crudo(etiqueta)
    if not respuesta:
        raise Cancelado()
    return respuesta


def pedir_entero(etiqueta: str, minimo: int = 1, maximo: int = 2_147_483_647) -> int:
    while True:
        respuesta = pedir(etiqueta)
        try:
            valor = int(respuesta)
        except ValueError:
            error("Debe ser un número entero.")
            continue
        if valor < minimo or valor > maximo:
            error(f"Debe estar entre {minimo} y {maximo}.")
            continue
        return valor


def pedir_texto(etiqueta: str, max_bytes: int = None, defecto: str = None, validar=None) -> str:
    """Pide texto no vacío. Con `defecto`, Enter lo conserva en lugar de cancelar."""
    while True:
        if defecto is not None:
            respuesta = pedir_crudo(f"{etiqueta} (Enter conserva «{defecto}»)") or defecto
        else:
            respuesta = pedir(etiqueta)
        if max_bytes and len(respuesta.encode("utf-8")) > max_bytes:
            error(f"Cabe en {max_bytes} bytes (los acentos ocupan 2) y el texto ocupa "
                  f"{len(respuesta.encode('utf-8'))}. Acórtalo.")
            continue
        problema = validar(respuesta) if validar else None
        if problema:
            error(problema)
            continue
        return respuesta


def confirmar(pregunta: str) -> bool:
    return pedir_crudo(f"{pregunta} (s/n)").lower() in ("s", "si", "sí")

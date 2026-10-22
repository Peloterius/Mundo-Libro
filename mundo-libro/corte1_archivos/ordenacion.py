"""Ordenación externa del archivo de libros por ID (Corte 1)."""
import os
from .registro import TAMANO, Libro


def _leer(f):
    datos = f.read(TAMANO)
    return Libro.desde_bytes(datos) if len(datos) == TAMANO else None


def ordenar_por_busqueda(entrada: str, salida: str) -> None:
    """Ordenación externa por búsqueda: en cada pasada se recorre el archivo de
    entrada para hallar el registro de menor ID aún no copiado y se escribe en
    el archivo de salida. Solo se guarda en memoria el conjunto de posiciones
    ya copiadas, nunca los registros."""
    total = os.path.getsize(entrada) // TAMANO
    copiados = set()
    with open(entrada, "rb") as fin, open(salida, "wb") as fout:
        while len(copiados) < total:
            fin.seek(0)
            menor_pos, menor_id = None, None
            for pos in range(total):
                libro = _leer(fin)
                if pos in copiados:
                    continue
                if menor_id is None or libro.id_libro < menor_id:
                    menor_pos, menor_id = pos, libro.id_libro
            fin.seek(menor_pos * TAMANO)
            fout.write(fin.read(TAMANO))
            copiados.add(menor_pos)


def ordenar_mezcla_directa(ruta: str) -> int:
    """Mezcla directa con dos archivos auxiliares (F1 y F2). Devuelve el número
    de pasadas realizadas. El archivo `ruta` queda ordenado por ID."""
    f1, f2 = ruta + ".f1", ruta + ".f2"
    total = os.path.getsize(ruta) // TAMANO
    n, pasadas = 1, 0
    while n < total:
        # Distribución: bloques de n registros alternados entre F1 y F2
        with open(ruta, "rb") as src, open(f1, "wb") as a, open(f2, "wb") as b:
            destino, leidos = a, 0
            for _ in range(total):
                destino.write(src.read(TAMANO))
                leidos += 1
                if leidos == n:
                    destino, leidos = (b if destino is a else a), 0
        # Mezcla: se combina un bloque de F1 con uno de F2 en orden de ID
        with open(f1, "rb") as a, open(f2, "rb") as b, open(ruta, "wb") as out:
            na = os.path.getsize(f1) // TAMANO
            nb = os.path.getsize(f2) // TAMANO
            ra, rb = 0, 0                      # registros ya consumidos de cada archivo
            while ra < na or rb < nb:
                ia, ib = 0, 0                  # consumidos del bloque actual
                la = min(n, na - ra)
                lb = min(n, nb - rb)
                x = _leer(a) if la else None
                y = _leer(b) if lb else None
                while ia < la or ib < lb:
                    if ib >= lb or (ia < la and x.id_libro <= y.id_libro):
                        out.write(x.a_bytes()); ia += 1
                        x = _leer(a) if ia < la else None
                    else:
                        out.write(y.a_bytes()); ib += 1
                        y = _leer(b) if ib < lb else None
                ra += la
                rb += lb
                # x/y pueden haber leído un registro adelantado: reposicionar
                a.seek(ra * TAMANO)
                b.seek(rb * TAMANO)
        n *= 2
        pasadas += 1
    for aux in (f1, f2):
        if os.path.exists(aux):
            os.remove(aux)
    return pasadas

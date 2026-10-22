"""Árbol genérico con operaciones recursivas y persistencia en texto (Corte 2)."""
from .nodo import Nodo


class Arbol:
    def __init__(self, dato_raiz: str = "Biblioteca Mundo Libro"):
        self.raiz = Nodo(dato_raiz)

    # ---- inserción ----
    def insertar(self, padre: str, dato: str) -> bool:
        """Agrega `dato` como hijo del nodo `padre`. False si el padre no existe."""
        return self._insertar(self.raiz, padre, dato)

    def _insertar(self, nodo: Nodo, padre: str, dato: str) -> bool:
        if nodo.coincide(padre):                  # caso base
            nodo.hijos.append(Nodo(dato))
            return True
        for hijo in nodo.hijos:                   # caso recursivo
            if self._insertar(hijo, padre, dato):
                return True
        return False

    # ---- recorridos ----
    def preorden(self):
        """Lista de (nivel, dato): primero el nodo y luego sus hijos."""
        salida = []
        self._preorden(self.raiz, 0, salida)
        return salida

    def _preorden(self, nodo, nivel, salida):
        if nodo is None:                          # caso base
            return
        salida.append((nivel, nodo.dato))         # visitar
        for hijo in nodo.hijos:                   # caso recursivo
            self._preorden(hijo, nivel + 1, salida)

    def posorden(self):
        """Lista de datos: primero los hijos y al final el nodo."""
        salida = []
        self._posorden(self.raiz, salida)
        return salida

    def _posorden(self, nodo, salida):
        if nodo is None:
            return
        for hijo in nodo.hijos:
            self._posorden(hijo, salida)
        salida.append(nodo.dato)

    # ---- búsqueda ----
    def buscar(self, dato: str):
        return self._buscar(self.raiz, dato)

    def _buscar(self, nodo, dato):
        if nodo is None:                          # caso base 1
            return None
        if nodo.coincide(dato):                   # caso base 2
            return nodo
        for hijo in nodo.hijos:                   # caso recursivo
            r = self._buscar(hijo, dato)
            if r is not None:
                return r
        return None

    def buscar_con_traza(self, dato: str):
        """Como `buscar`, pero devuelve (nodo, camino, visitados): el camino de datos
        desde la raíz hasta el nodo y cuántos nodos se visitaron. Si no existe,
        devuelve (None, [], total de nodos visitados)."""
        camino, visitados = [], [0]

        def rec(nodo):
            visitados[0] += 1
            camino.append(nodo.dato)
            if nodo.coincide(dato):               # caso base
                return nodo
            for hijo in nodo.hijos:               # caso recursivo
                r = rec(hijo)
                if r is not None:
                    return r
            camino.pop()
            return None

        nodo = rec(self.raiz)
        return nodo, (list(camino) if nodo else []), visitados[0]

    # ---- altura, nodos y hojas ----
    def medidas(self):
        """(altura, nodos, hojas). Árbol de un solo nodo: altura 0."""
        return self._medidas(self.raiz)

    def _medidas(self, nodo):
        if nodo is None:                          # caso base
            return (-1, 0, 0)
        if nodo.es_hoja():
            return (0, 1, 1)
        altura, nodos, hojas = 0, 1, 0
        for hijo in nodo.hijos:                   # caso recursivo
            a, n, h = self._medidas(hijo)
            altura = max(altura, a + 1)
            nodos += n
            hojas += h
        return (altura, nodos, hojas)

    # ---- eliminación ----
    def eliminar(self, dato: str) -> bool:
        """Elimina el nodo y toda su descendencia. La raíz no se puede eliminar."""
        return self._eliminar(self.raiz, dato)

    def _eliminar(self, nodo, dato):
        for hijo in nodo.hijos:
            if hijo.coincide(dato):               # caso base: se quita el subárbol
                nodo.hijos.remove(hijo)
                return True
        for hijo in nodo.hijos:                   # caso recursivo
            if self._eliminar(hijo, dato):
                return True
        return False

    def contar_hojas_de(self, dato: str) -> int:
        nodo = self.buscar(dato)
        return 0 if nodo is None else self._medidas(nodo)[2]

    # ---- persistencia ----
    def guardar(self, ruta: str) -> None:
        """Escribe una línea «nivel|dato» por nodo, en preorden."""
        with open(ruta, "w", encoding="utf-8") as f:
            for nivel, dato in self.preorden():
                f.write(f"{nivel}|{dato}\n")

    @staticmethod
    def cargar(ruta: str) -> "Arbol":
        """Reconstruye el árbol con una pila: el padre de una línea es el último
        nodo leído cuyo nivel es una unidad menor."""
        arbol, pila = None, []                    # pila de (nivel, nodo)
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                linea = linea.rstrip("\n")
                if not linea:
                    continue
                nivel_txt, dato = linea.split("|", 1)
                nivel = int(nivel_txt)
                if nivel == 0:
                    arbol = Arbol(dato)
                    pila = [(0, arbol.raiz)]
                    continue
                while pila and pila[-1][0] >= nivel:
                    pila.pop()
                if not pila:
                    raise ValueError(f"Línea sin padre: {linea}")
                nodo = Nodo(dato)
                pila[-1][1].hijos.append(nodo)
                pila.append((nivel, nodo))
        if arbol is None:
            raise ValueError("El archivo no contiene una raíz (nivel 0)")
        return arbol

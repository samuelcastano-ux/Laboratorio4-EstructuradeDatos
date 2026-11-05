"""
QuadTree 2D 

Cada nodo es un rectángulo (x0, y0, x1, y1). Si tiene más puntos que la
capacidad
Los hijos se guardan en este orden: [NO, NE, SO, SE].
"""
import heapq
import math


def distancia2(x1, y1, x2, y2):
    """Distancia al cuadrado entre dos puntos. Sin raíz, porque basta para comparar."""
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


def distancia2_rectangulo(x, y, nodo):
    """Distancia al cuadrado desde (x, y) hasta el rectángulo del nodo. Vale 0 si está dentro."""
    dx = 0
    if x < nodo.x0:
        dx = nodo.x0 - x
    elif x > nodo.x1:
        dx = x - nodo.x1

    dy = 0
    if y < nodo.y0:
        dy = nodo.y0 - y
    elif y > nodo.y1:
        dy = y - nodo.y1

    return dx * dx + dy * dy


class Nodo:
    def __init__(self, x0, y0, x1, y1, profundidad):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.profundidad = profundidad
        self.puntos = []    # solo se usa en las hojas
        self.hijos = None   # None significa que es hoja


class QuadTree:
    def __init__(self, x0, y0, x1, y1, capacidad=8, prof_max=20):
        if x0 >= x1 or y0 >= y1:
            raise ValueError("El rectángulo debe cumplir x0 < x1 e y0 < y1")
        self.raiz = Nodo(x0, y0, x1, y1, 0)
        self.capacidad = capacidad
        self.prof_max = prof_max  # evita dividir sin fin si hay puntos repetidos
        self.n = 0

    def __len__(self):
        return self.n

    def _cuadrante(self, nodo, x, y):
        """Índice del hijo que le toca al punto: 0=NO, 1=NE, 2=SO, 3=SE."""
        mitad_x = (nodo.x0 + nodo.x1) / 2
        mitad_y = (nodo.y0 + nodo.y1) / 2
        if y >= mitad_y:
            if x >= mitad_x:
                return 1
            return 0
        if x >= mitad_x:
            return 3
        return 2

    def _dividir(self, nodo):
        mitad_x = (nodo.x0 + nodo.x1) / 2
        mitad_y = (nodo.y0 + nodo.y1) / 2
        p = nodo.profundidad + 1
        nodo.hijos = [
            Nodo(nodo.x0, mitad_y, mitad_x, nodo.y1, p),   # NO
            Nodo(mitad_x, mitad_y, nodo.x1, nodo.y1, p),   # NE
            Nodo(nodo.x0, nodo.y0, mitad_x, mitad_y, p),   # SO
            Nodo(mitad_x, nodo.y0, nodo.x1, mitad_y, p),   # SE
        ]
        # pasar los puntos de la hoja a sus hijos
        for x, y in nodo.puntos:
            hijo = nodo.hijos[self._cuadrante(nodo, x, y)]
            hijo.puntos.append((x, y))
        nodo.puntos = []

        for hijo in nodo.hijos:
            if len(hijo.puntos) > self.capacidad and hijo.profundidad < self.prof_max:
                self._dividir(hijo)

    def insertar(self, punto):
        x, y = punto
        raiz = self.raiz
        if not (raiz.x0 <= x <= raiz.x1 and raiz.y0 <= y <= raiz.y1):
            raise ValueError("El punto %s está fuera del área del árbol" % (punto,))

        nodo = self.raiz
        while nodo.hijos is not None:        # bajar hasta la hoja que corresponde
            nodo = nodo.hijos[self._cuadrante(nodo, x, y)]

        nodo.puntos.append((x, y))
        self.n += 1
        if len(nodo.puntos) > self.capacidad and nodo.profundidad < self.prof_max:
            self._dividir(nodo)

    def hojas(self):
        """Lista de hojas del árbol. Sirve para dibujar las celdas."""
        resultado = []
        self._recoger_hojas(self.raiz, resultado)
        return resultado

    def _recoger_hojas(self, nodo, resultado):
        if nodo.hijos is None:
            resultado.append(nodo)
        else:
            for hijo in nodo.hijos:
                self._recoger_hojas(hijo, resultado)

    def rango(self, centro, radio):
        """Puntos a distancia menor o igual que radio (en metros) del centro."""
        if radio < 0:
            raise ValueError("El radio no puede ser negativo")
        cx, cy = centro
        encontrados = []
        self._rango(self.raiz, cx, cy, radio * radio, encontrados)
        return encontrados

    def _rango(self, nodo, cx, cy, radio2, encontrados):
        # si el rectángulo del nodo no toca el círculo, nos saltamos todo lo que hay dentro
        if distancia2_rectangulo(cx, cy, nodo) > radio2:
            return
        if nodo.hijos is None:
            for x, y in nodo.puntos:
                if distancia2(x, y, cx, cy) <= radio2:
                    encontrados.append((x, y))
        else:
            for hijo in nodo.hijos:
                self._rango(hijo, cx, cy, radio2, encontrados)

    def vecinos(self, consulta, k=1):
        """Los k puntos más cercanos, como lista de (distancia_en_metros, punto)."""
        if k < 1:
            raise ValueError("k debe ser >= 1")
        cx, cy = consulta
        mejores = []   # lista ordenada de (distancia2, punto), de menor a mayor
        self._vecinos(self.raiz, cx, cy, k, mejores)
        return [(math.sqrt(d2), p) for d2, p in mejores]

    def _vecinos(self, nodo, cx, cy, k, mejores):
        # si ya tenemos k puntos y este rectángulo está más lejos que el peor de ellos, saltar
        if len(mejores) == k and distancia2_rectangulo(cx, cy, nodo) > mejores[-1][0]:
            return
        if nodo.hijos is None:
            for x, y in nodo.puntos:
                mejores.append((distancia2(x, y, cx, cy), (x, y)))
            mejores.sort()
            del mejores[k:]
        else:
            # visitar primero los hijos más cercanos, así se poda más
            hijos = sorted(nodo.hijos, key=lambda h: distancia2_rectangulo(cx, cy, h))
            for hijo in hijos:
                self._vecinos(hijo, cx, cy, k, mejores)


# ---------------- fuerza bruta (para comparar) ----------------

def rango_fuerza_bruta(puntos, centro, radio):
    cx, cy = centro
    radio2 = radio * radio
    return [(x, y) for x, y in puntos if distancia2(x, y, cx, cy) <= radio2]


def vecinos_fuerza_bruta(puntos, consulta, k=1):
    cx, cy = consulta
    todos = ((distancia2(x, y, cx, cy), (x, y)) for x, y in puntos)
    mejores = heapq.nsmallest(k, todos)
    return [(math.sqrt(d2), p) for d2, p in mejores]
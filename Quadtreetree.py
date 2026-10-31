"""QuadTree 2D para coordenadas cartesianas en metros."""
import heapq
import itertools
import math


def _punto(p):
    if len(p) != 2:
        raise ValueError("Cada punto debe tener dos coordenadas (x, y)")
    x, y = float(p[0]), float(p[1])
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Las coordenadas deben ser finitas")
    return x, y


def _caja(caja):
    if len(caja) == 4:
        x0, y0, x1, y1 = map(float, caja)
    elif len(caja) == 2:
        (x0, x1), (y0, y1) = caja
        x0, x1, y0, y1 = float(x0), float(x1), float(y0), float(y1)
    else:
        raise ValueError("La caja debe ser (x0, y0, x1, y1)")
    if not all(map(math.isfinite, (x0, y0, x1, y1))) or x0 >= x1 or y0 >= y1:
        raise ValueError("La caja debe tener limites finitos y min < max")
    return x0, y0, x1, y1


def distancia2(p, q):
    """Distancia euclidiana al cuadrado entre dos puntos 2D."""
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return dx * dx + dy * dy


def _distancia2_caja(p, caja):
    x0, y0, x1, y1 = caja
    dx = max(x0 - p[0], 0, p[0] - x1)
    dy = max(y0 - p[1], 0, p[1] - y1)
    return dx * dx + dy * dy


class _Nodo:
    def __init__(self, caja, profundidad=0):
        self.caja = caja
        self.profundidad = profundidad
        self.puntos = []
        self.hijos = None

    @property
    def limites(self):
        x0, y0, x1, y1 = self.caja
        return (x0, x1), (y0, y1)


class QuadTree:
    def __init__(self, caja, capacidad=8, prof_max=20):
        self.caja = _caja(caja)
        if capacidad < 1 or prof_max < 0:
            raise ValueError("capacidad debe ser positiva y prof_max no negativo")
        self.capacidad = capacidad
        self.prof_max = prof_max
        self.raiz = _Nodo(self.caja)
        self._n = 0

    def __len__(self):
        return self._n

    @staticmethod
    def _cuadrante(nodo, punto):
        x0, y0, x1, y1 = nodo.caja
        mitad_x = (x0 + x1) / 2
        mitad_y = (y0 + y1) / 2
        return (1 if punto[0] >= mitad_x else 0) + (2 if punto[1] >= mitad_y else 0)

    def _dividir(self, nodo):
        x0, y0, x1, y1 = nodo.caja
        mitad_x = (x0 + x1) / 2
        mitad_y = (y0 + y1) / 2
        cajas = [
            (x0, y0, mitad_x, mitad_y),
            (mitad_x, y0, x1, mitad_y),
            (x0, mitad_y, mitad_x, y1),
            (mitad_x, mitad_y, x1, y1),
        ]
        nodo.hijos = [_Nodo(caja, nodo.profundidad + 1) for caja in cajas]
        for punto in nodo.puntos:
            indice = self._cuadrante(nodo, punto)
            nodo.hijos[indice].puntos.append(punto)
        nodo.puntos = []
        for hijo in nodo.hijos:
            if len(hijo.puntos) > self.capacidad and hijo.profundidad < self.prof_max:
                self._dividir(hijo)

    def insertar(self, punto):
        punto = _punto(punto)
        x0, y0, x1, y1 = self.caja
        if not (x0 <= punto[0] <= x1 and y0 <= punto[1] <= y1):
            raise ValueError(f"El punto {punto} esta fuera del area del arbol")
        nodo = self.raiz
        while nodo.hijos is not None:
            nodo = nodo.hijos[self._cuadrante(nodo, punto)]
        nodo.puntos.append(punto)
        self._n += 1
        if len(nodo.puntos) > self.capacidad and nodo.profundidad < self.prof_max:
            self._dividir(nodo)

    def cajas_hojas(self):
        pila = [self.raiz]
        while pila:
            nodo = pila.pop()
            if nodo.hijos is None:
                yield nodo.caja
            else:
                pila.extend(nodo.hijos)

    def rango(self, centro, radio):
        """Devuelve puntos a distancia menor o igual al radio en metros."""
        centro = _punto(centro)
        if radio < 0:
            raise ValueError("El radio no puede ser negativo")
        radio2 = radio * radio
        resultado = []
        pila = [self.raiz]
        while pila:
            nodo = pila.pop()
            if _distancia2_caja(centro, nodo.caja) > radio2:
                continue
            if nodo.hijos is None:
                resultado.extend(
                    punto for punto in nodo.puntos
                    if distancia2(punto, centro) <= radio2
                )
            else:
                pila.extend(nodo.hijos)
        return resultado

    def vecinos(self, consulta, k=1):
        """Devuelve los k puntos mas cercanos, ordenados por distancia."""
        consulta = _punto(consulta)
        if k < 1:
            raise ValueError("k debe ser >= 1")
        mejores = []
        contador = itertools.count()
        pendientes = [(_distancia2_caja(consulta, self.caja), next(contador), self.raiz)]

        while pendientes:
            distancia_caja, _, nodo = heapq.heappop(pendientes)
            if len(mejores) == k and distancia_caja > -mejores[0][0]:
                break
            if nodo.hijos is None:
                for punto in nodo.puntos:
                    d2 = distancia2(punto, consulta)
                    entrada = (-d2, tuple(-coord for coord in punto), punto)
                    if len(mejores) < k:
                        heapq.heappush(mejores, entrada)
                    elif entrada > mejores[0]:
                        heapq.heapreplace(mejores, entrada)
            else:
                for hijo in nodo.hijos:
                    heapq.heappush(
                        pendientes,
                        (_distancia2_caja(consulta, hijo.caja), next(contador), hijo),
                    )

        return sorted(
            ((math.sqrt(-fila[0]), fila[2]) for fila in mejores),
            key=lambda par: (par[0], par[1]),
        )


def rango_fuerza_bruta(puntos, centro, radio):
    centro = _punto(centro)
    if radio < 0:
        raise ValueError("El radio no puede ser negativo")
    radio2 = radio * radio
    return [p for p in (_punto(p) for p in puntos) if distancia2(p, centro) <= radio2]


def vecinos_fuerza_bruta(puntos, consulta, k=1):
    consulta = _punto(consulta)
    if k < 1:
        raise ValueError("k debe ser >= 1")
    return sorted(
        ((math.sqrt(distancia2(p, consulta)), p) for p in (_punto(p) for p in puntos)),
        key=lambda par: (par[0], par[1]),
    )[:k]

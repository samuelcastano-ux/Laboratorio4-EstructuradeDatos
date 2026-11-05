"""
Pruebas del Quadtree 2D y gráficas de verificación.
Ejecutar:  python test.py
Las gráficas se guardan en la carpeta graficas/ al lado de este archivo.
"""
import math
import os
import random
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from Quadtree import QuadTree, rango_fuerza_bruta, vecinos_fuerza_bruta

LADO = 10000          # metros (ciudad de 10 km x 10 km)
RADIO = 500           # metros
AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "graficas")


def crear_arbol(puntos, capacidad=8):
    arbol = QuadTree(0, 0, LADO, LADO, capacidad=capacidad)
    for p in puntos:
        arbol.insertar(p)
    return arbol


def puntos_aleatorios(n, rnd):
    return [(rnd.uniform(0, LADO), rnd.uniform(0, LADO)) for _ in range(n)]


def dibujar_celdas(ax, arbol):
    for nodo in arbol.hojas():
        ancho = nodo.x1 - nodo.x0
        alto = nodo.y1 - nodo.y0
        ax.add_patch(Rectangle((nodo.x0, nodo.y0), ancho, alto,
                               fill=False, lw=0.4, ec="gray"))


def separar_xy(puntos):
    return [p[0] for p in puntos], [p[1] for p in puntos]


# ---------------- pruebas ----------------

class TestQuadTree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rnd = random.Random(42)
        cls.puntos = puntos_aleatorios(2000, cls.rnd)
        cls.arbol = crear_arbol(cls.puntos)

    def test_cantidad(self):
        self.assertEqual(len(self.arbol), 2000)

    def test_rango_igual_fuerza_bruta(self):
        for _ in range(50):
            c = puntos_aleatorios(1, self.rnd)[0]
            self.assertEqual(sorted(self.arbol.rango(c, RADIO)),
                             sorted(rango_fuerza_bruta(self.puntos, c, RADIO)))

    def test_vecinos_igual_fuerza_bruta(self):
        for _ in range(50):
            c = puntos_aleatorios(1, self.rnd)[0]
            for k in (1, 5, 20):
                a = [round(d, 6) for d, _ in self.arbol.vecinos(c, k)]
                b = [round(d, 6) for d, _ in vecinos_fuerza_bruta(self.puntos, c, k)]
                self.assertEqual(a, b)

    def test_radio_incluye_borde(self):
        arbol = crear_arbol([(0, 0), (500, 0), (501, 0)])
        self.assertEqual(sorted(arbol.rango((0, 0), 500)), [(0, 0), (500, 0)])

    def test_empate_se_ordena_por_coordenadas(self):
        pts = [(5001, 5000), (4999, 5000), (5000, 5001), (5000, 4999)]
        arbol = crear_arbol(pts, capacidad=1)
        self.assertEqual(arbol.vecinos((5000, 5000), 2),
                         [(1.0, (4999, 5000)), (1.0, (5000, 4999))])

    def test_puntos_repetidos(self):
        arbol = crear_arbol([(5, 5)] * 50)
        self.assertEqual(len(arbol.rango((5, 5), 1)), 50)
        self.assertEqual([d for d, _ in arbol.vecinos((5, 5), 3)], [0, 0, 0])

    def test_arbol_vacio(self):
        arbol = QuadTree(0, 0, LADO, LADO)
        self.assertEqual(arbol.rango((1, 1), RADIO), [])
        self.assertEqual(arbol.vecinos((1, 1), 1), [])

    def test_k_mayor_que_cantidad(self):
        arbol = crear_arbol([(0, 0), (1, 1)])
        self.assertEqual(len(arbol.vecinos((0, 0), 10)), 2)

    def test_fuera_del_area(self):
        arbol = QuadTree(0, 0, LADO, LADO)
        with self.assertRaises(ValueError):
            arbol.insertar((LADO + 1, 0))

    def test_punto_con_tres_coordenadas(self):
        arbol = QuadTree(0, 0, LADO, LADO)
        with self.assertRaises(ValueError):
            arbol.insertar((1, 2, 3))

    def test_radio_negativo(self):
        arbol = QuadTree(0, 0, LADO, LADO)
        with self.assertRaises(ValueError):
            arbol.rango((0, 0), -1)


# ---------------- gráficas de verificación ----------------

def dibujar_circulo_y_consulta(ax, centro, radio):
    ax.add_patch(Circle(centro, radio, fill=False, ec="red", lw=1.5, zorder=4))
    ax.plot(centro[0], centro[1], "r+", ms=14, mew=2, zorder=5)


def grafica_radio(arbol, puntos, centro, radio, nombre):
    dentro = arbol.rango(centro, radio)
    conjunto = set(dentro)
    assert conjunto == set(rango_fuerza_bruta(puntos, centro, radio))
    fuera = [p for p in puntos if p not in conjunto]
    distancias = [math.hypot(x - centro[0], y - centro[1]) for x, y in dentro]

    fig, (ax, zoom) = plt.subplots(1, 2, figsize=(14, 6))
    dibujar_celdas(ax, arbol)
    ax.scatter(*separar_xy(puntos), s=5, c="#a8b0b5", alpha=0.55,
               label="puntos de entrega")
    ax.scatter(*separar_xy(dentro), s=24, c="#087e8b", edgecolors="white",
               linewidths=0.5, zorder=3, label=f"encontrados ({len(dentro)})")
    dibujar_circulo_y_consulta(ax, centro, radio)

    margen = radio * 1.45
    x0, y0 = centro[0] - margen, centro[1] - margen
    ax.add_patch(Rectangle((x0, y0), 2 * margen, 2 * margen, fill=False,
                           ls=":", ec="#087e8b", lw=1.5, zorder=6))

    zoom.scatter(*separar_xy(fuera), s=11, c="#a8b0b5", alpha=0.45,
                  label="fuera del radio")
    zoom.scatter(*separar_xy(dentro), s=38, c="#087e8b", edgecolors="white",
                  linewidths=0.7, zorder=3, label=f"encontrados ({len(dentro)})")
    zoom.add_patch(Circle(centro, radio, fill=False, ec="#e4572e", lw=2.2,
                          label=f"radio {radio} m", zorder=4))
    zoom.scatter(*centro, marker="X", s=95, c="#252525", edgecolors="white",
                 linewidths=0.8, zorder=5, label="consulta")
    zoom.set_xlim(x0, x0 + 2 * margen)
    zoom.set_ylim(y0, y0 + 2 * margen)
    zoom.set_aspect("equal")
    zoom.set_title("Detalle de la búsqueda")
    zoom.legend(loc="upper right", fontsize=8, framealpha=0.95)
    zoom.grid(alpha=0.2)

    ax.set_xlim(0, LADO)
    ax.set_ylim(0, LADO)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Distribución completa")
    ax.legend(loc="lower left", fontsize=8)
    fig.suptitle(f"Range search: radio de {radio} m")
    fig.tight_layout()

    fig.savefig(os.path.join(CARPETA, nombre), dpi=150, bbox_inches="tight")
    plt.close(fig)


def grafica_vecinos(arbol, puntos, consulta, k, nombre):
    vecinos = arbol.vecinos(consulta, k)
    cercanos = [p for _, p in vecinos]
    distancias = [d for d, _ in vecinos]

    fig, (ax, zoom) = plt.subplots(1, 2, figsize=(14, 6))
    dibujar_celdas(ax, arbol)
    ax.scatter(*separar_xy(puntos), s=5, c="#a8b0b5", alpha=0.55,
               label="puntos de entrega")
    ax.scatter(*separar_xy(cercanos), s=65, c="#f2a541", edgecolors="white",
               zorder=3, label=f"{k} vecino(s) más cercano(s)")

    margen = max(distancias, default=1) * 1.8
    x0, y0 = consulta[0] - margen, consulta[1] - margen
    ax.add_patch(Rectangle((x0, y0), 2 * margen, 2 * margen, fill=False,
                           ls=":", ec="#f2a541", lw=1.5, zorder=6))

    zoom.scatter(*separar_xy(puntos), s=12, c="#a8b0b5", alpha=0.45,
                 label="puntos de entrega")
    zoom.scatter(*separar_xy(cercanos), s=80, c="#f2a541", edgecolors="white",
                 linewidths=0.8, zorder=3, label=f"{k} vecinos")
    zoom.add_patch(Circle(consulta, max(distancias, default=0), fill=False,
                          ec="#e4572e", lw=2, label="distancia al vecino más lejano"))
    zoom.scatter(*consulta, marker="X", s=100, c="#252525", edgecolors="white",
                 linewidths=0.8, zorder=5, label="consulta")
    for i, (d, p) in enumerate(vecinos, 1):
        zoom.plot([consulta[0], p[0]], [consulta[1], p[1]], color="#e4572e",
                  ls="--", lw=0.9, zorder=2)
        zoom.annotate(f"{i}: {d:.0f} m", p, textcoords="offset points",
                      xytext=(6, 6), fontsize=8)
    zoom.set_xlim(x0, x0 + 2 * margen)
    zoom.set_ylim(y0, y0 + 2 * margen)
    zoom.set_aspect("equal")
    zoom.set_title(f"Detalle de los {k} vecinos")
    zoom.legend(loc="upper right", fontsize=8, framealpha=0.95)
    zoom.grid(alpha=0.2)

    ax.set_xlim(0, LADO)
    ax.set_ylim(0, LADO)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Distribución completa")
    ax.legend(loc="lower left", fontsize=8)
    fig.suptitle(f"Búsqueda de los {k} vecinos más cercanos")
    fig.tight_layout()

    fig.savefig(os.path.join(CARPETA, nombre), dpi=150, bbox_inches="tight")
    plt.close(fig)


def generar_graficas():
    os.makedirs(CARPETA, exist_ok=True)
    rnd = random.Random(2024)
    puntos = puntos_aleatorios(10000, rnd)
    arbol = crear_arbol(puntos)
    centro = (5000, 5000)

    grafica_radio(arbol, puntos, centro, RADIO, "rango_500m.png")
    grafica_vecinos(arbol, puntos, centro, 5, "vecinos_k5.png")
    print("Gráficas guardadas en:", CARPETA)


if __name__ == "__main__":
    generar_graficas()
    unittest.main(verbosity=2)
"""
Pruebas unitarias, comparación con fuerza bruta y visualizaciones.
Ejecutar:  python test.py
Las gráficas se guardan en ./graficas/
"""
import os
import random
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from Quadtreetree import QuadTree, rango_fuerza_bruta, vecinos_fuerza_bruta

LADO = 10_000
CARPETA = "graficas"
os.makedirs(CARPETA, exist_ok=True)


def _crear_arbol(pts, capacidad=8):
    arbol = QuadTree([(0, LADO), (0, LADO)], capacidad=capacidad)
    for p in pts:
        arbol.insertar(p)
    return arbol


def _aleatorios(n, rnd):
    return [(rnd.uniform(0, LADO), rnd.uniform(0, LADO)) for _ in range(n)]


def _dibujar_hojas(ax, nodo):
    if nodo.hijos is None:
        (x0, x1), (y0, y1) = nodo.limites
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.4, ec="gray"))
    else:
        for h in nodo.hijos:
            _dibujar_hojas(ax, h)


def _xy(puntos):
    return [p[0] for p in puntos], [p[1] for p in puntos]


# ---------------- pruebas unitarias ----------------

class TestQuadTree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rnd = random.Random(42)
        cls.pts = _aleatorios(2000, rnd)
        cls.arbol = _crear_arbol(cls.pts)
        cls.rnd = rnd

    def test_tamano(self):
        self.assertEqual(len(self.arbol), 2000)

    def test_rango_igual_fuerza_bruta(self):
        for _ in range(50):
            c = _aleatorios(1, self.rnd)[0]
            self.assertEqual(sorted(self.arbol.rango(c, 500)),
                             sorted(rango_fuerza_bruta(self.pts, c, 500)))

    def test_vecinos_igual_fuerza_bruta(self):
        for _ in range(50):
            c = _aleatorios(1, self.rnd)[0]
            for k in (1, 5, 20):
                a = [round(d, 6) for d, _ in self.arbol.vecinos(c, k)]
                b = [round(d, 6) for d, _ in vecinos_fuerza_bruta(self.pts, c, k)]
                self.assertEqual(a, b)

    def test_radio_incluye_borde(self):
        arbol = _crear_arbol([(0, 0), (500, 0), (501, 0)])
        self.assertEqual(sorted(arbol.rango((0, 0), 500)), [(0.0, 0.0), (500.0, 0.0)])

    def test_vecinos_desempatan_por_coordenadas(self):
        pts = [(5001, 5000), (4999, 5000), (5000, 5001), (5000, 4999)]
        arbol = _crear_arbol(pts, capacidad=1)
        self.assertEqual(
            arbol.vecinos((5000, 5000), 2),
            [(1.0, (4999.0, 5000.0)), (1.0, (5000.0, 4999.0))],
        )

    def test_puntos_duplicados(self):
        arbol = _crear_arbol([(5, 5)] * 50)
        self.assertEqual(len(arbol.rango((5, 5), 1)), 50)
        self.assertEqual([d for d, _ in arbol.vecinos((5, 5), 3)], [0, 0, 0])

    def test_arbol_vacio(self):
        arbol = QuadTree([(0, LADO), (0, LADO)])
        self.assertEqual(arbol.rango((1, 1), 500), [])
        self.assertEqual(arbol.vecinos((1, 1), 1), [])

    def test_fuera_de_limites(self):
        arbol = QuadTree([(0, LADO), (0, LADO)])
        with self.assertRaises(ValueError):
            arbol.insertar((LADO + 1, 0))

    def test_coordenadas_incorrectas(self):
        arbol = QuadTree([(0, LADO), (0, LADO)])
        with self.assertRaises(ValueError):
            arbol.insertar((1, 2, 3))

    def test_radio_negativo(self):
        arbol = QuadTree([(0, LADO), (0, LADO)])
        with self.assertRaises(ValueError):
            arbol.rango((0, 0), -1)


# ---------------- visualizaciones ----------------

def graficar_rango(arbol, pts, centro, radio, nombre):
    encontrados = arbol.rango(centro, radio)
    conjunto = set(encontrados)
    assert conjunto == set(rango_fuerza_bruta(pts, centro, radio))
    fuera = [p for p in pts if p not in conjunto]

    fig, ax = plt.subplots(figsize=(7, 7))
    _dibujar_hojas(ax, arbol.raiz)
    ax.scatter(*_xy(fuera), s=4, c="lightgray", label="fuera del radio")
    ax.scatter(*_xy(encontrados), s=14, c="green", label=f"dentro ({len(encontrados)})")
    ax.add_patch(Circle(centro, radio, fill=False, ec="red", lw=1.5))
    ax.plot(centro[0], centro[1], "r+", ms=14, mew=2)
    ax.set_xlim(0, LADO); ax.set_ylim(0, LADO)
    ax.set_aspect("equal")
    ax.set_title(f"Range search: radio {radio} m (celdas del Quadtree en gris)")
    ax.legend(loc="upper right")
    fig.savefig(os.path.join(CARPETA, nombre), dpi=150, bbox_inches="tight")
    plt.close(fig)


def graficar_vecinos(arbol, pts, consulta, k, nombre):
    vecinos = arbol.vecinos(consulta, k)
    fig, ax = plt.subplots(figsize=(7, 7))
    _dibujar_hojas(ax, arbol.raiz)
    ax.scatter(*_xy(pts), s=4, c="lightgray")
    ax.scatter(*_xy([p for _, p in vecinos]), s=40, c="orange", edgecolors="k",
               zorder=3, label=f"{k} vecino(s) más cercano(s)")
    for i, (d, p) in enumerate(vecinos, 1):
        ax.plot([consulta[0], p[0]], [consulta[1], p[1]], "k--", lw=0.8)
        ax.annotate(f"{i}: {d:.0f} m", p, textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.plot(consulta[0], consulta[1], "r*", ms=16, label="consulta")
    ax.set_xlim(0, LADO); ax.set_ylim(0, LADO)
    ax.set_aspect("equal")
    ax.set_title(f"Vecinos más cercanos (k={k})")
    ax.legend(loc="upper right")
    fig.savefig(os.path.join(CARPETA, nombre), dpi=150, bbox_inches="tight")
    plt.close(fig)


class TestVisual(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rnd = random.Random(2024)
        cls.pts = _aleatorios(1500, rnd)
        cls.arbol = _crear_arbol(cls.pts)
        cls.centro = (5000, 5000)

    def test_visual_rango(self):
        graficar_rango(self.arbol, self.pts, self.centro, 500, "rango_500m.png")
        self.assertTrue(os.path.exists(os.path.join(CARPETA, "rango_500m.png")))

    def test_visual_vecinos(self):
        graficar_vecinos(self.arbol, self.pts, self.centro, 5, "vecinos_k5.png")
        self.assertTrue(os.path.exists(os.path.join(CARPETA, "vecinos_k5.png")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
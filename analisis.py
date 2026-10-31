"""
Análisis comparativo Quadtree vs fuerza bruta.
Mide tiempos de construcción, range search y vecino más cercano para distintos N.
Genera: graficas/rendimiento.png y resultados.csv
Ejecutar:  python analisis.py
"""
import csv
import os
import random
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from Quadtreetree import QuadTree, rango_fuerza_bruta, vecinos_fuerza_bruta

LADO = 10_000                 # metros (ciudad de 10 km x 10 km)
RADIO = 500                   # metros
TAMAÑOS = [100, 250, 500, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000]
N_CONSULTAS = 100
REPETICIONES = 3              # se toma el mejor tiempo (estilo timeit)
CARPETA = "graficas"


def tiempo_medio(func, consultas):
    """Tiempo medio por consulta, usando la mejor de REPETICIONES pasadas."""
    mejor = float("inf")
    for _ in range(REPETICIONES):
        t0 = time.perf_counter()
        for q in consultas:
            func(q)
        mejor = min(mejor, time.perf_counter() - t0)
    return mejor / len(consultas)


def generar(n, semilla):
    rnd = random.Random(semilla)
    pts = [(rnd.uniform(0, LADO), rnd.uniform(0, LADO)) for _ in range(n)]
    consultas = [(rnd.uniform(0, LADO), rnd.uniform(0, LADO)) for _ in range(N_CONSULTAS)]
    return pts, consultas


def primer_cruce(tams, t_qt, t_bf):
    """Menor N desde el cual el Quadtree es más rápido y lo sigue siendo para todo N mayor."""
    cruce = None
    for n, a, b in zip(tams, t_qt, t_bf):
        if a < b:
            if cruce is None:
                cruce = n
        else:
            cruce = None
    return cruce


def main():
    os.makedirs(CARPETA, exist_ok=True)
    filas = []

    print(f"{'N':>8} {'build (s)':>10} {'rango QT':>10} {'rango BF':>10} "
          f"{'NN QT':>10} {'NN BF':>10}   (tiempos en ms por consulta)")
    for n in TAMAÑOS:
        pts, consultas = generar(n, semilla=n)

        t0 = time.perf_counter()
        arbol = QuadTree([(0, LADO), (0, LADO)], capacidad=8)
        for p in pts:
            arbol.insertar(p)
        t_build = time.perf_counter() - t0

        fila = {
            "n": n,
            "build_s": t_build,
            "rango_qt_ms": 1000 * tiempo_medio(lambda q: arbol.rango(q, RADIO), consultas),
            "rango_bf_ms": 1000 * tiempo_medio(lambda q: rango_fuerza_bruta(pts, q, RADIO), consultas),
            "nn_qt_ms": 1000 * tiempo_medio(lambda q: arbol.vecinos(q, 1), consultas),
            "nn_bf_ms": 1000 * tiempo_medio(lambda q: vecinos_fuerza_bruta(pts, q, 1), consultas),
        }
        filas.append(fila)
        print(f"{n:>8} {t_build:>10.3f} {fila['rango_qt_ms']:>10.4f} {fila['rango_bf_ms']:>10.4f} "
              f"{fila['nn_qt_ms']:>10.4f} {fila['nn_bf_ms']:>10.4f}")

    # ---- resultados en CSV ----
    with open("resultados.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)

    tams = [f["n"] for f in filas]
    rq = [f["rango_qt_ms"] for f in filas]
    rb = [f["rango_bf_ms"] for f in filas]
    nq = [f["nn_qt_ms"] for f in filas]
    nb = [f["nn_bf_ms"] for f in filas]

    cruce_rango = primer_cruce(tams, rq, rb)
    cruce_nn = primer_cruce(tams, nq, nb)

    # ---- gráficas ----
    fig, ejes = plt.subplots(1, 3, figsize=(17, 5))
    ejes[0].loglog(tams, rq, "o-", label="Quadtree")
    ejes[0].loglog(tams, rb, "s-", label="Fuerza bruta")
    ejes[0].set_title("Range search (radio 500 m)")
    ejes[0].set_xlabel("N puntos"); ejes[0].set_ylabel("ms por consulta")

    ejes[1].loglog(tams, nq, "o-", label="Quadtree")
    ejes[1].loglog(tams, nb, "s-", label="Fuerza bruta")
    ejes[1].set_title("Vecino más cercano (k=1)")
    ejes[1].set_xlabel("N puntos"); ejes[1].set_ylabel("ms por consulta")

    ejes[2].semilogx(tams, [b / a for a, b in zip(rq, rb)], "o-", label="rango")
    ejes[2].semilogx(tams, [b / a for a, b in zip(nq, nb)], "s-", label="vecino más cercano")
    ejes[2].axhline(1, color="k", ls="--", lw=1)
    ejes[2].set_title("Aceleración (fuerza bruta / Quadtree)")
    ejes[2].set_xlabel("N puntos"); ejes[2].set_ylabel("veces más rápido")

    for ax in ejes:
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "rendimiento.png"), dpi=150)
    plt.close(fig)

    # ---- discusión ----
    print("\n=== Discusión ===")
    print(f"Quadtree supera a fuerza bruta en range search desde N = {cruce_rango}")
    print(f"Quadtree supera a fuerza bruta en vecino más cercano desde N = {cruce_nn}")
    if rb[-1] > rq[-1]:
        ahorro = rb[-1] - rq[-1]            # segundos por consulta ahorrados
        print(f"Para N = {tams[-1]}, el coste de construcción ({filas[-1]['build_s']:.2f} s) "
              f"se amortiza tras ~{filas[-1]['build_s'] / (ahorro / 1000):.0f} consultas de rango.")
    print("Los resultados dependen de la máquina; el punto de cruce es lo que interesa comparar.")


if __name__ == "__main__":
    main()
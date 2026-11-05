"""
Análisis de rendimiento: Quadtree 2D contra fuerza bruta.

Para cada cantidad de puntos N se mide:
  - el tiempo de construir el Quadtree (una sola vez)
  - el tiempo por consulta de range search (radio 500 m)
  - el tiempo por consulta de vecino más cercano
  - cuántas consultas hacen falta para que la construcción valga la pena

Genera:
  resultados.csv
    graficas/rendimiento.png        (tiempo por consulta en escala log-log)
  graficas/construccion.png       (costo de construir y consultas necesarias)
Ejecutar:  python analisis.py
"""
import csv
import os
import random
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from Quadtree import QuadTree, rango_fuerza_bruta, vecinos_fuerza_bruta

LADO = 10000
RADIO = 500
TAMANOS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
N_CONSULTAS = 100
REPETICIONES = 3       # se guarda el mejor tiempo de las repeticiones
AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "graficas")


def tiempo_por_consulta(funcion, consultas):
    """Segundos por consulta (se usa el mejor de REPETICIONES)."""
    mejor = None
    for _ in range(REPETICIONES):
        inicio = time.perf_counter()
        for c in consultas:
            funcion(c)
        duracion = time.perf_counter() - inicio
        if mejor is None or duracion < mejor:
            mejor = duracion
    return mejor / len(consultas)


def generar(n):
    rnd = random.Random(n)   # misma semilla para cada N: resultados repetibles
    puntos = [(rnd.uniform(0, LADO), rnd.uniform(0, LADO)) for _ in range(n)]
    consultas = [(rnd.uniform(0, LADO), rnd.uniform(0, LADO)) for _ in range(N_CONSULTAS)]
    return puntos, consultas


def consultas_necesarias(construccion, t_arbol, t_fuerza_bruta):
    """
    Cuántas consultas hacen falta para que construir el árbol compense.
    Costo con árbol:  construccion + q * t_arbol
    Costo sin árbol:  q * t_fuerza_bruta
    Se igualan y se despeja q. Si el árbol no es más rápido, devuelve None.
    """
    ahorro = t_fuerza_bruta - t_arbol
    if ahorro <= 0:
        return None
    return construccion / ahorro


def primer_cruce(tamanos, t_arbol, t_fuerza_bruta):
    """Menor N desde el que el Quadtree es más rápido y lo sigue siendo para todo N mayor."""
    cruce = None
    for n, a, b in zip(tamanos, t_arbol, t_fuerza_bruta):
        if a < b:
            if cruce is None:
                cruce = n
        else:
            cruce = None
    return cruce


def medir():
    filas = []
    print(f"{'N':>7} {'construir(s)':>13} {'rango QT(ms)':>13} {'rango BF(ms)':>13} "
          f"{'vecino QT(ms)':>14} {'vecino BF(ms)':>14}")

    for n in TAMANOS:
        puntos, consultas = generar(n)

        inicio = time.perf_counter()
        arbol = QuadTree(0, 0, LADO, LADO, capacidad=8)
        for p in puntos:
            arbol.insertar(p)
        t_construir = time.perf_counter() - inicio

        fila = {
            "n": n,
            "construir_s": t_construir,
            "rango_qt_s": tiempo_por_consulta(lambda c: arbol.rango(c, RADIO), consultas),
            "rango_bf_s": tiempo_por_consulta(lambda c: rango_fuerza_bruta(puntos, c, RADIO), consultas),
            "vecino_qt_s": tiempo_por_consulta(lambda c: arbol.vecinos(c, 1), consultas),
            "vecino_bf_s": tiempo_por_consulta(lambda c: vecinos_fuerza_bruta(puntos, c, 1), consultas),
        }
        fila["consultas_rango"] = consultas_necesarias(
            t_construir, fila["rango_qt_s"], fila["rango_bf_s"])
        fila["consultas_vecino"] = consultas_necesarias(
            t_construir, fila["vecino_qt_s"], fila["vecino_bf_s"])
        filas.append(fila)

        print(f"{n:>7} {t_construir:>13.4f} {1000 * fila['rango_qt_s']:>13.4f} "
              f"{1000 * fila['rango_bf_s']:>13.4f} {1000 * fila['vecino_qt_s']:>14.4f} "
              f"{1000 * fila['vecino_bf_s']:>14.4f}")
    return filas


def guardar_csv(filas, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["n", "construir_s", "rango_qt_s", "rango_bf_s",
                           "vecino_qt_s", "vecino_bf_s",
                           "consultas_necesarias_rango", "consultas_necesarias_vecino"])
        for fila in filas:
            escritor.writerow([
                fila["n"], fila["construir_s"], fila["rango_qt_s"], fila["rango_bf_s"],
                fila["vecino_qt_s"], fila["vecino_bf_s"],
                "" if fila["consultas_rango"] is None else fila["consultas_rango"],
                "" if fila["consultas_vecino"] is None else fila["consultas_vecino"],
            ])


def graficar_rendimiento(filas, ruta):
    filas_grafica = [f for f in filas if f["n"] <= 10000]
    ns = [f["n"] for f in filas_grafica]
    fig, ejes = plt.subplots(1, 2, figsize=(14, 5.5))

    operaciones = (
        ("rango_qt_s", "rango_bf_s", "Range search (radio 500 m)"),
        ("vecino_qt_s", "vecino_bf_s", "Vecino más cercano (k = 1)"),
    )
    for ax, (tiempo_qt, tiempo_bf, titulo) in zip(ejes, operaciones):
        ax.loglog(ns, [1000 * f[tiempo_qt] for f in filas_grafica], "o-", label="Quadtree")
        ax.loglog(ns, [1000 * f[tiempo_bf] for f in filas_grafica], "s-", label="Fuerza bruta")
        ax.set_xlim(min(ns), 10000)
        ax.set_title(titulo)
        ax.set_xlabel("Número de puntos N")
        ax.set_ylabel("Tiempo por consulta (ms)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

    fig.suptitle("Tiempo por consulta frente al número de puntos (N hasta 10.000)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def graficar_construccion(filas, ruta):
    filas_grafica = [f for f in filas if f["n"] <= 10000]
    ns = [f["n"] for f in filas_grafica]
    fig, ejes = plt.subplots(1, 2, figsize=(14, 5.5))

    ejes[0].plot(ns, [1000 * f["construir_s"] for f in filas_grafica],
                 "o-", color="purple")
    ejes[0].set_title("Costo de construir el Quadtree")
    ejes[0].set_xlabel("Número de puntos N")
    ejes[0].set_ylabel("Tiempo de construcción (ms)")

    pares = [(f["n"], f["consultas_rango"]) for f in filas_grafica
             if f["consultas_rango"] is not None]
    pares_vecino = [(f["n"], f["consultas_vecino"]) for f in filas_grafica
                    if f["consultas_vecino"] is not None]
    if pares:
        ejes[1].plot([p[0] for p in pares], [p[1] for p in pares], "o-",
                     label="range search")
    if pares_vecino:
        ejes[1].plot([p[0] for p in pares_vecino], [p[1] for p in pares_vecino],
                     "s-", label="vecino más cercano")
    ejes[1].set_title("Consultas para amortizar la construcción")
    ejes[1].set_xlabel("Número de puntos N")
    ejes[1].set_ylabel("Consultas")
    ejes[1].set_yscale("log")
    ejes[1].legend()

    for ax in ejes:
        ax.set_xlim(0, 10000)
        ax.grid(True, alpha=0.3)
    fig.suptitle("Construcción del Quadtree 2D (N de 0 a 10.000)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main():
    os.makedirs(CARPETA, exist_ok=True)
    filas = medir()

    guardar_csv(filas, os.path.join(AQUI, "resultados.csv"))
    graficar_rendimiento(filas, os.path.join(CARPETA, "rendimiento.png"))
    graficar_construccion(filas, os.path.join(CARPETA, "construccion.png"))

    ns = [f["n"] for f in filas]
    print("\n=== Discusión ===")
    print("Range search: el Quadtree es más rápido desde N =",
          primer_cruce(ns, [f["rango_qt_s"] for f in filas], [f["rango_bf_s"] for f in filas]))
    print("Vecino más cercano: el Quadtree es más rápido desde N =",
          primer_cruce(ns, [f["vecino_qt_s"] for f in filas], [f["vecino_bf_s"] for f in filas]))
    print("Los tiempos dependen de la computadora; lo que se compara es la forma de las curvas.")
    print("Archivos: resultados.csv, graficas/rendimiento.png, graficas/construccion.png")


if __name__ == "__main__":
    main()
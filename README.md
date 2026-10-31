# Sistema de logística: QuadTree vs fuerza bruta

QuadTree 2D implementado desde cero para puntos de entrega en una ciudad de 10 km × 10 km.
Las coordenadas `(x, y)` y los radios se expresan en metros.

Consultas:
1. Range search: ¿qué puntos están a 500 m o menos de una ubicación?
2. Vecino más cercano: ¿cuál es el punto de entrega más cercano?

## Archivos

| Archivo | Contenido |
|---|---|
| `Quadtreetree.py` | Árbol 2D, range search, vecinos y fuerza bruta |
| `test.py` | Pruebas unitarias, comparación con fuerza bruta y visualizaciones |
| `analisis.py` | Benchmark, `resultados.csv` y `graficas/rendimiento.png` |
| `graficas/` | Imágenes generadas por las pruebas y el análisis |

## Uso

```bash
pip install matplotlib
python test.py
python analisis.py
```

```python
from Quadtreetree import QuadTree

arbol = QuadTree([(0, 10_000), (0, 10_000)], capacidad=8)
for x, y in puntos:
    arbol.insertar((x, y))

arbol.rango((5000, 5000), 500)     # lista de puntos a <= 500 m
arbol.vecinos((5000, 5000), k=1)   # [(distancia_m, punto)]
```

La caja puede escribirse como `[(xmin, xmax), (ymin, ymax)]` o `(x0, y0, x1, y1)`.
Cada nodo se divide en cuatro cuadrantes.

## Complejidad (casos típicos, datos uniformes en 2D)

| Operación | Quadtree | Fuerza bruta |
|---|---|---|
| Construcción | O(n log n) aprox. | — |
| Range search | O(√n + m), m = resultados | O(n) |
| Vecino más cercano | O(log n) aprox. | O(n) |

Con datos muy agrupados o puntos repetidos el árbol puede degradarse; `prof_max` limita la
profundidad. Las consultas miden metros siempre que los datos y el radio estén expresados en
metros.

## Respuesta a la pregunta del análisis

El punto de cruce se mide al ejecutar `analisis.py`; depende del equipo y de cuántas consultas
se realicen, porque el árbol tiene un coste inicial de construcción. La consola, `resultados.csv`
y `graficas/rendimiento.png` muestran los resultados obtenidos.

En una ejecución de referencia de este proyecto, el Quadtree ya fue más rápido en ambas consultas
desde el menor tamaño medido (`N = 100`); no es un umbral universal. Para los gráficos de prueba,
ejecuta `python test.py`.

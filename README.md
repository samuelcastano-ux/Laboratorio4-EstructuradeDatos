# Sistema de logística: Quadtree 2D vs fuerza bruta

Quadtree en 2D hecho desde cero, solo con la biblioteca estándar de Python, para
consultar puntos de entrega en una ciudad de 10 km × 10 km. Todas las coordenadas
y radios están en **metros**.

Consultas:
1. **Range search:** ¿qué puntos de entrega están a 500 m o menos de una ubicación?
2. **Vecino más cercano:** ¿cuál es el punto de entrega más cercano a una ubicación?

## Planteamiento de la solución

Un Quadtree divide el plano en cuadrados que se van partiendo por la mitad. Cada nodo
representa un rectángulo `(x0, y0, x1, y1)`. Si un nodo tiene más puntos que la
capacidad (8 por defecto), se divide en cuatro hijos, uno por cuadrante:

```
División de un rectángulo:

          Estructura del árbol:
┌───────────┬───────────┐                 Nodo
│    NO     │    NE     │             /   |   |   \
├───────────┼───────────┤           NO   NE  SO   SE
│    SO     │    SE     │           (cada hijo puede subdividirse)
└───────────┴───────────┘
```

Los hijos siempre se guardan en el orden `[NO, NE, SO, SE]`. Como la división ocurre
siempre en el centro del rectángulo, cada punto cae en un único cuadrante según si su
`x` está a la derecha o a la izquierda del centro, y si su `y` está arriba o abajo.

**Construcción.** Cada punto baja desde la raíz hasta la hoja que le corresponde. Si esa
hoja se llena, se divide y sus puntos se reparten entre los cuatro hijos. El límite
`prof_max` evita dividir sin fin cuando hay muchos puntos repetidos.

**Range search (radio).** Se recorre el árbol desde la raíz. Si el rectángulo de un
nodo está más lejos del centro que el radio, se descarta ese nodo completo, junto con
todos sus puntos. En las hojas que sobreviven se revisa punto por punto la distancia.

**Vecino más cercano (k vecinos).** Se recorre el árbol visitando primero los hijos más
cercanos a la consulta. Se guardan los `k` mejores encontrados hasta el momento, y un
nodo se descarta si su rectángulo está más lejos que el peor de esos `k` puntos.

**Fuerza bruta.** Calcula la distancia a los N puntos para cada consulta. Sirve como
referencia para comprobar que el árbol devuelve lo mismo y para medir el tiempo.

## Archivos

| Archivo | Contenido |
|---|---|
| `Quadtree.py` | Árbol 2D, range search, vecinos y fuerza bruta |
| `test.py` | Pruebas unitarias y gráficas de radio y de vecinos |
| `analisis.py` | Medición de tiempos, `resultados.csv` y gráficas de rendimiento |
| `graficas/` | Imágenes generadas por `test.py` y `analisis.py` |
| `resultados.csv` | Tiempos medidos para cada N |

## Uso

```bash
pip install matplotlib
python test.py       # pruebas y gráficas de radio y vecinos
python analisis.py   # benchmark, resultados.csv y gráficas de rendimiento
```

```python
from Quadtree import QuadTree

arbol = QuadTree(0, 0, 10000, 10000, capacidad=8)
for x, y in puntos:
    arbol.insertar((x, y))

arbol.rango((5000, 5000), 500)     # lista de puntos a 500 m o menos
arbol.vecinos((5000, 5000), k=1)   # [(distancia_en_metros, punto)]
```

## Gráficas

- `graficas/rango_500m.png`: puntos dentro y fuera del radio de 500 m, con las celdas del árbol.
- `graficas/vecinos_k5.png`: los 5 vecinos más cercanos a una consulta.
- `graficas/rendimiento.png`: tiempo por consulta frente a N en escala log-log para range
  search y vecino más cercano, comparando Quadtree y fuerza bruta.
- `graficas/construccion.png`: tiempo de construcción en milisegundos y consultas necesarias
  para compensar la construcción, con N en escala lineal de 0 a 10.000.

## Resultados

Medidos en la computadora de desarrollo con N desde 10 hasta 100 000 puntos
(100 consultas por tamaño, mejor de 3 repeticiones):

| N | Construir (s) | Rango QT (ms) | Rango BF (ms) | Vecino QT (ms) | Vecino BF (ms) |
|---:|---:|---:|---:|---:|---:|
| 100 | 0.0001 | 0.0026 | 0.0064 | 0.0055 | 0.0102 |
| 1 000 | 0.0009 | 0.0065 | 0.0648 | 0.0090 | 0.0954 |
| 10 000 | 0.0149 | 0.0353 | 0.7412 | 0.0145 | 1.1365 |
| 100 000 | 0.2469 | 0.3019 | 7.5901 | 0.0159 | 10.6940 |

- **¿Desde qué tamaño el Quadtree es más rápido?** En range search, desde **N ≈ 25**. En vecino
  más cercano, desde **N ≈ 50**. Por debajo de eso, la fuerza bruta gana porque el árbol tiene
  más sobrecarga de llamadas y objetos.
- **Costo de construcción.** Crece casi lineal (en loglog la pendiente es cercana a 1). Para
  N = 100 000 construir tarda unos 0.25 s.
- **Consultas necesarias para compensar la construcción.** Con N = 100 000 hacen falta unas
  34 consultas de range search o unas 23 de vecino más cercano. Si el sistema hace muchas
  más consultas que eso sobre los mismos datos, el árbol vale la pena.
- Los tiempos cambian de una computadora a otra. Lo que se compara es la forma de las curvas
  y el punto de cruce.

## Complejidad (casos típicos con datos repartidos)

| Operación | Quadtree | Fuerza bruta |
|---|---|---|
| Construcción | O(n log n) aprox. | — |
| Range search | Depende de cuántos nodos toca el círculo; en la práctica mucho menos que n | O(n) |
| Vecino más cercano | En la práctica mucho menos que n | O(n) |

Con datos muy agrupados o muchos puntos repetidos, el árbol puede hacerse más lento,
porque algunas hojas se llenan demasiado. `prof_max` limita la profundidad.

## Uso de IA

Se utilizo IA para generar el análisis estadístico de los resultados y gráficas, generar el test, verificar el código creado para el QuadTree y ayudar a redactar este README.

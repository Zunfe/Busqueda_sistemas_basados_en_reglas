# Sistema inteligente de rutas para transporte masivo (TransMilenio, Bogotá)

Sistema que, a partir de una **base de conocimiento escrita en reglas lógicas**,
calcula la **mejor ruta** entre una estación A y una estación B usando
**búsqueda heurística (A\*)**.

> La red (estaciones, velocidades y coordenadas) es una **simplificación didáctica**
> y aproximada de TransMilenio. Debe validarse con el mapa oficial para uso real.

## Requisitos

- Python 3.9 o superior (probado en 3.12). **No requiere librerías externas.**
- Solo para regenerar los PDF de `docs/`: `pip install reportlab`

## Ejecución

```bash
# Ver las líneas y estaciones de la base de conocimiento
python main.py --listar

# Ruta óptima (A*) de A a B
python main.py --origen "Portal Norte" --destino "Portal Américas"

# Comparar A*, Dijkstra y BFS (tiempo y nodos expandidos)
python main.py -o "Portal Norte" -d "Portal Américas" --comparar

# Ver qué reglas se dispararon y qué hechos se dedujeron
python main.py -o "Portal Suba" -d "Restrepo" --explicar

# Escenarios dinámicos
python main.py -o "Minuto de Dios" -d "Av. Jiménez" --cerrar "Héroes"   # estación cerrada
python main.py -o "Portal 80" -d "Museo del Oro" --hora-pico             # hora pico
python main.py -o "Portal Norte" -d "Portal Américas" --penalizacion-transbordo 15
```

Los nombres aceptan mayúsculas/minúsculas, omitir tildes y coincidencias
parciales únicas (`heroes`, `portal americas`, `museo`).

## Pruebas

```bash
python -m unittest -v test_sistema      # 18 pruebas automáticas
python docs/generar_pdfs.py             # regenera docs/Pruebas_realizadas.pdf y Entrega_actividad.pdf
```

## Arquitectura

| Archivo | Rol | Tema del libro (Benítez, 2014) |
|---|---|---|
| `base_conocimiento.py` | Hechos (`estacion`, `parada`, `velocidad`, `cerrada`, `hora_pico`) y 8 reglas lógicas | Cap. 2: lógica y representación del conocimiento |
| `motor_reglas.py` | Motor de inferencia con encadenamiento hacia adelante, unificación con variables y negación como fracaso | Cap. 3: sistemas basados en reglas |
| `busqueda.py` | A\*, Dijkstra y BFS sobre el espacio de estados (estación, línea) | Cap. 9: búsqueda heurística |
| `main.py` | Interfaz de línea de comandos | - |
| `test_sistema.py` | Pruebas unitarias | - |

### Reglas lógicas

```
R1  parada(L,i,a) Y parada(L,j,b) Y j=i+1                 => adyacente(a,b,L)
R2  adyacente(a,b,L)                                      => tramo(a,b,L) Y tramo(b,a,L)
R3  parada(L1,_,E) Y parada(L2,_,E) Y L1<>L2              => enlace(E,L1,L2)
R4  enlace(E,L1,L2)                                       => hub(E)
R5  tramo(a,b,L) Y NO cerrada(a) Y NO cerrada(b)          => habilitado(a,b,L)
R6  habilitado(a,b,L) Y velocidad(L,v) Y NO hora_pico     => costo(a,b,L, d/v + parada)
R7  habilitado(a,b,L) Y velocidad(L,v) Y hora_pico        => costo(a,b,L, 1.35*d/v + parada)
R8  enlace(E,L1,L2) Y NO cerrada(E)                       => transbordo_ok(E,L1,L2,penalización)
```

### Búsqueda

- **Estado:** `(estación, línea)`; permite modelar el costo de los transbordos.
- **Costo g(n):** minutos acumulados (viaje + paradas + transbordos), derivados por las reglas.
- **Heurística:** `h(n) = distancia_haversine(n, destino) / v_max`. Es **admisible y consistente**
  (la línea recta a la velocidad máxima nunca sobreestima), por lo que A\* es óptimo.
- Las pruebas verifican que A\* iguala el costo de Dijkstra en los 1.482 pares posibles.

## Cómo extender la base de conocimiento

Agregue la estación en `COORDENADAS` y las líneas en `LINEAS` (velocidad + lista ordenada
de paradas). Los tramos, transbordos y costos se deducen automáticamente por las reglas.



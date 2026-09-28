"""
busqueda.py
===========
Búsqueda heurística sobre el espacio de estados derivado por las reglas
(Benítez, 2014, cap. 9).

Espacio de estados
    Estado   = (estación, línea en la que va el pasajero)
    Acciones = viajar a la estación contigua de la misma línea (regla 'costo')
               o hacer transbordo en la misma estación (regla 'transbordo_ok')
    Costo    = minutos

Algoritmos
    astar    : f(n) = g(n) + h(n),  h = distancia_km(n, destino) / v_max
               h es ADMISIBLE y CONSISTENTE (nunca sobreestima el tiempo real),
               por lo tanto A* devuelve la ruta óptima.
    dijkstra : búsqueda de costo uniforme (h = 0), óptima pero expande más nodos.
    bfs      : minimiza el número de pasos (estaciones + transbordos), no el tiempo.
"""
import heapq
import itertools
from collections import defaultdict
from dataclasses import dataclass, field

from base_conocimiento import distancia_km


@dataclass
class Resultado:
    algoritmo: str
    encontrada: bool
    estados: list = field(default_factory=list)
    minutos: float = 0.0
    expandidos: int = 0
    generados: int = 0

    @property
    def transbordos(self):
        return sum(1 for a, b in zip(self.estados, self.estados[1:]) if a[0] == b[0])

    @property
    def estaciones_recorridas(self):
        return sum(1 for a, b in zip(self.estados, self.estados[1:]) if a[0] != b[0])


class Grafo:
    """Grafo de estados construido a partir de los hechos DERIVADOS."""

    def __init__(self, base):
        self.vecinos = defaultdict(list)
        self.vmax_km_min = max(h[2] for h in base.indice["velocidad"]) / 60.0
        cerradas = {h[1] for h in base.indice["cerrada"]}
        self.cerradas = cerradas
        self.lineas_en = defaultdict(set)
        for _, linea, _, est in base.indice["parada"]:
            if est not in cerradas:
                self.lineas_en[est].add(linea)
        for _, a, b, linea, costo in base.indice["costo"]:
            self.vecinos[(a, linea)].append(((b, linea), costo, "viaje"))
        for _, est, l1, l2, costo in base.indice["transbordo_ok"]:
            self.vecinos[(est, l1)].append(((est, l2), costo, "transbordo"))

    def estados_iniciales(self, origen):
        return [(origen, linea) for linea in sorted(self.lineas_en[origen])]


def buscar(grafo, origen, destino, algoritmo="astar"):
    if origen in grafo.cerradas or destino in grafo.cerradas:
        return Resultado(algoritmo, False)
    if origen == destino:
        inicio = grafo.estados_iniciales(origen)
        return Resultado(algoritmo, True, inicio[:1], 0.0, 0, 0)

    if algoritmo == "astar":
        def h(s):
            return distancia_km(s[0], destino) / grafo.vmax_km_min
    else:
        def h(s):
            return 0.0

    if algoritmo == "bfs":
        def peso(costo, tipo):
            return 1.0
    else:
        def peso(costo, tipo):
            return costo

    contador = itertools.count()
    abierta, g, padre = [], {}, {}
    for s in grafo.estados_iniciales(origen):
        g[s], padre[s] = 0.0, None
        heapq.heappush(abierta, (h(s), next(contador), s))

    cerrado, expandidos, generados = set(), 0, 0
    while abierta:
        _, _, s = heapq.heappop(abierta)
        if s in cerrado:
            continue
        if s[0] == destino:
            camino = []
            while s is not None:
                camino.append(s)
                s = padre[s]
            camino.reverse()
            return Resultado(algoritmo, True, camino, _tiempo_real(grafo, camino),
                             expandidos, generados)
        cerrado.add(s)
        expandidos += 1
        for t, costo, tipo in grafo.vecinos[s]:
            ng = g[s] + peso(costo, tipo)
            if t not in g or ng < g[t]:
                g[t], padre[t] = ng, s
                generados += 1
                heapq.heappush(abierta, (ng + h(t), next(contador), t))
    return Resultado(algoritmo, False, [], 0.0, expandidos, generados)


def _tiempo_real(grafo, camino):
    total = 0.0
    for a, b in zip(camino, camino[1:]):
        total += min(c for t, c, _ in grafo.vecinos[a] if t == b)
    return total


def itinerario(res):
    """Agrupa el camino en tramos: [(línea, [estaciones...]), ...]."""
    tramos = []
    for est, linea in res.estados:
        if not tramos or tramos[-1][0] != linea:
            tramos.append((linea, [est]))
        elif tramos[-1][1][-1] != est:
            tramos[-1][1].append(est)
    return tramos

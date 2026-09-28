"""
motor_reglas.py
===============
Motor de inferencia con encadenamiento hacia adelante (forward chaining) para
un sistema basado en reglas (Benítez, 2014, cap. 2 y 3).

Representación del conocimiento
-------------------------------
* Un HECHO es una tupla:  ("parada", "Caracas", 3, "Calle 72")
  equivale al predicado    parada(Caracas, 3, Calle 72).
* Una REGLA tiene la forma  SI premisas Y condición ENTONCES conclusiones.
  Las premisas son patrones (tuplas) donde los elementos que empiezan por '?'
  son variables lógicas (?L, ?a, ...).
* Se soporta negación como fracaso: No(patron) es cierto si NO existe
  ningún hecho que unifique con el patrón (hipótesis de mundo cerrado).
"""
from collections import defaultdict


def es_variable(x):
    return isinstance(x, str) and x.startswith("?")


class No:
    """Premisa negada (negación como fracaso)."""

    def __init__(self, patron):
        self.patron = patron


class Regla:
    def __init__(self, nombre, si, entonces, condicion=None, descripcion=""):
        self.nombre = nombre
        self.si = si                                   # lista de premisas
        self.entonces = entonces                       # f(enlaces) -> [hechos]
        self.condicion = condicion or (lambda b: True)  # guarda aritmética
        self.descripcion = descripcion


class BaseHechos:
    """Memoria de trabajo: conjunto de hechos indexado por predicado."""

    def __init__(self):
        self.hechos = set()
        self.indice = defaultdict(set)

    def agregar(self, hecho):
        if hecho in self.hechos:
            return False
        self.hechos.add(hecho)
        self.indice[hecho[0]].add(hecho)
        return True

    def __len__(self):
        return len(self.hechos)


def _unificar(patron, hecho, enlaces):
    """Unifica un patrón con un hecho. Devuelve nuevos enlaces o None."""
    if len(patron) != len(hecho):
        return None
    nuevo = dict(enlaces)
    for p, v in zip(patron, hecho):
        if es_variable(p):
            if p in nuevo:
                if nuevo[p] != v:
                    return None
            else:
                nuevo[p] = v
        elif p != v:
            return None
    return nuevo


def _resolver(premisas, base, enlaces):
    """Genera todos los enlaces que satisfacen la lista de premisas."""
    if not premisas:
        yield dict(enlaces)
        return
    primera, resto = premisas[0], premisas[1:]
    if isinstance(primera, No):
        patron = tuple(enlaces.get(x, x) if es_variable(x) else x
                       for x in primera.patron)
        existe = any(_unificar(patron, h, {}) is not None
                     for h in base.indice[patron[0]])
        if not existe:
            yield from _resolver(resto, base, enlaces)
        return
    for hecho in list(base.indice[primera[0]]):
        nuevo = _unificar(primera, hecho, enlaces)
        if nuevo is not None:
            yield from _resolver(resto, base, nuevo)


class MotorInferencia:
    def __init__(self, reglas):
        self.reglas = reglas
        self.conteo = {r.nombre: 0 for r in reglas}   # hechos nuevos por regla
        self.origen = {}                              # hecho -> nombre de regla

    def inferir(self, base):
        """Aplica las reglas hasta alcanzar el punto fijo. Devuelve #rondas."""
        rondas = 0
        cambio = True
        while cambio:
            cambio = False
            rondas += 1
            for regla in self.reglas:
                for b in list(_resolver(regla.si, base, {})):
                    if not regla.condicion(b):
                        continue
                    for hecho in regla.entonces(b):
                        if base.agregar(hecho):
                            self.conteo[regla.nombre] += 1
                            self.origen[hecho] = regla.nombre
                            cambio = True
        return rondas

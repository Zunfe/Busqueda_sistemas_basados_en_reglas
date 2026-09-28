"""
main.py - Sistema inteligente de rutas para transporte masivo (TransMilenio).

Ejemplos:
    python main.py --listar
    python main.py --origen "Portal Norte" --destino "Portal Américas"
    python main.py -o "Portal 80" -d "Museo del Oro" --hora-pico
    python main.py -o "Minuto de Dios" -d "Av. Jiménez" --cerrar "Héroes"
    python main.py -o "Portal Suba" -d "Restrepo" --comparar --explicar
"""
import argparse
import difflib
import sys
import unicodedata

from base_conocimiento import LINEAS, COORDENADAS, construir_base, reglas
from motor_reglas import MotorInferencia
from busqueda import Grafo, buscar, itinerario


def _norm(texto):
    t = unicodedata.normalize("NFD", texto)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def resolver_estacion(texto):
    """Acepta nombres sin tildes/mayúsculas y coincidencias parciales únicas."""
    nombres = list(COORDENADAS)
    mapa = {_norm(n): n for n in nombres}
    clave = _norm(texto)
    if clave in mapa:
        return mapa[clave]
    parciales = [n for k, n in mapa.items() if clave in k]
    if len(parciales) == 1:
        return parciales[0]
    sugeridas = difflib.get_close_matches(clave, list(mapa), n=3, cutoff=0.5)
    sug = ", ".join(mapa[s] for s in sugeridas) or "use --listar"
    raise ValueError(f"Estación no reconocida: '{texto}'. ¿Quiso decir: {sug}?")


def preparar(cerradas=(), hora_pico=False, penalizacion=4.0):
    """Carga hechos, ejecuta el motor de reglas y construye el grafo."""
    base = construir_base(cerradas, hora_pico)
    motor = MotorInferencia(reglas(penalizacion))
    n_iniciales = len(base)
    rondas = motor.inferir(base)
    return base, motor, Grafo(base), n_iniciales, rondas


def formatear(res, origen, destino):
    if not res.encontrada:
        return f"[{res.algoritmo}] No existe ruta habilitada entre {origen} y {destino}."
    lineas = [f"[{res.algoritmo}] Ruta {origen} -> {destino}"]
    for i, (linea, ests) in enumerate(itinerario(res), start=1):
        if len(ests) == 1:
            lineas.append(f"  {i}. Permanezca en {ests[0]} (línea {linea})")
        else:
            lineas.append(f"  {i}. Línea {linea}: " + " -> ".join(ests))
    lineas.append(f"  Tiempo estimado : {res.minutos:.1f} min")
    lineas.append(f"  Estaciones      : {res.estaciones_recorridas} tramos | Transbordos: {res.transbordos}")
    lineas.append(f"  Nodos expandidos: {res.expandidos} | generados: {res.generados}")
    return "\n".join(lineas)


def explicar(motor, base, n_iniciales, rondas):
    out = [f"Hechos iniciales: {n_iniciales} | totales tras inferencia: {len(base)} | rondas: {rondas}",
           "Reglas disparadas (hechos nuevos deducidos):"]
    for r in motor.reglas:
        out.append(f"  {r.nombre:<24} {motor.conteo[r.nombre]:>4}   {r.descripcion}")
    hubs = sorted(h[1] for h in base.indice["hub"])
    out.append(f"Estaciones de transbordo (hub) deducidas: {', '.join(hubs)}")
    return "\n".join(out)


def listar():
    out = []
    for linea, (vel, ests) in LINEAS.items():
        out.append(f"{linea} ({vel} km/h): " + " - ".join(ests))
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Planificador de rutas TransMilenio (reglas + A*)")
    p.add_argument("-o", "--origen")
    p.add_argument("-d", "--destino")
    p.add_argument("--cerrar", action="append", default=[], help="estación fuera de servicio (repetible)")
    p.add_argument("--hora-pico", action="store_true")
    p.add_argument("--algoritmo", choices=["astar", "dijkstra", "bfs"], default="astar")
    p.add_argument("--comparar", action="store_true", help="ejecuta los tres algoritmos")
    p.add_argument("--explicar", action="store_true", help="muestra la inferencia de reglas")
    p.add_argument("--penalizacion-transbordo", type=float, default=4.0)
    p.add_argument("--listar", action="store_true")
    a = p.parse_args(argv)

    if a.listar:
        print(listar())
        return 0
    if not a.origen or not a.destino:
        p.error("se requieren --origen y --destino (o use --listar)")
    try:
        o, d = resolver_estacion(a.origen), resolver_estacion(a.destino)
        cerradas = [resolver_estacion(c) for c in a.cerrar]
    except ValueError as e:
        print(e)
        return 2

    base, motor, grafo, n0, rondas = preparar(cerradas, a.hora_pico, a.penalizacion_transbordo)
    if cerradas or a.hora_pico:
        print(f"Contexto: cerradas={cerradas or 'ninguna'} | hora pico={a.hora_pico}")
    if a.explicar:
        print(explicar(motor, base, n0, rondas))
    algos = ["astar", "dijkstra", "bfs"] if a.comparar else [a.algoritmo]
    for alg in algos:
        print(formatear(buscar(grafo, o, d, alg), o, d))
    return 0


if __name__ == "__main__":
    sys.exit(main())

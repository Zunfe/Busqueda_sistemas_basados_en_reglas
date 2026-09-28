"""
base_conocimiento.py
====================
Base de conocimiento (hechos + reglas lógicas) de una red SIMPLIFICADA del
sistema TransMilenio de Bogotá.

AVISO: la topología, las velocidades y las coordenadas son aproximadas y con
fines didácticos. Para uso real deben validarse con el mapa oficial.

HECHOS (extensionales)
    estacion(E, lat, lon)      parada(L, n, E)  -> la línea L pasa por E en la posición n
    velocidad(L, km/h)         cerrada(E)       -> estación fuera de servicio
    hora_pico()                -> contexto de hora pico

REGLAS (intensionales) -> ver función reglas()
"""
import math
from motor_reglas import BaseHechos, Regla, No

# --- Parámetros del modelo ---------------------------------------------------
TIEMPO_PARADA_MIN = 0.75            # minutos de detención en cada estación
PENALIZACION_TRANSBORDO_MIN = 4.0   # caminata + espera al cambiar de línea
FACTOR_HORA_PICO = 1.35             # el tiempo de viaje aumenta en hora pico

# --- Líneas (troncales): velocidad comercial y estaciones en orden -----------
LINEAS = {
    "Autonorte": (28, ["Portal Norte", "Toberín", "Calle 127", "Calle 100", "Héroes"]),
    "Caracas": (22, ["Héroes", "Calle 76", "Calle 72", "Calle 45", "Calle 26",
                     "Av. Jiménez", "Hospital", "Restrepo"]),
    "Calle 80": (26, ["Portal 80", "Minuto de Dios", "Boyacá", "Av. 68", "Polo", "Héroes"]),
    "Calle 26": (26, ["Portal Eldorado", "Av. Rojas", "Salitre El Greco", "CAN",
                      "Corferias", "Ciudad Universitaria", "Concejo de Bogotá",
                      "Universidades"]),
    "Eje Ambiental": (18, ["Universidades", "Las Aguas", "Museo del Oro", "Av. Jiménez"]),
    "Américas": (26, ["Portal Américas", "Mandalay", "Marsella", "Puente Aranda",
                      "Ricaurte", "Paloquemao", "Av. Jiménez"]),
    "NQS Central": (26, ["Polo", "Movistar Arena", "Campín", "Ciudad Universitaria", "Ricaurte"]),
    "Suba": (25, ["Portal Suba", "Gratamira", "Av. Suba", "Rio Negro", "Calle 100"]),
}

# --- Coordenadas aproximadas (lat, lon) --------------------------------------
COORDENADAS = {
    "Portal Norte": (4.7540, -74.0455), "Toberín": (4.7430, -74.0460),
    "Calle 127": (4.7120, -74.0555), "Calle 100": (4.6850, -74.0575),
    "Héroes": (4.6735, -74.0620), "Calle 76": (4.6680, -74.0610),
    "Calle 72": (4.6600, -74.0620), "Calle 45": (4.6330, -74.0650),
    "Calle 26": (4.6170, -74.0680), "Av. Jiménez": (4.6010, -74.0710),
    "Hospital": (4.5915, -74.0800), "Restrepo": (4.5830, -74.0975),
    "Portal 80": (4.7230, -74.1130), "Minuto de Dios": (4.6980, -74.0930),
    "Boyacá": (4.6940, -74.0850), "Av. 68": (4.6900, -74.0790),
    "Polo": (4.6800, -74.0700),
    "Portal Eldorado": (4.6560, -74.1290), "Av. Rojas": (4.6520, -74.1120),
    "Salitre El Greco": (4.6500, -74.1020), "CAN": (4.6460, -74.0940),
    "Corferias": (4.6420, -74.0900), "Ciudad Universitaria": (4.6350, -74.0840),
    "Concejo de Bogotá": (4.6270, -74.0800), "Universidades": (4.6080, -74.0690),
    "Las Aguas": (4.6030, -74.0680), "Museo del Oro": (4.6020, -74.0720),
    "Portal Américas": (4.6190, -74.1560), "Mandalay": (4.6250, -74.1420),
    "Marsella": (4.6290, -74.1300), "Puente Aranda": (4.6200, -74.1120),
    "Ricaurte": (4.6125, -74.0940), "Paloquemao": (4.6110, -74.0860),
    "Movistar Arena": (4.6520, -74.0770), "Campín": (4.6440, -74.0790),
    "Portal Suba": (4.7450, -74.0930), "Gratamira": (4.7280, -74.0850),
    "Av. Suba": (4.7040, -74.0760), "Rio Negro": (4.6900, -74.0680),
}


def distancia_km(a, b):
    """Distancia de círculo máximo (haversine) entre dos estaciones, en km."""
    lat1, lon1 = map(math.radians, COORDENADAS[a])
    lat2, lon2 = map(math.radians, COORDENADAS[b])
    h = (math.sin((lat2 - lat1) / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def construir_base(cerradas=(), hora_pico=False):
    """Carga los HECHOS iniciales (conocimiento extensional)."""
    base = BaseHechos()
    for nombre, (lat, lon) in COORDENADAS.items():
        base.agregar(("estacion", nombre, lat, lon))
    for linea, (vel, paradas) in LINEAS.items():
        base.agregar(("velocidad", linea, vel))
        for i, est in enumerate(paradas, start=1):
            base.agregar(("parada", linea, i, est))
    for est in cerradas:
        base.agregar(("cerrada", est))
    if hora_pico:
        base.agregar(("hora_pico",))
    return base


def reglas(penalizacion_transbordo=PENALIZACION_TRANSBORDO_MIN):
    """Reglas lógicas (conocimiento intensional)."""

    def minutos(b, factor):
        d = distancia_km(b["?a"], b["?b"])
        return (d / b["?v"]) * 60.0 * factor + TIEMPO_PARADA_MIN

    return [
        Regla("R1_adyacente",
              si=[("parada", "?L", "?i", "?a"), ("parada", "?L", "?j", "?b")],
              condicion=lambda b: b["?j"] == b["?i"] + 1,
              entonces=lambda b: [("adyacente", b["?a"], b["?b"], b["?L"])],
              descripcion="parada(L,i,a) Y parada(L,j,b) Y j=i+1  =>  adyacente(a,b,L)"),

        Regla("R2_tramo_bidireccional",
              si=[("adyacente", "?a", "?b", "?L")],
              entonces=lambda b: [("tramo", b["?a"], b["?b"], b["?L"]),
                                  ("tramo", b["?b"], b["?a"], b["?L"])],
              descripcion="adyacente(a,b,L)  =>  tramo(a,b,L) Y tramo(b,a,L)"),

        Regla("R3_enlace_transbordo",
              si=[("parada", "?L1", "?i", "?E"), ("parada", "?L2", "?j", "?E")],
              condicion=lambda b: b["?L1"] != b["?L2"],
              entonces=lambda b: [("enlace", b["?E"], b["?L1"], b["?L2"])],
              descripcion="parada(L1,_,E) Y parada(L2,_,E) Y L1<>L2  =>  enlace(E,L1,L2)"),

        Regla("R4_estacion_hub",
              si=[("enlace", "?E", "?L1", "?L2")],
              entonces=lambda b: [("hub", b["?E"])],
              descripcion="enlace(E,L1,L2)  =>  hub(E)"),

        Regla("R5_tramo_habilitado",
              si=[("tramo", "?a", "?b", "?L"), No(("cerrada", "?a")), No(("cerrada", "?b"))],
              entonces=lambda b: [("habilitado", b["?a"], b["?b"], b["?L"])],
              descripcion="tramo(a,b,L) Y NO cerrada(a) Y NO cerrada(b)  =>  habilitado(a,b,L)"),

        Regla("R6_costo_normal",
              si=[("habilitado", "?a", "?b", "?L"), ("velocidad", "?L", "?v"),
                  No(("hora_pico",))],
              entonces=lambda b: [("costo", b["?a"], b["?b"], b["?L"], minutos(b, 1.0))],
              descripcion="habilitado(a,b,L) Y velocidad(L,v) Y NO hora_pico  =>  costo(a,b,L,d/v+parada)"),

        Regla("R7_costo_hora_pico",
              si=[("habilitado", "?a", "?b", "?L"), ("velocidad", "?L", "?v"),
                  ("hora_pico",)],
              entonces=lambda b: [("costo", b["?a"], b["?b"], b["?L"],
                                   minutos(b, FACTOR_HORA_PICO))],
              descripcion="habilitado(a,b,L) Y velocidad(L,v) Y hora_pico  =>  costo(a,b,L,1.35*d/v+parada)"),

        Regla("R8_transbordo_posible",
              si=[("enlace", "?E", "?L1", "?L2"), No(("cerrada", "?E"))],
              entonces=lambda b: [("transbordo_ok", b["?E"], b["?L1"], b["?L2"],
                                   penalizacion_transbordo)],
              descripcion="enlace(E,L1,L2) Y NO cerrada(E)  =>  transbordo_ok(E,L1,L2,penalización)"),
    ]

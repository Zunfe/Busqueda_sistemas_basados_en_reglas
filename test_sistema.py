"""
test_sistema.py - Pruebas automáticas.   Ejecutar:  python -m unittest -v test_sistema
"""
import itertools
import unittest

from base_conocimiento import LINEAS, COORDENADAS, distancia_km
from main import preparar, resolver_estacion
from busqueda import buscar, itinerario


class TestBaseConocimiento(unittest.TestCase):
    def test_todas_las_paradas_tienen_coordenadas(self):
        for linea, (_, ests) in LINEAS.items():
            for e in ests:
                self.assertIn(e, COORDENADAS, f"{e} ({linea}) sin coordenadas")

    def test_reglas_deducen_hubs(self):
        base, *_ = preparar()
        hubs = {h[1] for h in base.indice["hub"]}
        self.assertEqual(hubs, {"Héroes", "Av. Jiménez", "Polo", "Ricaurte",
                                "Ciudad Universitaria", "Universidades", "Calle 100"})

    def test_tramos_son_bidireccionales(self):
        base, *_ = preparar()
        self.assertIn(("tramo", "Calle 72", "Calle 76", "Caracas"), base.hechos)
        self.assertIn(("tramo", "Calle 76", "Calle 72", "Caracas"), base.hechos)

    def test_estacion_cerrada_deshabilita_tramos_y_transbordos(self):
        base, *_ = preparar(cerradas=["Héroes"])
        for h in base.indice["habilitado"]:
            self.assertNotIn("Héroes", h[1:3])
        self.assertFalse(any(h[1] == "Héroes" for h in base.indice["transbordo_ok"]))

    def test_hora_pico_aumenta_costos(self):
        normal, *_ = preparar()
        pico, *_ = preparar(hora_pico=True)
        cn = {h[1:4]: h[4] for h in normal.indice["costo"]}
        cp = {h[1:4]: h[4] for h in pico.indice["costo"]}
        self.assertEqual(cn.keys(), cp.keys())
        self.assertTrue(all(cp[k] > cn[k] for k in cn))


class TestBusqueda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafo = preparar()[2]

    def test_ruta_simple_una_linea(self):
        r = buscar(self.grafo, "Portal Norte", "Héroes")
        self.assertTrue(r.encontrada)
        self.assertEqual(r.transbordos, 0)
        self.assertEqual([e for e, _ in r.estados][0], "Portal Norte")
        self.assertEqual(r.estados[-1][0], "Héroes")

    def test_origen_igual_destino(self):
        r = buscar(self.grafo, "Polo", "Polo")
        self.assertTrue(r.encontrada)
        self.assertEqual(r.minutos, 0.0)

    def test_astar_es_optimo_y_expande_menos_o_igual_que_dijkstra(self):
        """Para TODOS los pares origen-destino A* debe igualar el costo de Dijkstra."""
        estaciones = list(COORDENADAS)
        for o, d in itertools.permutations(estaciones, 2):
            a = buscar(self.grafo, o, d, "astar")
            u = buscar(self.grafo, o, d, "dijkstra")
            self.assertTrue(a.encontrada and u.encontrada, f"{o}->{d}")
            self.assertAlmostEqual(a.minutos, u.minutos, places=6, msg=f"{o}->{d}")
            self.assertLessEqual(a.expandidos, u.expandidos, f"{o}->{d}")

    def test_heuristica_admisible(self):
        """h(n) nunca supera el costo real óptimo hasta el destino."""
        destino = "Portal Américas"
        for e in COORDENADAS:
            real = buscar(self.grafo, e, destino, "dijkstra").minutos
            h = distancia_km(e, destino) / self.grafo.vmax_km_min
            self.assertLessEqual(h, real + 1e-9, e)

    def test_bfs_minimiza_pasos_no_tiempo(self):
        for o, d in [("Portal Norte", "Portal Américas"), ("Portal Suba", "Restrepo"),
                     ("Portal 80", "Universidades")]:
            b = buscar(self.grafo, o, d, "bfs")
            u = buscar(self.grafo, o, d, "dijkstra")
            self.assertLessEqual(len(b.estados), len(u.estados))
            self.assertGreaterEqual(b.minutos, u.minutos - 1e-9)

    def test_itinerario_agrupa_por_linea(self):
        r = buscar(self.grafo, "Minuto de Dios", "Av. Jiménez")
        self.assertEqual([l for l, _ in itinerario(r)], ["Calle 80", "Caracas"])
        self.assertEqual(r.transbordos, 1)


class TestEscenariosDinamicos(unittest.TestCase):
    def test_cierre_de_estacion_reencamina(self):
        g0 = preparar()[2]
        g1 = preparar(cerradas=["Héroes"])[2]
        r0 = buscar(g0, "Minuto de Dios", "Av. Jiménez")
        r1 = buscar(g1, "Minuto de Dios", "Av. Jiménez")
        self.assertTrue(r1.encontrada)
        self.assertNotIn("Héroes", [e for e, _ in r1.estados])
        self.assertGreater(r1.minutos, r0.minutos)

    def test_sin_ruta_cuando_se_parte_la_red(self):
        g = preparar(cerradas=["Calle 100"])[2]
        self.assertFalse(buscar(g, "Portal Suba", "Restrepo").encontrada)

    def test_origen_cerrado(self):
        g = preparar(cerradas=["Polo"])[2]
        self.assertFalse(buscar(g, "Polo", "Héroes").encontrada)

    def test_hora_pico_aumenta_tiempo_total(self):
        r0 = buscar(preparar()[2], "Portal 80", "Museo del Oro")
        r1 = buscar(preparar(hora_pico=True)[2], "Portal 80", "Museo del Oro")
        self.assertGreater(r1.minutos, r0.minutos)

    def test_mayor_penalizacion_reduce_transbordos(self):
        g_bajo = preparar(penalizacion=0.0)[2]
        g_alto = preparar(penalizacion=30.0)[2]
        r_bajo = buscar(g_bajo, "Portal Norte", "Portal Américas")
        r_alto = buscar(g_alto, "Portal Norte", "Portal Américas")
        self.assertLessEqual(r_alto.transbordos, r_bajo.transbordos)


class TestEntrada(unittest.TestCase):
    def test_nombres_sin_tildes_y_parciales(self):
        self.assertEqual(resolver_estacion("heroes"), "Héroes")
        self.assertEqual(resolver_estacion("portal americas"), "Portal Américas")
        self.assertEqual(resolver_estacion("museo"), "Museo del Oro")

    def test_estacion_invalida(self):
        with self.assertRaises(ValueError):
            resolver_estacion("Estación Fantasma")


if __name__ == "__main__":
    unittest.main(verbosity=2)

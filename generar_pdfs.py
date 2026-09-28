"""
generar_pdfs.py - Ejecuta los escenarios de prueba REALES y genera:
    docs/Pruebas_realizadas.pdf   (evidencia de pruebas)
    docs/Entrega_actividad.pdf    (documento de entrega con enlaces a completar)
Requiere:  pip install reportlab      Ejecutar desde la raíz:  python docs/generar_pdfs.py
"""
import os
import subprocess
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Preformatted,
                                Table, TableStyle, PageBreak)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(RAIZ, "docs")

ESCENARIOS = [
    ("P1", "Ruta directa, una sola línea",
     ["-o", "Portal Norte", "-d", "Héroes"],
     "Ruta por Autonorte, 0 transbordos."),
    ("P2", "Ruta con un transbordo",
     ["-o", "Minuto de Dios", "-d", "Av. Jiménez"],
     "Calle 80 -> Caracas con transbordo en Héroes."),
    ("P3", "Ruta larga y comparación de algoritmos",
     ["-o", "Portal Norte", "-d", "Portal Américas", "--comparar"],
     "A* y Dijkstra con igual tiempo; A* expande menos nodos."),
    ("P4", "Estación cerrada: reencaminamiento",
     ["-o", "Minuto de Dios", "-d", "Av. Jiménez", "--cerrar", "Héroes"],
     "Ruta alterna por NQS Central y Américas, más lenta que P2."),
    ("P5", "Hora pico",
     ["-o", "Portal 80", "-d", "Museo del Oro", "--hora-pico"],
     "Mismo recorrido pero con mayor tiempo estimado."),
    ("P6", "Red partida: no existe ruta",
     ["-o", "Portal Suba", "-d", "Restrepo", "--cerrar", "Calle 100"],
     "El sistema informa que no hay ruta habilitada."),
    ("P7", "Entrada inválida con sugerencia",
     ["-o", "Portal Amerikas", "-d", "Héroes"],
     "Mensaje de error con sugerencias de nombre."),
    ("P8", "Explicación de la inferencia (reglas)",
     ["-o", "Portal Suba", "-d", "Portal Suba", "--explicar"],
     "Muestra hechos iniciales/deducidos y reglas disparadas."),
]


def ejecutar(args):
    r = subprocess.run([sys.executable, "main.py"] + args, cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8")
    return (r.stdout + r.stderr).rstrip()


def estilos():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Cod", parent=s["Code"], fontSize=7.4, leading=9,
                         backColor=colors.HexColor("#f3f4f6"), borderPadding=4))
    return s


def pdf_pruebas():
    s = estilos()
    h = []
    h.append(Paragraph("Documento de pruebas realizadas", s["Title"]))
    h.append(Paragraph("Sistema inteligente de rutas para transporte masivo (TransMilenio, Bogotá) "
                       "- reglas lógicas + búsqueda heurística A*", s["Normal"]))
    h.append(Spacer(1, 10))
    h.append(Paragraph("1. Pruebas de escenarios (línea de comandos)", s["Heading2"]))
    h.append(Paragraph("Cada escenario se ejecutó con <font face='Courier'>python main.py</font>. "
                       "La salida mostrada es la real, generada automáticamente por "
                       "<font face='Courier'>docs/generar_pdfs.py</font>.", s["Normal"]))
    h.append(Spacer(1, 6))
    for cod, titulo, args, esperado in ESCENARIOS:
        comando = "python main.py " + " ".join(f'"{a}"' if " " in a else a for a in args)
        h.append(Paragraph(f"{cod}. {escape(titulo)}", s["Heading3"]))
        h.append(Paragraph(f"<b>Resultado esperado:</b> {escape(esperado)}", s["Normal"]))
        h.append(Preformatted("$ " + comando + "\n" + ejecutar(args), s["Cod"]))
        h.append(Spacer(1, 6))
    h.append(PageBreak())
    h.append(Paragraph("2. Pruebas unitarias automáticas", s["Heading2"]))
    r = subprocess.run([sys.executable, "-m", "unittest", "test_sistema", "-v"], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8")
    salida = (r.stdout + r.stderr).replace("\n\n", "\n")
    h.append(Preformatted("$ python -m unittest -v test_sistema\n" + salida, s["Cod"]))
    h.append(Spacer(1, 8))
    h.append(Paragraph("3. Propiedades verificadas", s["Heading2"]))
    filas = [["Propiedad", "Cómo se verificó"],
             ["Optimalidad de A*", "Mismo costo que Dijkstra en los 1.482 pares origen-destino"],
             ["Eficiencia de A*", "Nodos expandidos de A* <= Dijkstra en todos los pares"],
             ["Heurística admisible", "h(n) <= costo real óptimo hasta el destino, todas las estaciones"],
             ["Reglas lógicas", "Hubs, tramos bidireccionales, cierres y hora pico deducidos correctamente"],
             ["Robustez", "Origen cerrado, red partida, entradas inválidas y origen = destino"]]
    t = Table(filas, colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    h.append(t)
    SimpleDocTemplate(os.path.join(DOCS, "Pruebas_realizadas.pdf"), pagesize=letter,
                      leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                      bottomMargin=2 * cm, title="Pruebas realizadas").build(h)


def pdf_entrega():
    s = estilos()
    P = lambda t, st="Normal": Paragraph(t, s[st])
    h = [P("Entrega de la actividad: sistema inteligente de rutas", "Title"),
         P("Unidad: sistemas basados en conocimiento y búsqueda heurística"), Spacer(1, 8),
         P("1. Integrantes del equipo (máximo 4)", "Heading2"),
         P("[COMPLETAR] Nombre 1 - usuario Git"), P("[COMPLETAR] Nombre 2 - usuario Git"),
         P("[COMPLETAR] Nombre 3 - usuario Git"), P("[COMPLETAR] Nombre 4 - usuario Git"),
         P("2. Enlaces de entrega", "Heading2"),
         P("<b>Repositorio Git/GitLab:</b> [COMPLETAR: https://...]  "
           "(el tutor fue agregado como colaborador: [COMPLETAR: usuario del tutor])"),
         P("<b>Video (máx. 10 min):</b> [COMPLETAR: https://...]"),
         P("3. Contenido del repositorio", "Heading2"),
         P("- <b>Código fuente y ejecución:</b> main.py, motor_reglas.py, base_conocimiento.py, "
           "busqueda.py y README.md (instrucciones de instalación y uso)."),
         P("- <b>Pruebas:</b> test_sistema.py y docs/Pruebas_realizadas.pdf."),
         P("- <b>Guion del video:</b> docs/guion_video.md."),
         P("4. Resumen técnico", "Heading2"),
         P("<b>Representación del conocimiento (cap. 2):</b> hechos en forma de predicados "
           "(estacion, parada, velocidad, cerrada, hora_pico) almacenados en una base de hechos."),
         P("<b>Sistema basado en reglas (cap. 3):</b> 8 reglas SI-ENTONCES con variables, guardas y "
           "negación como fracaso, ejecutadas por encadenamiento hacia adelante hasta el punto fijo. "
           "Deducen tramos, transbordos, estaciones hub, tramos habilitados y costos en minutos."),
         P("<b>Búsqueda heurística (cap. 9):</b> A* sobre estados (estación, línea) con "
           "h = distancia haversine / velocidad máxima, admisible y consistente. Se compara con "
           "Dijkstra (h=0) y BFS (mínimo de pasos)."),
         P("<b>Limitaciones:</b> la red, velocidades y coordenadas son una simplificación "
           "didáctica de TransMilenio; no usa datos en tiempo real ni rutas zonales/duales."),
         P("5. Evidencia del trabajo en equipo", "Heading2"),
         P("El log de Git (<font face='Courier'>git log --format='%an %ad %s'</font>) muestra "
           "los commits de cada integrante. [COMPLETAR: pegar salida o captura]")]
    SimpleDocTemplate(os.path.join(DOCS, "Entrega_actividad.pdf"), pagesize=letter,
                      leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                      bottomMargin=2 * cm, title="Entrega de la actividad").build(h)


if __name__ == "__main__":
    pdf_pruebas()
    pdf_entrega()
    print("PDF generados en", DOCS)

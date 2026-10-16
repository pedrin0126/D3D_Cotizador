"""Cotizador D3D - impresión 3D.

Precio = (gramos x $/g + horas x $/h) x multiplicador + extras, redondeado.
"""
from datetime import date, timedelta

import streamlit as st
from fpdf import FPDF

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
TEAL = (15, 123, 138)
INK = (23, 32, 42)
GRAY = (91, 104, 117)


def cop(n: float) -> str:
    return "$" + f"{round(n):,}".replace(",", ".")


def md(texto: str) -> str:
    """Escapa $ para que Streamlit no lo tome como fórmula matemática."""
    return texto.replace("$", "\\$")


def fecha_txt(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def num_txt(n: float, dec: int = 1) -> str:
    s = f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def calcular(g, horas, pg, ph, mult, extras, redondeo, abono_pct):
    material = g * pg
    maquina = horas * ph
    base = material + maquina
    sub = base * mult
    total = sub + extras
    if redondeo > 0:
        total = round(total / redondeo) * redondeo
    abono = total * abono_pct / 100
    return dict(material=material, maquina=maquina, base=base, sub=sub,
                total=total, abono=abono, saldo=total - abono)


def generar_pdf(d: dict) -> bytes:
    pdf = FPDF(format="letter", unit="mm")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    W = pdf.w
    L, R = 20, W - 20

    # Encabezado
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, W, 34, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 30)
    pdf.text(L, 22, "D3D")
    pdf.set_font("helvetica", "", 10)
    pdf.text(L + 28, 22, "Impresión 3D")
    pdf.set_font("helvetica", "B", 14)
    pdf.text(R - pdf.get_string_width("COTIZACIÓN"), 17, "COTIZACIÓN")
    pdf.set_font("helvetica", "", 10)
    pdf.text(R - pdf.get_string_width(d["numero"]), 24, d["numero"])

    def par(label, valor, x, y):
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*GRAY)
        pdf.text(x, y, label.upper())
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(*INK)
        pdf.text(x, y + 6, valor or "-")

    y = 50
    par("Fecha", fecha_txt(d["fecha"]), L, y)
    par("Válida hasta", fecha_txt(d["fecha"] + timedelta(days=d["validez"])), W / 2, y)
    y += 16
    par("Cliente", d["cliente"], L, y)
    par("Cotizado por", d["cotizador"], W / 2, y)
    y += 22

    # Tabla
    pdf.set_fill_color(238, 241, 243)
    pdf.rect(L, y, R - L, 9, "F")
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*GRAY)
    pdf.text(L + 3, y + 6, "DESCRIPCIÓN")
    pdf.text(R - 3 - pdf.get_string_width("VALOR"), y + 6, "VALOR")
    y += 11

    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*INK)
    pdf.set_xy(L + 2, y)
    pdf.multi_cell(R - L - 55, 5.5, d["descripcion"] or "Servicio de impresión 3D")
    y_fin = pdf.get_y()
    valor_imp = cop(d["total"] - d["extras"])
    pdf.text(R - 3 - pdf.get_string_width(valor_imp), y + 4, valor_imp)
    y = y_fin + 4
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*GRAY)
    pdf.text(L + 3, y, f"Material: {num_txt(d['g'], 0)} g  ·  Tiempo de impresión: {num_txt(d['horas'])} h")
    y += 8
    if d["extras"] > 0:
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(*INK)
        pdf.text(L + 3, y, "Diseño y acabados")
        v = cop(d["extras"])
        pdf.text(R - 3 - pdf.get_string_width(v), y, v)
        y += 8
    pdf.set_draw_color(213, 220, 226)
    pdf.line(L, y, R, y)
    y += 10

    # Totales
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*INK)
    pdf.text(R - 70, y, "TOTAL")
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(*TEAL)
    v = cop(d["total"])
    pdf.text(R - 3 - pdf.get_string_width(v), y, v)
    y += 9
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*INK)
    for etiqueta, valor in ((f"Abono para iniciar ({d['abono_pct']:g}%)", d["abono"]),
                            ("Saldo a la entrega", d["saldo"])):
        pdf.text(R - 70, y, etiqueta)
        v = cop(valor)
        pdf.text(R - 3 - pdf.get_string_width(v), y, v)
        y += 6
    y += 14

    # Condiciones
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*GRAY)
    pdf.text(L, y, "CONDICIONES")
    y += 5
    pdf.set_font("helvetica", "", 9)
    notas = []
    if d["entrega"] > 0:
        s = "" if d["entrega"] == 1 else "s"
        notas.append(f"Entrega estimada: {d['entrega']} día{s} después de recibir el abono.")
    notas.append(f"Cotización válida por {d['validez']} días.")
    notas.append("Los tiempos y el material son estimados del software de laminado y pueden variar ligeramente.")
    for n in notas:
        pdf.text(L, y, "- " + n)
        y += 5

    # Pie
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.8)
    pdf.line(L, 262, R, 262)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*GRAY)
    pdf.text(L, 268, "D3D · Impresión 3D")
    pdf.text(R - pdf.get_string_width(d["cotizador"]), 268, d["cotizador"])
    return bytes(pdf.output())


# ---------------- Interfaz ----------------
st.set_page_config(page_title="Cotizador D3D", page_icon="🧮", layout="centered")
st.title("Cotizador D3D")
st.caption("Precio = (gramos × \\$/g + horas × \\$/h) × multiplicador + extras")

with st.container(border=True):
    st.subheader("Datos de la cotización", divider=False)
    c1, c2 = st.columns(2)
    cotizador = c1.text_input("Cotizado por", value="Diego")
    fecha = c2.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")
    c1, c2 = st.columns(2)
    cliente = c1.text_input("Cliente", placeholder="Ej: Lindsay")
    numero = c2.text_input("N.º cotización", value="D3D-001")
    descripcion = st.text_input("Descripción del trabajo",
                                placeholder="Ej: 3 bloques y losas para maqueta, PLA blanco")
    c1, c2 = st.columns(2)
    validez = c1.number_input("Validez (días)", min_value=1, value=15, step=1)
    entrega = c2.number_input("Entrega estimada (días)", min_value=0, value=2, step=1)

with st.container(border=True):
    st.subheader("Datos del slicer", divider=False)
    c1, c2, c3 = st.columns(3)
    g = c1.number_input("Filamento (g)", min_value=0.0, value=590.0, step=1.0)
    h = c2.number_input("Horas", min_value=0, value=25, step=1)
    m = c3.number_input("Minutos", min_value=0, max_value=59, value=0, step=1)
    st.caption("Escribe el tiempo como lo da el slicer (12 h 34 min). La app lo pasa a horas decimales.")

with st.container(border=True):
    st.subheader("Tarifas", divider=False)
    c1, c2 = st.columns(2)
    pg = c1.number_input("Material (\\$/g)", min_value=0.0, value=100.0, step=5.0)
    ph = c2.number_input("Máquina (\\$/h)", min_value=0.0, value=1500.0, step=100.0)
    opciones = {"3 · competitivo": 3.0, "3,5 · normal": 3.5, "4 · urgente/difícil": 4.0, "Otro": None}
    elegido = st.radio("Multiplicador", list(opciones), index=2, horizontal=True)
    mult = opciones[elegido]
    if mult is None:
        mult = st.number_input("Multiplicador personalizado", min_value=0.0, value=4.0, step=0.1)
    c1, c2, c3 = st.columns(3)
    extras = c1.number_input("Extras (\\$)", min_value=0, value=0, step=1000,
                             help="Diseño, lijado, pintura, ensamble")
    redondeo = c2.number_input("Redondear a (\\$)", min_value=0, value=1000, step=100)
    abono_pct = c3.number_input("Abono (%)", min_value=0, max_value=100, value=50, step=5)

horas = h + m / 60
r = calcular(g, horas, pg, ph, mult, extras, redondeo, abono_pct)

with st.container(border=True):
    st.subheader("Desglose", divider=False)
    st.markdown(md(
        f"""
| Concepto | Cálculo | Valor |
|---|---|--:|
| Material | {num_txt(g, 2)} g × {cop(pg)} | {cop(r['material'])} |
| Máquina | {num_txt(horas, 2)} h × {cop(ph)} | {cop(r['maquina'])} |
| **Costo base** | | **{cop(r['base'])}** |
| × multiplicador | × {num_txt(mult, 2)} | {cop(r['sub'])} |
| + Extras | | {cop(extras)} |
"""
    ))

c1, c2, c3 = st.columns(3)
c1.metric("Precio a cotizar", cop(r["total"]))
c2.metric(f"Abono {abono_pct}%", cop(r["abono"]))
c3.metric("Saldo a la entrega", cop(r["saldo"]))

datos = dict(numero=numero.strip() or "D3D", fecha=fecha, validez=int(validez), entrega=int(entrega),
             cliente=cliente.strip(), cotizador=cotizador.strip(), descripcion=descripcion.strip(),
             g=g, horas=horas, extras=extras, abono_pct=abono_pct, **r)
nombre_pdf = f"Cotizacion {datos['numero']}" + (f" - {datos['cliente']}" if datos["cliente"] else "") + ".pdf"

st.download_button("Descargar PDF D3D", data=generar_pdf(datos), file_name=nombre_pdf,
                   mime="application/pdf", type="primary", use_container_width=True)

texto = "\n".join(x for x in [
    f"Cotización D3D {datos['numero']}" + (f" – {datos['cliente']}" if datos["cliente"] else ""),
    f"Fecha: {fecha_txt(fecha)}",
    f"Material: {num_txt(g, 0)} g · Tiempo: {num_txt(horas)} h",
    f"Incluye diseño/acabados: {cop(extras)}" if extras > 0 else None,
    f"Total: {cop(r['total'])}",
    f"Abono para iniciar: {cop(r['abono'])} · Saldo a la entrega: {cop(r['saldo'])}",
] if x)
with st.expander("Texto para WhatsApp"):
    st.code(texto, language=None)

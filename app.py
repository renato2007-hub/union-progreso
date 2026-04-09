import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import json
import io

# ─── PDF GENERATOR ─────────────────────────────────────────────────────────────
def generar_pdf_partido(pid):
    """Genera PDF completo del partido. Retorna bytes o None si no existe."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, HRFlowable, KeepTogether)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    # ── Paleta ──────────────────────────────────────────────────────────
    ROJO   = colors.HexColor("#9b2335")
    ROJO_L = colors.HexColor("#f5e8ea")
    AMAR   = colors.HexColor("#f0c040")
    AMAR_L = colors.HexColor("#fdf7e0")
    GRIS   = colors.HexColor("#555555")
    GRIS_L = colors.HexColor("#f4f4f4")
    VERDE  = colors.HexColor("#1a7a2e")
    VERDE_L= colors.HexColor("#e8f5ec")
    NEG    = colors.HexColor("#ff4444")
    BLANCO = colors.white

    W = 17*cm   # ancho útil de la página (A4 = 21cm - 4cm márgenes)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.8*cm, bottomMargin=1.8*cm,
                            title="Informe de Partido - Union y Progreso")

    # ── Estilos ──────────────────────────────────────────────────────────
    SS = getSampleStyleSheet()

    def E(name, base='Normal', **kw):
        return ParagraphStyle(name, parent=SS[base], **kw)

    sT  = E('sT',  'Title',   fontSize=20, textColor=ROJO, alignment=TA_CENTER,
             spaceAfter=2, leading=24)
    sSub= E('sSub','Normal',  fontSize=10, textColor=GRIS, alignment=TA_CENTER,
             spaceAfter=0, leading=14)
    sSec= E('sSec','Normal',  fontSize=11, textColor=BLANCO, fontName='Helvetica-Bold',
             leading=14, spaceAfter=0, spaceBefore=0)
    sN  = E('sN',  'Normal',  fontSize=9,  leading=13, textColor=colors.HexColor("#222222"))
    sBold=E('sBold','Normal', fontSize=9,  leading=13, fontName='Helvetica-Bold',
             textColor=colors.HexColor("#222222"))
    sPie= E('sPie','Normal',  fontSize=7.5,textColor=GRIS, alignment=TA_CENTER)
    sCtr= E('sCtr','Normal',  fontSize=9,  alignment=TA_CENTER,
             textColor=colors.HexColor("#222222"))

    def hr(c=ROJO, t=0.6):
        return HRFlowable(width="100%", thickness=t, color=c,
                          spaceAfter=5, spaceBefore=3)
    def sp(h=5): return Spacer(1, h)

    # Cabecera de sección con color configurable
    def sec_header(txt, bg_color):
        t = Table([[Paragraph(txt, sSec)]], colWidths=[W])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        return t

    # Paleta de colores por sección
    C_ALIN  = colors.HexColor("#1a5c8a")   # azul — alineación
    C_GOLES = colors.HexColor("#1a7a2e")   # verde — goles
    C_TARJ  = colors.HexColor("#9b2335")   # rojo — tarjetas
    C_COBRO = colors.HexColor("#6b3010")   # café — cobros
    C_FIN   = colors.HexColor("#2a5c2a")   # verde oscuro — finanzas
    C_STATS = colors.HexColor("#4a1060")   # morado — estadísticas
    C_GOL_TOP=colors.HexColor("#b07800")   # dorado — goleadores
    C_ARB   = colors.HexColor("#444444")   # gris oscuro — arbitral
    C_NOTAS = colors.HexColor("#555555")   # gris — notas

    # Fondos claros correspondientes
    F_ALIN  = colors.HexColor("#e8f2f9")
    F_GOLES = colors.HexColor("#e8f5ec")
    F_TARJ  = colors.HexColor("#fdf0f2")
    F_COBRO = colors.HexColor("#fdf3ed")
    F_FIN   = colors.HexColor("#edf5ed")
    F_STATS = colors.HexColor("#f3eef7")

    # Tabla genérica — header_color configurable
    def tabla(data, widths, align_cols=None, header_color=None):
        if header_color is None: header_color = ROJO
        t = Table(data, colWidths=widths, repeatRows=1)
        style = [
            ('FONTNAME',  (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE',  (0,0), (-1,-1), 8.5),
            ('LEADING',   (0,0), (-1,-1), 12),
            ('BACKGROUND',(0,0), (-1,0),  header_color),
            ('TEXTCOLOR', (0,0), (-1,0),  BLANCO),
            ('FONTNAME',  (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',  (0,0), (-1,0),  8.5),
            ('ALIGN',     (0,0), (-1,0),  'CENTER'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [BLANCO, GRIS_L]),
            ('GRID',      (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
            ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',(0,0), (-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('LEFTPADDING', (0,0),(-1,-1), 5),
            ('RIGHTPADDING',(0,0),(-1,-1), 5),
        ]
        if align_cols:
            for col, align in align_cols.items():
                style.append(('ALIGN', (col,1), (col,-1), align))
        t.setStyle(TableStyle(style))
        return t

    # Tabla con última fila destacada (totales)
    def tabla_con_total(data, widths, align_cols=None, header_color=None, total_color=None):
        if header_color is None: header_color = ROJO
        if total_color  is None: total_color  = ROJO_L
        t = tabla(data, widths, align_cols, header_color)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,-1), (-1,-1), total_color),
            ('FONTNAME',   (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,-1), (-1,-1), 8.5),
        ]))
        return t

    # Celda de métrica pequeña
    def celdas_metricas(items):
        """items = list of (label, valor, color_valor)"""
        n = len(items)
        w = W / n
        header = [Paragraph(f'<font size="7" color="#888888">{lb}</font>', sCtr) for lb,_,_ in items]
        vals   = [Paragraph(f'<font size="16" color="{vc}"><b>{vl}</b></font>', sCtr)
                  for _,vl,vc in items]
        t = Table([header, vals], colWidths=[w]*n)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GRIS_L),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#dddddd")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    # ── Consultas de datos ────────────────────────────────────────────────
    p = q("SELECT * FROM partidos WHERE id=?", (pid,))
    if len(p) == 0: return None
    p = p.iloc[0]
    gf = int(p['goles_favor'] or 0)
    gc = int(p['goles_contra'] or 0)
    resultado   = "GANADO" if gf>gc else ("EMPATE" if gf==gc else "PERDIDO")
    color_res   = "#1a7a2e" if gf>gc else ("#c08000" if gf==gc else "#cc0000")
    rival       = str(p['rival'] or 'N/D')
    fecha_str   = str(p['fecha'] or '')
    cancha_str  = str(p['cancha'] or 'N/D')

    partic = q("""SELECT j.nombre, pa.rol FROM participaciones pa
                  JOIN jugadores j ON pa.jugador_id=j.id
                  WHERE pa.partido_id=? ORDER BY pa.rol DESC, j.nombre""", (pid,))
    titulares_list = partic[partic['rol']=='titular']['nombre'].tolist()
    cambios_list   = partic[partic['rol']=='cambio']['nombre'].tolist()

    cambios_det = q("""SELECT js.nombre as sale, je.nombre as entra, c.minuto
                       FROM cambios c
                       JOIN jugadores js ON c.jugador_sale_id=js.id
                       JOIN jugadores je ON c.jugador_entra_id=je.id
                       WHERE c.partido_id=? ORDER BY c.minuto""", (pid,))

    goles_det = q("""SELECT COALESCE(j.nombre,'Desconocido') as nombre, g.minuto, g.tipo
                     FROM goles g LEFT JOIN jugadores j ON g.jugador_id=j.id
                     WHERE g.partido_id=? ORDER BY g.minuto""", (pid,))

    tarj = q("""SELECT j.nombre, t.tipo FROM tarjetas t
                JOIN jugadores j ON t.jugador_id=j.id
                WHERE t.partido_id=? ORDER BY t.tipo, j.nombre""", (pid,))

    sanciones_p = q("""SELECT j.nombre, s.motivo, s.partidos_suspension, s.partidos_cumplidos
                        FROM sanciones s JOIN jugadores j ON s.jugador_id=j.id
                        WHERE s.partido_origen_id=?""", (pid,))

    pagos = q("""SELECT j.nombre, pg.monto, COALESCE(pg.monto_pagado,0) as pagado,
                        COALESCE(pa.rol,'N/D') as rol
                 FROM pagos pg JOIN jugadores j ON pg.jugador_id=j.id
                 LEFT JOIN participaciones pa
                    ON pa.jugador_id=pg.jugador_id AND pa.partido_id=pg.partido_id
                 WHERE pg.partido_id=? ORDER BY j.nombre""", (pid,))

    multas_p = q("""SELECT j.nombre, m.concepto, m.monto, COALESCE(m.monto_pagado,0) as pagado
                    FROM multas m JOIN jugadores j ON m.jugador_id=j.id
                    WHERE m.partido_id=? ORDER BY j.nombre""", (pid,))

    # Movimientos de caja de este partido
    caja_p = q("""SELECT concepto, monto FROM caja
                  WHERE partido_id=? ORDER BY monto DESC""", (pid,))
    ingresos_caja = float(caja_p[caja_p['monto']>0]['monto'].sum()) if len(caja_p)>0 else 0.0
    egresos_caja  = float(abs(caja_p[caja_p['monto']<0]['monto'].sum())) if len(caja_p)>0 else 0.0
    saldo_caja_p  = ingresos_caja - egresos_caja

    # Estadísticas acumuladas hasta este partido (orden cronológico)
    todos_p = q("SELECT * FROM partidos ORDER BY fecha ASC, id ASC")
    sa = {"pts":0,"g":0,"e":0,"p":0,"gf":0,"gc":0}
    for _, pp in todos_p.iterrows():
        pgf = int(pp['goles_favor'] or 0)
        pgc = int(pp['goles_contra'] or 0)
        if pgf > pgc:   sa['g']+=1; sa['pts']+=3
        elif pgf==pgc:  sa['e']+=1; sa['pts']+=1
        else:           sa['p']+=1
        sa['gf']+=pgf; sa['gc']+=pgc
        if int(pp['id'])==pid: break

    goleadores_top = q("""SELECT j.nombre, COUNT(g.id) as goles
                           FROM goles g JOIN jugadores j ON g.jugador_id=j.id
                           WHERE g.tipo='normal'
                           GROUP BY j.id ORDER BY goles DESC LIMIT 5""")

    informe_arb = str(p.get('informe_arbitral', '') or '')

    # ── Construir PDF ────────────────────────────────────────────────────
    story = []

    # ── ENCABEZADO ───────────────────────────────────────────────────────
    story.append(Paragraph("UNION Y PROGRESO", sT))
    story.append(Paragraph("Barrio La Libertad  |  Informe de Partido", sSub))
    story.append(hr())
    story.append(sp(4))

    # Marcador grande
    s_score = E('score','Normal', fontSize=40, fontName='Helvetica-Bold',
                 alignment=TA_CENTER, leading=46)
    s_vs    = E('vs','Normal', fontSize=16, textColor=GRIS,
                 alignment=TA_CENTER, leading=20)
    s_res   = E('res','Normal', fontSize=13, fontName='Helvetica-Bold',
                 alignment=TA_CENTER, leading=16)

    score_tbl = Table(
        [[Paragraph(str(gf), s_score),
          Paragraph("VS", s_vs),
          Paragraph(str(gc), s_score)],
         [Paragraph("Union y Progreso", sSub),
          Paragraph(f'<font color="{color_res}">{resultado}</font>', s_res),
          Paragraph(rival, sSub)]],
        colWidths=[5.5*cm, 6*cm, 5.5*cm]
    )
    score_tbl.setStyle(TableStyle([
        ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor("#eeeeee")),
    ]))
    story.append(score_tbl)
    story.append(sp(6))
    story.append(Paragraph(
        f'Fecha: <b>{fecha_str}</b>   |   Cancha: <b>{cancha_str}</b>',
        sSub))
    story.append(sp(8))
    story.append(hr())

    # ── ALINEACION (azul) ────────────────────────────────────────────────
    story.append(sp(4))
    story.append(sec_header("ALINEACION", C_ALIN))
    story.append(sp(5))

    max_r = max(len(titulares_list), len(cambios_list), 1)
    alin  = [["TITULARES", "ENTRARON AL CAMBIO"]]
    for i in range(max_r):
        alin.append([
            titulares_list[i] if i < len(titulares_list) else "",
            cambios_list[i]   if i < len(cambios_list)   else ""
        ])
    story.append(tabla(alin, [8.5*cm, 8.5*cm], header_color=C_ALIN))

    if len(cambios_det) > 0:
        story.append(sp(6))
        det_cambios = [["SALE", "ENTRA", "MINUTO"]]
        for _, ch in cambios_det.iterrows():
            min_s = f"{int(ch['minuto'])}'" if ch['minuto'] else "—"
            det_cambios.append([str(ch['sale']), str(ch['entra']), min_s])
        story.append(tabla(det_cambios, [7*cm, 7*cm, 3*cm],
                           align_cols={2: 'CENTER'}, header_color=C_ALIN))

    # ── GOLES (verde) ────────────────────────────────────────────────────
    story.append(sp(8))
    story.append(sec_header("GOLES DEL PARTIDO", C_GOLES))
    story.append(sp(5))

    if len(goles_det) > 0:
        g_data = [["#", "JUGADOR", "MIN.", "TIPO"]]
        for i, (_, g) in enumerate(goles_det.iterrows(), 1):
            tipo = "Normal" if g['tipo']=='normal' else "Propia puerta"
            min_s = f"{int(g['minuto'])}'" if g['minuto'] else "—"
            g_data.append([str(i), str(g['nombre']), min_s, tipo])
        story.append(tabla(g_data, [1.2*cm, 9*cm, 2.8*cm, 4*cm],
                           align_cols={0:'CENTER', 2:'CENTER'},
                           header_color=C_GOLES))
    else:
        story.append(Paragraph("Sin goles registrados.", sN))

    # ── TARJETAS Y SANCIONES (rojo) ───────────────────────────────────────
    story.append(sp(8))
    story.append(sec_header("TARJETAS Y SANCIONES", C_TARJ))
    story.append(sp(5))

    if len(tarj) > 0:
        tarj_data = [["JUGADOR", "TARJETA"]]
        from collections import Counter
        am_count = Counter(tarj[tarj['tipo']=='amarilla']['nombre'].tolist())
        procesados = set()
        for _, t in tarj.iterrows():
            nombre = str(t['nombre'])
            tipo   = str(t['tipo'])
            if tipo == 'amarilla':
                if nombre in procesados: continue
                procesados.add(nombre)
                tarj_data.append([nombre,
                    "Doble Amarilla" if am_count[nombre]>=2 else "Amarilla"])
            else:
                tarj_data.append([nombre, "Roja Directa"])
        story.append(tabla(tarj_data, [11*cm, 6*cm], header_color=C_TARJ))
    else:
        story.append(Paragraph("Sin tarjetas en este partido.", sN))

    if len(sanciones_p) > 0:
        story.append(sp(6))
        ml = {'roja_directa': 'Roja directa - 2 partidos de suspension',
              'doble_amarilla': 'Doble amarilla - 1 partido de suspension',
              'acumulacion_amarillas': '5 amarillas acumuladas - 1 partido'}
        sanc_data = [["JUGADOR", "MOTIVO", "ESTADO"]]
        for _, s in sanciones_p.iterrows():
            pend = int(s['partidos_suspension']) - int(s['partidos_cumplidos'])
            estado = "Cumplida" if pend==0 else f"Pendiente ({pend} partido(s))"
            sanc_data.append([str(s['nombre']),
                               ml.get(str(s['motivo']), str(s['motivo'])),
                               estado])
        t_sanc = tabla(sanc_data, [4.5*cm, 9*cm, 3.5*cm], header_color=C_TARJ)
        for i, row in enumerate(sanc_data[1:], 1):
            if "Pendiente" in row[2]:
                t_sanc.setStyle(TableStyle([
                    ('BACKGROUND', (0,i), (-1,i), ROJO_L),
                    ('TEXTCOLOR', (2,i), (2,i), colors.HexColor("#aa0000")),
                    ('FONTNAME', (2,i), (2,i), 'Helvetica-Bold'),
                ]))
        story.append(t_sanc)

    # ── COBROS DEL PARTIDO (café) ─────────────────────────────────────────
    story.append(sp(8))
    story.append(sec_header("COBROS DEL PARTIDO", C_COBRO))
    story.append(sp(5))

    if len(pagos) > 0:
        story.append(Paragraph("Cuotas de arbitraje:", sBold))
        story.append(sp(4))
        p_data = [["JUGADOR", "ROL", "TOTAL", "PAGADO", "DEBE"]]
        tot_total = tot_pagado = 0.0
        for _, row in pagos.iterrows():
            debe = float(row['monto']) - float(row['pagado'])
            tot_total  += float(row['monto'])
            tot_pagado += float(row['pagado'])
            rol_s = "Titular" if row['rol']=='titular' else \
                    ("Cambio"  if row['rol']=='cambio'  else "—")
            p_data.append([str(row['nombre']), rol_s,
                            f"${float(row['monto']):,.2f}",
                            f"${float(row['pagado']):,.2f}",
                            f"${debe:,.2f}" if debe>0.001 else "Al dia"])
        p_data.append(["TOTAL", "", f"${tot_total:,.2f}",
                        f"${tot_pagado:,.2f}",
                        f"${tot_total-tot_pagado:,.2f}"])
        story.append(tabla_con_total(p_data,
            [5.5*cm, 2.5*cm, 2.8*cm, 2.8*cm, 3.4*cm],
            align_cols={2:'RIGHT', 3:'RIGHT', 4:'RIGHT'},
            header_color=C_COBRO,
            total_color=colors.HexColor("#fde8d8")))

    if len(multas_p) > 0:
        story.append(sp(8))
        story.append(Paragraph("Multas por tarjetas:", sBold))
        story.append(sp(4))
        m_data = [["JUGADOR", "CONCEPTO", "MULTA", "PAGADO", "DEBE"]]
        for _, row in multas_p.iterrows():
            debe = float(row['monto']) - float(row['pagado'])
            m_data.append([str(row['nombre']),
                            str(row['concepto']),
                            f"${float(row['monto']):,.2f}",
                            f"${float(row['pagado']):,.2f}",
                            f"${debe:,.2f}" if debe>0.001 else "Al dia"])
        story.append(tabla(m_data,
            [4*cm, 6*cm, 2.3*cm, 2.3*cm, 2.4*cm],
            align_cols={2:'RIGHT', 3:'RIGHT', 4:'RIGHT'},
            header_color=C_COBRO))

    # ── RESUMEN FINANCIERO (verde oscuro) ─────────────────────────────────
    story.append(sp(8))
    story.append(sec_header("RESUMEN FINANCIERO DEL PARTIDO", C_FIN))
    story.append(sp(5))

    fin_data = [["CONCEPTO", "TIPO", "MONTO"]]
    for _, row in caja_p.iterrows():
        tipo_s = "Ingreso" if float(row['monto'])>=0 else "Egreso"
        fin_data.append([str(row['concepto']), tipo_s,
                          f"${float(row['monto']):,.2f}"])
    if len(fin_data) > 1:
        story.append(tabla(fin_data, [10*cm, 3*cm, 4*cm],
                           align_cols={2:'RIGHT'}, header_color=C_FIN))
        story.append(sp(6))

    color_saldo = "#1a7a2e" if saldo_caja_p >= 0 else "#cc0000"
    story.append(celdas_metricas([
        ("Total Ingresos",    f"${ingresos_caja:,.2f}", "#1a7a2e"),
        ("Total Egresos",     f"${egresos_caja:,.2f}",  "#cc0000"),
        ("Saldo del Partido", f"${saldo_caja_p:,.2f}",  color_saldo),
    ]))

    # ── ESTADISTICAS ACUMULADAS (morado) ──────────────────────────────────
    story.append(sp(8))
    story.append(sec_header("ESTADISTICAS ACUMULADAS DEL EQUIPO", C_STATS))
    story.append(sp(5))

    n_part = sa['g'] + sa['e'] + sa['p']
    dif = sa['gf'] - sa['gc']
    dif_s = f"+{dif}" if dif >= 0 else str(dif)

    story.append(celdas_metricas([
        ("Partidos", str(n_part),    "#333333"),
        ("Puntos",   str(sa['pts']), "#4a1060"),
        ("Ganados",  str(sa['g']),   "#1a7a2e"),
        ("Empates",  str(sa['e']),   "#c08000"),
        ("Perdidos", str(sa['p']),   "#cc0000"),
    ]))
    story.append(sp(5))
    story.append(celdas_metricas([
        ("Goles a Favor",   str(sa['gf']), "#1a7a2e"),
        ("Goles en Contra", str(sa['gc']), "#cc0000"),
        ("Diferencia",      dif_s,          color_saldo),
    ]))

    # ── GOLEADORES GLOBALES (dorado) ──────────────────────────────────────
    if len(goleadores_top) > 0:
        story.append(sp(8))
        story.append(sec_header("TOP GOLEADORES DEL EQUIPO", C_GOL_TOP))
        story.append(sp(5))
        gt_data = [["POS.", "JUGADOR", "GOLES"]]
        for i, (_, row) in enumerate(goleadores_top.iterrows(), 1):
            pos = ["1ro", "2do", "3ro", "4to", "5to"][i-1]
            gt_data.append([pos, str(row['nombre']), str(int(row['goles']))])
        story.append(tabla(gt_data, [2*cm, 12*cm, 3*cm],
                           align_cols={0:'CENTER', 2:'CENTER'},
                           header_color=C_GOL_TOP))

    # ── COMENTARIOS ARBITRALES (gris oscuro) ─────────────────────────────
    if informe_arb.strip():
        story.append(sp(8))
        story.append(sec_header("COMENTARIOS DEL INFORME ARBITRAL", C_ARB))
        story.append(sp(5))
        # Caja con fondo gris claro para el texto
        arb_tbl = Table([[Paragraph(informe_arb, sN)]], colWidths=[W])
        arb_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f7f7f7")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(arb_tbl)

    # ── NOTAS (gris) ─────────────────────────────────────────────────────
    if p['notas'] and str(p['notas']).strip():
        story.append(sp(8))
        story.append(sec_header("NOTAS DEL PARTIDO", C_NOTAS))
        story.append(sp(5))
        notas_tbl = Table([[Paragraph(str(p['notas']), sN)]], colWidths=[W])
        notas_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f7f7f7")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(notas_tbl)

    # ── PIE DE PAGINA ─────────────────────────────────────────────────────
    story.append(sp(14))
    story.append(hr(GRIS, 0.4))
    story.append(Paragraph(
        f"Informe generado el {date.today().strftime('%d/%m/%Y')}  |  "
        f"Union y Progreso  |  Barrio La Libertad",
        sPie))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚽ Unión y Progreso",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── LOGIN ─────────────────────────────────────────────────────────────────────
# Las contraseñas se leen desde Streamlit Secrets (seguro).
# En local usa los valores por defecto si no hay secrets configurados.
try:
    PASS_ADMIN   = st.secrets["PASS_ADMIN"]
    PASS_JUGADOR = st.secrets["PASS_JUGADOR"]
except Exception:
    # Valores por defecto para desarrollo local
    PASS_ADMIN   = "Renato"
    PASS_JUGADOR = "Progreso"

USUARIOS = {
    "admin":   {"password": PASS_ADMIN,   "rol": "admin"},
    "jugador": {"password": PASS_JUGADOR, "rol": "jugador"},
}

def login_screen():
    st.markdown("""
    <div style="max-width:380px;margin:60px auto 0 auto;text-align:center;">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:52px;
                  color:#f0c040;letter-spacing:4px;">⚽</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:32px;
                  color:#f0c040;letter-spacing:3px;">UNIÓN Y PROGRESO</div>
      <div style="color:#d4b8b8;font-size:12px;letter-spacing:2px;
                  margin-bottom:32px;">BARRIO LA LIBERTAD</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown("<div style='max-width:380px;margin:0 auto;'>", unsafe_allow_html=True)
        usuario  = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        entrar   = st.form_submit_button("ENTRAR", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

        if entrar:
            u = usuario.strip().lower()
            if u in USUARIOS and USUARIOS[u]["password"] == password:
                st.session_state["usuario"] = u
                st.session_state["rol"]     = USUARIOS[u]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

if "usuario" not in st.session_state:
    login_screen()
    st.stop()

# Botón de cerrar sesión en sidebar
with st.sidebar:
    rol_actual = st.session_state.get("rol", "jugador")
    icono_rol  = "🔐 Admin" if rol_actual == "admin" else "👤 Jugador"
    st.markdown(f"**{icono_rol}** — {st.session_state['usuario']}")
    if st.button("🚪 Cerrar sesión"):
        for k in ["usuario", "rol"]:
            st.session_state.pop(k, None)
        st.rerun()

IS_ADMIN = st.session_state.get("rol") == "admin"

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Nunito:wght@400;600;700;800&display=swap');

:root {
    --verde: #9b2335;
    --verde-claro: #f0c040;
    --verde-oscuro: #6b1020;
    --blanco: #ffffff;
    --gris: #d4b8b8;
    --alerta: #f0c040;
    --peligro: #ff6b6b;
    --fondo: #1a0808;
    --card: #2d1010;
    --card2: #3d1515;
    --borde: #6b2525;
}

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
    background-color: var(--fondo);
    color: var(--blanco);
}

h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }

.stApp { background-color: var(--fondo); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--card);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid var(--borde);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--gris);
    border-radius: 8px;
    font-family: 'Nunito', sans-serif;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 14px;
}
.stTabs [aria-selected="true"] {
    background: var(--verde) !important;
    color: white !important;
}

/* Metric cards */
.metric-card {
    background: var(--card);
    border: 1px solid var(--borde);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.metric-card .label {
    font-size: 11px;
    color: var(--gris);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}
.metric-card .valor {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 36px;
    color: var(--verde-claro);
    line-height: 1;
}
.metric-card .sub {
    font-size: 12px;
    color: var(--gris);
    margin-top: 4px;
}

/* Player cards */
.jugador-card {
    background: var(--card);
    border: 1px solid var(--borde);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.jugador-num {
    background: var(--verde-oscuro);
    color: var(--verde-claro);
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    margin-right: 4px;
}
.badge-amarilla { background: #3d3000; color: #f0c040; border: 1px solid #f0c040; }
.badge-roja { background: #3d0000; color: #ff6b6b; border: 1px solid #ff6b6b; }
.badge-deuda { background: #3d1500; color: #ffaa55; border: 1px solid #ffaa55; }
.badge-ok { background: #003d1a; color: #50e080; border: 1px solid #50e080; }
.badge-exento { background: #003340; color: #55bbee; border: 1px solid #55bbee; }
.badge-sancion { background: #9b2335; color: white; }

/* Tables */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background: var(--card2) !important;
    border: 1px solid var(--borde) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}
.stDateInput input {
    background: var(--card2) !important;
    border: 1px solid var(--borde) !important;
    color: #ffffff !important;
}
label, .stTextInput label, .stNumberInput label, .stSelectbox label,
.stDateInput label, .stMultiSelect label, .stTextArea label,
div[data-testid="stWidgetLabel"] p { color: #ffffff !important; font-weight: 600 !important; }
.stTextArea textarea {
    background: var(--card2) !important; border: 1px solid var(--borde) !important;
    color: #ffffff !important; border-radius: 8px !important;
}
.stMultiSelect div[data-baseweb="select"] { background: var(--card2) !important; }
.stMultiSelect [data-baseweb="tag"] { background: var(--verde) !important; color: white !important; }
.stMultiSelect input { color: #ffffff !important; }
.stSelectbox div[data-baseweb="select"] > div { background: var(--card2) !important; color: #ffffff !important; }

/* Buttons */
.stButton button {
    background: var(--verde);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Nunito', sans-serif;
    font-weight: 700;
    padding: 8px 20px;
    transition: background 0.2s;
}
.stButton button:hover { background: var(--verde-claro); }

/* Section headers */
.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    color: #f0c040;
    letter-spacing: 2px;
    border-bottom: 2px solid var(--borde);
    padding-bottom: 6px;
    margin: 18px 0 12px 0;
}

/* Alert boxes */
.alerta-box {
    background: #2a1a00;
    border: 1px solid var(--alerta);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 14px;
}
.peligro-box {
    background: #2a0000;
    border: 1px solid var(--peligro);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 14px;
}
.ok-box {
    background: #002a10;
    border: 1px solid var(--verde-claro);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 14px;
}

div[data-testid="stCheckbox"] label { color: #ffffff !important; }
div[data-testid="stMultiSelect"] span { background: var(--verde-oscuro) !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ─── DATABASE ──────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect("equipo.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS jugadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        numero INTEGER,
        posicion TEXT,
        exento_arbitraje INTEGER DEFAULT 0,
        exento_uniforme INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        rival TEXT,
        cancha TEXT,
        goles_favor INTEGER DEFAULT 0,
        goles_contra INTEGER DEFAULT 0,
        costo_arbitraje REAL DEFAULT 0,
        costo_agua REAL DEFAULT 0,
        notas TEXT
    );

    CREATE TABLE IF NOT EXISTS participaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER,
        jugador_id INTEGER,
        rol TEXT,
        FOREIGN KEY(partido_id) REFERENCES partidos(id),
        FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
    );

    CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER,
        jugador_id INTEGER,
        monto REAL DEFAULT 0,
        pagado INTEGER DEFAULT 0,
        FOREIGN KEY(partido_id) REFERENCES partidos(id),
        FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
    );

    CREATE TABLE IF NOT EXISTS tarjetas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER,
        jugador_id INTEGER,
        tipo TEXT,
        cumplida INTEGER DEFAULT 0,
        FOREIGN KEY(partido_id) REFERENCES partidos(id),
        FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
    );

    CREATE TABLE IF NOT EXISTS caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER,
        concepto TEXT,
        monto REAL,
        fecha TEXT,
        FOREIGN KEY(partido_id) REFERENCES partidos(id)
    );

    CREATE TABLE IF NOT EXISTS sanciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jugador_id INTEGER NOT NULL,
        partido_origen_id INTEGER NOT NULL,
        motivo TEXT NOT NULL,
        partidos_suspension INTEGER NOT NULL DEFAULT 1,
        partidos_cumplidos INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(jugador_id) REFERENCES jugadores(id),
        FOREIGN KEY(partido_origen_id) REFERENCES partidos(id)
    );

    CREATE TABLE IF NOT EXISTS goles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER NOT NULL,
        jugador_id INTEGER,
        minuto INTEGER,
        tipo TEXT DEFAULT 'normal',
        FOREIGN KEY(partido_id) REFERENCES partidos(id),
        FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
    );

    CREATE TABLE IF NOT EXISTS cambios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER NOT NULL,
        jugador_sale_id INTEGER NOT NULL,
        jugador_entra_id INTEGER NOT NULL,
        minuto INTEGER,
        FOREIGN KEY(partido_id) REFERENCES partidos(id),
        FOREIGN KEY(jugador_sale_id) REFERENCES jugadores(id),
        FOREIGN KEY(jugador_entra_id) REFERENCES jugadores(id)
    );

    CREATE TABLE IF NOT EXISTS multas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partido_id INTEGER NOT NULL,
        jugador_id INTEGER NOT NULL,
        concepto TEXT NOT NULL,
        monto REAL NOT NULL DEFAULT 0,
        pagado INTEGER DEFAULT 0,
        FOREIGN KEY(partido_id) REFERENCES partidos(id),
        FOREIGN KEY(jugador_id) REFERENCES jugadores(id)
    );
    """)
    # Migraciones seguras — agregan columnas si no existen
    migraciones = [
        "ALTER TABLE pagos ADD COLUMN monto_pagado REAL DEFAULT 0",
        "ALTER TABLE multas ADD COLUMN monto_pagado REAL DEFAULT 0",
        "ALTER TABLE partidos ADD COLUMN informe_arbitral TEXT DEFAULT ''",
    ]
    for sql in migraciones:
        try:
            conn.execute(sql)
        except Exception:
            pass  # columna ya existe
    conn.commit()
    conn.close()

init_db()

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def q(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def run(sql, params=()):
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

def get_jugadores():
    return q("SELECT * FROM jugadores WHERE activo=1 ORDER BY numero")

def get_partidos():
    return q("SELECT * FROM partidos ORDER BY fecha DESC")

def saldo_caja():
    r = q("SELECT SUM(monto) as total FROM caja")
    v = r['total'][0]
    return v if v else 0.0

# ── Disciplina ─────────────────────────────────────────────────────────────────
def amarillas_totales(jugador_id):
    return q("SELECT COUNT(*) as c FROM tarjetas WHERE jugador_id=? AND tipo='amarilla'", (jugador_id,))['c'][0]

def amarillas_simples_total(jugador_id):
    """Amarillas en partidos donde solo sacó 1 (no dobles). Estas cuentan para acumulación de 5."""
    dobles = q("""SELECT partido_id FROM tarjetas WHERE jugador_id=? AND tipo='amarilla'
                  GROUP BY partido_id HAVING COUNT(*)>=2""", (jugador_id,))
    ids_doble = set(dobles['partido_id'].tolist()) if len(dobles) > 0 else set()
    todas = q("""SELECT partido_id, COUNT(*) as c FROM tarjetas
                 WHERE jugador_id=? AND tipo='amarilla' GROUP BY partido_id""", (jugador_id,))
    return sum(row['c'] for _, row in todas.iterrows() if row['partido_id'] not in ids_doble) if len(todas) > 0 else 0

def tarjetas_amarillas_activas(jugador_id):
    """Amarillas simples en el ciclo actual (0-4). Al llegar a 5 genera suspensión y reinicia."""
    return amarillas_simples_total(jugador_id) % 5

def partidos_doble_amarilla(jugador_id):
    r = q("""SELECT COUNT(*) as c FROM (
                SELECT partido_id FROM tarjetas WHERE jugador_id=? AND tipo='amarilla'
                GROUP BY partido_id HAVING COUNT(*)>=2)""", (jugador_id,))
    return r['c'][0]

def sanciones_pendientes(jugador_id):
    r = q("""SELECT COALESCE(SUM(partidos_suspension - partidos_cumplidos),0) as p
             FROM sanciones WHERE jugador_id=? AND partidos_cumplidos < partidos_suspension""", (jugador_id,))
    return int(r['p'][0])

def esta_sancionado(jugador_id):
    pendientes = sanciones_pendientes(jugador_id)
    activas    = tarjetas_amarillas_activas(jugador_id)
    if pendientes > 0:
        detalle = q("""SELECT motivo, (partidos_suspension-partidos_cumplidos) as r
                       FROM sanciones WHERE jugador_id=? AND partidos_cumplidos<partidos_suspension""", (jugador_id,))
        labels = {'roja_directa':'roja directa','doble_amarilla':'doble amarilla','acumulacion_amarillas':'5 amarillas'}
        partes = [f"{labels.get(d['motivo'],d['motivo'])} ({int(d['r'])} partido(s))" for _, d in detalle.iterrows()]
        return f"🔴 Suspendido — {', '.join(partes)}"
    if activas == 4:
        return "⚠️ En riesgo — próxima amarilla = suspensión"
    return ""

def deuda_jugador(jugador_id):
    """Suma deuda real = monto total - lo que ya pagó (soporta pagos parciales)."""
    r = q("""SELECT COALESCE(SUM(monto - COALESCE(monto_pagado,0)),0) as d
             FROM pagos WHERE jugador_id=? AND pagado=0""", (jugador_id,))
    d1 = r['d'][0]
    r2 = q("""SELECT COALESCE(SUM(monto - COALESCE(monto_pagado,0)),0) as d
              FROM multas WHERE jugador_id=? AND pagado=0""", (jugador_id,))
    d2 = r2['d'][0]
    return d1 + d2

# ── Goles ──────────────────────────────────────────────────────────────────────
def goles_jugador(jugador_id):
    r = q("SELECT COUNT(*) as c FROM goles WHERE jugador_id=?", (jugador_id,))
    return r['c'][0]

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 10px 0 20px 0;">
  <span style="font-family:'Bebas Neue',sans-serif; font-size:48px; color:#f0c040; letter-spacing:4px;">⚽ UNIÓN Y PROGRESO</span><br>
  <span style="color:#d4b8b8; font-size:13px; letter-spacing:2px;">BARRIO LA LIBERTAD · CONTROL FINANCIERO · ALINEACIONES · DISCIPLINA</span>
</div>
""", unsafe_allow_html=True)

# ─── TABS (según rol) ──────────────────────────────────────────────────────────
if IS_ADMIN:
    tabs = st.tabs(["🏠 INICIO", "👥 JUGADORES", "⚽ PARTIDO", "💰 FINANZAS", "🟨 DISCIPLINA", "📊 HISTORIAL"])
    TAB_INICIO    = tabs[0]
    TAB_JUGADORES = tabs[1]
    TAB_PARTIDO   = tabs[2]
    TAB_FINANZAS  = tabs[3]
    TAB_DISCIPLINA= tabs[4]
    TAB_HISTORIAL = tabs[5]
else:
    tabs_j = st.tabs(["🏠 INICIO", "🟨 DISCIPLINA", "📊 HISTORIAL"])
    TAB_INICIO    = tabs_j[0]
    TAB_JUGADORES = None
    TAB_PARTIDO   = None
    TAB_FINANZAS  = None
    TAB_DISCIPLINA= tabs_j[1]
    TAB_HISTORIAL = tabs_j[2]

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INICIO
# ══════════════════════════════════════════════════════════════════════════════
with TAB_INICIO:
    jugadores = get_jugadores()
    partidos = get_partidos()
    saldo = saldo_caja()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="label">💰 Saldo en Caja</div>
            <div class="valor">${saldo:,.0f}</div>
            <div class="sub">Fondo acumulado</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        n_partidos = len(partidos)
        st.markdown(f"""<div class="metric-card">
            <div class="label">📅 Partidos Jugados</div>
            <div class="valor">{n_partidos}</div>
            <div class="sub">En el historial</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        n_jugadores = len(jugadores)
        st.markdown(f"""<div class="metric-card">
            <div class="label">👥 Jugadores Activos</div>
            <div class="valor">{n_jugadores}</div>
            <div class="sub">En el plantel</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        total_deudas = sum(deuda_jugador(int(row['id'])) for _, row in jugadores.iterrows())
        st.markdown(f"""<div class="metric-card">
            <div class="label">⚠️ Deudas Pendientes</div>
            <div class="valor">${total_deudas:,.0f}</div>
            <div class="sub">Total sin cobrar</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🚨 ALERTAS DEL PLANTEL</div>', unsafe_allow_html=True)

    hay_alertas = False
    for _, j in jugadores.iterrows():
        jid = int(j['id'])
        sancion = esta_sancionado(jid)
        deuda = deuda_jugador(jid)
        amarillas = amarillas_totales(jid)
        activas = tarjetas_amarillas_activas(jid)

        if sancion and "Suspendido" in sancion:
            hay_alertas = True
            st.markdown(f'<div class="peligro-box">🔴 <b>{j["nombre"]}</b> — {sancion}</div>', unsafe_allow_html=True)
        elif activas == 4:
            hay_alertas = True
            st.markdown(f'<div class="alerta-box">🟨 <b>{j["nombre"]}</b> — 4 amarillas acumuladas. ¡Una más y se suspende!</div>', unsafe_allow_html=True)
        if deuda > 0:
            hay_alertas = True
            st.markdown(f'<div class="alerta-box">💸 <b>{j["nombre"]}</b> — Debe <b>${deuda:,.0f}</b></div>', unsafe_allow_html=True)

    if not hay_alertas:
        st.markdown('<div class="ok-box">✅ Todo en orden. Sin alertas pendientes.</div>', unsafe_allow_html=True)

    if len(partidos) > 0:
        st.markdown('<div class="section-header">📅 ÚLTIMO PARTIDO</div>', unsafe_allow_html=True)
        ult = partidos.iloc[0]
        g_f = int(ult['goles_favor']) if ult['goles_favor'] else 0
        g_c = int(ult['goles_contra']) if ult['goles_contra'] else 0
        resultado = "Ganado ✅" if g_f > g_c else ("Empate 🤝" if g_f == g_c else "Perdido ❌")
        st.markdown(f"""<div class="metric-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div class="label">{ult['fecha']} vs {ult['rival'] or 'Rival'}</div>
                    <div class="valor" style="font-size:48px;">{g_f} - {g_c}</div>
                    <div class="sub">{resultado} · Cancha: {ult['cancha'] or 'N/D'}</div>
                </div>
                <div style="font-size:64px; opacity:0.3;">⚽</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — JUGADORES (solo admin)
# ══════════════════════════════════════════════════════════════════════════════
if IS_ADMIN:
 with TAB_JUGADORES:
    st.markdown('<div class="section-header">👥 PLANTEL</div>', unsafe_allow_html=True)
    jugadores = get_jugadores()

    for _, j in jugadores.iterrows():
        jid = int(j['id'])
        amarillas = amarillas_totales(jid)
        activas = tarjetas_amarillas_activas(jid)
        rojas = q("SELECT COUNT(*) as c FROM tarjetas WHERE jugador_id=? AND tipo='roja'", (jid,))['c'][0]
        rojas_pend = sanciones_pendientes(jid)
        deuda = deuda_jugador(jid)
        sancion = esta_sancionado(jid)

        badges = ""
        if j['exento_arbitraje']:
            badges += '<span class="badge badge-exento">Exento árb.</span>'
        if j['exento_uniforme']:
            badges += '<span class="badge badge-exento">Exento unif.</span>'
        if activas > 0:
            badges += f'<span class="badge badge-amarilla">🟨 {activas} amarilla(s)</span>'
        if rojas > 0:
            color = "badge-roja" if rojas_pend > 0 else "badge-ok"
            badges += f'<span class="badge {color}">🟥 {rojas} roja(s)</span>'
        if deuda > 0:
            badges += f'<span class="badge badge-deuda">💸 Debe ${deuda:,.0f}</span>'
        if sancion and "Suspendido" in sancion:
            badges += f'<span class="badge badge-sancion">SUSPENDIDO</span>'

        num_display = j['numero'] if j['numero'] else "—"
        st.markdown(f"""
        <div class="jugador-card">
            <div class="jugador-num">{num_display}</div>
            <div style="flex:1;">
                <div style="font-weight:800; font-size:16px;">{j['nombre']}</div>
                <div style="color:var(--gris); font-size:12px; margin-bottom:4px;">{j['posicion'] or 'Sin posición'}</div>
                <div>{badges}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">➕ AGREGAR JUGADOR</div>', unsafe_allow_html=True)
    with st.form("form_jugador", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre completo")
            numero = st.number_input("Número de camiseta", min_value=1, max_value=99, value=1)
        with c2:
            posicion = st.selectbox("Posición", ["Portero", "Defensa", "Mediocampista", "Delantero"])
            c3, c4 = st.columns(2)
            with c3:
                exento_arb = st.checkbox("Exento de arbitraje")
            with c4:
                exento_uni = st.checkbox("Exento de uniforme")
        if st.form_submit_button("✅ Agregar jugador"):
            if nombre:
                run("INSERT INTO jugadores (nombre, numero, posicion, exento_arbitraje, exento_uniforme) VALUES (?,?,?,?,?)",
                    (nombre, numero, posicion, int(exento_arb), int(exento_uni)))
                st.success(f"✅ {nombre} agregado al plantel")
                st.rerun()

    # Editar/desactivar jugador
    st.markdown('<div class="section-header">✏️ EDITAR JUGADOR</div>', unsafe_allow_html=True)
    jugadores = get_jugadores()
    if len(jugadores) > 0:
        nombres_lista = jugadores['nombre'].tolist()
        sel = st.selectbox("Selecciona jugador a editar", nombres_lista, key="edit_j")
        j_sel = jugadores[jugadores['nombre'] == sel].iloc[0]
        with st.form("form_editar_j"):
            c1, c2 = st.columns(2)
            with c1:
                n_nombre = st.text_input("Nombre", value=j_sel['nombre'])
                n_num = st.number_input("Número", min_value=1, max_value=99, value=int(j_sel['numero']) if j_sel['numero'] else 1)
            with c2:
                posiciones = ["Portero", "Defensa", "Mediocampista", "Delantero"]
                pos_idx = posiciones.index(j_sel['posicion']) if j_sel['posicion'] in posiciones else 0
                n_pos = st.selectbox("Posición", posiciones, index=pos_idx)
                c3, c4 = st.columns(2)
                with c3:
                    n_exarb = st.checkbox("Exento arbitraje", value=bool(j_sel['exento_arbitraje']))
                with c4:
                    n_exuni = st.checkbox("Exento uniforme", value=bool(j_sel['exento_uniforme']))
            col_s, col_d = st.columns(2)
            with col_s:
                if st.form_submit_button("💾 Guardar cambios"):
                    run("UPDATE jugadores SET nombre=?, numero=?, posicion=?, exento_arbitraje=?, exento_uniforme=? WHERE id=?",
                        (n_nombre, n_num, n_pos, int(n_exarb), int(n_exuni), int(j_sel['id'])))
                    st.success("✅ Jugador actualizado")
                    st.rerun()
            with col_d:
                if st.form_submit_button("🗑️ Desactivar jugador"):
                    run("UPDATE jugadores SET activo=0 WHERE id=?", (int(j_sel['id']),))
                    st.warning(f"Jugador {j_sel['nombre']} desactivado")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PARTIDO (4 FASES)
# ══════════════════════════════════════════════════════════════════════════════
if IS_ADMIN:
 with TAB_PARTIDO:

    MOTIVO_LABELS = {
        'roja_directa':         '🟥 Roja directa (2 partidos)',
        'doble_amarilla':       '🟨🟨 Doble amarilla (1 partido)',
        'acumulacion_amarillas':'🟨×5 Acumulación (1 partido)'
    }

    def fase_header(num, titulo, subtitulo, color):
        st.markdown(f"""
        <div style="background:{color};border-radius:12px;padding:14px 20px;margin-bottom:14px;">
          <div style="font-family:'Bebas Neue',sans-serif;font-size:22px;letter-spacing:2px;color:#fff;">
            FASE {num} — {titulo}
          </div>
          <div style="font-size:13px;color:rgba(255,255,255,0.8);margin-top:2px;">{subtitulo}</div>
        </div>""", unsafe_allow_html=True)

    # ── selector de partido activo para fases 2/3/4 ──────────────────────────
    partidos_list = get_partidos()
    jugadores     = get_jugadores()
    nombres       = jugadores['nombre'].tolist()

    # ════════════════════════════════════════════════════════════════════
    # FASE 1 — ALINEACIÓN (antes del partido)
    # ════════════════════════════════════════════════════════════════════
    fase_header(1, "ALINEACIÓN", "Antes del partido — registra los jugadores y guarda", "#1a5c8a")

    # ── Borrador automático en session_state ─────────────────────────────
    # Los campos se guardan en memoria automáticamente mientras escribes.
    # Si refrescas la página se pierden, pero si el servidor sigue corriendo
    # (pérdida de internet breve) los datos se conservan.
    if 'f1_draft' not in st.session_state:
        st.session_state['f1_draft'] = {}
    draft = st.session_state['f1_draft']

    f1c1, f1c2, f1c3 = st.columns(3)
    with f1c1:
        f1_fecha = st.date_input("Fecha", value=date.today(), key="f1_fecha")
        f1_rival = st.text_input("Rival", key="f1_rival",
                                  value=draft.get('rival',''))
    with f1c2:
        f1_cancha  = st.text_input("Cancha / Lugar", key="f1_cancha",
                                    value=draft.get('cancha',''))
        f1_arb     = st.number_input("Costo árbitro ($)", min_value=0.0, step=0.5, key="f1_arb",
                                      value=draft.get('arb', 0.0))
        f1_agua    = st.number_input("Costo botellón ($)", min_value=0.0, step=0.5, key="f1_agua",
                                      value=draft.get('agua', 0.0))
    with f1c3:
        f1_monto   = st.number_input("💰 Cuota por jugador ($)", min_value=0.0, step=0.5, key="f1_monto",
                        value=draft.get('monto', 0.0),
                        help="Monto que paga cada jugador NO exento. Ajustable después por jugador.")

    # Guardar borrador automáticamente al cambiar cualquier campo
    st.session_state['f1_draft'] = {
        'rival': f1_rival, 'cancha': f1_cancha,
        'arb': f1_arb, 'agua': f1_agua, 'monto': f1_monto
    }

    st.markdown("**⚽ Titulares**")
    f1_titulares = st.multiselect("Selecciona titulares (hasta 11)", nombres, key="f1_tit",
                                   default=draft.get('titulares', []))
    st.session_state['f1_draft']['titulares'] = f1_titulares

    # ── Cambios con jugador que sale y entra ──────────────────────────────
    st.markdown("**🔄 Cambios** *(quién sale, quién entra y a qué minuto)*")
    n_cambios = st.number_input("¿Cuántos cambios hubo?", min_value=0, max_value=5,
                                 value=0, step=1, key="f1_ncambios")
    cambios_data = []  # lista de (sale, entra, minuto)
    nombres_disponibles_salida = f1_titulares if f1_titulares else nombres
    nombres_ya_entran = []
    for i in range(int(n_cambios)):
        st.markdown(f"<small style='color:#d4b8b8;'>Cambio #{i+1}</small>", unsafe_allow_html=True)
        cc1, cc2, cc3 = st.columns([3, 3, 1])
        with cc1:
            sale = st.selectbox("Sale ↗️", nombres_disponibles_salida,
                                key=f"f1_sale_{i}")
        with cc2:
            entra_opts = [n for n in nombres if n not in f1_titulares and n not in nombres_ya_entran]
            entra = st.selectbox("Entra ↘️", entra_opts if entra_opts else nombres,
                                 key=f"f1_entra_{i}")
        with cc3:
            min_c = st.number_input("Min.", min_value=1, max_value=120,
                                    value=45, key=f"f1_minc_{i}")
        cambios_data.append((sale, entra, min_c))
        nombres_ya_entran.append(entra)

    # Los jugadores que entran al cambio se extraen de cambios_data
    f1_entraron = [entra for _, entra, _ in cambios_data] if cambios_data else []

    if st.button("💾 GUARDAR ALINEACIÓN", type="primary", key="btn_fase1"):
        if not f1_rival.strip():
            st.error("⚠️ Ingresa el nombre del rival.")
        elif len(f1_titulares) == 0:
            st.error("⚠️ Selecciona al menos un titular.")
        else:
            # ── Validar partido duplicado (misma fecha + mismo rival) ───
            duplicado = q("""SELECT id FROM partidos
                             WHERE fecha=? AND LOWER(rival)=LOWER(?)""",
                          (str(f1_fecha), f1_rival.strip()))
            if len(duplicado) > 0:
                st.error(f"⚠️ Ya existe un partido registrado el {f1_fecha} contra '{f1_rival.strip()}'. "
                         f"Revisa el Historial o elige otra fecha.")
            else:
                conn = get_conn(); c = conn.cursor()
                c.execute("""INSERT INTO partidos (fecha,rival,cancha,goles_favor,goles_contra,
                             costo_arbitraje,costo_agua,notas) VALUES (?,?,?,0,0,?,?,?)""",
                          (str(f1_fecha), f1_rival.strip(), f1_cancha, f1_arb, f1_agua, ""))
                pid = c.lastrowid
                # Titulares
                for nombre in f1_titulares:
                    jrow = jugadores[jugadores['nombre']==nombre].iloc[0]
                    c.execute("INSERT INTO participaciones (partido_id,jugador_id,rol) VALUES (?,?,?)",
                              (pid, int(jrow['id']), 'titular'))
                # Cambios: registrar participación del que entra y guardar el cambio
                for sale, entra, min_c in cambios_data:
                    jrow_entra = jugadores[jugadores['nombre']==entra]
                    jrow_sale  = jugadores[jugadores['nombre']==sale]
                    if len(jrow_entra)>0:
                        c.execute("INSERT INTO participaciones (partido_id,jugador_id,rol) VALUES (?,?,?)",
                                  (pid, int(jrow_entra.iloc[0]['id']), 'cambio'))
                    if len(jrow_entra)>0 and len(jrow_sale)>0:
                        c.execute("""INSERT INTO cambios (partido_id,jugador_sale_id,jugador_entra_id,minuto)
                                     VALUES (?,?,?,?)""",
                                  (pid, int(jrow_sale.iloc[0]['id']),
                                   int(jrow_entra.iloc[0]['id']), min_c))
                # Cobros pendientes para no exentos
                participantes = list(set(f1_titulares + f1_entraron))
                for nombre in participantes:
                    jrow = jugadores[jugadores['nombre']==nombre].iloc[0]
                    if not bool(jrow['exento_arbitraje']) and f1_monto > 0:
                        c.execute("INSERT INTO pagos (partido_id,jugador_id,monto,pagado) VALUES (?,?,?,0)",
                                  (pid, int(jrow['id']), f1_monto))
                if f1_arb + f1_agua > 0:
                    c.execute("INSERT INTO caja (partido_id,concepto,monto,fecha) VALUES (?,?,?,?)",
                              (pid, f"Gastos partido vs {f1_rival.strip()}", -(f1_arb+f1_agua), str(f1_fecha)))
                conn.commit(); conn.close()
                # Limpiar borrador al guardar exitosamente
                st.session_state['f1_draft'] = {}
                resumen_cambios = ", ".join([f"{e} x {s} (min.{m})" for s,e,m in cambios_data]) if cambios_data else "ninguno"
                st.success(f"✅ Alineación guardada — {len(f1_titulares)} titulares, "
                           f"{len(cambios_data)} cambio(s). Ve a Fase 2 para registrar los eventos.")
                st.rerun()

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # FASE 2 — EVENTOS DEL PARTIDO (goles y tarjetas)
    # ════════════════════════════════════════════════════════════════════
    fase_header(2, "EVENTOS DEL PARTIDO", "Durante o al terminar — goles, tarjetas y resultado final", "#6b3010")

    if len(partidos_list) == 0:
        st.info("Primero guarda una alineación en la Fase 1.")
    else:
        opciones_f2 = [f"{r['fecha']} vs {r['rival']}" for _, r in partidos_list.iterrows()]
        sel_f2 = st.selectbox("Selecciona el partido", opciones_f2, key="sel_f2")
        pid_f2 = int(partidos_list.iloc[opciones_f2.index(sel_f2)]['id'])
        p_data = partidos_list[partidos_list['id']==pid_f2].iloc[0]

        # Participantes de este partido para los selectores
        partic_f2 = q("""SELECT j.nombre, pa.rol FROM participaciones pa
                         JOIN jugadores j ON pa.jugador_id=j.id
                         WHERE pa.partido_id=?""", (pid_f2,))
        nombres_f2 = partic_f2['nombre'].tolist() if len(partic_f2)>0 else nombres

        f2c1, f2c2 = st.columns(2)
        with f2c1:
            f2_gf = st.number_input("Goles a favor ⚽", min_value=0, step=1,
                                    value=int(p_data['goles_favor'] or 0), key="f2_gf")
        with f2c2:
            f2_gc = st.number_input("Goles en contra 🥅", min_value=0, step=1,
                                    value=int(p_data['goles_contra'] or 0), key="f2_gc")

        # Goleadores
        if f2_gf > 0:
            st.markdown("**⚽ ¿Quién anotó cada gol?**")
            nombres_con_desc = nombres_f2 + ["⬛ Desconocido / propia puerta"]
            goles_nuevos = []
            for i in range(int(f2_gf)):
                gc1, gc2 = st.columns([4, 1])
                with gc1:
                    gol_jug = st.selectbox(f"Gol #{i+1}", nombres_con_desc, key=f"f2_gol_{i}")
                with gc2:
                    gol_min = st.number_input("Min.", min_value=1, max_value=120,
                                              value=1, key=f"f2_min_{i}")
                goles_nuevos.append((gol_jug, gol_min))

        # Tarjetas — sistema de tarjetas individuales
        st.markdown("**🟨🟥 Tarjetas del partido**")
        st.caption("Agrega una fila por cada tarjeta. Si un jugador recibe 2 amarillas en el mismo partido = doble amarilla automática.")

        # Inicializar lista de tarjetas en session_state
        key_tarj = f"tarjetas_f2_{pid_f2}"
        if key_tarj not in st.session_state:
            # Cargar tarjetas ya guardadas de este partido
            tarj_existentes = q("""SELECT t.tipo, j.nombre FROM tarjetas t
                                   JOIN jugadores j ON t.jugador_id=j.id
                                   WHERE t.partido_id=? ORDER BY t.id""", (pid_f2,))
            st.session_state[key_tarj] = [
                {"jugador": row['nombre'], "tipo": row['tipo'], "minuto": 1}
                for _, row in tarj_existentes.iterrows()
            ] if len(tarj_existentes) > 0 else []

        # Multas por tarjeta
        key_multa_am  = f"multa_am_{pid_f2}"
        key_multa_dam = f"multa_dam_{pid_f2}"
        key_multa_ro  = f"multa_ro_{pid_f2}"
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            multa_amarilla = st.number_input("💰 Multa amarilla ($)", min_value=0.0,
                step=0.5, key=key_multa_am, value=0.0,
                help="Monto que paga el jugador por 1 amarilla simple")
        with mc2:
            multa_dam = st.number_input("💰 Multa doble amarilla ($)", min_value=0.0,
                step=0.5, key=key_multa_dam, value=0.0,
                help="Monto que paga el jugador por doble amarilla (2 amarillas en el mismo partido)")
        with mc3:
            multa_roja = st.number_input("💰 Multa roja directa ($)", min_value=0.0,
                step=0.5, key=key_multa_ro, value=0.0,
                help="Monto que paga el jugador por roja directa")

        # Mostrar tarjetas actuales
        tarjetas_actuales = st.session_state[key_tarj]
        if tarjetas_actuales:
            st.markdown("<small style='color:#d4b8b8;'>Tarjetas registradas:</small>", unsafe_allow_html=True)
            to_remove = []
            for i, t in enumerate(tarjetas_actuales):
                tc1, tc2, tc3, tc4 = st.columns([3, 2, 1, 1])
                with tc1:
                    st.markdown(f"**{t['jugador']}**")
                with tc2:
                    tipo_emoji = "🟨" if t['tipo']=='amarilla' else "🟥"
                    st.markdown(f"{tipo_emoji} {t['tipo'].capitalize()}")
                with tc3:
                    st.markdown(f"min. {t['minuto']}")
                with tc4:
                    if st.button("✕", key=f"rm_tarj_{i}_{pid_f2}"):
                        to_remove.append(i)
            for idx in reversed(to_remove):
                st.session_state[key_tarj].pop(idx)
            if to_remove:
                st.rerun()

            # Detectar y mostrar dobles amarillas
            from collections import Counter
            conteo_por_jugador = Counter(
                t['jugador'] for t in tarjetas_actuales if t['tipo']=='amarilla'
            )
            for jugador, cant in conteo_por_jugador.items():
                if cant >= 2:
                    st.markdown(f'<div class="alerta-box">🟨🟨 <b>{jugador}</b> tiene {cant} amarillas en este partido → <b>doble amarilla</b> (1 partido suspensión)</div>',
                                unsafe_allow_html=True)

        # Agregar nueva tarjeta
        st.markdown("<small style='color:#d4b8b8;'>Agregar tarjeta:</small>", unsafe_allow_html=True)
        na1, na2, na3, na4 = st.columns([3, 2, 1, 1])
        with na1:
            nueva_tarj_jug = st.selectbox("Jugador", nombres_f2, key=f"ntj_{pid_f2}")
        with na2:
            nueva_tarj_tipo = st.selectbox("Tipo", ["amarilla", "roja"], key=f"ntt_{pid_f2}")
        with na3:
            nueva_tarj_min = st.number_input("Min.", min_value=1, max_value=120,
                                             value=1, key=f"ntm_{pid_f2}")
        with na4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Agregar", key=f"add_tarj_{pid_f2}"):
                st.session_state[key_tarj].append({
                    "jugador": nueva_tarj_jug,
                    "tipo": nueva_tarj_tipo,
                    "minuto": nueva_tarj_min
                })
                st.rerun()

        f2_notas = st.text_area("📝 Notas del partido", height=60,
                                value=str(p_data['notas'] or ""), key="f2_notas")

        st.markdown("**📋 Comentarios del informe arbitral**")
        st.caption("Observaciones del árbitro, incidencias, protestas, decisiones polémicas, etc.")
        f2_arbitral = st.text_area("Informe arbitral", height=80,
                                   value=str(p_data.get('informe_arbitral', '') or ""),
                                   key="f2_arbitral",
                                   placeholder="Ej: El árbitro anuló un gol por fuera de juego en el min. 67. Hubo protestas por la tarjeta roja de Santiago. El partido se detuvo 3 minutos por lluvia...")

        # Vista previa de sanciones
        tarjetas_preview = st.session_state.get(key_tarj, [])
        if tarjetas_preview:
            from collections import Counter
            st.markdown("**⚠️ Sanciones que se generarán al guardar:**")
            conteo_am = Counter(t['jugador'] for t in tarjetas_preview if t['tipo']=='amarilla')
            for nombre, cant in conteo_am.items():
                if cant >= 2:
                    st.markdown(f"&nbsp;&nbsp;🟨🟨 **{nombre}** — doble amarilla → 1 partido suspensión")
                else:
                    rows = jugadores[jugadores['nombre']==nombre]
                    if len(rows)>0:
                        act = tarjetas_amarillas_activas(int(rows.iloc[0]['id']))
                        if act+1 >= 5:
                            st.markdown(f"&nbsp;&nbsp;🟨 **{nombre}** — llega a 5 amarillas → 1 partido suspensión")
                        else:
                            st.markdown(f"&nbsp;&nbsp;🟨 **{nombre}** — amarilla #{act+1} (sin suspensión aún)")
            for t in tarjetas_preview:
                if t['tipo'] == 'roja':
                    st.markdown(f"&nbsp;&nbsp;🟥 **{t['jugador']}** — roja directa → 2 partidos suspensión")

        if st.button("💾 GUARDAR EVENTOS", type="primary", key="btn_fase2"):
            from collections import Counter
            tarjetas_guardar = st.session_state.get(key_tarj, [])
            conn = get_conn(); c = conn.cursor()

            # Actualizar resultado, notas e informe arbitral
            c.execute("UPDATE partidos SET goles_favor=?,goles_contra=?,notas=?,informe_arbitral=? WHERE id=?",
                      (f2_gf, f2_gc, f2_notas, f2_arbitral, pid_f2))

            # Borrar goles anteriores y reinsertar
            c.execute("DELETE FROM goles WHERE partido_id=?", (pid_f2,))
            if f2_gf > 0:
                for gol_jug, gol_min in goles_nuevos:
                    if gol_jug == "⬛ Desconocido / propia puerta":
                        c.execute("INSERT INTO goles (partido_id,jugador_id,minuto,tipo) VALUES (?,NULL,?,?)",
                                  (pid_f2, gol_min, 'desconocido'))
                    else:
                        rows = jugadores[jugadores['nombre']==gol_jug]
                        if len(rows)>0:
                            c.execute("INSERT INTO goles (partido_id,jugador_id,minuto,tipo) VALUES (?,?,?,?)",
                                      (pid_f2, int(rows.iloc[0]['id']), gol_min, 'normal'))

            # Borrar tarjetas, sanciones y multas anteriores de este partido
            c.execute("DELETE FROM tarjetas WHERE partido_id=?", (pid_f2,))
            c.execute("DELETE FROM sanciones WHERE partido_origen_id=?", (pid_f2,))
            c.execute("DELETE FROM multas WHERE partido_id=?", (pid_f2,))

            # Insertar tarjetas individuales + sanciones + multas
            conteo_am_g = Counter(t['jugador'] for t in tarjetas_guardar if t['tipo']=='amarilla')
            sanciones_gen = []
            jugadores_multa_am_procesados = set()

            for t in tarjetas_guardar:
                rows = jugadores[jugadores['nombre']==t['jugador']]
                if len(rows)==0: continue
                jid = int(rows.iloc[0]['id'])
                c.execute("INSERT INTO tarjetas (partido_id,jugador_id,tipo,cumplida) VALUES (?,?,?,0)",
                          (pid_f2, jid, t['tipo']))

                # Multas: amarilla simple, doble amarilla o roja
                if t['tipo'] == 'amarilla' and t['jugador'] not in jugadores_multa_am_procesados:
                    es_doble = conteo_am_g.get(t['jugador'], 0) >= 2
                    if es_doble:
                        monto_m = st.session_state.get(key_multa_dam, 0.0)
                        concepto_m = f"Multa doble amarilla vs {p_data['rival']}"
                    else:
                        monto_m = st.session_state.get(key_multa_am, 0.0)
                        concepto_m = f"Multa amarilla vs {p_data['rival']}"
                    if monto_m > 0:
                        c.execute("""INSERT INTO multas (partido_id,jugador_id,concepto,monto,monto_pagado,pagado)
                                     VALUES (?,?,?,?,0,0)""",
                                  (pid_f2, jid, concepto_m, monto_m))
                    jugadores_multa_am_procesados.add(t['jugador'])

                if t['tipo'] == 'roja':
                    monto_m = st.session_state.get(key_multa_ro, 0.0)
                    if monto_m > 0:
                        c.execute("""INSERT INTO multas (partido_id,jugador_id,concepto,monto,monto_pagado,pagado)
                                     VALUES (?,?,?,?,0,0)""",
                                  (pid_f2, jid, f"Multa roja directa vs {p_data['rival']}", monto_m))

            # Sanciones según conteo final
            for nombre, cant in conteo_am_g.items():
                rows = jugadores[jugadores['nombre']==nombre]
                if len(rows)==0: continue
                jid = int(rows.iloc[0]['id'])
                if cant >= 2:
                    c.execute("""INSERT INTO sanciones (jugador_id,partido_origen_id,motivo,
                                 partidos_suspension,partidos_cumplidos) VALUES (?,?,'doble_amarilla',1,0)""",
                              (jid, pid_f2))
                    sanciones_gen.append(f"🟨🟨 {nombre}: 1 partido")
                else:
                    total_s = amarillas_simples_total(jid) + 1
                    if total_s % 5 == 0:
                        c.execute("""INSERT INTO sanciones (jugador_id,partido_origen_id,motivo,
                                     partidos_suspension,partidos_cumplidos) VALUES (?,?,'acumulacion_amarillas',1,0)""",
                                  (jid, pid_f2))
                        sanciones_gen.append(f"🟨×5 {nombre}: 1 partido")

            for t in tarjetas_guardar:
                if t['tipo'] == 'roja':
                    rows = jugadores[jugadores['nombre']==t['jugador']]
                    if len(rows)==0: continue
                    jid = int(rows.iloc[0]['id'])
                    c.execute("""INSERT INTO sanciones (jugador_id,partido_origen_id,motivo,
                                 partidos_suspension,partidos_cumplidos) VALUES (?,?,'roja_directa',2,0)""",
                              (jid, pid_f2))
                    sanciones_gen.append(f"🟥 {t['jugador']}: 2 partidos")

            conn.commit(); conn.close()
            # Limpiar session_state de tarjetas de este partido
            if key_tarj in st.session_state:
                del st.session_state[key_tarj]
            res_str = "Ganado ✅" if f2_gf>f2_gc else ("Empate 🤝" if f2_gf==f2_gc else "Perdido ❌")
            msg = f"✅ Eventos guardados — {f2_gf}:{f2_gc} ({res_str}). {len(tarjetas_guardar)} tarjeta(s)."
            if sanciones_gen: msg += f" Sanciones: {' | '.join(sanciones_gen)}"
            msg += " Ve a Fase 3 para registrar los cobros."
            st.success(msg)
            st.rerun()

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # FASE 3 — COBROS (mismo día o después)
    # ════════════════════════════════════════════════════════════════════
    fase_header(3, "COBROS", "Registra cuánto pagó cada uno — los valores pendientes se acumulan como deuda", "#1a5c2a")

    partidos_list = get_partidos()
    if len(partidos_list) == 0:
        st.info("Aún no hay partidos registrados.")
    else:
        opciones_f3 = [f"{r['fecha']} vs {r['rival']}" for _, r in partidos_list.iterrows()]
        sel_f3 = st.selectbox("Selecciona el partido", opciones_f3, key="sel_f3")
        pid_f3 = int(partidos_list.iloc[opciones_f3.index(sel_f3)]['id'])

        # ── Cuotas de arbitraje ──────────────────────────────────────────
        pagos_df = q("""
            SELECT pg.id, j.nombre, j.id as jugador_id,
                   pg.monto, COALESCE(pg.monto_pagado,0) as monto_pagado, pg.pagado,
                   COALESCE(pa.rol,'N/D') as rol
            FROM pagos pg
            JOIN jugadores j ON pg.jugador_id=j.id
            LEFT JOIN participaciones pa ON pa.jugador_id=pg.jugador_id AND pa.partido_id=pg.partido_id
            WHERE pg.partido_id=? ORDER BY pa.rol DESC, j.nombre
        """, (pid_f3,))

        if len(pagos_df) > 0:
            st.markdown("**⚽ Cuotas de arbitraje**")
            total_cuotas   = pagos_df['monto'].sum()
            cobrado_cuotas = pagos_df['monto_pagado'].sum()
            pend_cuotas    = total_cuotas - cobrado_cuotas
            cp1,cp2,cp3 = st.columns(3)
            with cp1:
                st.markdown(f"""<div class="metric-card"><div class="label">💰 Total cuotas</div>
                    <div class="valor" style="font-size:24px;">${total_cuotas:,.2f}</div></div>""", unsafe_allow_html=True)
            with cp2:
                st.markdown(f"""<div class="metric-card"><div class="label">✅ Cobrado</div>
                    <div class="valor" style="font-size:24px;color:#f0c040;">${cobrado_cuotas:,.2f}</div></div>""", unsafe_allow_html=True)
            with cp3:
                st.markdown(f"""<div class="metric-card"><div class="label">⏳ Pendiente</div>
                    <div class="valor" style="font-size:24px;color:#ff6b6b;">${pend_cuotas:,.2f}</div></div>""", unsafe_allow_html=True)

            st.markdown("<small style='color:#d4b8b8;'>Ingresa cuánto pagó cada jugador. Si paga menos del total, la diferencia queda como deuda acumulada.</small>", unsafe_allow_html=True)
            nuevos_pagos_cuota = {}
            for _, row in pagos_df.iterrows():
                deuda_previa = float(row['monto']) - float(row['monto_pagado'])
                if bool(row['pagado']): continue  # ya saldado
                rol_str = "⚽ Titular" if row['rol']=='titular' else ("🔄 Cambio" if row['rol']=='cambio' else "")
                col_nom, col_debe, col_paga = st.columns([3, 2, 2])
                with col_nom:
                    st.markdown(f"**{row['nombre']}** <small style='color:#d4b8b8;'>{rol_str}</small>", unsafe_allow_html=True)
                with col_debe:
                    st.markdown(f"Debe: <span style='color:#ff6b6b;font-weight:700;'>${deuda_previa:,.2f}</span>", unsafe_allow_html=True)
                with col_paga:
                    paga_ahora = st.number_input("Paga ahora $", min_value=0.0,
                        max_value=float(deuda_previa), value=0.0, step=0.5,
                        key=f"f3_cuota_{row['id']}", label_visibility="visible")
                nuevos_pagos_cuota[int(row['id'])] = (float(row['monto_pagado']), float(row['monto']), paga_ahora)

        # ── Multas por tarjetas ──────────────────────────────────────────
        multas_df = q("""SELECT m.id, j.nombre, m.concepto, m.monto,
                               COALESCE(m.monto_pagado,0) as monto_pagado, m.pagado
                         FROM multas m JOIN jugadores j ON m.jugador_id=j.id
                         WHERE m.partido_id=? AND m.pagado=0 ORDER BY j.nombre""", (pid_f3,))

        nuevas_multas = {}
        if len(multas_df) > 0:
            st.markdown("**⚠️ Multas por tarjetas**")
            for _, row in multas_df.iterrows():
                deuda_m = float(row['monto']) - float(row['monto_pagado'])
                mc_nom, mc_debe, mc_paga = st.columns([3, 2, 2])
                with mc_nom:
                    st.markdown(f"**{row['nombre']}** — {row['concepto']}")
                with mc_debe:
                    st.markdown(f"Debe: <span style='color:#ff6b6b;font-weight:700;'>${deuda_m:,.2f}</span>", unsafe_allow_html=True)
                with mc_paga:
                    paga_m = st.number_input("Paga ahora $", min_value=0.0,
                        max_value=float(deuda_m), value=0.0, step=0.5,
                        key=f"f3_multa_{row['id']}", label_visibility="visible")
                nuevas_multas[int(row['id'])] = (float(row['monto_pagado']), float(row['monto']), paga_m)

        # ── Gasto / ingreso adicional ─────────────────────────────────────
        st.markdown("**➕ Gasto / ingreso adicional del partido**")
        ga1, ga2 = st.columns([3, 1])
        with ga1:
            f3_concepto = st.text_input("Concepto", key="f3_concepto",
                placeholder="Ej: Botellón extra, bono patrocinador…")
        with ga2:
            f3_monto_extra = st.number_input("Monto ($)", step=0.5, key="f3_monto_extra",
                help="Positivo = ingreso, Negativo = gasto")

        if st.button("💾 GUARDAR COBROS", type="primary", key="btn_fase3"):
            conn = get_conn(); cambios = 0

            # Cuotas con pago parcial
            if len(pagos_df) > 0:
                for pid_p, (ya_pagado, monto_total, paga_ahora) in nuevos_pagos_cuota.items():
                    if paga_ahora > 0:
                        nuevo_total_pagado = ya_pagado + paga_ahora
                        saldado = nuevo_total_pagado >= monto_total - 0.001
                        conn.execute("UPDATE pagos SET monto_pagado=?, pagado=? WHERE id=?",
                                     (nuevo_total_pagado, int(saldado), pid_p))
                        # Registrar en caja solo el monto que paga ahora
                        pr = q("SELECT jugador_id, partido_id FROM pagos WHERE id=?", (pid_p,)).iloc[0]
                        jn = q("SELECT nombre FROM jugadores WHERE id=?", (int(pr['jugador_id']),)).iloc[0]['nombre']
                        conn.execute("INSERT INTO caja (partido_id,concepto,monto,fecha) VALUES (?,?,?,?)",
                            (pid_f3,
                             f"Pago {jn} — {sel_f3}" + (" (parcial)" if not saldado else ""),
                             paga_ahora, str(date.today())))
                        cambios += 1

            # Multas con pago parcial
            for multa_id, (ya_pagado, monto_total, paga_ahora) in nuevas_multas.items():
                if paga_ahora > 0:
                    nuevo_total_pagado = ya_pagado + paga_ahora
                    saldado = nuevo_total_pagado >= monto_total - 0.001
                    conn.execute("UPDATE multas SET monto_pagado=?, pagado=? WHERE id=?",
                                 (nuevo_total_pagado, int(saldado), multa_id))
                    mr = q("SELECT jugador_id, concepto FROM multas WHERE id=?", (multa_id,)).iloc[0]
                    jn = q("SELECT nombre FROM jugadores WHERE id=?", (int(mr['jugador_id']),)).iloc[0]['nombre']
                    conn.execute("INSERT INTO caja (partido_id,concepto,monto,fecha) VALUES (?,?,?,?)",
                        (pid_f3,
                         f"Multa {jn} — {mr['concepto']}" + (" (parcial)" if not saldado else ""),
                         paga_ahora, str(date.today())))
                    cambios += 1

            if f3_concepto.strip():
                conn.execute("INSERT INTO caja (partido_id,concepto,monto,fecha) VALUES (?,?,?,?)",
                    (pid_f3, f3_concepto.strip(), f3_monto_extra, str(date.today())))
                cambios += 1

            conn.commit(); conn.close()
            st.success(f"✅ {cambios} cobro(s) registrado(s). Los valores no pagados quedan como deuda acumulada.") if cambios else st.info("Sin cambios.")
            if cambios: st.rerun()

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # FASE 4 — SANCIONES (antes del próximo partido)
    # ════════════════════════════════════════════════════════════════════
    fase_header(4, "SANCIONES PENDIENTES", "Antes del próximo partido — marca suspensiones cumplidas", "#4a1060")

    sanciones_df = q("""
        SELECT s.id, j.nombre, s.motivo, s.partidos_suspension, s.partidos_cumplidos,
               p.fecha, p.rival, (s.partidos_suspension-s.partidos_cumplidos) as restantes
        FROM sanciones s JOIN jugadores j ON s.jugador_id=j.id
        JOIN partidos p ON s.partido_origen_id=p.id
        WHERE s.partidos_cumplidos<s.partidos_suspension ORDER BY p.fecha DESC
    """)
    if len(sanciones_df) == 0:
        st.markdown('<div class="ok-box">✅ No hay suspensiones pendientes. Todos pueden jugar.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alerta-box">⚠️ <b>{len(sanciones_df)}</b> sanción(es) pendiente(s). '
                    f'Marca como cumplida después de que el jugador se pierda el partido.</div>',
                    unsafe_allow_html=True)
        for _, s in sanciones_df.iterrows():
            sc1, sc2 = st.columns([5, 2])
            with sc1:
                st.markdown(
                    f'<div class="peligro-box">🚫 <b>{s["nombre"]}</b> — {MOTIVO_LABELS.get(s["motivo"],s["motivo"])}<br>'
                    f'<small>Partido vs <b>{s["rival"]}</b> ({s["fecha"]}) — '
                    f'<b>{int(s["restantes"])} partido(s)</b> pendiente(s) de {int(s["partidos_suspension"])}</small></div>',
                    unsafe_allow_html=True)
            with sc2:
                kc = f"kc_{s['id']}"
                if st.session_state.get(kc):
                    if st.button("✅ Confirmar cumplida", key=f"cfm_{s['id']}"):
                        run("UPDATE sanciones SET partidos_cumplidos=? WHERE id=?",
                            (int(s['partidos_cumplidos'])+1, int(s['id'])))
                        st.session_state[kc] = False; st.rerun()
                else:
                    if st.button("Marcar cumplida", key=f"mc_{s['id']}"):
                        st.session_state[kc] = True; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FINANZAS
# ══════════════════════════════════════════════════════════════════════════════
if IS_ADMIN:
 with TAB_FINANZAS:
    saldo = saldo_caja()
    partidos = get_partidos()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="label">💰 Saldo Total en Caja</div>
            <div class="valor">${saldo:,.0f}</div></div>""", unsafe_allow_html=True)
    jugadores = get_jugadores()
    total_deuda = sum(deuda_jugador(int(j['id'])) for _, j in jugadores.iterrows())
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="label">⚠️ Total Deudas</div>
            <div class="valor" style="color:#ff7b2e;">${total_deuda:,.0f}</div></div>""", unsafe_allow_html=True)
    total_gastado = q("SELECT COALESCE(SUM(costo_arbitraje+costo_agua),0) as t FROM partidos")['t'][0]
    with c3:
        st.markdown(f"""<div class="metric-card"><div class="label">💸 Total Gastado</div>
            <div class="valor" style="color:#ff6b6b;">${total_gastado:,.0f}</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">📒 MOVIMIENTOS DE CAJA</div>', unsafe_allow_html=True)
    caja_df = q("""SELECT c.fecha, c.concepto, c.monto,
                   CASE WHEN c.monto>=0 THEN '✅ Ingreso' ELSE '❌ Gasto' END as tipo
                   FROM caja c ORDER BY c.fecha DESC""")
    if len(caja_df) > 0:
        st.dataframe(caja_df, use_container_width=True, hide_index=True)
    else:
        st.info("Sin movimientos aún.")

    st.markdown('<div class="section-header">➕ REGISTRAR GASTO / INGRESO MANUAL</div>', unsafe_allow_html=True)
    with st.form("form_caja", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: concepto_caja = st.text_input("Concepto")
        with c2: monto_caja = st.number_input("Monto ($)", step=0.5, help="Positivo=ingreso, Negativo=gasto")
        with c3: fecha_caja = st.date_input("Fecha", value=date.today(), key="fecha_caja")
        if st.form_submit_button("💾 Registrar"):
            if concepto_caja:
                run("INSERT INTO caja (partido_id,concepto,monto,fecha) VALUES (?,?,?,?)",
                    (None, concepto_caja, monto_caja, str(fecha_caja)))
                st.success("✅ Movimiento registrado"); st.rerun()

    st.markdown('<div class="section-header">💸 DEUDAS POR JUGADOR</div>', unsafe_allow_html=True)
    jugadores = get_jugadores()
    deudas = []
    for _, j in jugadores.iterrows():
        jid = int(j['id'])
        d = deuda_jugador(jid)
        if d > 0:
            # Detalle cuotas pendientes
            cuotas_pend = q("""SELECT pa.fecha, pa.rival, pg.monto, COALESCE(pg.monto_pagado,0) as pagado
                               FROM pagos pg JOIN partidos pa ON pg.partido_id=pa.id
                               WHERE pg.jugador_id=? AND pg.pagado=0""", (jid,))
            detalle_c = ", ".join([
                f"vs {r['rival']} (${r['monto']-r['pagado']:,.2f})"
                for _, r in cuotas_pend.iterrows()
            ])
            # Detalle multas pendientes
            multas_pend = q("""SELECT m.concepto, m.monto, COALESCE(m.monto_pagado,0) as pagado
                               FROM multas m WHERE m.jugador_id=? AND m.pagado=0""", (jid,))
            detalle_m = ", ".join([
                f"{r['concepto']} (${r['monto']-r['pagado']:,.2f})"
                for _, r in multas_pend.iterrows()
            ])
            detalle = " | ".join(filter(None, [detalle_c, detalle_m]))
            deudas.append({"Jugador": j['nombre'], "Total Deuda": f"${d:,.2f}", "Detalle": detalle})
    if deudas:
        st.dataframe(pd.DataFrame(deudas), use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="ok-box">✅ Ningún jugador tiene deudas pendientes.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DISCIPLINA
# ══════════════════════════════════════════════════════════════════════════════
with TAB_DISCIPLINA:
    st.markdown('<div class="section-header">🟨 TARJETAS Y SANCIONES</div>', unsafe_allow_html=True)
    st.markdown("""<div class="alerta-box" style="font-size:13px;">
    📋 <b>Reglas:</b> 🟨×5 acumuladas = 1 partido &nbsp;|&nbsp;
    🟨🟨 doble amarilla = 1 partido &nbsp;|&nbsp; 🟥 roja directa = 2 partidos
    </div>""", unsafe_allow_html=True)

    jugadores = get_jugadores()
    datos_disc = []
    for _, j in jugadores.iterrows():
        jid = int(j['id'])
        am_t = amarillas_totales(jid)
        am_c = tarjetas_amarillas_activas(jid)
        am_d = partidos_doble_amarilla(jid)
        ro_t = q("SELECT COUNT(*) as c FROM tarjetas WHERE jugador_id=? AND tipo='roja'", (jid,))['c'][0]
        pend = sanciones_pendientes(jid)
        sanc = esta_sancionado(jid)
        estado = sanc if sanc else "✅ Disponible"
        datos_disc.append({"Jugador": j['nombre'], "🟨 Total": am_t, "🟨 Ciclo": am_c,
            "🟨🟨 Dobles": am_d, "🟥 Rojas": ro_t, "🚫 Pendientes": pend, "Estado": estado})

    st.dataframe(pd.DataFrame(datos_disc), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">🚫 NO PUEDEN JUGAR EL PRÓXIMO PARTIDO</div>', unsafe_allow_html=True)
    suspendidos = [(r['Jugador'], r['Estado']) for _, r in pd.DataFrame(datos_disc).iterrows() if "Suspendido" in r['Estado']]
    if suspendidos:
        for nombre, motivo in suspendidos:
            st.markdown(f'<div class="peligro-box">🔴 <b>{nombre}</b> — {motivo}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-box">✅ Todos los jugadores están disponibles.</div>', unsafe_allow_html=True)

    en_riesgo = [(r['Jugador'], r['🟨 Ciclo']) for _, r in pd.DataFrame(datos_disc).iterrows() if r['🟨 Ciclo'] == 4]
    if en_riesgo:
        st.markdown('<div class="section-header">⚠️ EN RIESGO — 4 AMARILLAS</div>', unsafe_allow_html=True)
        for nombre, _ in en_riesgo:
            st.markdown(f'<div class="alerta-box">🟨 <b>{nombre}</b> — 4 amarillas en el ciclo. ¡Una más = suspensión!</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">📋 HISTORIAL DE SANCIONES</div>', unsafe_allow_html=True)
    hist_sanc = q("""SELECT j.nombre, s.motivo, s.partidos_suspension, s.partidos_cumplidos,
               p.fecha, p.rival,
               CASE WHEN s.partidos_cumplidos>=s.partidos_suspension THEN '✅ Cumplida' ELSE '🚫 Pendiente' END as estado_sancion
               FROM sanciones s JOIN jugadores j ON s.jugador_id=j.id
               JOIN partidos p ON s.partido_origen_id=p.id ORDER BY p.fecha DESC""")
    if len(hist_sanc) > 0:
        ml = {'roja_directa':'🟥 Roja directa','doble_amarilla':'🟨🟨 Doble amarilla','acumulacion_amarillas':'🟨×5 Acumulación'}
        hist_sanc['motivo'] = hist_sanc['motivo'].map(ml).fillna(hist_sanc['motivo'])
        hist_sanc = hist_sanc.rename(columns={'nombre':'Jugador','motivo':'Motivo','partidos_suspension':'Partidos',
            'partidos_cumplidos':'Cumplidos','fecha':'Fecha','rival':'Rival','estado_sancion':'Estado'})
        st.dataframe(hist_sanc, use_container_width=True, hide_index=True)
    else:
        st.info("Sin sanciones registradas aún.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — HISTORIAL Y ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════════════════════
with TAB_HISTORIAL:
    partidos = get_partidos()

    if len(partidos) == 0:
        st.info("Aún no hay partidos registrados.")
    else:
        # ── EDITAR PARTIDO ──────────────────────────────────────────────────
        st.markdown('<div class="section-header">✏️ EDITAR PARTIDO</div>', unsafe_allow_html=True)
        st.caption("Selecciona un partido para corregir cualquier dato. Los cambios se guardan inmediatamente.")

        opciones_edit = [f"{r['fecha']} vs {r['rival']}" for _, r in partidos.iterrows()]
        sel_edit = st.selectbox("Partido a editar", opciones_edit, key="sel_edit")
        pid_edit = int(partidos.iloc[opciones_edit.index(sel_edit)]['id'])
        pe = partidos[partidos['id']==pid_edit].iloc[0]

        with st.expander("✏️ Abrir editor", expanded=False):
            jugadores_all = get_jugadores()
            nombres_all = jugadores_all['nombre'].tolist()

            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                e_fecha = st.date_input("Fecha", value=date.fromisoformat(str(pe['fecha'])), key="e_fecha")
                e_rival = st.text_input("Rival", value=str(pe['rival'] or ''), key="e_rival")
            with ec2:
                e_cancha = st.text_input("Cancha", value=str(pe['cancha'] or ''), key="e_cancha")
                e_arb    = st.number_input("Costo árbitro ($)", min_value=0.0, step=0.5,
                                            value=float(pe['costo_arbitraje'] or 0), key="e_arb")
                e_agua   = st.number_input("Costo botellón ($)", min_value=0.0, step=0.5,
                                            value=float(pe['costo_agua'] or 0), key="e_agua")
            with ec3:
                e_gf     = st.number_input("Goles a favor", min_value=0, step=1,
                                            value=int(pe['goles_favor'] or 0), key="e_gf")
                e_gc     = st.number_input("Goles en contra", min_value=0, step=1,
                                            value=int(pe['goles_contra'] or 0), key="e_gc")

            e_notas = st.text_area("Notas", value=str(pe['notas'] or ''), height=60, key="e_notas")
            e_arbitral = st.text_area("Comentarios arbitrales", height=70,
                                      value=str(pe.get('informe_arbitral','') or ''),
                                      key="e_arbitral")

            # Participantes actuales
            partic_edit = q("""SELECT j.nombre, pa.rol FROM participaciones pa
                               JOIN jugadores j ON pa.jugador_id=j.id
                               WHERE pa.partido_id=? ORDER BY pa.rol DESC, j.nombre""", (pid_edit,))
            tit_act = partic_edit[partic_edit['rol']=='titular']['nombre'].tolist()
            cam_act = partic_edit[partic_edit['rol']=='cambio']['nombre'].tolist()

            st.markdown("**Titulares**")
            e_titulares = st.multiselect("Titulares", nombres_all, default=tit_act, key="e_tit")
            st.markdown("**Jugadores al cambio**")
            e_cambios   = st.multiselect("Cambios", nombres_all, default=cam_act, key="e_cam")

            # Validación duplicado al editar (excluyendo el propio partido)
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                if st.button("💾 Guardar cambios del partido", type="primary", key="btn_edit_partido"):
                    # Verificar duplicado solo si cambia fecha o rival
                    dup = q("""SELECT id FROM partidos
                               WHERE fecha=? AND LOWER(rival)=LOWER(?) AND id!=?""",
                            (str(e_fecha), e_rival.strip(), pid_edit))
                    if len(dup) > 0:
                        st.error(f"⚠️ Ya existe otro partido el {e_fecha} contra '{e_rival.strip()}'.")
                    else:
                        conn = get_conn()
                        conn.execute("""UPDATE partidos SET fecha=?,rival=?,cancha=?,goles_favor=?,
                                       goles_contra=?,costo_arbitraje=?,costo_agua=?,notas=?,informe_arbitral=?
                                       WHERE id=?""",
                                     (str(e_fecha), e_rival.strip(), e_cancha,
                                      e_gf, e_gc, e_arb, e_agua, e_notas, e_arbitral, pid_edit))
                        # Actualizar participaciones
                        conn.execute("DELETE FROM participaciones WHERE partido_id=?", (pid_edit,))
                        for nombre in e_titulares:
                            rows = jugadores_all[jugadores_all['nombre']==nombre]
                            if len(rows)>0:
                                conn.execute("INSERT INTO participaciones (partido_id,jugador_id,rol) VALUES (?,?,?)",
                                             (pid_edit, int(rows.iloc[0]['id']), 'titular'))
                        for nombre in e_cambios:
                            rows = jugadores_all[jugadores_all['nombre']==nombre]
                            if len(rows)>0:
                                conn.execute("INSERT INTO participaciones (partido_id,jugador_id,rol) VALUES (?,?,?)",
                                             (pid_edit, int(rows.iloc[0]['id']), 'cambio'))
                        # Actualizar gasto en caja
                        conn.execute("DELETE FROM caja WHERE partido_id=? AND concepto LIKE 'Gastos partido%'",
                                     (pid_edit,))
                        if e_arb + e_agua > 0:
                            conn.execute("INSERT INTO caja (partido_id,concepto,monto,fecha) VALUES (?,?,?,?)",
                                         (pid_edit, f"Gastos partido vs {e_rival.strip()}",
                                          -(e_arb+e_agua), str(e_fecha)))
                        conn.commit(); conn.close()
                        st.success("✅ Partido actualizado correctamente.")
                        st.rerun()
            with e_col2:
                if st.button("🗑️ Eliminar este partido", key=f"del_edit_{pid_edit}"):
                    conn = get_conn()
                    for tbl, col in [('participaciones','partido_id'),('tarjetas','partido_id'),
                                     ('pagos','partido_id'),('caja','partido_id'),
                                     ('goles','partido_id'),('cambios','partido_id'),
                                     ('multas','partido_id'),('sanciones','partido_origen_id')]:
                        conn.execute(f"DELETE FROM {tbl} WHERE {col}=?", (pid_edit,))
                    conn.execute("DELETE FROM partidos WHERE id=?", (pid_edit,))
                    conn.commit(); conn.close()
                    st.success("Partido eliminado."); st.rerun()

        st.markdown("---")
        st.markdown('<div class="section-header">📈 ESTADÍSTICAS GENERALES</div>', unsafe_allow_html=True)

        total_p  = len(partidos)
        ganados  = len(partidos[partidos['goles_favor'] > partidos['goles_contra']])
        empates  = len(partidos[partidos['goles_favor'] == partidos['goles_contra']])
        perdidos = len(partidos[partidos['goles_favor'] < partidos['goles_contra']])
        puntos   = ganados * 3 + empates
        gf_total = int(partidos['goles_favor'].sum())
        gc_total = int(partidos['goles_contra'].sum())
        dif_goles = gf_total - gc_total

        kg1, kg2, kg3, kg4, kg5, kg6, kg7 = st.columns(7)
        def mk(col, label, val, color="#f0c040"):
            col.markdown(f"""<div class="metric-card" style="text-align:center;">
                <div class="label">{label}</div>
                <div class="valor" style="color:{color};font-size:30px;">{val}</div>
            </div>""", unsafe_allow_html=True)
        mk(kg1, "🏆 Puntos",   puntos,   "#f0c040")
        mk(kg2, "✅ Ganados",  ganados,  "#50e080")
        mk(kg3, "🤝 Empates",  empates,  "#f0c040")
        mk(kg4, "❌ Perdidos", perdidos, "#ff6b6b")
        mk(kg5, "⚽ GF",       gf_total, "#f0c040")
        mk(kg6, "🥅 GC",       gc_total, "#ff6b6b")
        mk(kg7, "📊 DIF",      f"+{dif_goles}" if dif_goles >= 0 else str(dif_goles),
           "#50e080" if dif_goles >= 0 else "#ff6b6b")

        # ── Tabla acumulada partido a partido ───────────────────────────────
        st.markdown('<div class="section-header">📊 TABLA ACUMULADA PARTIDO A PARTIDO</div>', unsafe_allow_html=True)
        st.caption("Los partidos están ordenados del más antiguo al más reciente para ver la progresión.")

        partidos_asc = partidos.sort_values('fecha', ascending=True).reset_index(drop=True)
        tabla_acum = []
        pts_acum = gf_acum = gc_acum = g_acum = e_acum = p_acum = 0
        for _, p in partidos_asc.iterrows():
            gf = int(p['goles_favor']) if p['goles_favor'] else 0
            gc = int(p['goles_contra']) if p['goles_contra'] else 0
            if gf > gc:   res = "✅ G"; pts = 3; g_acum += 1
            elif gf == gc: res = "🤝 E"; pts = 1; e_acum += 1
            else:          res = "❌ P"; pts = 0; p_acum += 1
            pts_acum += pts
            gf_acum  += gf
            gc_acum  += gc
            dif = gf_acum - gc_acum
            tabla_acum.append({
                "Fecha": p['fecha'],
                "Rival": p['rival'] or "—",
                "Marcador": f"{gf} - {gc}",
                "Res.": res,
                "Pts partido": pts,
                "🏆 Pts acum.": pts_acum,
                "✅ G": g_acum,
                "🤝 E": e_acum,
                "❌ P": p_acum,
                "⚽ GF acum.": gf_acum,
                "🥅 GC acum.": gc_acum,
                "📊 Dif.": f"+{dif}" if dif >= 0 else str(dif),
            })
        st.dataframe(pd.DataFrame(tabla_acum), use_container_width=True, hide_index=True)

        # ── Tabla de goleadores ─────────────────────────────────────────────
        st.markdown('<div class="section-header">🥇 TABLA DE GOLEADORES</div>', unsafe_allow_html=True)
        goleadores_df = q("""
            SELECT j.nombre, j.posicion,
                   COUNT(g.id) as goles,
                   COUNT(CASE WHEN g.tipo='normal' THEN 1 END) as goles_normales
            FROM jugadores j
            LEFT JOIN goles g ON j.id=g.jugador_id
            WHERE j.activo=1
            GROUP BY j.id, j.nombre, j.posicion
            HAVING goles > 0
            ORDER BY goles DESC
        """)
        if len(goleadores_df) > 0:
            for rank, (_, row) in enumerate(goleadores_df.iterrows(), 1):
                medal = "🥇" if rank==1 else ("🥈" if rank==2 else ("🥉" if rank==3 else f"#{rank}"))
                st.markdown(f"""<div class="jugador-card">
                    <div class="jugador-num" style="background:#3d2000;color:#f0c040;font-size:18px;">{medal}</div>
                    <div style="flex:1;">
                        <div style="font-weight:800;font-size:16px;">{row['nombre']}</div>
                        <div style="color:#d4b8b8;font-size:12px;">{row['posicion'] or '—'}</div>
                    </div>
                    <div style="font-family:'Bebas Neue',sans-serif;font-size:36px;color:#f0c040;">{int(row['goles'])} ⚽</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aún no hay goles registrados.")

        # ── Participaciones por jugador ─────────────────────────────────────
        st.markdown('<div class="section-header">👟 PARTICIPACIONES POR JUGADOR</div>', unsafe_allow_html=True)
        stats = q("""
            SELECT j.nombre, j.posicion,
                   COUNT(CASE WHEN pa.rol='titular' THEN 1 END) as titulares,
                   COUNT(CASE WHEN pa.rol='cambio' THEN 1 END) as cambios,
                   COUNT(DISTINCT g.partido_id) as partidos_gol,
                   COALESCE(SUM(CASE WHEN g2.jugador_id=j.id THEN 1 ELSE 0 END),0) as goles,
                   COUNT(CASE WHEN t.tipo='amarilla' THEN 1 END) as amarillas,
                   COUNT(CASE WHEN t.tipo='roja' THEN 1 END) as rojas
            FROM jugadores j
            LEFT JOIN participaciones pa ON j.id=pa.jugador_id
            LEFT JOIN goles g ON j.id=g.jugador_id
            LEFT JOIN goles g2 ON j.id=g2.jugador_id
            LEFT JOIN tarjetas t ON j.id=t.jugador_id
            WHERE j.activo=1
            GROUP BY j.id, j.nombre, j.posicion
            ORDER BY (titulares+cambios) DESC
        """)
        if len(stats) > 0:
            st.dataframe(stats.rename(columns={
                'nombre':'Jugador','posicion':'Posición',
                'titulares':'⚽ Titular','cambios':'🔄 Cambio',
                'goles':'⚽ Goles','amarillas':'🟨','rojas':'🟥'
            }).drop(columns=['partidos_gol']), use_container_width=True, hide_index=True)

        # ── Historial detallado ─────────────────────────────────────────────
        st.markdown('<div class="section-header">📅 HISTORIAL DETALLADO DE PARTIDOS</div>', unsafe_allow_html=True)
        for _, p in partidos.iterrows():
            pid = int(p['id'])
            gf = int(p['goles_favor']) if p['goles_favor'] else 0
            gc = int(p['goles_contra']) if p['goles_contra'] else 0
            resultado = "✅ Ganado" if gf > gc else ("🤝 Empate" if gf == gc else "❌ Perdido")

            partic = q("""SELECT j.nombre, pa.rol FROM participaciones pa
                JOIN jugadores j ON pa.jugador_id=j.id WHERE pa.partido_id=?""", (pid,))
            tit_str = ", ".join(partic[partic['rol']=='titular']['nombre'].tolist()) or "N/D"
            cam_str = ", ".join(partic[partic['rol']=='cambio']['nombre'].tolist()) or "Ninguno"

            tarj = q("""SELECT j.nombre, t.tipo FROM tarjetas t
                JOIN jugadores j ON t.jugador_id=j.id WHERE t.partido_id=?""", (pid,))
            am_str = ", ".join(tarj[tarj['tipo']=='amarilla']['nombre'].tolist()) or "—"
            ro_str = ", ".join(tarj[tarj['tipo']=='roja']['nombre'].tolist()) or "—"

            goles_p = q("""SELECT COALESCE(j.nombre,'Desconocido') as nombre, g.minuto, g.tipo
                FROM goles g LEFT JOIN jugadores j ON g.jugador_id=j.id
                WHERE g.partido_id=? ORDER BY g.minuto""", (pid,))

            pagos_p = q("SELECT COUNT(*) as total, SUM(pagado) as pagaron FROM pagos WHERE partido_id=?", (pid,))
            total_j = int(pagos_p['total'][0]) if pagos_p['total'][0] else 0
            pagaron = int(pagos_p['pagaron'][0]) if pagos_p['pagaron'][0] else 0

            with st.expander(f"📅 {p['fecha']} — vs {p['rival'] or 'Rival'} — {gf}:{gc} {resultado}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    st.markdown(f"**Cancha:** {p['cancha'] or 'N/D'}")
                    st.markdown(f"**Resultado:** {gf} — {gc} ({resultado})")
                    st.markdown(f"**Árbitro:** ${p['costo_arbitraje'] or 0:,.0f} | **Agua:** ${p['costo_agua'] or 0:,.0f}")
                    st.markdown(f"**Pagos:** {pagaron}/{total_j} jugadores pagaron")
                with ec2:
                    st.markdown(f"**🟨 Amarillas:** {am_str}")
                    st.markdown(f"**🟥 Rojas:** {ro_str}")
                    if p['notas']:
                        st.markdown(f"**📝 Notas:** {p['notas']}")
                st.markdown(f"**⚽ Titulares:** {tit_str}")
                st.markdown(f"**🔄 Cambios:** {cam_str}")

                # Mostrar cambios detallados
                cambios_det = q("""SELECT js.nombre as sale, je.nombre as entra, c.minuto
                                   FROM cambios c
                                   JOIN jugadores js ON c.jugador_sale_id=js.id
                                   JOIN jugadores je ON c.jugador_entra_id=je.id
                                   WHERE c.partido_id=? ORDER BY c.minuto""", (pid,))
                if len(cambios_det) > 0:
                    st.markdown("**↔️ Detalles de cambios:**")
                    for _, ch in cambios_det.iterrows():
                        min_str = f"min. {int(ch['minuto'])}" if ch['minuto'] else ""
                        st.markdown(f"&nbsp;&nbsp;↗️ Sale **{ch['sale']}** → Entra **{ch['entra']}** {min_str}")

                if len(goles_p) > 0:
                    st.markdown("**⚽ Goles:**")
                    for _, g in goles_p.iterrows():
                        min_str = f"min. {int(g['minuto'])}" if g['minuto'] else ""
                        st.markdown(f"&nbsp;&nbsp;⚽ **{g['nombre']}** {min_str}")

                if st.button("🗑️ Eliminar partido", key=f"del_{pid}"):
                    conn = get_conn()
                    for tbl, col in [('participaciones','partido_id'),('tarjetas','partido_id'),
                                     ('pagos','partido_id'),('caja','partido_id'),
                                     ('goles','partido_id'),('cambios','partido_id'),
                                     ('multas','partido_id'),('sanciones','partido_origen_id')]:
                        conn.execute(f"DELETE FROM {tbl} WHERE {col}=?", (pid,))
                    conn.execute("DELETE FROM partidos WHERE id=?", (pid,))
                    conn.commit(); conn.close()
                    st.success("Partido eliminado"); st.rerun()

                # Botón de descarga PDF
                pdf_bytes = generar_pdf_partido(pid)
                if pdf_bytes:
                    nombre_pdf = f"informe_{p['fecha']}_vs_{(p['rival'] or 'rival').replace(' ','_')}.pdf"
                    st.download_button(
                        label="📄 Descargar informe PDF",
                        data=pdf_bytes,
                        file_name=nombre_pdf,
                        mime="application/pdf",
                        key=f"pdf_{pid}"
                    )

# ══════════════════════════════════════════════════════════════════
# app.py — Punto de entrada OVOMAS Streamlit
# Panel General + Navegación lateral
# v2.0 — con persistencia Google Drive
# ══════════════════════════════════════════════════════════════════
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

st.set_page_config(
    page_title="OVOMAS v4.1",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import require_auth, can_write, can_delete, current_user, logout
from state import (
    get_engine, reset_engine,
    engine_to_excel_bytes, load_engine_from_excel,
    guardar_estado, estado_drive,
)
from ui_components import inject_css, header, section, alert, badge, fig_barras, fig_pie, PAL

inject_css()
require_auth()

ov = get_engine()

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    # ── Logo + marca ─────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #E65100, #BF360C);
        border-radius: 10px;
        padding: 14px 16px;
        margin: -8px -8px 8px -8px;
    ">
        <div style="font-size:1.6em; margin-bottom:3px;">🐔</div>
        <div style="
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 1.05em;
            letter-spacing: 2.5px;
            color: #FFFFFF;
        ">OVOMAS v4.1</div>
        <div style="
            font-size: 0.68em;
            color: rgba(255,255,255,0.6);
            letter-spacing: 1.5px;
            margin-top: 2px;
            text-transform: uppercase;
        ">Sistema Integral Avícola</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Menú modular agrupado ────────────────────────────────────
    st.markdown("""
    <style>
    .nav-divider {
        border: none; border-top: 1px solid rgba(255,255,255,0.08);
        margin: 8px 0;
    }

    <hr class="nav-divider">
    """, unsafe_allow_html=True)

    # ── Fábrica de Balanceado ─────────────────────────────────
    st.markdown("""<div style="
        background:linear-gradient(90deg,rgba(230,81,0,0.35),rgba(230,81,0,0.08));
        border-left:3px solid #E65100; border-radius:0 6px 6px 0;
        padding:6px 10px; margin:8px 0 3px 0;
        font-size:0.7em; font-weight:800; letter-spacing:1.5px;
        color:#FFCCBC; font-family:monospace; text-transform:uppercase;
    ">🏭 Fábrica de Balanceado</div>""", unsafe_allow_html=True)
    st.page_link("pages/1___Materia_Prima.py",   label="🌾  Materia Prima",   use_container_width=True)
    st.page_link("pages/2___Balanceado.py",      label="🎒  Balanceados",     use_container_width=True)

    # ── Galpones Avícolas ─────────────────────────────────────
    st.markdown("""<div style="
        background:linear-gradient(90deg,rgba(27,94,32,0.45),rgba(27,94,32,0.08));
        border-left:3px solid #4CAF50; border-radius:0 6px 6px 0;
        padding:6px 10px; margin:10px 0 3px 0;
        font-size:0.7em; font-weight:800; letter-spacing:1.5px;
        color:#C8E6C9; font-family:monospace; text-transform:uppercase;
    ">🐔 Galpones Avícolas</div>""", unsafe_allow_html=True)
    st.page_link("pages/3___Lotes_de_Aves.py",   label="🐣  Lotes de Aves",  use_container_width=True)
    st.page_link("pages/4___Registro_Diario.py", label="📝  Registro Diario", use_container_width=True)
    st.page_link("pages/5___Huevos.py",          label="🥚  Huevos",          use_container_width=True)
    st.page_link("pages/6_💉_Salud.py",          label="💉  Salud",           use_container_width=True)

    # ── Administración ────────────────────────────────────────
    st.markdown("""<div style="
        background:linear-gradient(90deg,rgba(21,101,192,0.35),rgba(21,101,192,0.08));
        border-left:3px solid #2196F3; border-radius:0 6px 6px 0;
        padding:6px 10px; margin:10px 0 3px 0;
        font-size:0.7em; font-weight:800; letter-spacing:1.5px;
        color:#BBDEFB; font-family:monospace; text-transform:uppercase;
    ">📊 Administración</div>""", unsafe_allow_html=True)
    st.page_link("pages/7_📈_Kardex_y_Reportes.py", label="📈  Kardex y Reportes", use_container_width=True)
    st.page_link("pages/8___Costos.py",             label="💰  Costos",             use_container_width=True)
    st.page_link("pages/9___Planificacion.py",       label="📋  Planificación",      use_container_width=True)

    st.markdown("---")

    # ── Cerrar sesión ────────────────────────────────────────
    user_info = current_user()
    st.markdown(f"""<div style="font-size:0.75em;color:#78909C;padding:4px 0">👤 {user_info.get('username','')} · {user_info.get('role_info',{}).get('label','')}</div>""", unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", use_container_width=True, key="btn_logout"):
        logout()
        st.rerun()

    st.markdown("---")

    # ── Estado Google Drive ───────────────────────────────────────
    st.markdown("### ☁️ Google Drive")
    try:
        from sheets_sync import sheets_disponible
        _drive_ok = sheets_disponible()
    except Exception:
        _drive_ok = False

    if _drive_ok:
        _ultimo = st.session_state.get("ultimo_guardado", "")
        try:
            dt = datetime.fromisoformat(str(_ultimo).replace("Z",""))
            _ultimo_fmt = dt.strftime("%d/%m/%Y  %H:%M")
        except Exception:
            _ultimo_fmt = "Esta sesión"
        st.markdown(f"""
        <div style="
            background: rgba(46,125,50,0.18);
            border: 1px solid rgba(76,175,80,0.35);
            border-left: 3px solid #4CAF50;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            font-family: monospace;
        ">
            <div style="color:#69F0AE; font-size:0.75em; font-weight:700; letter-spacing:1px">● CONECTADO</div>
            <div style="color:#78909C; font-size:0.7em; margin-top:3px">Último guardado</div>
            <div style="color:#E8EDF2; font-size:0.8em; font-weight:600">{_ultimo_fmt}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("☁️  Guardar en Drive", use_container_width=True, disabled=not can_write()):
            with st.spinner("Guardando..."):
                res = guardar_estado(ov)
            if res["ok"]:
                st.session_state["ultimo_guardado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success("Guardado ✓")
            else:
                st.error(res["msg"])
    else:
        st.markdown("""
        <div style="
            background: rgba(230,81,0,0.12);
            border: 1px solid rgba(230,81,0,0.3);
            border-left: 3px solid #E65100;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            font-family: monospace;
        ">
            <div style="color:#FF8A65; font-size:0.75em; font-weight:700; letter-spacing:1px">● NO DISPONIBLE</div>
            <div style="color:#78909C; font-size:0.7em; margin-top:2px">Verifica credenciales .json</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Estado rápido ─────────────────────────────────────────────
    st.markdown("### 📊 Estado del sistema")
    n_mp  = len(ov.materias_primas)
    n_rec = len(ov.recetas[ov.recetas["estado"] == "ACTIVA"]) if len(ov.recetas) > 0 else 0
    n_lot = len(ov.lotes_aves[ov.lotes_aves["estado"] == "ACTIVO"]) if len(ov.lotes_aves) > 0 else 0
    n_reg = len(ov.registro_diario)

    def _stat(icon, label, valor, ok):
        c = "#69F0AE" if ok else "#FF5252"
        return (
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:5px 8px;border-radius:6px;margin:2px 0;"
            f"background:rgba(255,255,255,0.04);'>"
            f"<span style='color:#90A4AE;font-size:0.78em;font-family:monospace'>{icon} {label}</span>"
            f"<span style='color:{c};font-size:0.78em;font-weight:700;font-family:monospace'>{valor}</span>"
            f"</div>"
        )

    st.markdown(
        _stat("🌾", "Mat. Prima",  f"{n_mp} ing.",      n_mp > 0) +
        _stat("🎒", "Recetas",     f"{n_rec} activas",  n_rec > 0) +
        _stat("🐔", "Lotes",       f"{n_lot} activos",  n_lot > 0) +
        _stat("📝", "Registros",   f"{n_reg} días",     n_reg > 0),
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ── Backup ────────────────────────────────────────────────────
    st.markdown("### 💾 Backup local")
    st.markdown("""
    <style>
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] > button,
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
        background: rgba(230,81,0,0.35) !important;
        border: 1px solid #E65100 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.06) !important;
        border: 1px dashed rgba(255,255,255,0.2) !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #90A4AE !important;
        font-size: 0.75em !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("⬇️  Exportar a Excel", use_container_width=True):
        try:
            xls_bytes = engine_to_excel_bytes(ov)
            nombre = f"ovomas_backup_{date.today().strftime('%Y%m%d')}.xlsx"
            st.download_button(
                "📥 Descargar backup", data=xls_bytes,
                file_name=nombre,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error: {e}")

    if can_delete():
        uploaded = st.file_uploader("Cargar backup .xlsx", type=["xlsx"], label_visibility="collapsed")
        if uploaded:
            try:
                ov, tablas_ok = load_engine_from_excel(uploaded.read())
                guardar_estado(ov)
                st.success(f"✓ {tablas_ok} tablas restauradas")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")

    # ── Sistema ───────────────────────────────────────────────────
    st.markdown("### ⚙️ Sistema")
    if st.button("🔄  Reiniciar sistema", use_container_width=True, disabled=not can_delete()):
        reset_engine()
        st.rerun()


header("PANEL GENERAL", date.today().strftime("📅 %d de %B de %Y"))

hoy = date.today().strftime("%Y-%m-%d")

# ── KPIs globales ─────────────────────────────────────────────────
total_aves    = 0
total_hue_hoy = 0
gal_activos   = 0
total_cubetas = 0

galpones_prod = [g for g in ov.GALPONES if not ov.GALPONES[g].get("temporal")]

resumen_galp = []
for g in galpones_prod:
    lts = ov.lotes_aves[
        (ov.lotes_aves["galpon_actual"] == g) & (ov.lotes_aves["estado"] == "ACTIVO")
    ]
    if len(lts) == 0:
        resumen_galp.append({
            "galpon": g, "planta": ov.GALPONES[g]["planta"],
            "aves": 0, "edad_s": 0, "fase": "—",
            "pct_pos": 0, "huevos": 0, "estado": "vacío",
        })
        continue

    lote   = lts.iloc[0]
    edad_s = ov._edad_dias(lote["fecha_nacimiento"]) // 7
    params = ov._params_edad(edad_s)
    fase   = params["fase"] if params else "—"

    reg_df = ov.registro_diario[ov.registro_diario["galpon"] == g]
    reg_op = ov._filtro_operativo(reg_df).sort_values("fecha")
    pct  = float(reg_op.iloc[-1]["pct_produccion"]) if len(reg_op) > 0 else 0
    hue  = int(float(reg_op.iloc[-1]["huevos_producidos"])) if len(reg_op) > 0 else 0
    en_r, _ = ov._en_retiro(g, hoy)

    # Calcular aves actuales = inicial - mortalidad acumulada histórica + operativa
    aves_inicial = int(float(lote.get("cantidad_inicial", lote["cantidad_actual"])))
    mort_acum = 0
    if len(ov.registro_diario) > 0:
        reg_g = ov.registro_diario[ov.registro_diario["galpon"] == g]
        mort_acum = int(pd.to_numeric(reg_g["mortalidad"], errors="coerce").fillna(0).sum())
    aves = max(0, aves_inicial - mort_acum)

    total_aves    += aves
    total_hue_hoy += hue
    gal_activos   += 1
    total_cubetas += hue / 30

    resumen_galp.append({
        "galpon": g, "planta": ov.GALPONES[g]["planta"],
        "aves": aves, "edad_s": edad_s, "fase": fase,
        "pct_pos": round(pct, 1), "huevos": hue,
        "estado": "⚠️ RETIRO" if en_r else "✅ OK",
    })

# KPI row
def _cubetas_planta(planta):
    bodegas = [b for b, info in ov.BODEGAS.items()
               if info.get("tipo") == "huevos" and info.get("planta") == planta]
    if not bodegas or len(ov.inventario_huevos) == 0:
        return 0.0
    total = ov.inventario_huevos[ov.inventario_huevos["bodega"].isin(bodegas)]["cubetas_disponibles"].apply(
        pd.to_numeric, errors="coerce").fillna(0).sum()
    return round(float(total), 1)

cub_central  = _cubetas_planta("Central")
cub_sucursal = _cubetas_planta("Sucursal")
n_mp_bajos = len(ov.materias_primas[ov.materias_primas["stock_kg"] < ov.materias_primas["stock_minimo"]]) if n_mp > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🐔 Aves totales",        f"{total_aves:,}")
col2.metric("📦 Cubetas P. Central",  f"{cub_central:.1f}")
col3.metric("📦 Cubetas P. Sucursal", f"{cub_sucursal:.1f}")
col4.metric("🏠 Galpones activos",    gal_activos)
col5.metric("⚠️ MP bajo mínimo",     n_mp_bajos,
            delta="-" if n_mp_bajos > 0 else "OK", delta_color="inverse")

st.markdown("---")

# ── Tabla de galpones ─────────────────────────────────────────────
section("ESTADO POR GALPÓN")

df_galp = pd.DataFrame(resumen_galp)
if len(df_galp) > 0:
    df_show = df_galp.rename(columns={
        "galpon": "Galpón", "planta": "Planta", "aves": "Aves",
        "edad_s": "Semanas", "fase": "Fase Productiva",
        "pct_pos": "% Postura", "huevos": "Huevos", "estado": "Estado",
    })
    st.dataframe(df_show, use_container_width=True, height=240,
                 column_config={
                     "Aves":      st.column_config.NumberColumn(format="%d"),
                     "Huevos":    st.column_config.NumberColumn(format="%d"),
                     "% Postura": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                 })

st.markdown("---")

# ── Gráficos ──────────────────────────────────────────────────────
col_g1, col_g2 = st.columns(2)

with col_g1:
    aves_vals = [r["aves"] for r in resumen_galp]
    gal_names = [r["galpon"] for r in resumen_galp]
    if any(a > 0 for a in aves_vals):
        colores = [PAL["verde"] if a > 0 else PAL["gris_cl"] for a in aves_vals]
        fig = go.Figure(go.Bar(
            x=gal_names, y=aves_vals,
            marker_color=colores, marker_line_color="white", marker_line_width=1.5,
            text=[f"{a:,}" if a > 0 else "—" for a in aves_vals],
            textposition="outside",
        ))
        fig.update_layout(
            title="🐔 Aves por galpón", template="plotly_white",
            plot_bgcolor="#F9FBE7", paper_bgcolor="#FAFAFA",
            font_family="monospace", height=320,
            margin=dict(t=40, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        alert("Sin aves registradas. Ve a <b>Lotes de Aves</b> para registrar el primer lote.", "amber")

with col_g2:
    vals_pie = [(r["galpon"], r["aves"]) for r in resumen_galp if r["aves"] > 0]
    if vals_pie:
        labs, vals = zip(*vals_pie)
        st.plotly_chart(fig_pie(labs, vals, "📊 Distribución de aves"), use_container_width=True)
    else:
        alert("Sin datos para gráfico de distribución.", "amber")

# ── Tendencia producción últimos 14 días ──────────────────────────
st.markdown("---")
section("TENDENCIA DE PRODUCCIÓN — ÚLTIMOS 14 DÍAS")

fecha_14 = (date.today() - timedelta(days=14)).strftime("%Y-%m-%d")
reg_rec  = ov.registro_diario[ov.registro_diario["fecha"] >= fecha_14].copy()
reg_rec  = ov._filtro_operativo(reg_rec)

if len(reg_rec) > 1:
    df_trend = reg_rec.groupby("fecha").agg(
        huevos=("huevos_producidos", "sum"),
        pct_avg=("pct_produccion", "mean"),
        bal_kg=("kg_balanceado", "sum"),
    ).reset_index().sort_values("fecha")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fig_hue = go.Figure()
        fig_hue.add_trace(go.Bar(
            x=df_trend["fecha"], y=df_trend["huevos"],
            name="Huevos/día", marker_color=PAL["naranja_cl"],
        ))
        fig_hue.add_trace(go.Scatter(
            x=df_trend["fecha"], y=df_trend["pct_avg"],
            name="% Postura", yaxis="y2",
            line=dict(color=PAL["verde"], width=2.5),
            mode="lines+markers", marker=dict(size=5),
        ))
        fig_hue.update_layout(
            title="🥚 Huevos y % Postura diarios", template="plotly_white",
            yaxis=dict(title="Huevos", gridcolor="#E0E0E0"),
            yaxis2=dict(title="% Postura", overlaying="y", side="right"),
            font_family="monospace", height=320, plot_bgcolor="#FFF9F0",
            paper_bgcolor="#FAFAFA", legend=dict(orientation="h"),
            margin=dict(t=40, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_hue, use_container_width=True)

    with col_t2:
        fig_bal = go.Figure(go.Bar(
            x=df_trend["fecha"], y=df_trend["bal_kg"],
            marker_color=PAL["azul_cl"], marker_line_color="white",
        ))
        fig_bal.update_layout(
            title="🎒 Balanceado consumido (kg/día)", template="plotly_white",
            font_family="monospace", height=320, plot_bgcolor="#F3F8FF",
            paper_bgcolor="#FAFAFA", yaxis_title="kg",
            margin=dict(t=40, b=10, l=10, r=10),
        )
        fig_bal.update_yaxes(gridcolor="#E0E0E0")
        st.plotly_chart(fig_bal, use_container_width=True)
else:
    alert("Se necesitan al menos 2 días de registro para ver tendencias. Completa el <b>Registro Diario</b>.", "blue")

# ── Alertas activas ───────────────────────────────────────────────
alertas = []
if n_mp_bajos > 0:
    ings_bajos = ov.materias_primas[
        ov.materias_primas["stock_kg"] < ov.materias_primas["stock_minimo"]
    ]["ingrediente"].tolist()
    alertas.append(f"🔴 <b>Stock MP bajo mínimo:</b> {', '.join(ings_bajos)}")

ev_activos = ov.eventos_salud[ov.eventos_salud["estado"] == "EN CURSO"] if len(ov.eventos_salud) > 0 else pd.DataFrame()
if len(ev_activos) > 0:
    for _, ev in ev_activos.iterrows():
        alertas.append(f"🚨 <b>Evento salud activo:</b> {ev['galpon']} — {ev['enfermedad']} ({ev['gravedad']})")

inv_bal      = ov.inventario_balanceado[ov.inventario_balanceado["bultos_disponibles"] > 0] if len(ov.inventario_balanceado) > 0 else pd.DataFrame()
total_bultos = int(float(inv_bal["bultos_disponibles"].sum())) if len(inv_bal) > 0 else 0
if total_bultos < 50:
    alertas.append(f"⚠️ <b>Balanceado bajo:</b> solo {total_bultos} bultos en inventario total.")

if alertas:
    st.markdown("---")
    section("🔔 ALERTAS ACTIVAS")
    for a in alertas:
        alert(a, "red")

# ⚽ Sistema de Gestión de Equipo de Fútbol

Dashboard completo para gestionar tu equipo: finanzas, alineaciones, tarjetas y sanciones.

---

## 🚀 CÓMO SUBIR A STREAMLIT CLOUD (paso a paso)

### Paso 1 — Crear cuenta en GitHub
1. Ve a [github.com](https://github.com) y crea una cuenta gratuita si no tienes.

### Paso 2 — Crear un repositorio nuevo
1. Haz clic en el botón verde **"New"** (o el ícono `+` arriba a la derecha).
2. Ponle un nombre, por ejemplo: `mi-equipo-futbol`
3. Deja todo por defecto y haz clic en **"Create repository"**.

### Paso 3 — Subir los archivos
Sube estos 2 archivos al repositorio:
- `app.py`
- `requirements.txt`

Para subirlos: en la página del repositorio haz clic en **"uploading an existing file"** y arrastra los dos archivos.

### Paso 4 — Crear cuenta en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub.

### Paso 5 — Desplegar la app
1. Haz clic en **"New app"**
2. Selecciona tu repositorio `mi-equipo-futbol`
3. En "Main file path" escribe: `app.py`
4. Haz clic en **"Deploy!"**

¡Listo! En 2-3 minutos tendrás tu app en internet con una URL que puedes abrir desde el celular.

---

## 📱 Usar desde el celular
- Abre la URL que te da Streamlit Cloud desde cualquier navegador.
- Funciona perfectamente en Chrome o Safari en el celular.
- Puedes agregarla a la pantalla de inicio como si fuera una app.

---

## ✅ Funcionalidades incluidas

### 🏠 Inicio
- Saldo actual de la caja
- Alertas de jugadores sancionados o con deudas
- Resumen del último partido

### 👥 Jugadores
- Agregar, editar y desactivar jugadores
- Marcar quién es exento de arbitraje o uniforme
- Ver estado de tarjetas y deudas de cada jugador

### ⚽ Partido
- Registrar fecha, rival, resultado (goles)
- Seleccionar titulares y jugadores que entraron al cambio
- Registrar tarjetas amarillas y rojas del partido
- Definir cuota por jugador (solo a los no exentos)
- Marcar quién pagó y quién quedó debiendo
- Cumplir sanciones por tarjeta roja

### 💰 Finanzas
- Saldo total de la caja
- Movimientos detallados (ingresos y gastos)
- Registrar gastos/ingresos manuales
- Tabla de deudas pendientes por jugador con detalle de partidos

### 🟨 Disciplina
- Tabla completa de tarjetas por jugador
- Alertas automáticas: 5 amarillas = suspensión 1 partido
- Tarjeta roja = suspensión 2 partidos
- Aviso cuando un jugador lleva 4 amarillas (en riesgo)

### 📊 Historial
- Historial completo de partidos con todos los datos
- Estadísticas: ganados, empates, perdidos, goles
- Tabla de participaciones por jugador (titular/cambio)

---

## ⚠️ Notas importantes
- La base de datos (`equipo.db`) se guarda en el servidor de Streamlit Cloud.
  **Se resetea si la app lleva más de 7 días inactiva** en el plan gratuito.
- Para evitar perder datos, se recomienda hacer un respaldo periódico descargando
  el archivo `equipo.db` desde el panel de Streamlit Cloud.
- Si quieres datos permanentes, considera actualizar a Streamlit Cloud Teams 
  o usar una base de datos externa gratuita como [Supabase](https://supabase.com).

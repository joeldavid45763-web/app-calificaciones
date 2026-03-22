import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="App Calificaciones", page_icon="📚", layout="wide")

# --- 2. CONEXIÓN A GOOGLE SHEETS (USANDO LA BÓVEDA SECRETA) ---
try:
    # Cargar la llave desde la bóveda secreta de Streamlit
    creds_dict = json.loads(st.secrets["google_creds"])
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    cliente = gspread.authorize(creds)
    # IMPORTANTE: El nombre aquí debe ser EXACTAMENTE el de tu archivo de Google Sheets
    hoja = cliente.open("Base_Datos_Calificaciones_Panuco").sheet1 
    conexion_exitosa = True
except Exception as e:
    conexion_exitosa = False
    error_msg = str(e)

# --- 3. SISTEMA DE INICIO DE SESIÓN ---
def login():
    st.title("🔒 Acceso al Sistema - ITS Pánuco")
    usuario = st.text_input("Usuario")
    contrasena = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        if usuario == "admin" and contrasena == "panuco123": # Puedes cambiar la contraseña aquí
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
    st.stop()

# --- 4. INTERFAZ PRINCIPAL ---
st.title("📚 Sistema de Calificaciones - ITS Pánuco")

if not conexion_exitosa:
    st.error(f"⚠️ Error al conectar con Google Sheets. Verifica que hayas guardado bien el secreto en Streamlit. Error técnico: {error_msg}")
    st.stop()

# Pestañas
tab_registrar, tab_modificar = st.tabs(["➕ Registrar Calificaciones", "✏️ Ver y Modificar Datos"])

# --- PESTAÑA 1: REGISTRAR ---
with tab_registrar:
    st.header("Ingreso de Calificaciones")
    
    # Usamos un formulario para que no se envíe hasta presionar el botón
    with st.form("formulario_registro"):
        st.subheader("Datos del Alumno")
        col1, col2, col3 = st.columns(3)
        with col1:
            alumno = st.text_input("Nombre del Alumno (Ej. PAREDES ARTEAGA...)")
        with col2:
            semestre = st.selectbox("Semestre", ["1°", "2°", "3°", "4°", "5°", "6°", "7°", "8°", "9°"])
        with col3:
            grupo = st.text_input("Grupo (Ej. E401)")
            
        st.divider()
        st.subheader("Datos de la Asignatura")
        col4, col5 = st.columns(2)
        with col4:
            asignatura = st.text_input("Materia (Ej. DISEÑO DIGITAL)")
        with col5:
            docente = st.text_input("Nombre del Docente")
            
        st.write("Calificaciones por Unidad (Deja en 0 si no hay calificación)")
        cu1, cu2, cu3, cu4, cu5, cu6, cu7 = st.columns(7)
        u1 = cu1.number_input("U1", min_value=0, max_value=100, step=1)
        u2 = cu2.number_input("U2", min_value=0, max_value=100, step=1)
        u3 = cu3.number_input("U3", min_value=0, max_value=100, step=1)
        u4 = cu4.number_input("U4", min_value=0, max_value=100, step=1)
        u5 = cu5.number_input("U5", min_value=0, max_value=100, step=1)
        u6 = cu6.number_input("U6", min_value=0, max_value=100, step=1)
        u7 = cu7.number_input("U7", min_value=0, max_value=100, step=1)
        
        st.divider()
        col6, col7 = st.columns(2)
        with col6:
            actividades = st.text_area("Actividades del P.A.T.")
        with col7:
            fecha = st.date_input("Fecha de registro")
            
        # Botón para enviar
        enviado = st.form_submit_button("Guardar en Google Sheets", type="primary")
        
        if enviado:
            if alumno == "" or asignatura == "":
                st.warning("⚠️ El nombre del alumno y la asignatura son obligatorios.")
            else:
                # Preparamos los datos EXACTAMENTE en el orden de las columnas de tu Excel
                nueva_fila = [alumno, semestre, grupo, asignatura, u1, u2, u3, u4, u5, u6, u7, docente, actividades, str(fecha)]
                
                # Enviamos a Google Sheets
                hoja.append_row(nueva_fila)
                st.success(f"✅ ¡Calificaciones de {asignatura} guardadas correctamente en la nube!")

# --- PESTAÑA 2: MODIFICAR ---
with tab_modificar:
    st.header("Base de Datos Actual")
    st.write("Aquí puedes ver todos los registros. Si editas una celda y presionas 'Actualizar', se cambiará en tu Excel de Google.")
    
    # Descargamos los datos de Google Sheets
    datos = hoja.get_all_records()
    
    if len(datos) > 0:
        df = pd.DataFrame(datos)
        
        # Mostramos la tabla editable
        df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        if st.button("🔄 Actualizar Google Sheets con estos cambios", type="primary"):
            with st.spinner("Actualizando base de datos..."):
                # Borramos todo y reescribimos con los nuevos cambios
                hoja.clear()
                # Preparamos los datos: Primero los encabezados, luego las filas
                datos_nuevos = [df_editado.columns.values.tolist()] + df_editado.values.tolist()
                hoja.update(values=datos_nuevos, range_name="A1")
                st.success("✨ ¡Base de datos actualizada con éxito!")
    else:
        st.info("La base de datos está vacía. Ve a la pestaña de Registrar y guarda tu primera calificación.")
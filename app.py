import streamlit as st
import pandas as pd
from io import BytesIO
# --- Cargar maestro desde Excel ---
@st.cache_data
def load_maestro(file_path="maestro_instalaciones.xlsx"):
   return pd.read_excel(file_path)  # Instalación | Referencia | Descripción | Cantidad
maestro = load_maestro()
st.title("Plantilla de instalaciones")
# --- 1. Selección de Operación ---
operacion = st.selectbox("Operación", ["10", "20", "30", "40"])
# --- 2. Selección de Instalaciones ---
instalaciones = st.multiselect(
   "Selecciona las instalaciones:",
   maestro["Instalación"].unique()
)
# --- 3. Instalación de Agua ---
incluye_agua = st.radio("¿Quieres incluir instalación de agua?", ["No", "Sí"])
agua_cantidad = 0
if incluye_agua == "Sí":
   agua_cantidad = st.number_input("¿Cuántas instalaciones de agua?", min_value=1, value=1)
# --- 4. Técnico ---
tecnico = st.text_input("Técnico que atiende la solicitud")
# --- 5. Fecha requerida ---
fecha_requerida = st.date_input("Fecha de necesidad")
# --- Calcular referencias ---
resultado = pd.DataFrame()
if instalaciones:
   resultado = maestro[maestro["Instalación"].isin(instalaciones)].copy()
   resultado = resultado.groupby(
       ["Referencia", "Descripción"], as_index=False
   )["Cantidad"].sum()
   # Si incluye AGUA, añadir
   if incluye_agua == "Sí":
       agua_refs = maestro[maestro["Instalación"] == "AGUA"].copy()
       agua_refs["Cantidad"] *= agua_cantidad
       resultado = pd.concat([resultado, agua_refs.groupby(
           ["Referencia","Descripción"],as_index=False)["Cantidad"].sum()])
   # Agrupar por referencia final
   resultado = resultado.groupby(["Referencia", "Descripción"], as_index=False)["Cantidad"].sum()
# --- Mostrar editor para revisar y editar ---
if not resultado.empty:
   st.subheader("Revisa, edita o añade referencias")
   # Permitir edición interactiva
   edited_df = st.data_editor(
       resultado,
       num_rows="dynamic",  # Permite añadir filas nuevas
       use_container_width=True,
       key="editable_refs"
   )
   # Botón para generar Excel con lo editado
   if st.button("Generar Excel"):
       final = pd.DataFrame({
           "Operación": [operacion] * len(edited_df),
           "Línea": [(i+1)*10 for i in range(len(edited_df))],
           "Referencia": edited_df["Referencia"],
           "Cantidad": edited_df["Cantidad"],
           "Tecnico": [tecnico] * len(edited_df),
           "Fecha requerida": [str(fecha_requerida) + " 0:00:00"] * len(edited_df)
       })
       output = BytesIO()
       with pd.ExcelWriter(output, engine="openpyxl") as writer:
           final.to_excel(writer, index=False, sheet_name="WO")
       st.download_button(
           label="📥 Descargar Excel",
           data=output.getvalue(),
           file_name="work_order.xlsx",
           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
       )


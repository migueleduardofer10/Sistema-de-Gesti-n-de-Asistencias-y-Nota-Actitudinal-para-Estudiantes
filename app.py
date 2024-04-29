import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os

ts = time.time()
date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
cutoff_time = datetime.strptime("19:35", "%H:%M").time()  # Hora de corte para la asistencia

count = st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")

if count == 0:
    st.write("El contador está en cero")
elif count % 3 == 0 and count % 5 == 0:
    st.write("FizzBuzz")
elif count % 3 == 0:
    st.write("Fizz")
elif count % 5 == 0:
    st.write("Buzz")
else:
    st.write(f"Contador: {count}")

selected_student = st.sidebar.selectbox('Selecciona un estudiante', os.listdir('Attendance'))


try:
    df = pd.read_csv(f"Attendance/{selected_student}")
    df['ENTRY_TIME'] = pd.to_datetime(df['ENTRY_TIME'], errors='coerce', format='%H:%M:%S').dt.time
    
    # Crear la columna 'Status' basada en 'ENTRY_TIME'
    df['Status'] = df['ENTRY_TIME'].apply(lambda x: 'Asistencia' if x < cutoff_time else 'Tardanza')

    # Función para aplicar estilo a las filas completas donde la llegada es tarde
    def highlight_late(row):
        entry_time = row['ENTRY_TIME']
        if pd.isna(entry_time):
            return [''] * len(row)
        return ['background-color: #ffff99' if entry_time >= cutoff_time else '' for _ in row]

    st.dataframe(df.style.apply(highlight_late, axis=1))
except FileNotFoundError:
    st.error(f"No se encontraron datos de asistencia para {date}. Asegúrese de que el sistema esté capturando datos.")
except Exception as e:
    st.error(f"Ocurrió un error: {str(e)}")

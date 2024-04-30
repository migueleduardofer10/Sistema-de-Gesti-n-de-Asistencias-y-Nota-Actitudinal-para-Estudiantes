import streamlit as st
import pandas as pd
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import os

def load_data(student_file):

    base_name = student_file.split('_times')[0]  
    times_path = f"Attendance/{student_file}"
    details_path = f"Attendance/{base_name}_details.csv"

    times_df = pd.read_csv(times_path)
    details_df = pd.read_csv(details_path)
    
    return times_df, details_df

def highlight_late(entry_time, cutoff_time):
    if pd.isna(entry_time):
        return ''
    return 'background-color: #ffff99' if entry_time >= cutoff_time else ''

# Configurar la función de autorefresco de Streamlit
count = st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")

# Lógica de FizzBuzz para el contador de autorefresco
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

st.title("Sistema de Asistencia Estudiantil")

selected_student = st.sidebar.selectbox('Selecciona un estudiante', [f for f in os.listdir('Attendance') if '_times.csv' in f])

try:
    df_times, df_details = load_data(selected_student)
    
    df_times['ENTRY_TIME'] = pd.to_datetime(df_times['ENTRY_TIME'], errors='coerce').dt.time
    df_times['EXIT_TIME'] = pd.to_datetime(df_times['EXIT_TIME'], errors='coerce').dt.time

    cutoff_time = datetime.strptime("19:35", "%H:%M").time()  # Hora de corte para la asistencia

    st.write("Registros de Tiempos:")
    st.dataframe(df_times.style.applymap(lambda x: highlight_late(x, cutoff_time), subset=['ENTRY_TIME']))

    st.write("Detalles del Día:")
    st.markdown(f"**Estado:** {df_details['STATUS'].iat[0]}")
    st.markdown(f"**Puntuación de Actitud:** {df_details['ATTITUDE_SCORE'].iat[0]}")
except FileNotFoundError:
    st.error(f"No se encontraron datos de asistencia. Asegúrate de que el sistema esté capturando datos correctamente.")
except Exception as e:
    st.error(f"Ocurrió un error: {str(e)}")

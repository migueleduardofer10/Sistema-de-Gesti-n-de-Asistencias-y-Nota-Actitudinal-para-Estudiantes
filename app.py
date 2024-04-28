import streamlit as st
import pandas as pd  
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Obtener el tiempo actual y convertirlo a una fecha y hora formateadas
ts = time.time()
date = datetime.fromtimestamp(ts).strftime("%d-%m-%y")
timestamp = datetime.fromtimestamp(ts).strftime("%H:%M-%S")

# Configurar la función de autorefresco de Streamlit
count = st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")

# Lógica de FizzBuzz para el contador de autorefresco
if count == 0: 
    st.write("Count is zero")
elif count % 3 == 0 and count % 5 == 0:
    st.write("FizzBuzz")
elif count % 3 == 0: 
    st.write("Fizz")
elif count % 5 == 0: 
    st.write("Buzz")
else:
    st.write(f"Count: {count}")

# Cargar datos de asistencia del día actual desde un archivo CSV
df = pd.read_csv("Attendance/Attendance_" + date + ".csv")

# Definir la hora de corte para considerar asistencia o tardanza
cutoff_time = datetime.strptime("09:35", "%H:%M").time()

# Añadir una columna de estado basada en la hora de llegada
df['Time'] = pd.to_datetime(df['TIME'], format='%H:%M-%S').dt.time
df['Status'] = df['Time'].apply(lambda x: 'Asistencia' if x < cutoff_time else 'Tardanza')

# Función para aplicar estilo a las filas completas donde la llegada es tarde
def highlight_late(row):
    # Si la hora de llegada en la fila es tardía, aplicar el estilo a toda la fila
    if row['Time'] >= cutoff_time:
        return ['background-color: #ffff99'] * len(row)  # Un tono de amarillo más suave
    else:
        return [''] * len(row)

# Aplicar el estilo al DataFrame y mostrarlo en la aplicación
st.dataframe(df.style.apply(highlight_late, axis=1))

"""
import streamlit as st
import pandas as pd  
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

ts = time.time()
date = datetime.fromtimestamp(ts).strftime("%d-%m-%y")
timestamp = datetime.fromtimestamp(ts).strftime("%H:%M-%S")

count = st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")

if count == 0: 
    st.write("Count is zero")
elif count % 3 == 0 and count % 5 == 0:
    st.write("FizzBuzz")
elif count % 3 == 0: 
    st.write("Fizz")
elif count % 5 == 0: 
    st.write("Buzz")
else:
    st.write(f"Count: {count}")

df = pd.read_csv("Attendance/Attendance_" + date + ".csv")

cutoff_time = datetime.strptime("00:10", "%H:%M").time()

df['Time'] = pd.to_datetime(df['TIME'], format='%H:%M-%S').dt.time
df['Status'] = df['Time'].apply(lambda x: 'Asistencia' if x < cutoff_time else 'Tardanza')

def highlight_late(arrival_times):
    return ['background-color: yellow' if time >= cutoff_time else '' for time in arrival_times]

st.dataframe(df.style.apply(highlight_late, subset=['Time']))
"""
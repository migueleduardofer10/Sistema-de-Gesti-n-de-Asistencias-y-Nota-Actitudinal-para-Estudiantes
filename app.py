import streamlit as st
import pandas as pd
import os
from datetime import datetime
import subprocess
from functools import partial
import re 

def load_data(student_file):
    base_name = student_file.split('_times')[0]
    times_path = f"Attendance/{student_file}"
    details_path = f"Attendance/{base_name}_details.csv"
    times_df = pd.read_csv(times_path)
    details_df = pd.read_csv(details_path)
    return times_df, details_df


def run_script(script_name, course_name, session_date):
    try:
        # Format the date and execute the script
        subprocess.run(['python', script_name, course_name, session_date.strftime('%Y-%m-%d')], check=True)
        st.success(f"El proceso para {script_name} ha comenzado con éxito.")
    except subprocess.CalledProcessError as e:
        st.error(f"Falló la ejecución de {script_name}: {e}")
    except Exception as e:
        st.error(f"Error desconocido al ejecutar {script_name}: {str(e)}")

def setup_course_page():
    st.title("Configuración del Curso")
    with st.form("course_form"):
        class_name = st.text_input("Nombre del Curso")
        start_date = st.date_input("Fecha de Inicio")
        end_date = st.date_input("Fecha Fin")
        submitted = st.form_submit_button("Guardar Configuración del Curso")
    if submitted:
        course_info = {
            'class_name': class_name,
            'start_date': str(start_date),
            'end_date': str(end_date)
        }
        if 'courses' not in st.session_state:
            st.session_state['courses'] = []
        st.session_state['courses'].append(course_info)
        st.success(f"Configuración guardada para el curso {class_name} desde {start_date} hasta {end_date}")

        # Botón para iniciar el proceso de agregar caras al curso
        if st.button("Agregar Caras al Curso"):
            run_script('add_faces.py', class_name, start_date)


def list_files(course_name, date):
    session_date_str = date.strftime('%Y-%m-%d')
    folder_path = "Attendance"
    if not os.path.exists(folder_path):
        st.sidebar.write(f"Directorio no encontrado: {folder_path}")
        return [], []
    all_files = os.listdir(folder_path)
    detail_files = [f for f in all_files if f.startswith(f"{course_name}_{session_date_str}") and "_details.csv" in f]
    time_files = [f for f in all_files if f.startswith(f"{course_name}_{session_date_str}") and "_times.csv" in f]
    return detail_files, time_files

def view_file(file_path):
    df = pd.read_csv(f"Attendance/{file_path}")
    st.write(df)
    
def session_page():
    st.title("Registro de Sesión")
    if 'courses' in st.session_state and st.session_state['courses']:
        course_list = [course['class_name'] for course in st.session_state['courses']]
        selected_course = st.selectbox('Selecciona un curso', course_list)
        with st.form("session_form"):
            session_date = st.date_input("Fecha de la Sesión")
            session_start = st.time_input("Hora de Inicio")
            session_end = st.time_input("Hora de Fin")
            session_submit = st.form_submit_button("Registrar Sesión")
        if session_submit:
            session_info = {
                'date': str(session_date),
                'start': str(session_start),
                'end': str(session_end)
            }
            if 'sessions' not in st.session_state:
                st.session_state['sessions'] = {}
            if selected_course not in st.session_state['sessions']:
                st.session_state['sessions'][selected_course] = []
            st.session_state['sessions'][selected_course].append(session_info)
            st.success(f"Sesión registrada para {selected_course} el {session_date} de {session_start} a {session_end}")
            # Setup button with partial to avoid lambda issues and ensure correct parameter passing
            button_callback = partial(run_script, 'test.py', selected_course, session_date)
            st.button("Iniciar Asistencia", on_click=button_callback)


def main():
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a", ["Configuración del Curso", "Registro de Sesión", "Visualizar Archivos"])

    if page == "Configuración del Curso":
        setup_course_page()
    elif page == "Registro de Sesión":
        session_page()
    elif page == "Visualizar Archivos":
        if 'courses' in st.session_state and st.session_state['courses']:
            course_list = [course['class_name'] for course in st.session_state['courses']]
            selected_course = st.selectbox('Selecciona un Curso para visualizar archivos', course_list)
            selected_date = st.date_input("Selecciona la fecha del curso")
            detail_files, time_files = list_files(selected_course, selected_date)
            
            if detail_files or time_files:
                file_type = st.radio("Tipo de Archivo", ("Detalles", "Tiempos"))
                selected_file_list = detail_files if file_type == "Detalles" else time_files
                selected_file = st.selectbox('Selecciona un archivo', selected_file_list)
                if st.button('Cargar Archivo'):
                    view_file(selected_file)
            else:
                st.error("No se encontraron archivos para este curso y fecha.")

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import subprocess

def load_data(student_file):
    base_name = student_file.split('_times')[0]
    times_path = f"Attendance/{student_file}"
    details_path = f"Attendance/{base_name}_details.csv"
    times_df = pd.read_csv(times_path)
    details_df = pd.read_csv(details_path)
    return times_df, details_df

def run_script(script_name):
    try:
        subprocess.run(['python', script_name], check=True)
        st.success(f"El proceso para {script_name} ha comenzado con éxito.")
    except subprocess.CalledProcessError as e:
        st.error(f"Falló la ejecución de {script_name}: {e}")

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
    if 'courses' in st.session_state and st.session_state['courses']:
        st.button("Agregar Caras al Curso", on_click=lambda: run_script('add_faces.py'))

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
            st.button("Iniciar Asistencia", on_click=lambda: run_script('test.py'))

def main():
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a", ["Configuración del Curso", "Registro de Sesión"])

    if page == "Configuración del Curso":
        setup_course_page()
    elif page == "Registro de Sesión":
        session_page()

if __name__ == "__main__":
    main()

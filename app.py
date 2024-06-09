import streamlit as st
import pandas as pd
import os
from datetime import datetime
import subprocess
from functools import partial
from firebase_config import db
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
from twilio.rest import Client
import time

def load_data(student_file):
    base_name = student_file.split('_times')[0]
    times_path = f"Attendance/{student_file}"
    details_path = f"Attendance/{base_name}_details.csv"
    times_df = pd.read_csv(times_path)
    details_df = pd.read_csv(details_path)
    return times_df, details_df


def run_script(script_name, course_name=None, session_date=None):
    try:
        command = ['python', script_name]
        if course_name and session_date:
            # Añadimos los argumentos necesarios para el script de test.py
            command.extend([course_name, session_date.strftime('%Y-%m-%d')])
        # Ejecutar el comando completo
        subprocess.run(command, check=True)
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
        # Guardar en Firestore
        db.collection('courses').add(course_info)
        st.success(f"Configuración guardada para el curso {class_name} desde {start_date} hasta {end_date}")
        st.button("Agregar caras al curso", on_click=lambda: run_script('add_faces.py'))

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
    
def send_whatsapp_message(parent_name, parent_phone, report_content, student_name):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=f"Hola {parent_name}, le envío el reporte de entradas y salidas de su hijo {student_name} y su respectiva nota actitudinal:\n\n{report_content}",
            to=f"whatsapp:{parent_phone}"
        )
       
        return message.sid
    except Exception as e:
        st.error(f"Error al enviar el mensaje de WhatsApp: {e}")
        return None
    
def handle_send_report(parent_name, parent_phone, report_content, student_name):
    placeholder = st.empty()
    if not parent_name or not parent_phone:
        st.error("Por favor, complete todos los campos.")
    else:
        full_parent_phone = f"+51{parent_phone}"
        message_sid = send_whatsapp_message(parent_name, full_parent_phone, report_content, student_name)
        if message_sid:
            placeholder.success(f"Reporte enviado a {parent_name} al número {full_parent_phone}. (SID del mensaje: {message_sid})")
            time.sleep(2)
            placeholder.empty()
        else:
            placeholder.error("Error al enviar el mensaje de WhatsApp.")
            time.sleep(2)
            placeholder.empty()
            
def generate_semestral_report_for_student(course_name, student_name):
    folder_path = "Attendance"
    all_files = os.listdir(folder_path)
    detail_files = [f for f in all_files if f.startswith(course_name) and "_details.csv" in f and student_name in f]

    all_scores = []

    for file in detail_files:
        details_df = pd.read_csv(os.path.join(folder_path, file))
        if 'ATTITUDE_SCORE' in details_df.columns:
            all_scores.extend(details_df['ATTITUDE_SCORE'].tolist())

    if all_scores:
        semestral_average = sum(all_scores) / len(all_scores)
        st.write(f"Promedio actitudinal semestral para {student_name} en {course_name}: {semestral_average:.2f}")
    else:
        st.write(f"No se encontraron datos de puntajes actitudinales para {student_name} en el curso {course_name}")

def generate_semestral_report_for_course(course_name):
    folder_path = "Attendance"
    all_files = os.listdir(folder_path)
    detail_files = [f for f in all_files if f.startswith(course_name) and "_details.csv" in f]

    student_scores = {}

    for file in detail_files:
        student_name = file.split('_')[-2]  # Extraer el nombre del estudiante del nombre del archivo
        details_df = pd.read_csv(os.path.join(folder_path, file))
        if 'ATTITUDE_SCORE' in details_df.columns:
            if student_name not in student_scores:
                student_scores[student_name] = []
            student_scores[student_name].extend(details_df['ATTITUDE_SCORE'].tolist())

    if student_scores:
        st.write(f"Promedios actitudinales semestrales para el curso {course_name}:")
        for student_name, scores in student_scores.items():
            semestral_average = sum(scores) / len(scores)
            st.write(f"{student_name}: {semestral_average:.2f}")
    else:
        st.write(f"No se encontraron datos de puntajes actitudinales para el curso {course_name}")


def session_page():
    st.title("Registro de Sesión")
    courses_ref = db.collection('courses')
    courses = courses_ref.stream()
    courses_data = {course.id: course.to_dict() for course in courses}

    if courses_data:
        course_list = [course['class_name'] for course in courses_data.values()]
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
            # Actualizar curso en Firestore
            for course_id, course in courses_data.items():
                if course['class_name'] == selected_course:
                    if 'sessions' not in course:
                        course['sessions'] = []
                    course['sessions'].append(session_info)
                    courses_ref.document(course_id).set(course)
                    break

            st.success(f"Sesión registrada para {selected_course} el {session_date} de {session_start} a {session_end}")

            button_callback = partial(run_script, 'test.py', selected_course, session_date)
            st.button("Iniciar Asistencia", on_click=button_callback)
    else:
        st.error("No se ha configurado ningún curso aún.")


def main():
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a", ["Configuración del Curso", "Registro de Sesión", "Reporte Actitudinal Diario", "Reporte Semestral del Curso por Estudiante", "Reporte Semestral General del Curso"])

    if page == "Configuración del Curso":
        setup_course_page()
    elif page == "Registro de Sesión":
        session_page()

    elif page == "Reporte Actitudinal Diario":
        st.title("Reporte actitudinal diario")
        courses_ref = db.collection('courses')
        courses = courses_ref.stream()
        courses_data = {course.id: course.to_dict() for course in courses}

        if courses_data:
            course_list = [course['class_name'] for course in courses_data.values()]
            selected_course = st.selectbox('Selecciona un Curso para visualizar el reporte actitudinal diario', course_list)
            selected_date = st.date_input("Selecciona la fecha del curso")
            detail_files, time_files = list_files(selected_course, selected_date)

            if detail_files or time_files:
                file_type = st.radio("Tipo de Archivo", ("Reporte de Entradas y Salidas", "Reporte Actitudinal Diario"))
                selected_file_list = detail_files if file_type == "Reporte Actitudinal Diario" else time_files
                selected_file = st.selectbox('Selecciona un archivo', selected_file_list)
                if st.button('Cargar Archivo'):
                    view_file(selected_file)
                    student_name = selected_file.split('_')[2]
                    report_content = open(f"Attendance/{selected_file}").read()

                    def on_submit():
                        parent_name = st.session_state["parent_name"]
                        parent_phone = st.session_state["parent_phone"]
                        handle_send_report(parent_name, parent_phone, report_content, student_name)

                    with st.form("send_report_form"):
                        parent_name = st.text_input("Nombre del Padre", key="parent_name")
                        parent_phone = st.text_input("Teléfono del Padre", key="parent_phone", placeholder="960904256")
                        st.form_submit_button(label='Enviar', on_click=on_submit)

            else:
                st.error("No se encontraron archivos para este curso y fecha.")
        else:
            st.error("No hay cursos configurados.")
            
    elif page == "Reporte Semestral del Curso por Estudiante":
        st.title("Reporte semestral del curso por estudiante")
        # Cargar los nombres de los cursos desde Firestore
        courses_ref = db.collection('courses')
        courses = courses_ref.stream()
        courses_data = {course.id: course.to_dict() for course in courses}

        if courses_data:
            course_list = [course['class_name'] for course in courses_data.values()]
            selected_course = st.selectbox('Selecciona un Curso para generar el reporte semestral por alumno', course_list)
            student_name = st.text_input("Nombre del Estudiante")
            if st.button('Generar Reporte'):
                generate_semestral_report_for_student(selected_course, student_name)
        else:
            st.error("No hay cursos configurados.")
    elif page == "Reporte Semestral General del Curso":
        st.title("Reporte semestral general del curso")
        # Cargar los nombres de los cursos desde Firestore
        courses_ref = db.collection('courses')
        courses = courses_ref.stream()
        courses_data = {course.id: course.to_dict() for course in courses}

        if courses_data:
            course_list = [course['class_name'] for course in courses_data.values()]
            selected_course = st.selectbox('Selecciona un Curso para generar el reporte semestral', course_list)
            if st.button('Generar Reporte'):
                generate_semestral_report_for_course(selected_course)
        else:
            st.error("No hay cursos configurados.")

if __name__ == "__main__":
    main()

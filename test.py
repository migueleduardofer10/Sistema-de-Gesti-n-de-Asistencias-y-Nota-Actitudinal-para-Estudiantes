import sys
import cv2
import pandas as pd
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime, timedelta
from win32com.client import Dispatch
from sklearn.neighbors import KNeighborsClassifier

def speak(text):
    speaker = Dispatch("SAPI.SpVoice")
    speaker.Speak(text)

def check_and_create_files(course_name, session_date, student_name):
    session_date_str = session_date.strftime('%Y-%m-%d')
    folder_path = f"Attendance/{course_name}_{session_date_str}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    attendance_filepath = f"{folder_path}/{student_name}_times.csv"
    details_filepath = f"{folder_path}/{student_name}_details.csv"

    if not os.path.isfile(attendance_filepath):
        with open(attendance_filepath, 'w', newline='') as csvfile:
            fieldnames = ['ENTRY_TIME', 'EXIT_TIME', 'DIFF_TIME', 'DISCOUNTED_POINTS']
            writer = pd.DataFrame(columns=fieldnames)
            writer.to_csv(csvfile, index=False)

    if not os.path.isfile(details_filepath):
        with open(details_filepath, 'w', newline='') as csvfile:
            fieldnames = ['STATUS', 'ATTITUDE_SCORE']
            writer = pd.DataFrame(columns=fieldnames)
            writer.to_csv(csvfile, index=False)

    return attendance_filepath, details_filepath

def log_attendance(course_name, session_date, student_name, timestamp, is_entry):
    attendance_filepath, details_filepath = check_and_create_files(course_name, session_date, student_name)
    df_times = pd.read_csv(attendance_filepath)
    df_details = pd.read_csv(details_filepath) if os.path.getsize(details_filepath) > 0 else pd.DataFrame(columns=['STATUS', 'ATTITUDE_SCORE'])

    if is_entry:
        discounted_points = 0
        if not df_times.empty and pd.notna(df_times['EXIT_TIME'].iloc[-1]):
            previous_exit_time = df_times['EXIT_TIME'].iloc[-1]
            diff_time = (datetime.strptime(timestamp, "%H:%M:%S") - datetime.strptime(previous_exit_time, "%H:%M:%S")).seconds // 60
            if diff_time > 30:
                discounted_points = diff_time // 30

            df_times.at[len(df_times) - 1, 'DIFF_TIME'] = diff_time
            df_times.at[len(df_times) - 1, 'DISCOUNTED_POINTS'] = discounted_points

        new_entry = {'ENTRY_TIME': timestamp, 'EXIT_TIME': None, 'DIFF_TIME': None, 'DISCOUNTED_POINTS': None}
        df_times = df_times.append(new_entry, ignore_index=True)
        df_times.to_csv(attendance_filepath, index=False)

        cutoff_time = datetime.strptime("07:00", "%H:%M").time()
        current_time = datetime.strptime(timestamp, "%H:%M:%S").time()
        status = "Asistencia" if current_time <= cutoff_time else "Tardanza"

        if not df_details.empty:
            last_score = df_details['ATTITUDE_SCORE'].iloc[-1]
            already_penalized = df_details['STATUS'].eq('Tardanza').any()
        else:
            last_score = 20
            already_penalized = False

        tardiness_penalty = 4 if status == "Tardanza" and not already_penalized else 0
        new_score = max(0, last_score - tardiness_penalty - discounted_points)
        new_detail = {'STATUS': status, 'ATTITUDE_SCORE': new_score}
        df_details = df_details.append(new_detail, ignore_index=True)
        df_details.to_csv(details_filepath, index=False)
        
        speak("Entrada registrada.")

    else:
        if not df_times.empty and pd.isna(df_times['EXIT_TIME'].iloc[-1]):
            df_times.at[len(df_times) - 1, 'EXIT_TIME'] = timestamp
            df_times.to_csv(attendance_filepath, index=False)
            speak("Salida registrada.")
        else:
            speak("No puedes registrar una salida sin una entrada previa.")

if __name__ == "__main__":
    course_name = sys.argv[1]
    session_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    # Assume that the script runs continuously to monitor a live video feed.
    video = cv2.VideoCapture(0)
    facedetect = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')

    with open('data/names.pkl', 'rb') as f:
        LABELS = pickle.load(f)
    with open('data/faces_data.pkl', 'rb') as f:
        FACES = pickle.load(f)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(FACES, LABELS)
    imgBackground = cv2.imread("background2.jpg")

    while True:
        ret, frame = video.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facedetect.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            crop_img = frame[y:y+h, x:x+w]
            resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
            student_name = str(knn.predict(resized_img)[0])
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_attendance(course_name, session_date, student_name, timestamp, is_entry=True)

        if ret:
            cv2.imshow("Attendance Monitoring", imgBackground)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

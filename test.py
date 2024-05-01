from sklearn.neighbors import KNeighborsClassifier
import cv2
import pandas as pd
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime, timedelta


from win32com.client import Dispatch

def speak(text):
    from win32com.client import Dispatch
    speaker = Dispatch("SAPI.SpVoice")
    speaker.Speak(text)

def check_and_create_files(student_name):
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_filepath = f"Attendance/{student_name}_{today}_times.csv"
    details_filepath = f"Attendance/{student_name}_{today}_details.csv"

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

def log_attendance(student_name, timestamp, is_entry):
    attendance_filepath, details_filepath = check_and_create_files(student_name)
    df_times = pd.read_csv(attendance_filepath)
    df_details = pd.read_csv(details_filepath) if os.path.getsize(details_filepath) > 0 else pd.DataFrame(columns=['STATUS', 'ATTITUDE_SCORE'])

    if is_entry:
        discounted_points = 0
        if not df_times.empty and pd.notna(df_times['EXIT_TIME'].iloc[-1]):
            previous_exit_time = df_times['EXIT_TIME'].iloc[-1]
            diff_time = (datetime.strptime(timestamp, "%H:%M:%S") - datetime.strptime(previous_exit_time, "%H:%M:%S")).seconds // 60
            if diff_time > 30:
                discounted_points = diff_time // 30  # Apply discount only for time over 30 minutes

            df_times.at[len(df_times) - 1, 'DIFF_TIME'] = diff_time
            df_times.at[len(df_times) - 1, 'DISCOUNTED_POINTS'] = discounted_points

        new_entry = {'ENTRY_TIME': timestamp, 'EXIT_TIME': None, 'DIFF_TIME': None, 'DISCOUNTED_POINTS': None}
        df_times = df_times._append(new_entry, ignore_index=True)
        df_times.to_csv(attendance_filepath, index=False)

        cutoff_time = datetime.strptime("07:00", "%H:%M").time()
        current_time = datetime.strptime(timestamp, "%H:%M:%S").time()
        status = "Asistencia" if current_time <= cutoff_time else "Tardanza"

        if not df_details.empty:
            last_score = df_details['ATTITUDE_SCORE'].iloc[-1]
            already_penalized = df_details['STATUS'].eq('Tardanza').any()
        else:
            last_score = 20  # Initial score for the first entry
            already_penalized = False

        # Apply tardiness penalty only once
        tardiness_penalty = 4 if status == "Tardanza" and not already_penalized else 0
        new_score = max(0, last_score - tardiness_penalty - discounted_points)
        df_details = df_details._append({'STATUS': status, 'ATTITUDE_SCORE': new_score}, ignore_index=True)
        df_details.to_csv(details_filepath, index=False)
        
        speak("Entrada registrada.")

    else:
        if not df_times.empty and pd.isna(df_times['EXIT_TIME'].iloc[-1]):
            df_times.at[len(df_times) - 1, 'EXIT_TIME'] = timestamp
            df_times.to_csv(attendance_filepath, index=False)
            speak("Salida registrada.")
        else:
            speak("No puedes registrar una salida sin una entrada previa.")


def calculate_status_and_score(entry_time, exit_time):
    entry_dt = datetime.strptime(entry_time, "%H:%M:%S")
    exit_dt = datetime.strptime(exit_time, "%H:%M:%S")
    initial_score = 20
    cutoff_time = datetime.strptime("21:05", "%H:%M").time()
    if entry_dt.time() > cutoff_time:
        initial_score -= 4  # Tardanza
    diff_time = int((exit_dt - entry_dt).total_seconds() / 60)
    extra_time = max(0, (exit_dt - entry_dt - timedelta(minutes=30)).total_seconds() / 1800)
    score = max(0, initial_score - int(extra_time))
    discounted_points = initial_score - score
    status = 'Asistencia' if entry_dt.time() <= cutoff_time else 'Tardanza'
    return status, score, diff_time, discounted_points

video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')


with open('data/names.pkl', 'rb') as f:
    LABELS=pickle.load(f)

with open('data/faces_data.pkl','rb') as f:
    FACES=pickle.load(f)

knn=KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)


imgBackground=cv2.imread("background2.jpg")

COL_NAMES = ['NAME', 'ENTRY_TIME', 'EXIT_TIME', 'ATTITUDE_SCORE']


while True:

    ret, frame = video.read()
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces=facedetect.detectMultiScale(gray, 1.3, 5)

    for(x,y,w,h) in faces:
        crop_img = frame[y: y+h, x:x+w, :]
        resized_img = cv2.resize(crop_img, (50,50)).flatten().reshape(1, -1)
        output=knn.predict(resized_img)
        ts=time.time()
        date=datetime.fromtimestamp(ts).strftime("%y-%m-%d")
        timestamp=datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        exist=os.path.isfile("Attendance/Attendance_" + date + ".csv")
        cv2.rectangle(frame, (x,y), (x+w, y+h), (39,32,0), 2)
        cv2.rectangle(frame, (x,y-40), (x+w, y), (39,32,0), -1)
        cv2.putText(frame, str(output[0]), (x,y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255,255), 1)
        cv2.rectangle(frame,(x,y), (x+w, y+h), (39,32,0), 1)
        attendance=[str(output[0]), str(timestamp)]

    
    imgBackground[162:162 + 480, 55:55 + 640] = frame

    if ret:
        cv2.imshow("frame", imgBackground)
    

    k = cv2.waitKey(1)
    if k == ord('e'): 
        log_attendance(str(output[0]), timestamp, is_entry=True)
    elif k == ord('x'): 
        log_attendance(str(output[0]), timestamp, is_entry=False)
    elif k == ord('q'):
        break


video.release()
cv2.destroyAllWindows()
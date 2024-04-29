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

def check_and_create_student_file(student_name):
    filepath = f"Attendance/{student_name}_{datetime.now().strftime('%Y-%m-%d')}.csv"
    if not os.path.isfile(filepath):
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['ENTRY_TIME', 'EXIT_TIME', 'STATUS', 'ATTITUDE_SCORE']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    return filepath

def log_attendance(student_name, timestamp, is_entry):
    filepath = check_and_create_student_file(student_name)
    df = pd.read_csv(filepath)
    if is_entry:
        if df.empty or pd.notna(df['EXIT_TIME'].iloc[-1]):
            # Permite nueva entrada si el dataframe está vacío o la última salida está registrada
            new_data = {'ENTRY_TIME': timestamp, 'EXIT_TIME': None, 'STATUS': '', 'ATTITUDE_SCORE': 20}
            df = df._append(new_data, ignore_index=True)
            df.to_csv(filepath, index=False)
            speak("Entrada registrada.")
        else:
            speak("No puedes registrar una entrada sin haber registrado una salida.")
    else:
        if not df.empty and pd.isna(df['EXIT_TIME'].iloc[-1]):
            # Registra la salida si la última entrada no tiene salida
            df.at[len(df)-1, 'EXIT_TIME'] = timestamp
            df.at[len(df)-1, 'STATUS'], df.at[len(df)-1, 'ATTITUDE_SCORE'] = calculate_status_and_score(df.at[len(df)-1, 'ENTRY_TIME'], timestamp)
            df.to_csv(filepath, index=False)
            speak("Salida registrada.")
        else:
            speak("No puedes registrar una salida sin una entrada previa.")

def calculate_status_and_score(entry_time, exit_time):
    entry_dt = datetime.strptime(entry_time, "%H:%M:%S")
    exit_dt = datetime.strptime(exit_time, "%H:%M:%S")
    initial_score = 20
    cutoff_time = datetime.strptime("08:00", "%H:%M").time()
    if entry_dt.time() > cutoff_time:
        initial_score -= 4  # Tardanza
    extra_time = max(0, (exit_dt - entry_dt - timedelta(minutes=30)).total_seconds() / 1800)
    score = max(0, initial_score - int(extra_time))
    status = 'Asistencia' if entry_dt.time() <= cutoff_time else 'Tardanza'
    return status, score


video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier('data/haarcascade_frontalface_default.xml')


with open('data/names.pkl', 'rb') as f:
    LABELS=pickle.load(f)

with open('data/faces_data.pkl','rb') as f:
    FACES=pickle.load(f)

knn=KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)


imgBackground=cv2.imread("background.png")

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
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 1)
        cv2.rectangle(frame, (x,y), (x+w, y+h), (50,50,255), 2)
        cv2.rectangle(frame, (x,y-40), (x+w, y), (50,50,255), -1)
        cv2.putText(frame, str(output[0]), (x,y-15), cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255,255), 1)
        cv2.rectangle(frame,(x,y), (x+w, y+h), (50,50,255), 1)
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